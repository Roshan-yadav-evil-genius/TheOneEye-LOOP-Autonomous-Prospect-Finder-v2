import pytest
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage
from langchain_core.tools import tool

from agents.planner_graph import create_planner_graph, stream_planner_graph


class DummyAgent:
    def __init__(self, response_text: str = "Hello from planner agent"):
        self.response_text = response_text

    async def ainvoke(self, state: dict):
        messages = state.get("planner_chat") or state.get("messages", [])
        return {"planner_chat": messages + [AIMessage(content=self.response_text)]}


@tool
def sample_planning_tool(query: str) -> str:
    """Sample planning tool for testing graph integration."""
    return f"Tool result for {query}"


@pytest.mark.asyncio
async def test_create_planner_graph_and_checkpoint():
    checkpointer = MemorySaver()
    graph = create_planner_graph(checkpointer=checkpointer, effort_prefix="LOOP_123")

    thread_id = "LOOP_123_planner_1"
    config = {"configurable": {"thread_id": thread_id}}

    result = await graph.ainvoke(
        {"planner_chat": [{"role": "user", "content": "Hi!"}]},
        config=config,
    )

    assert "planner_chat" in result
    assert result["planner_chat"][-1].content == "Planner agent completed step."

    # Verify state saved under thread_id checkpoint
    saved_state = await graph.aget_state(config)
    assert saved_state.values["planner_chat"][-1].content == "Planner agent completed step."


@pytest.mark.asyncio
async def test_stream_planner_graph():
    checkpointer = MemorySaver()
    graph = create_planner_graph(checkpointer=checkpointer, effort_prefix="LOOP_456")

    thread_id = "LOOP_456_planner_1"
    events = []
    async for event in stream_planner_graph(
        graph,
        messages=[{"role": "user", "content": "Generate strategy"}],
        thread_id=thread_id,
    ):
        events.append(event)

    assert len(events) > 0
    # State checkpointer verify
    config = {"configurable": {"thread_id": thread_id}}
    state = await graph.aget_state(config)
    assert state.values["planner_chat"][-1].content == "Planner agent completed step."


@pytest.mark.asyncio
async def test_planner_graph_evaluator_and_db_plan():
    from application.planner_service import PlannerService
    from persistence.database import SessionFactory, create_schema
    from domain.planner_models import Planner, Phase, Task

    await create_schema()

    effort_prefix = "LOOP_test_org_prod_strat_1"
    async with SessionFactory() as session:
        svc = PlannerService(session)
        plan = Planner(
            planner_id=f"planner-{effort_prefix}",
            goal="Identify target company",
            objective="B2B Prospecting",
            phases=[
                Phase(
                    id="phase-1",
                    title="Phase 1",
                    tasks=[
                        Task(
                            id="task-1",
                            title="Task 1",
                            goal="Search LinkedIn",
                            tools=["company_finder"],
                        )
                    ],
                )
            ],
        )
        await svc.save_plan(effort_prefix, plan)

    checkpointer = MemorySaver()
    graph = create_planner_graph(checkpointer=checkpointer, effort_prefix=effort_prefix)

    thread_id = f"{effort_prefix}_planner_1"
    config = {"configurable": {"thread_id": thread_id, "effort_prefix": effort_prefix}}

    result = await graph.ainvoke(
        {"planner_chat": [{"role": "user", "content": "Build execution plan"}]},
        config=config,
    )

    assert "plan" in result
    assert result["plan"] is not None
    assert result["plan"].goal == "Identify target company"
    assert result["evaluation"] is not None
    assert result["evaluation"].decision == "accept"
    assert len(result["evaluator_chat"]) > 0


@pytest.mark.asyncio
async def test_stream_planner_graph_empty_messages():
    checkpointer = MemorySaver()
    graph = create_planner_graph(checkpointer=checkpointer, effort_prefix="LOOP_789")

    thread_id = "LOOP_789_planner_1"
    events = []
    async for event in stream_planner_graph(
        graph,
        messages=None,
        thread_id=thread_id,
    ):
        events.append(event)

    assert len(events) > 0
    config = {"configurable": {"thread_id": thread_id}}
    state = await graph.aget_state(config)
    assert state.values["planner_chat"][-1].content == "Planner agent completed step."


