from __future__ import annotations

from types import SimpleNamespace

import pytest

from loop_api.agents.runtime import (
    ConfiguredAgent,
    LoopAgentToolContext,
    validate_registration_authority,
)
from loop_api.agents.stack_builders import (
    build_company_finder_stack,
    build_contact_finder_stack,
)
from loop_api.agents.vector_memory import InMemoryVectorStore, local_hash_embedding


def test_registration_authority_blocks_browser_registration() -> None:
    with pytest.raises(ValueError, match="Browser agents"):
        validate_registration_authority("browser_agent", {"navigate", "register_company"})


def test_company_finder_stack_dry_run_structure() -> None:
    ctx = LoopAgentToolContext(
        sales_strategy_id="s1",
        company_id=None,
        effort_prefix="LOOP_p_s_1",
    )
    company_tools = [
        SimpleNamespace(name="get_sales_strategy_bundle"),
        SimpleNamespace(name="register_company"),
        SimpleNamespace(name="set_scratch_pad"),
    ]
    browser_tools = [
        SimpleNamespace(name="navigate"),
        SimpleNamespace(name="inspect"),
        SimpleNamespace(name="is_profile_present"),
    ]
    brain_tools = [SimpleNamespace(name="remember"), SimpleNamespace(name="recall")]
    stack = build_company_finder_stack(
        effort_prefix=ctx.effort_prefix,
        loop_context=ctx,
        company_tools=company_tools,
        browser_tools=browser_tools,
        brain_tools=brain_tools,
        checkpointer=None,
        model=None,
    )
    assert isinstance(stack.company_finder, ConfiguredAgent)
    assert stack.company_finder.config.role_suffix == "company_finder"
    assert stack.browser.config.role_suffix == "browser_agent"
    assert stack.brain.config.role_suffix == "company_finder_brain"
    assert len(stack.company_finder.config.subagents) == 2


def test_contact_finder_stack_requires_company_context() -> None:
    ctx = LoopAgentToolContext(
        sales_strategy_id="s1",
        company_id=None,
        effort_prefix="LOOP_p_s_1_c_1",
    )
    with pytest.raises(ValueError, match="company_id"):
        build_contact_finder_stack(
            effort_prefix=ctx.effort_prefix,
            company_id="c1",
            loop_context=ctx,
            contact_tools=[SimpleNamespace(name="register_contact")],
            browser_tools=[SimpleNamespace(name="navigate")],
            brain_tools=[SimpleNamespace(name="recall")],
            checkpointer=None,
            model=None,
        )


@pytest.mark.asyncio
async def test_vector_memory_round_trip() -> None:
    store = InMemoryVectorStore()
    await store.ensure_schema()
    embedding = local_hash_embedding("enterprise SaaS ICP")
    await store.upsert(
        memory_id="m1",
        strategy_id="s1",
        agent_type="company_finder",
        category="lesson",
        content="Prefer mid-market SaaS with hiring signals",
        embedding=embedding,
    )
    hits = await store.search(
        strategy_id="s1",
        agent_type="company_finder",
        embedding=local_hash_embedding("SaaS mid-market hiring"),
        limit=3,
    )
    assert hits
    assert hits[0]["memory_id"] == "m1"
