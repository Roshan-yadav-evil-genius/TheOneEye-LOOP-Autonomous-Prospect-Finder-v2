"""
PlannerService handles persistent CRUD operations and state mutators for Planner domain models.
"""

from typing import Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.planner_models import (
    Planner,
    Phase,
    Task,
    Step,
    TaskStatus,
    PlannerStatus,
    utc_now,
)
from persistence import models


class PlannerService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_plan(self, effort_prefix: str) -> Optional[Planner]:
        """Fetch and deserialize Planner state for an effort_prefix."""
        stmt = select(models.PlannerState).where(
            models.PlannerState.effort_prefix == effort_prefix
        )
        record = await self.session.scalar(stmt)
        if not record or not record.plan_data:
            return None
        return Planner.model_validate(record.plan_data)

    async def save_plan(
        self,
        effort_prefix: str,
        plan: Planner,
        strategy_id: Optional[str] = None,
    ) -> Planner:
        """Persist or update Planner state in the database."""
        plan.updated_at = utc_now()

        stmt = select(models.PlannerState).where(
            models.PlannerState.effort_prefix == effort_prefix
        )
        record = await self.session.scalar(stmt)
        plan_dict = plan.model_dump(mode="json")

        if strategy_id:
            strat_exists = await self.session.scalar(
                select(models.SalesStrategy.id).where(models.SalesStrategy.id == strategy_id)
            )
            if not strat_exists:
                strategy_id = None

        if record:
            record.plan_data = plan_dict
            if strategy_id:
                record.sales_strategy_id = strategy_id
        else:
            record = models.PlannerState(
                effort_prefix=effort_prefix,
                sales_strategy_id=strategy_id,
                plan_data=plan_dict,
            )
            self.session.add(record)

        await self.session.commit()
        return plan

    async def get_or_create_plan(
        self,
        effort_prefix: str,
        goal: str = "Autonomous Prospecting & Research Effort",
        objective: str = "Execute strategic client discovery and outreach pipeline",
        strategy_id: Optional[str] = None,
    ) -> Planner:
        """Get existing plan or instantiate a default plan structure."""
        plan = await self.get_plan(effort_prefix)
        if plan:
            return plan

        initial_plan = Planner(
            planner_id=f"planner-{effort_prefix}",
            goal=goal,
            objective=objective,
            phases=[
                Phase(
                    id="phase-1",
                    title="Initial Discovery & Planning",
                    objective="Formulate research approach and target search space",
                    status=TaskStatus.RUNNING,
                    tasks=[],
                )
            ],
        )
        return await self.save_plan(effort_prefix, initial_plan, strategy_id=strategy_id)
