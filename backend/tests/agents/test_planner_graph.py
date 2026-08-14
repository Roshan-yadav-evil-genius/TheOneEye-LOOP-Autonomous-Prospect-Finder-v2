import pytest
from langchain_core.language_models import FakeListChatModel
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.tools import tool

from agents.planner_graph import create_planner_graph, stream_planner_graph


class MockChatModel(FakeListChatModel):
    profile: dict = {"max_input_tokens": 128000}

    def bind_tools(self, tools, **kwargs):
        return self

    def with_structured_output(self, schema, **kwargs):
        from agents.planner_graph import Decision, Evaluation

        eval_obj = Evaluation(feedback="Good plan", decision=Decision.ACCEPT)

        class StructuredMock:
            async def ainvoke(self, *args, **kwargs):
                return {"structured_response": eval_obj, "messages": [AIMessage(content="Approved")]}

            def invoke(self, *args, **kwargs):
                return {"structured_response": eval_obj, "messages": [AIMessage(content="Approved")]}

        return StructuredMock()



def create_mock_model():
    return MockChatModel(responses=["Planner agent completed step."])



@pytest.mark.asyncio
async def test_create_planner_graph_and_checkpoint():
    checkpointer = MemorySaver()
    mock_model = create_mock_model()
    graph = create_planner_graph(model=mock_model, checkpointer=checkpointer, effort_prefix="LOOP_123")

    thread_id = "LOOP_123_planner_1"
    config = {"configurable": {"thread_id": thread_id}}

    result = await graph.ainvoke(
        {"planner_chat": [HumanMessage(content="Hi!")]},
        config=config,
    )


    assert "planner_chat" in result

    # Verify state saved under thread_id checkpoint
    saved_state = await graph.aget_state(config)
    assert len(saved_state.values["planner_chat"]) > 0


@pytest.mark.asyncio
async def test_stream_planner_graph():
    checkpointer = MemorySaver()
    mock_model = create_mock_model()
    graph = create_planner_graph(model=mock_model, checkpointer=checkpointer, effort_prefix="LOOP_456")

    thread_id = "LOOP_456_planner_1"
    events = []
    async for event in stream_planner_graph(
        graph,
        input_data={"planner_chat": [HumanMessage(content="Generate strategy")]},
        thread_id=thread_id,
    ):
        events.append(event)

    assert len(events) > 0
    # State checkpointer verify
    config = {"configurable": {"thread_id": thread_id}}
    state = await graph.aget_state(config)
    assert len(state.values["planner_chat"]) > 0


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
    mock_model = create_mock_model()
    graph = create_planner_graph(model=mock_model, checkpointer=checkpointer, effort_prefix=effort_prefix)

    thread_id = f"{effort_prefix}_planner_1"
    config = {"configurable": {"thread_id": thread_id, "effort_prefix": effort_prefix}}

    result = await graph.ainvoke(
        {"planner_chat": [HumanMessage(content="Build execution plan")]},
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
    mock_model = create_mock_model()
    graph = create_planner_graph(model=mock_model, checkpointer=checkpointer, effort_prefix="LOOP_789")

    thread_id = "LOOP_789_planner_1"
    events = []
    async for event in stream_planner_graph(
        graph,
        input_data={},
        thread_id=thread_id,
    ):
        events.append(event)

    assert len(events) > 0
    config = {"configurable": {"thread_id": thread_id}}
    state = await graph.aget_state(config)
    assert state.values["planner_chat"][-1].content == "Planner agent completed step."


