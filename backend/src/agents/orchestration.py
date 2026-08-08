import asyncio
import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agents.cancel import is_cancel_requested, run_cancellable
from agents.factory import (
    company_finder_agent_scope,
    contact_finder_agent_scope,
)
from agents.model_provider import DiscoveryModel
from agents.redaction import redact_text
from agents.runtime import (
    build_company_effort_prefix,
    build_contact_effort_prefix,
    build_role_thread_id,
)
from agents.usage import apply_usage
from application.common import DomainError, utcnow
from application.company_service import CompanyService
from application.product_service import ProductService
from application.prospect_service import ProspectService
from application.strategy_service import StrategyService
from browser.pool import BrowserPool
from contracts.domain import (
    BlacklistProspectRequest,
    RegisterCompanyRequest,
    RegisterContactRequest,
)
from core.config import get_settings
from observability.logging import get_logger
from observability.telemetry import AGENT_EFFORTS
from persistence import models

log = get_logger("loop.orchestration")


async def _process_state(
    session: AsyncSession, strategy_id: str, role: str
) -> models.AgentProcessState | None:
    return await session.scalar(
        select(models.AgentProcessState).where(
            models.AgentProcessState.sales_strategy_id == strategy_id,
            models.AgentProcessState.role == role,
        )
    )


async def _record_success(state: models.AgentProcessState | None) -> None:
    if state:
        state.consecutive_failures = 0
        state.last_error = None


async def _record_failure(
    session: AsyncSession,
    state: models.AgentProcessState | None,
    *,
    role: str,
    strategy_id: str,
    error: str,
) -> None:
    if not state:
        return
    state.consecutive_failures = int(state.consecutive_failures or 0) + 1
    state.last_error = redact_text(error)[:2000]
    limit = get_settings().agent_consecutive_failure_limit
    if state.consecutive_failures >= limit:
        state.desired_state = "stopped"
        state.actual_state = "paused"
        session.add(
            models.ProcessLog(
                sales_strategy_id=strategy_id,
                role=role,
                level="error",
                event_code="process_paused_failures",
                message=f"Paused after {state.consecutive_failures} consecutive failures.",
            )
        )
    else:
        state.actual_state = "error"


def _usage_from_result(result: Any) -> dict[str, Any]:
    if not isinstance(result, dict):
        return {}
    for key in ("usage", "usage_metadata", "token_usage"):
        payload = result.get(key)
        if isinstance(payload, dict):
            return payload
    messages = result.get("messages") or []
    for message in reversed(messages):
        meta = getattr(message, "usage_metadata", None) or getattr(message, "response_metadata", None)
        if isinstance(meta, dict):
            usage = meta.get("token_usage") or meta.get("usage") or meta
            if isinstance(usage, dict) and (
                "prompt_tokens" in usage
                or "input_tokens" in usage
                or "completion_tokens" in usage
                or "output_tokens" in usage
            ):
                return usage
    return {}


async def _reconcile_company_run(
    session: AsyncSession, run: models.AgentRun, thread_id: str, parent_state: dict[str, Any]
) -> None:
    link = await session.scalar(
        select(models.SalesStrategyCompany).where(
            models.SalesStrategyCompany.discovery_thread_id == thread_id
        )
    )
    if link:
        run.company_id = link.company_id
    active = parent_state.get("active_subagent_threads") or {}
    children = [str(item["thread_id"]) for item in active.values() if item.get("thread_id")]
    if children:
        run.child_thread_ids = sorted(set(list(run.child_thread_ids or []) + children))


async def _reconcile_contact_run(
    session: AsyncSession, run: models.AgentRun, thread_id: str, parent_state: dict[str, Any]
) -> None:
    link = await session.scalar(
        select(models.SalesStrategyProspect).where(
            models.SalesStrategyProspect.discovery_thread_id == thread_id
        )
    )
    if link:
        run.sales_strategy_prospect_id = link.id
        run.company_id = link.company_id
    active = parent_state.get("active_subagent_threads") or {}
    children = [str(item["thread_id"]) for item in active.values() if item.get("thread_id")]
    if children:
        run.child_thread_ids = sorted(set(list(run.child_thread_ids or []) + children))


class CompanyFinderEffort:
    def __init__(self, session: AsyncSession, model: DiscoveryModel) -> None:
        self.session = session
        self.model = model

    async def execute(self, strategy_id: str) -> models.AgentRun | None:
        log.info("company_finder.execute.enter", strategy_id=strategy_id)
        strat_svc = StrategyService(self.session)
        comp_svc = CompanyService(self.session)

        bundle = await strat_svc.bundle(strategy_id)
        strategy = await strat_svc.get_strategy(strategy_id)
        registered = await comp_svc.companies_registered(strategy_id)
        if registered >= strategy.target_companies:
            log.info(
                "company_finder.target_reached",
                strategy_id=strategy_id,
                registered=registered,
                target=strategy.target_companies,
            )
            state = await _process_state(self.session, strategy_id, "company-finder")
            if state:
                state.desired_state = state.actual_state = "stopped"
                state.heartbeat_at = utcnow()
                self.session.add(
                    models.ProcessLog(
                        sales_strategy_id=strategy_id,
                        role="company-finder",
                        level="info",
                        event_code="process_auto_stopped",
                        message="Company Finder stopped: company target reached.",
                    )
                )
                await self.session.commit()
            return None  # type: ignore[return-value]

        strategy.company_effort_seq += 1
        prefix = build_company_effort_prefix(
            bundle.organization.id, strategy.product_id, strategy.id, strategy.company_effort_seq
        )
        thread_id = build_role_thread_id(effort_prefix=prefix, role_suffix="company_finder")
        log.info(
            "company_finder.effort_prepared",
            strategy_id=strategy_id,
            effort_prefix=prefix,
            thread_id=thread_id,
            attempt=strategy.company_effort_seq,
        )
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
        memory: list[Any] = []
        prompt = json.dumps(
            {
                "sales_strategy_bundle": bundle.model_dump(mode="json"),
                "brain_recall": [item.content for item in memory],
                "instruction": "Return one JSON company decision or action=no_candidate.",
            }
        )
        provider = get_settings().model_provider
        try:
            if is_cancel_requested(strategy_id, "company-finder"):
                log.info("company_finder.cancelled_before_start", strategy_id=strategy_id)
                raise asyncio.CancelledError("company-finder cancelled before start")
            log.info(
                "company_finder.provider_branch",
                strategy_id=strategy_id,
                model_provider=provider,
            )
            if provider != "deterministic":
                pool = BrowserPool(self.session)
                log.info("company_finder.browser_lease_acquire", strategy_id=strategy_id, effort_prefix=prefix)
                lease = await pool.acquire(prefix)
                try:
                    log.info(
                        "company_finder.agent_scope_enter",
                        strategy_id=strategy_id,
                        effort_prefix=prefix,
                    )
                    async with company_finder_agent_scope(
                        self.session, strategy_id, prefix, lease_owner=prefix
                    ) as (graph, config, parent_store):
                        thread = (config.get("configurable") or {}).get("thread_id")
                        log.info(
                            "company_finder.ainvoke.start",
                            strategy_id=strategy_id,
                            thread_id=thread,
                            config=config,
                        )
                        result = await run_cancellable(
                            strategy_id,
                            "company-finder",
                            graph.ainvoke(
                                {"messages": [{"role": "user", "content": prompt}]},
                                config,
                            ),
                        )
                        log.info(
                            "company_finder.ainvoke.done",
                            strategy_id=strategy_id,
                            thread_id=thread,
                        )
                        await _reconcile_company_run(
                            self.session, run, thread_id, parent_store.sync_load(thread_id)
                        )
                        apply_usage(run, _usage_from_result(result))
                finally:
                    await pool.release(lease.id, prefix)
                    log.info(
                        "company_finder.browser_lease_release",
                        strategy_id=strategy_id,
                        effort_prefix=prefix,
                    )
            else:
                log.info("company_finder.deterministic_decide", strategy_id=strategy_id)
                decision = await self.model.decide(prompt)
                if decision.get("action") == "register_company":
                    result = await comp_svc.register_company(
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
            state = await _process_state(self.session, strategy_id, "company-finder")
            if state:
                state.heartbeat_at = utcnow()
                await _record_success(state)
                if await comp_svc.companies_registered(strategy_id) >= strategy.target_companies:
                    state.actual_state = state.desired_state = "stopped"
            await self.session.commit()
            log.info(
                "company_finder.execute.completed",
                strategy_id=strategy_id,
                effort_prefix=prefix,
            )
        except asyncio.CancelledError:
            log.info("company_finder.execute.stopped", strategy_id=strategy_id, effort_prefix=prefix)
            run.status = "stopped"
            run.completed_at = utcnow()
            AGENT_EFFORTS.labels("company-finder", "stopped").inc()
            state = await _process_state(self.session, strategy_id, "company-finder")
            if state:
                state.desired_state = state.actual_state = "stopped"
                state.heartbeat_at = utcnow()
            self.session.add(
                models.ProcessLog(
                    sales_strategy_id=strategy_id,
                    role="company-finder",
                    level="info",
                    event_code="effort_stopped",
                    message=f"Stopped {prefix}",
                )
            )
            await self.session.commit()
            return run
        except Exception as exc:
            log.exception(
                "company_finder.execute.failed",
                strategy_id=strategy_id,
                effort_prefix=prefix,
                error=str(exc),
            )
            AGENT_EFFORTS.labels("company-finder", "failed").inc()
            run.status = "failed"
            run.completed_at = utcnow()
            state = await _process_state(self.session, strategy_id, "company-finder")
            await _record_failure(
                self.session,
                state,
                role="company-finder",
                strategy_id=strategy_id,
                error=str(exc),
            )
            self.session.add(
                models.ProcessLog(
                    sales_strategy_id=strategy_id,
                    role="company-finder",
                    level="error",
                    event_code="effort_failed",
                    message=redact_text(str(exc)),
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
        rows = (
            await self.session.scalars(
                select(models.SalesStrategyCompany)
                .where(
                    models.SalesStrategyCompany.sales_strategy_id == strategy_id,
                    models.SalesStrategyCompany.is_blacklisted.is_(False),
                    models.SalesStrategyCompany.funnel_stage.in_(
                        ("company_validated", "finding_contacts", "contacts_batch_done")
                    ),
                    models.SalesStrategyCompany.contacts_target > 0,
                    models.SalesStrategyCompany.validated_at.is_not(None),
                )
                .order_by(models.SalesStrategyCompany.validated_at)
            )
        ).all()
        prospect_svc = ProspectService(self.session)
        for row in rows:
            registered = await prospect_svc.contacts_registered(strategy_id, row.company_id)
            if registered < row.contacts_target:
                # Company-level lock: skip companies with a running contact effort.
                active = await self.session.scalar(
                    select(models.AgentRun).where(
                        models.AgentRun.sales_strategy_id == strategy_id,
                        models.AgentRun.company_id == row.company_id,
                        models.AgentRun.agent_role == "contact_finder",
                        models.AgentRun.status == "running",
                    )
                )
                if active:
                    continue
                return row
        raise DomainError("contact_queue_empty", "No validated company has open contact quota.")

    async def execute(self, strategy_id: str) -> models.AgentRun | None:
        log.info("contact_finder.execute.enter", strategy_id=strategy_id)
        strat_svc = StrategyService(self.session)
        prod_svc = ProductService(self.session)
        comp_svc = CompanyService(self.session)
        prospect_svc = ProspectService(self.session)

        strategy = await strat_svc.get_strategy(strategy_id)
        try:
            company_link = await self._next_company(strategy_id)
        except DomainError as exc:
            if getattr(exc, "code", None) == "contact_queue_empty" or "contact_queue_empty" in str(
                exc
            ):
                log.info("contact_finder.queue_empty", strategy_id=strategy_id)
                state = await _process_state(self.session, strategy_id, "contact-finder")
                if state:
                    state.desired_state = state.actual_state = "stopped"
                    state.active_company_id = None
                    state.heartbeat_at = utcnow()
                    self.session.add(
                        models.ProcessLog(
                            sales_strategy_id=strategy_id,
                            role="contact-finder",
                            level="info",
                            event_code="process_auto_stopped",
                            message="Contact Finder stopped: contact queue empty.",
                        )
                    )
                    await self.session.commit()
                return None
            raise

        company_link.contact_effort_seq += 1
        product = await prod_svc.get_product(strategy.product_id)
        prefix = build_contact_effort_prefix(
            product.organization_id,
            strategy.product_id,
            strategy.id,
            company_link.sales_strategy_attempt_at_register,
            company_link.company_id,
            company_link.contact_effort_seq,
        )
        thread_id = build_role_thread_id(effort_prefix=prefix, role_suffix="contact_finder")
        log.info(
            "contact_finder.effort_prepared",
            strategy_id=strategy_id,
            company_id=company_link.company_id,
            effort_prefix=prefix,
            thread_id=thread_id,
        )
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
        state = await _process_state(self.session, strategy_id, "contact-finder")
        if state:
            state.active_company_id = company_link.company_id
            state.heartbeat_at = utcnow()
        await self.session.commit()
        prompt = json.dumps(
            {
                "bundle": (await strat_svc.bundle(strategy_id)).model_dump(mode="json"),
                "company": (
                    await comp_svc.company_detail(strategy_id, company_link.company_id)
                ).model_dump(mode="json"),
                "instruction": "Return register_contact, blacklist_prospect, or no_candidate JSON.",
            }
        )
        provider = get_settings().model_provider
        try:
            # Abort if company was blacklisted while queued.
            await self.session.refresh(company_link)
            if company_link.is_blacklisted:
                raise DomainError(
                    "company_blacklisted",
                    "Active company was blacklisted; aborting contact effort.",
                )
            if is_cancel_requested(strategy_id, "contact-finder"):
                log.info("contact_finder.cancelled_before_start", strategy_id=strategy_id)
                raise asyncio.CancelledError("contact-finder cancelled before start")
            log.info(
                "contact_finder.provider_branch",
                strategy_id=strategy_id,
                model_provider=provider,
            )
            if provider != "deterministic":
                pool = BrowserPool(self.session)
                lease = await pool.acquire(prefix)
                try:
                    log.info(
                        "contact_finder.agent_scope_enter",
                        strategy_id=strategy_id,
                        effort_prefix=prefix,
                    )
                    async with contact_finder_agent_scope(
                        self.session,
                        strategy_id,
                        company_link.company_id,
                        prefix,
                        lease_owner=prefix,
                    ) as (graph, config, parent_store):
                        thread = (config.get("configurable") or {}).get("thread_id")
                        log.info(
                            "contact_finder.ainvoke.start",
                            strategy_id=strategy_id,
                            thread_id=thread,
                        )
                        result = await run_cancellable(
                            strategy_id,
                            "contact-finder",
                            graph.ainvoke(
                                {"messages": [{"role": "user", "content": prompt}]},
                                config,
                            ),
                        )
                        log.info(
                            "contact_finder.ainvoke.done",
                            strategy_id=strategy_id,
                            thread_id=thread,
                        )
                        await _reconcile_contact_run(
                            self.session, run, thread_id, parent_store.sync_load(thread_id)
                        )
                        apply_usage(run, _usage_from_result(result))
                finally:
                    await pool.release(lease.id, prefix)
            else:
                decision: dict[str, Any] = await self.model.decide(prompt)
                action = decision.get("action")
                if action == "register_contact":
                    result = await prospect_svc.register_contact(
                        strategy_id,
                        company_link.company_id,
                        RegisterContactRequest.model_validate(decision["contact"]),
                        thread_id=thread_id,
                    )
                    run.sales_strategy_prospect_id = (
                        result.sales_strategy_prospect_id
                    )
                elif action == "blacklist_prospect":
                    await prospect_svc.blacklist_prospect(
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
            state = await _process_state(self.session, strategy_id, "contact-finder")
            if state:
                state.heartbeat_at = utcnow()
                await _record_success(state)
                # Clear active company between efforts; next execute re-sets.
                state.active_company_id = None
            # Auto-stop when no open quotas remain.
            try:
                await self._next_company(strategy_id)
            except DomainError:
                state = await _process_state(self.session, strategy_id, "contact-finder")
                if state:
                    state.desired_state = state.actual_state = "stopped"
                    state.active_company_id = None
            await self.session.commit()
            log.info(
                "contact_finder.execute.completed",
                strategy_id=strategy_id,
                effort_prefix=prefix,
            )
        except asyncio.CancelledError:
            log.info("contact_finder.execute.stopped", strategy_id=strategy_id, effort_prefix=prefix)
            run.status = "stopped"
            run.completed_at = utcnow()
            AGENT_EFFORTS.labels("contact-finder", "stopped").inc()
            state = await _process_state(self.session, strategy_id, "contact-finder")
            if state:
                state.desired_state = state.actual_state = "stopped"
                state.active_company_id = None
                state.heartbeat_at = utcnow()
            self.session.add(
                models.ProcessLog(
                    sales_strategy_id=strategy_id,
                    role="contact-finder",
                    level="info",
                    event_code="effort_stopped",
                    message=f"Stopped {prefix}",
                )
            )
            await self.session.commit()
            return run
        except Exception as exc:
            log.exception(
                "contact_finder.execute.failed",
                strategy_id=strategy_id,
                effort_prefix=prefix,
                error=str(exc),
            )
            AGENT_EFFORTS.labels("contact-finder", "failed").inc()
            run.status = "failed"
            run.completed_at = utcnow()
            state = await _process_state(self.session, strategy_id, "contact-finder")
            if state:
                state.active_company_id = None
            await _record_failure(
                self.session,
                state,
                role="contact-finder",
                strategy_id=strategy_id,
                error=str(exc),
            )
            self.session.add(
                models.ProcessLog(
                    sales_strategy_id=strategy_id,
                    role="contact-finder",
                    level="error",
                    event_code="effort_failed",
                    message=redact_text(str(exc)),
                )
            )
            await self.session.commit()
            raise
        return run
