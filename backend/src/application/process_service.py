from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from application.loop_service import DomainError, LoopService, utcnow
from contracts.domain import AgentRunSummary, EffortDetailRead, ProcessLogRead, ProcessStatus, WhiteboardRead
from observability.logging import get_logger
from persistence import models

log = get_logger("loop.process")


class ProcessService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _state(self, strategy_id: str, role: str) -> models.AgentProcessState:
        row = await self.session.scalar(
            select(models.AgentProcessState).where(
                models.AgentProcessState.sales_strategy_id == strategy_id,
                models.AgentProcessState.role == role,
            )
        )
        if not row:
            raise DomainError("process_not_found", "Agent process was not found.", 404)
        return row

    async def start(self, strategy_id: str, role: str) -> ProcessStatus:
        from agents.cancel import clear_cancel

        clear_cancel(strategy_id, role)
        strategy = await LoopService(self.session).get_strategy(strategy_id)
        state = await self._state(strategy_id, role)
        if role == "company-finder":
            progress = await LoopService(self.session).progress(strategy_id)
            if progress.companies_registered >= strategy.target_companies:
                raise DomainError(
                    "company_quota_reached", "The strategy company target has been reached."
                )
        elif strategy.contacts_per_company_default <= 0:
            raise DomainError(
                "contacts_disabled", "Contact Finder requires a positive contacts default."
            )
        if state.actual_state == "running":
            log.info("process_start_noop_already_running", strategy_id=strategy_id, role=role)
            return await self.status(strategy_id, role)
        state.desired_state = state.actual_state = "running"
        state.consecutive_failures = 0
        state.last_error = None
        state.heartbeat_at = utcnow()
        self.session.add(
            models.JobRun(
                task_key=role,
                payload={"sales_strategy_id": strategy_id},
            )
        )
        self.session.add(
            models.ProcessLog(
                sales_strategy_id=strategy_id,
                role=role,
                event_code="process_started",
                message=f"{role} process started.",
            )
        )
        await self.session.commit()
        log.info("process_started_job_enqueued", strategy_id=strategy_id, role=role)
        return await self.status(strategy_id, role)

    async def stop(self, strategy_id: str, role: str) -> ProcessStatus:
        from agents.cancel import request_cancel

        request_cancel(strategy_id, role)
        state = await self._state(strategy_id, role)
        state.desired_state = state.actual_state = "stopped"
        state.active_company_id = None
        self.session.add(
            models.ProcessLog(
                sales_strategy_id=strategy_id,
                role=role,
                event_code="process_stopped",
                message=f"{role} process stopped immediately.",
            )
        )
        runs = (
            await self.session.scalars(
                select(models.AgentRun).where(
                    models.AgentRun.sales_strategy_id == strategy_id,
                    models.AgentRun.agent_role == role.replace("-", "_"),
                    models.AgentRun.status == "running",
                )
            )
        ).all()
        for run in runs:
            run.status = "stopped"
            run.completed_at = utcnow()
        queued_jobs = (
            await self.session.scalars(
                select(models.JobRun).where(
                    models.JobRun.task_key == role,
                    models.JobRun.status.in_(("queued", "retry", "running")),
                )
            )
        ).all()
        for job in queued_jobs:
            if job.payload.get("sales_strategy_id") == strategy_id:
                job.status = "cancelled"
                job.completed_at = utcnow()
        await self.session.commit()
        return await self.status(strategy_id, role)

    async def status(self, strategy_id: str, role: str) -> ProcessStatus:
        state = await self._state(strategy_id, role)
        logs = (
            await self.session.scalars(
                select(models.ProcessLog)
                .where(
                    models.ProcessLog.sales_strategy_id == strategy_id,
                    models.ProcessLog.role == role,
                )
                .order_by(models.ProcessLog.created_at.desc())
                .limit(100)
            )
        ).all()
        count = int(
            await self.session.scalar(
                select(func.count())
                .select_from(models.AgentRun)
                .where(
                    models.AgentRun.sales_strategy_id == strategy_id,
                    models.AgentRun.agent_role == role.replace("-", "_"),
                )
            )
            or 0
        )
        return ProcessStatus(
            role=role,  # type: ignore[arg-type]
            desired_state=state.desired_state,
            actual_state=state.actual_state,
            active_company_id=state.active_company_id,
            last_error=state.last_error,
            execution_count=count,
            logs=[ProcessLogRead.model_validate(item) for item in logs],
        )

    async def whiteboard(self, strategy_id: str, role: str) -> WhiteboardRead:
        row = await self.session.scalar(
            select(models.Whiteboard).where(
                models.Whiteboard.sales_strategy_id == strategy_id, models.Whiteboard.role == role
            )
        )
        return WhiteboardRead(
            role=role,  # type: ignore[arg-type]
            content=row.content if row else "",
            effort_prefix=row.effort_prefix if row else None,
            updated_at=row.updated_at if row else None,
        )

    async def update_whiteboard(self, strategy_id: str, role: str, content: str) -> WhiteboardRead:
        row = await self.session.scalar(
            select(models.Whiteboard).where(
                models.Whiteboard.sales_strategy_id == strategy_id, models.Whiteboard.role == role
            )
        )
        if not row:
            row = models.Whiteboard(sales_strategy_id=strategy_id, role=role)
            self.session.add(row)
        row.content = content
        await self.session.commit()
        return await self.whiteboard(strategy_id, role)

    async def threads(self, strategy_id: str) -> list[AgentRunSummary]:
        rows = (
            await self.session.scalars(
                select(models.AgentRun)
                .where(models.AgentRun.sales_strategy_id == strategy_id)
                .order_by(models.AgentRun.created_at.desc())
            )
        ).all()
        return [AgentRunSummary.model_validate(row) for row in rows]

    async def list_efforts(
        self, strategy_id: str, role: str | None = None, company_id: str | None = None
    ) -> list[AgentRunSummary]:
        query = select(models.AgentRun).where(models.AgentRun.sales_strategy_id == strategy_id)
        if role:
            db_role = role.replace("-", "_")
            query = query.where(models.AgentRun.agent_role == db_role)
        if company_id:
            query = query.where(models.AgentRun.company_id == company_id)
        query = query.order_by(models.AgentRun.created_at.desc())
        rows = (await self.session.scalars(query)).all()
        return [AgentRunSummary.model_validate(row) for row in rows]

    async def effort_detail(self, effort_prefix: str) -> EffortDetailRead:
        from agents.checkpoints import ThreadCheckpointStore

        run = await self.session.scalar(
            select(models.AgentRun).where(models.AgentRun.effort_prefix == effort_prefix)
        )
        if not run:
            raise DomainError("effort_not_found", f"Effort prefix '{effort_prefix}' not found.", 404)

        store = ThreadCheckpointStore()
        cp_threads = await store.search_threads(prefix=effort_prefix)

        all_children = set(run.child_thread_ids or [])
        all_children.update(cp_threads)
        if run.primary_thread_id in all_children:
            all_children.remove(run.primary_thread_id)

        subagent_row = await self.session.scalar(
            select(models.AgentSubagentState).where(
                models.AgentSubagentState.parent_thread_id == run.primary_thread_id
            )
        )
        active_subagents = subagent_row.active_subagent_threads if subagent_row else {}

        return EffortDetailRead(
            id=run.id,
            sales_strategy_id=run.sales_strategy_id,
            product_id=run.product_id,
            company_id=run.company_id,
            sales_strategy_prospect_id=run.sales_strategy_prospect_id,
            agent_role=run.agent_role,
            effort_prefix=run.effort_prefix,
            primary_thread_id=run.primary_thread_id,
            status=run.status,
            attempt_iteration=run.attempt_iteration,
            contact_attempt_iteration=run.contact_attempt_iteration,
            child_thread_ids=sorted(list(all_children)),
            active_subagent_threads=active_subagents or {},
            created_at=run.created_at,
            completed_at=run.completed_at,
        )

