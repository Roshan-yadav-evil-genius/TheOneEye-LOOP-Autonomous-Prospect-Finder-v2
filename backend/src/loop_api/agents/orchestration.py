import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from loop_api.agents.brain import BrainMemoryService
from loop_api.agents.factory import (
    company_finder_agent_scope,
    contact_finder_agent_scope,
)
from loop_api.agents.model_provider import DiscoveryModel
from loop_api.agents.runtime import (
    build_company_effort_prefix,
    build_contact_effort_prefix,
    build_role_thread_id,
)
from loop_api.agents.usage import apply_usage
from loop_api.application.loop_service import DomainError, LoopService, utcnow
from loop_api.browser.pool import BrowserPool
from loop_api.contracts.domain import (
    BlacklistProspectRequest,
    RegisterCompanyRequest,
    RegisterContactRequest,
)
from loop_api.core.config import get_settings
from loop_api.observability.telemetry import AGENT_EFFORTS
from loop_api.persistence import models


class CompanyFinderEffort:
    def __init__(self, session: AsyncSession, model: DiscoveryModel) -> None:
        self.session = session
        self.model = model

    async def execute(self, strategy_id: str) -> models.AgentRun:
        service = LoopService(self.session)
        bundle = await service.bundle(strategy_id)
        strategy = await service.get_strategy(strategy_id)
        strategy.company_effort_seq += 1
        prefix = build_company_effort_prefix(
            strategy.product_id, strategy.id, strategy.company_effort_seq
        )
        thread_id = build_role_thread_id(effort_prefix=prefix, role_suffix="company_finder")
        run = models.AgentRun(
            product_id=strategy.product_id,
            sales_strategy_id=strategy.id,
            agent_role="company_finder",
            effort_prefix=prefix,
            primary_thread_id=thread_id,
            attempt_iteration=strategy.company_effort_seq,
            child_thread_ids=[
                build_role_thread_id(effort_prefix=prefix, role_suffix="browser_agent"),
                build_role_thread_id(effort_prefix=prefix, role_suffix="company_finder_brain"),
            ],
        )
        self.session.add(run)
        self.session.add(
            models.ProcessLog(
                sales_strategy_id=strategy_id,
                role="company-finder",
                level="info",
                event_code="effort_started",
                message=f"Started {prefix}",
            )
        )
        await self.session.commit()
        memory = await BrainMemoryService(self.session).recall(
            strategy_id=strategy_id,
            agent_type="company_finder",
            query=strategy.name,
        )
        prompt = json.dumps(
            {
                "sales_strategy_bundle": bundle.model_dump(mode="json"),
                "brain_recall": [item.content for item in memory],
                "instruction": "Return one JSON company decision or action=no_candidate.",
            }
        )
        try:
            if get_settings().model_provider != "deterministic":
                pool = BrowserPool(self.session)
                lease = await pool.acquire(prefix)
                try:
                    async with company_finder_agent_scope(
                        self.session, strategy_id, prefix
                    ) as (graph, config):
                        await graph.ainvoke(
                            {"messages": [{"role": "user", "content": prompt}]},
                            config,
                        )
                finally:
                    await pool.release(lease.id, prefix)
            else:
                decision = await self.model.decide(prompt)
                if decision.get("action") == "register_company":
                    result = await service.register_company(
                        strategy_id,
                        RegisterCompanyRequest.model_validate(decision["company"]),
                        thread_id=thread_id,
                    )
                    run.company_id = result.company_id
                apply_usage(run, {"prompt_tokens": 0, "completion_tokens": 0})
            run.status = "completed"
            run.completed_at = utcnow()
            AGENT_EFFORTS.labels("company-finder", "completed").inc()
            self.session.add(
                models.ProcessLog(
                    sales_strategy_id=strategy_id,
                    role="company-finder",
                    level="info",
                    event_code="effort_completed",
                    message=f"Completed {prefix}",
                )
            )
            state = await self.session.scalar(
                select(models.AgentProcessState).where(
                    models.AgentProcessState.sales_strategy_id == strategy_id,
                    models.AgentProcessState.role == "company-finder",
                )
            )
            if state:
                state.heartbeat_at = utcnow()
                if await service.companies_registered(strategy_id) >= strategy.target_companies:
                    state.actual_state = state.desired_state = "stopped"
            await self.session.commit()
        except Exception as exc:
            AGENT_EFFORTS.labels("company-finder", "failed").inc()
            run.status = "failed"
            run.completed_at = utcnow()
            state = await self.session.scalar(
                select(models.AgentProcessState).where(
                    models.AgentProcessState.sales_strategy_id == strategy_id,
                    models.AgentProcessState.role == "company-finder",
                )
            )
            if state:
                state.actual_state = "error"
                state.last_error = str(exc)
            self.session.add(
                models.ProcessLog(
                    sales_strategy_id=strategy_id,
                    role="company-finder",
                    level="error",
                    event_code="effort_failed",
                    message=str(exc),
                )
            )
            await self.session.commit()
            raise
        return run


class ContactFinderEffort:
    def __init__(self, session: AsyncSession, model: DiscoveryModel) -> None:
        self.session = session
        self.model = model

    async def _next_company(self, strategy_id: str) -> models.SalesStrategyCompany:
        row = await self.session.scalar(
            select(models.SalesStrategyCompany)
            .where(
                models.SalesStrategyCompany.sales_strategy_id == strategy_id,
                models.SalesStrategyCompany.is_blacklisted.is_(False),
                models.SalesStrategyCompany.funnel_stage.in_(
                    ("company_validated", "finding_contacts", "contacts_batch_done")
                ),
                models.SalesStrategyCompany.contacts_target > 0,
            )
            .order_by(models.SalesStrategyCompany.validated_at)
        )
        if not row:
            raise DomainError("contact_queue_empty", "No validated company has open contact quota.")
        if (
            await LoopService(self.session).contacts_registered(strategy_id, row.company_id)
            >= row.contacts_target
        ):
            raise DomainError("contact_queue_empty", "No validated company has open contact quota.")
        return row

    async def execute(self, strategy_id: str) -> models.AgentRun:
        service = LoopService(self.session)
        strategy = await service.get_strategy(strategy_id)
        company_link = await self._next_company(strategy_id)
        company_link.contact_effort_seq += 1
        prefix = build_contact_effort_prefix(
            strategy.product_id,
            strategy.id,
            company_link.sales_strategy_attempt_at_register,
            company_link.company_id,
            company_link.contact_effort_seq,
        )
        thread_id = build_role_thread_id(effort_prefix=prefix, role_suffix="contact_finder")
        run = models.AgentRun(
            product_id=strategy.product_id,
            sales_strategy_id=strategy.id,
            company_id=company_link.company_id,
            agent_role="contact_finder",
            effort_prefix=prefix,
            primary_thread_id=thread_id,
            attempt_iteration=company_link.sales_strategy_attempt_at_register,
            contact_attempt_iteration=company_link.contact_effort_seq,
            child_thread_ids=[
                build_role_thread_id(effort_prefix=prefix, role_suffix="browser_agent"),
                build_role_thread_id(effort_prefix=prefix, role_suffix="contact_finder_brain"),
            ],
        )
        self.session.add(run)
        self.session.add(
            models.ProcessLog(
                sales_strategy_id=strategy_id,
                role="contact-finder",
                level="info",
                event_code="effort_started",
                message=f"Started {prefix}",
            )
        )
        company_link.funnel_stage = "finding_contacts"
        company_link.prospect_queue_status = "in_progress"
        await self.session.commit()
        prompt = json.dumps(
            {
                "bundle": (await service.bundle(strategy_id)).model_dump(mode="json"),
                "company": (
                    await service.company_detail(strategy_id, company_link.company_id)
                ).model_dump(mode="json"),
                "instruction": "Return register_contact, blacklist_prospect, or no_candidate JSON.",
            }
        )
        try:
            if get_settings().model_provider != "deterministic":
                pool = BrowserPool(self.session)
                lease = await pool.acquire(prefix)
                try:
                    async with contact_finder_agent_scope(
                        self.session, strategy_id, company_link.company_id, prefix
                    ) as (graph, config):
                        await graph.ainvoke(
                            {"messages": [{"role": "user", "content": prompt}]},
                            config,
                        )
                finally:
                    await pool.release(lease.id, prefix)
            else:
                decision: dict[str, Any] = await self.model.decide(prompt)
                action = decision.get("action")
                if action == "register_contact":
                    result = await service.register_contact(
                        strategy_id,
                        company_link.company_id,
                        RegisterContactRequest.model_validate(decision["contact"]),
                        thread_id=thread_id,
                    )
                    run.sales_strategy_prospect_id = (
                        result.sales_strategy_prospect_id
                    )
                elif action == "blacklist_prospect":
                    await service.blacklist_prospect(
                        strategy_id,
                        company_link.company_id,
                        BlacklistProspectRequest.model_validate(decision["prospect"]),
                    )
                apply_usage(run, {"prompt_tokens": 0, "completion_tokens": 0})
            run.status = "completed"
            run.completed_at = utcnow()
            AGENT_EFFORTS.labels("contact-finder", "completed").inc()
            self.session.add(
                models.ProcessLog(
                    sales_strategy_id=strategy_id,
                    role="contact-finder",
                    level="info",
                    event_code="effort_completed",
                    message=f"Completed {prefix}",
                )
            )
            state = await self.session.scalar(
                select(models.AgentProcessState).where(
                    models.AgentProcessState.sales_strategy_id == strategy_id,
                    models.AgentProcessState.role == "contact-finder",
                )
            )
            if state:
                state.heartbeat_at = utcnow()
            await self.session.commit()
        except Exception as exc:
            AGENT_EFFORTS.labels("contact-finder", "failed").inc()
            run.status = "failed"
            run.completed_at = utcnow()
            state = await self.session.scalar(
                select(models.AgentProcessState).where(
                    models.AgentProcessState.sales_strategy_id == strategy_id,
                    models.AgentProcessState.role == "contact-finder",
                )
            )
            if state:
                state.actual_state = "error"
                state.last_error = str(exc)
            self.session.add(
                models.ProcessLog(
                    sales_strategy_id=strategy_id,
                    role="contact-finder",
                    level="error",
                    event_code="effort_failed",
                    message=str(exc),
                )
            )
            await self.session.commit()
            raise
        return run
