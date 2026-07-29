"""Tests for allocate_next_setup_thread_id."""
from agents.runtime import (
    allocate_next_setup_thread_id,
    build_org_setup_thread_id,
    build_product_setup_thread_id,
    build_strategy_setup_thread_id,
)


BASE_ORG = build_org_setup_thread_id("org1")
BASE_PROD = build_product_setup_thread_id("org1", "prod1")
BASE_STRAT = build_strategy_setup_thread_id("org1", "prod1", "strat1")


def test_first_new_thread_when_base_exists() -> None:
    """Base thread (_1) exists → next is _2."""
    result = allocate_next_setup_thread_id(BASE_ORG, [BASE_ORG])
    assert result == "LOOP_org1_org_setup_chat_2"


def test_second_new_thread() -> None:
    result = allocate_next_setup_thread_id(
        BASE_ORG, [BASE_ORG, "LOOP_org1_org_setup_chat_2"]
    )
    assert result == "LOOP_org1_org_setup_chat_3"


def test_no_existing_threads_starts_at_1() -> None:
    """No existing threads: sequence numbering starts at 1 (_1)."""
    result = allocate_next_setup_thread_id(BASE_ORG, [])
    assert result == "LOOP_org1_org_setup_chat_1"


def test_gaps_take_max() -> None:
    """Skipped sequences pick up from max."""
    result = allocate_next_setup_thread_id(
        BASE_ORG, [BASE_ORG, "LOOP_org1_org_setup_chat_5"]
    )
    assert result == "LOOP_org1_org_setup_chat_6"


def test_product_setup_thread_allocation() -> None:
    result = allocate_next_setup_thread_id(
        BASE_PROD, [BASE_PROD, "LOOP_org1_prod1_product_setup_chat_2"]
    )
    assert result == "LOOP_org1_prod1_product_setup_chat_3"


def test_strategy_setup_thread_allocation() -> None:
    result = allocate_next_setup_thread_id(BASE_STRAT, [BASE_STRAT])
    assert result == "LOOP_org1_prod1_strat1_strategy_setup_chat_2"


def test_does_not_match_similar_but_different_prefix() -> None:
    """Another entity's threads must not pollute the sequence."""
    other = build_org_setup_thread_id("org2")
    result = allocate_next_setup_thread_id(BASE_ORG, [BASE_ORG, "LOOP_org2_org_setup_chat_2"])
    # Only BASE_ORG itself counts (seq=1), so next is 2
    assert result == "LOOP_org1_org_setup_chat_2"
