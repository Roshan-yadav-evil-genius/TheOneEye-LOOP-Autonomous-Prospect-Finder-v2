import pytest
from domain.planner_models import Planner, Phase, Task, TaskStatus, PlannerStatus
from application.planner_service import PlannerService


@pytest.mark.asyncio
async def test_get_or_create_and_save_plan(session):
    service = PlannerService(session)
    effort_prefix = "LOOP_org1_prod1_strat1_1"

    # Plan should initially not exist
    plan = await service.get_plan(effort_prefix)
    assert plan is None

    # Get or create plan
    plan = await service.get_or_create_plan(
        effort_prefix=effort_prefix,
        goal="Test Goal",
        objective="Test Objective",
    )
    assert plan is not None
    assert plan.goal == "Test Goal"
    assert len(plan.phases) == 1

    # Add task to phase 1
    task1 = Task(
        id="task-101",
        title="Find Target Companies",
        description="Search for ICP target companies",
        status=TaskStatus.COMPLETED,
    )
    task2 = Task(
        id="task-102",
        title="Extract Contacts",
        description="Find decision makers",
        status=TaskStatus.PENDING,
    )
    plan.phases[0].tasks.extend([task1, task2])

    saved_plan = await service.save_plan(effort_prefix, plan)
    assert len(saved_plan.phases[0].tasks) == 2

    # Fetch fresh from database
    fetched = await service.get_plan(effort_prefix)
    assert fetched is not None
    assert len(fetched.phases[0].tasks) == 2
    assert fetched.phases[0].tasks[0].title == "Find Target Companies"
