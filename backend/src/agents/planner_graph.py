"""Planner StateGraph workflow module.

Encapsulates planner model/agent state in a LangGraph StateGraph, compiled with
a checkpointer and invoked via streaming using thread configurations.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from enum import StrEnum
from typing import Annotated, Any, Optional

import uuid
import structlog
from deepagents import create_deep_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    AnyMessage,
    BaseMessage,
    HumanMessage,
    convert_to_messages,
)
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, StateGraph, add_messages
from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel

from agents.filesystem_backend import default_filesystem_backend
from agents.loop_agent import create_loop_agent
from agents.prompts import (
    COMPANY_FINDER_PLANNER_EVALUATOR_PROMPT,
    COMPANY_FINDER_PLANNER_PROMPT,
)
from application.planner_service import PlannerService
from domain.planner_models import Planner
from persistence.database import SessionFactory
from agents.planner_middleware import AgentContext, PlannerMode
from agents.planner_tools import get_plan_creation_tools, get_plan_evaluator_tools

logger = structlog.get_logger(__name__)


def _ensure_message_ids(msgs: list[Any]) -> list[Any]:
    """Ensure all messages in the list are valid BaseMessages with unique IDs for add_messages reducer deduplication."""
    if not msgs:
        return []
    converted = convert_to_messages(msgs)
    result = []
    for msg in converted:
        if not getattr(msg, "id", None):
            try:
                msg.id = str(uuid.uuid4())
            except Exception:
                pass
        result.append(msg)
    return result




class Decision(StrEnum):
    ACCEPT = "accept"
    RETRY = "retry"


class NodeName(StrEnum):
    PREP_PLANNER = "prep_planner"
    PLANNER = "planner"
    SYNC_PLANNER_OUTPUT = "sync_planner_output"
    PREP_EVALUATOR = "prep_evaluator"
    EVALUATOR = "evaluator"
    PARSE_EVALUATOR_OUTPUT = "parse_evaluator_output"
    INCREMENT_RETRY = "increment_retry"


class Evaluation(BaseModel):
    feedback: str
    decision: Decision


class AgentState(BaseModel):
    task: str = None
    evaluation: Optional[Evaluation] = None
    retries: int = 0
    plan: Optional[Planner] = None
    planner_chat: list[AnyMessage] = []
    evaluator_chat: list[AnyMessage] = []
    messages: list[AnyMessage] = []
    structured_response:Any=None


def increment_retry(state: AgentState) -> dict[str, Any]:
    attempt = state.retries + 1
    feedback = (
        state.evaluation.feedback
        if state.evaluation
        else "Please refine and complete the execution plan."
    )
    logger.info(
        "executing_node",
        node_name=NodeName.INCREMENT_RETRY,
        attempt=attempt,
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
            "router_decision",
            decision=END,
            reason="Evaluation accepted",
        )
        return END

    if state.retries >= MAX_RETRIES:
        logger.info(
            "router_decision",
            decision=END,
            reason=f"Reached max retries ({MAX_RETRIES})",
        )
        return END

    logger.info(
        "router_decision",
        decision=NodeName.INCREMENT_RETRY,
        reason="Evaluation requested retry",
    )
    return NodeName.INCREMENT_RETRY


def create_planner_graph(
    model: BaseChatModel,
    checkpointer: BaseCheckpointSaver | None = None,
    store: Any = None,
    effort_prefix: str = "",
    strategy_id: str | None = None,
    session: Any | None = None,
) -> CompiledStateGraph:
    """Build a StateGraph(AgentState) graph using native subgraph nodes and isolated state channels.

    Compiles planner and evaluator subgraphs directly into the parent StateGraph.
    Checkpoints are natively tracked across hierarchical namespaces for seamless continuation.
    """
    # 1. Instantiate Planner & Evaluator Subgraph Agents
    creation_tools = get_plan_creation_tools(session, strategy_id, effort_prefix)
    planner_subgraph = create_loop_agent(
        name="Planner Agent",
        model=model,
        tools=creation_tools,
        system_prompt=COMPANY_FINDER_PLANNER_PROMPT,
        session=session,
        strategy_id=strategy_id,
        effort_prefix=effort_prefix,
        checkpointer=checkpointer,
        store=store,
        context_schema=AgentContext,
        backend=default_filesystem_backend(),
    )

    eval_tools = get_plan_evaluator_tools(session, strategy_id, effort_prefix)
    evaluator_subgraph = create_loop_agent(
        name="Evaluator Agent",
        model=model,
        system_prompt=COMPANY_FINDER_PLANNER_EVALUATOR_PROMPT,
        tools=eval_tools,
        session=session,
        strategy_id=strategy_id,
        effort_prefix=effort_prefix,
        checkpointer=checkpointer,
        store=store,
        context_schema=AgentContext,
        response_format=Evaluation,
        backend=default_filesystem_backend(),
    )


    # 2. State Transformation Nodes
    def prep_planner(state: AgentState) -> dict[str, Any]:
        task = "Create a detailed execution plan for identifying and selecting one companies based on the defined sales strategy."
        logger.info(
            "executing_node",
            node_name=NodeName.PREP_PLANNER,
        )
        input_msgs = (
            state.planner_chat
            if state.planner_chat
            else (getattr(state, "messages", None) or [])
        )
        if not input_msgs:
            input_msgs = [HumanMessage(content=task)]
        return {"messages": input_msgs, "task": task}

    async def sync_planner_output(
        state: AgentState, config: Optional[RunnableConfig] = None
    ) -> dict[str, Any]:
        logger.info(
            "executing_node",
            node_name=NodeName.SYNC_PLANNER_OUTPUT,
        )
        plan_obj = None
        if effort_prefix:
            try:
                async with SessionFactory() as session:
                    svc = PlannerService(session)
                    plan_obj = await svc.get_plan(effort_prefix)
            except Exception as err:
                logger.warning(
                    "planner_graph_sync_db_warning",
                    effort_prefix=effort_prefix,
                    error=str(err),
                )

        new_planner_msgs = (
            list(state.messages)
            if hasattr(state, "messages") and state.messages
            else []
        )
        return {
            "planner_chat": new_planner_msgs,
            "plan": plan_obj,
            "messages": [],
        }

    def prep_evaluator(state: AgentState) -> dict[str, Any]:
        logger.info(
            "executing_node",
            node_name=NodeName.PREP_EVALUATOR,
        )
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
        return {"messages": _ensure_message_ids([eval_prompt])}


    def parse_evaluator_output(state: AgentState) -> dict[str, Any]:
        logger.info(
            "executing_node",
            node_name=NodeName.PARSE_EVALUATOR_OUTPUT,
        )
        evaluation = state.structured_response
        if evaluation is None:
            evaluation = Evaluation(feedback="Plan evaluation complete.", decision=Decision.ACCEPT)

        return {
            "evaluator_chat": state.messages,
            "evaluation": evaluation,
            "messages": [],
        }


    # 3. Build StateGraph Pipeline
    builder = StateGraph(AgentState)

    builder.add_node(NodeName.PREP_PLANNER, prep_planner)
    builder.add_node(NodeName.PLANNER, planner_subgraph)
    builder.add_node(NodeName.SYNC_PLANNER_OUTPUT, sync_planner_output)

    builder.add_node(NodeName.PREP_EVALUATOR, prep_evaluator)
    builder.add_node(NodeName.EVALUATOR, evaluator_subgraph)
    builder.add_node(NodeName.PARSE_EVALUATOR_OUTPUT, parse_evaluator_output)

    builder.add_node(NodeName.INCREMENT_RETRY, increment_retry)

    # 4. Configure Edges
    builder.set_entry_point(NodeName.PREP_PLANNER)
    builder.add_edge(NodeName.PREP_PLANNER, NodeName.PLANNER)
    builder.add_edge(NodeName.PLANNER, NodeName.SYNC_PLANNER_OUTPUT)
    builder.add_edge(NodeName.SYNC_PLANNER_OUTPUT, NodeName.PREP_EVALUATOR)
    builder.add_edge(NodeName.PREP_EVALUATOR, NodeName.EVALUATOR)
    builder.add_edge(NodeName.EVALUATOR, NodeName.PARSE_EVALUATOR_OUTPUT)

    builder.add_conditional_edges(
        NodeName.PARSE_EVALUATOR_OUTPUT,
        replan_router,
        {
            NodeName.INCREMENT_RETRY: NodeName.INCREMENT_RETRY,
            END: END,
        },
    )
    builder.add_edge(NodeName.INCREMENT_RETRY, NodeName.PREP_PLANNER)

    return builder.compile(checkpointer=checkpointer)


async def stream_planner_graph(
    graph: CompiledStateGraph,
    messages: list[dict[str, Any]] | dict[str, Any] | list[AnyMessage] | None,
    thread_id: str,
    version: str = "v2",
) -> AsyncIterator[dict[str, Any]]:
    """Invoke the compiled planner graph through stream, passing the planner thread ID."""
    from core.config import get_settings

    logger.info("planner_graph_stream_start", thread_id=thread_id)
    config = {
        "recursion_limit": get_settings().agent_recursion_limit,
        "configurable": {
            "thread_id": thread_id,
        },
    }
    if messages is None:
        input_data = {}
    elif isinstance(messages, dict):
        input_data = messages
    else:
        input_data = {"planner_chat": _ensure_message_ids(messages)}


    async for event in graph.astream_events(input_data, config=config, version=version, subgraphs=True):
        yield event

    logger.info("planner_graph_stream_complete", thread_id=thread_id)
