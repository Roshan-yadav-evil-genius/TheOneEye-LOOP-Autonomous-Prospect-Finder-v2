"""Planner StateGraph workflow module.

Encapsulates planner model/agent state in a LangGraph StateGraph, compiled with
a checkpointer and invoked via streaming using thread configurations.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from enum import StrEnum
from typing import Annotated, Any, Optional

import structlog
from langchain.agents.factory import create_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, AnyMessage, BaseMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, StateGraph, add_messages
from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel

from agents.prompts import (
    COMPANY_FINDER_PLANNER_EVALUATOR_PROMPT,
    COMPANY_FINDER_PLANNER_PROMPT,
)
from application.planner_service import PlannerService
from domain.planner_models import Planner
from persistence.database import SessionFactory
from agents.planner_middleware import AgentContext, PlannerMode, PlannerModeMiddleware
from agents.planner_tools import get_plan_creation_tools, get_plan_evaluator_tools

logger = structlog.get_logger(__name__)


def create_planner_agent(
    model: BaseChatModel | None = None,
    system_prompt: str = COMPANY_FINDER_PLANNER_PROMPT,
    tools: list[Any] | None = None,
    response_format: Any | None = None,
) -> Any:
    if model is None:
        return None
    kwargs: dict[str, Any] = {
        "model": model,
        "tools": tools or [],
        "system_prompt": system_prompt,
        "middleware": [PlannerModeMiddleware()],
    }
    if response_format is not None:
        kwargs["response_format"] = response_format
    return create_agent(**kwargs)


class Decision(StrEnum):
    ACCEPT = "accept"
    RETRY = "retry"


class NodeName(StrEnum):
    PLANNER = "planner"
    EVALUATOR = "evaluator"
    INCREMENT_RETRY = "increment_retry"


class Evaluation(BaseModel):
    feedback: str
    decision: Decision


class AgentState(BaseModel):
    task: str = "Create execution plan"
    evaluation: Optional[Evaluation] = None
    retries: int = 0
    plan: Optional[Planner] = None
    planner_chat: Annotated[list[AnyMessage], add_messages] = []
    evaluator_chat: Annotated[list[AnyMessage], add_messages] = []


def increment_retry(state: AgentState) -> dict[str, Any]:
    attempt = state.retries + 1
    feedback = (
        state.evaluation.feedback
        if state.evaluation
        else "Please refine and complete the execution plan."
    )
    logger.info(
        "planner_graph_node_increment_retry",
        attempt=attempt,
        feedback=feedback,
    )
    feedback_msg = HumanMessage(
        content=f"Evaluator Feedback (Attempt {attempt}):\n{feedback}"
    )
    return {
        "retries": attempt,
        "planner_chat": [feedback_msg],
    }


MAX_RETRIES = 1


def replan_router(state: AgentState) -> str:
    if state.evaluation and state.evaluation.decision == Decision.ACCEPT:
        logger.info(
            "planner_graph_router_decision",
            decision=END,
            reason="Evaluation accepted",
        )
        return END

    if state.retries >= MAX_RETRIES:
        logger.info(
            "planner_graph_router_decision",
            decision=END,
            reason=f"Reached max retries ({MAX_RETRIES})",
        )
        return END

    logger.info(
        "planner_graph_router_decision",
        decision=NodeName.INCREMENT_RETRY,
        reason="Evaluation requested retry",
    )
    return NodeName.INCREMENT_RETRY


def create_planner_graph(
    checkpointer: BaseCheckpointSaver | None = None,
    model: BaseChatModel | None = None,
    effort_prefix: str = "",
    strategy_id: str | None = None,
    system_prompt: str = COMPANY_FINDER_PLANNER_PROMPT,
) -> CompiledStateGraph:
    """Build a StateGraph(AgentState) graph that wraps the planner and evaluator agent nodes.

    Compiles the graph with the provided checkpointer, effort_prefix, and strategy_id scope.
    """
    async def planner(state: AgentState, config: Optional[RunnableConfig] = None) -> dict[str, Any]:
        # Context containing operational mode
        agent_context = AgentContext(mode=PlannerMode.PLAN)

        logger.info(
            "planner_graph_node_planner_start",
            effort_prefix=effort_prefix,
            retries=state.retries,
            task=state.task,
            chat_history_length=len(state.planner_chat),
        )

        input_msgs = state.planner_chat if state.planner_chat else (getattr(state, "messages", None) or [])
        if not input_msgs:
            input_msgs = [
                HumanMessage(
                    content="Create a detailed execution plan for identifying and selecting target companies based on the defined sales strategy."
                )
            ]

        # Dynamically instantiate agent with creation tools if model provided
        planner_agent_to_use = None
        if model is not None:
            async with SessionFactory() as session:
                creation_tools = get_plan_creation_tools(session, strategy_id, effort_prefix)
                planner_agent_to_use = create_planner_agent(
                    model=model, system_prompt=system_prompt, tools=creation_tools
                )

        if planner_agent_to_use:
            result = await planner_agent_to_use.ainvoke(
                {"messages": input_msgs}, config=config, context=agent_context
            )
        else:
            result = AIMessage(content="Planner agent completed step.")

        if isinstance(result, dict) and "planner_chat" in result:
            out_messages = result["planner_chat"]
        elif isinstance(result, dict) and "messages" in result:
            out_messages = result["messages"]
        elif isinstance(result, BaseMessage):
            out_messages = [result]
        elif isinstance(result, list):
            out_messages = result
        else:
            out_messages = [AIMessage(content=str(result))]

        if isinstance(out_messages, list):
            new_msgs = [m for m in out_messages if m not in input_msgs]
            if new_msgs:
                out_messages = new_msgs

        # Fetch plan from DB for this effort
        plan_obj = None
        if effort_prefix:
            try:
                async with SessionFactory() as session:
                    svc = PlannerService(session)
                    plan_obj = await svc.get_plan(effort_prefix)
            except Exception as err:
                logger.warning(
                    "planner_graph_node_planner_db_fetch_warning",
                    effort_prefix=effort_prefix,
                    error=str(err),
                )

        logger.info(
            "planner_graph_node_planner_complete",
            effort_prefix=effort_prefix,
            messages_generated=len(out_messages),
            plan_retrieved=bool(plan_obj),
        )

        return {
            "planner_chat": out_messages,
            "plan": plan_obj,
        }

    async def evaluator(state: AgentState, config: Optional[RunnableConfig] = None) -> dict[str, Any]:
        logger.info(
            "planner_graph_node_evaluator_start",
            effort_prefix=effort_prefix,
            has_plan=bool(state.plan),
            retries=state.retries,
        )

        # Context containing operational mode
        agent_context = AgentContext(mode=PlannerMode.EVALUATE)

        plan_json = ""
        if state.plan:
            if hasattr(state.plan, "model_dump_json"):
                plan_json = state.plan.model_dump_json(indent=2)
            elif isinstance(state.plan, dict):
                plan_json = json.dumps(state.plan, indent=2)
            else:
                plan_json = str(state.plan)
        else:
            plan_json = "No structured plan in database."

        eval_prompt = HumanMessage(
            content=f"Evaluate the following execution plan for task: {state.task}\n\nPlan:\n{plan_json}"
        )
        eval_input = list(state.evaluator_chat) + [eval_prompt]

        # Dynamically build Evaluator Agent with Evaluator tools if model provided
        eval_agent_to_use = None
        if model is not None:
            async with SessionFactory() as session:
                eval_tools = get_plan_evaluator_tools(session, strategy_id, effort_prefix)
                eval_agent_to_use = create_planner_agent(
                    model=model,
                    system_prompt=COMPANY_FINDER_PLANNER_EVALUATOR_PROMPT,
                    tools=eval_tools,
                    response_format=Evaluation,
                )

        res = None
        if eval_agent_to_use:
            try:
                res = await eval_agent_to_use.ainvoke(
                    {"messages": eval_input}, config=config, context=agent_context
                )
            except Exception as err:
                logger.warning(
                    "planner_graph_node_evaluator_invocation_warning",
                    effort_prefix=effort_prefix,
                    error=str(err),
                )
                res = None

        evaluation = None
        if isinstance(res, Evaluation):
            evaluation = res
        elif isinstance(res, dict):
            evaluation = res.get("structured_response")
            if isinstance(evaluation, dict):
                evaluation = Evaluation(**evaluation)
            if not evaluation and "messages" in res and res["messages"]:
                last_msg = res["messages"][-1]
                content = getattr(last_msg, "content", str(last_msg))
                evaluation = Evaluation(feedback=content, decision=Decision.ACCEPT)

        if not evaluation:
            evaluation = Evaluation(
                feedback="Execution plan successfully reviewed and accepted.",
                decision=Decision.ACCEPT,
            )

        eval_reply = AIMessage(
            content=f"Evaluation complete. Decision: {evaluation.decision.value}. Feedback: {evaluation.feedback}"
        )

        logger.info(
            "planner_graph_node_evaluator_complete",
            effort_prefix=effort_prefix,
            decision=evaluation.decision.value,
            feedback=evaluation.feedback,
        )

        return {
            "evaluator_chat": [eval_prompt, eval_reply],
            "evaluation": evaluation,
        }

    builder = StateGraph(AgentState)

    builder.add_node(NodeName.PLANNER, planner)
    builder.add_node(NodeName.EVALUATOR, evaluator)
    builder.add_node(NodeName.INCREMENT_RETRY, increment_retry)
    builder.set_entry_point(NodeName.PLANNER)
    builder.add_edge(NodeName.PLANNER, NodeName.EVALUATOR)
    builder.add_conditional_edges(
        NodeName.EVALUATOR,
        replan_router,
        {
            NodeName.INCREMENT_RETRY: NodeName.INCREMENT_RETRY,
            END: END,
        },
    )
    builder.add_edge(NodeName.INCREMENT_RETRY, NodeName.PLANNER)
    return builder.compile(checkpointer=checkpointer)


async def stream_planner_graph(
    graph: CompiledStateGraph,
    messages: list[dict[str, Any]] | dict[str, Any] | list[AnyMessage] | None,
    thread_id: str,
    version: str = "v2",
) -> AsyncIterator[dict[str, Any]]:
    """Invoke the compiled planner graph through stream, passing the planner thread ID."""
    logger.info("planner_graph_stream_start", thread_id=thread_id)
    config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }
    if messages is None:
        input_data = {}
    elif isinstance(messages, dict):
        input_data = messages
    else:
        input_data = {"planner_chat": messages}

    async for event in graph.astream_events(input_data, config=config, version=version):
        yield event
    logger.info("planner_graph_stream_complete", thread_id=thread_id)

