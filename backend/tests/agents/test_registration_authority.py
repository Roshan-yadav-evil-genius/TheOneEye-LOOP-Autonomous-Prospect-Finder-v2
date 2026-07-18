from agents.runtime import validate_registration_authority
from agents.stack_builders import build_company_finder_stack, build_contact_finder_stack
from agents.runtime import LoopAgentToolContext


class _Tool:
    def __init__(self, name: str) -> None:
        self.name = name


def test_browser_cannot_receive_register_tools() -> None:
    try:
        validate_registration_authority(
            "browser_agent", {"navigate", "register_company"}
        )
        raised = False
    except ValueError:
        raised = True
    assert raised


def test_company_finder_cannot_register_contact() -> None:
    try:
        validate_registration_authority("company_finder", {"register_contact"})
        raised = False
    except ValueError:
        raised = True
    assert raised


def test_contact_finder_cannot_register_company() -> None:
    try:
        validate_registration_authority("contact_finder", {"register_company"})
        raised = False
    except ValueError:
        raised = True
    assert raised


def test_company_stack_rejects_browser_register_tools() -> None:
    ctx = LoopAgentToolContext(
        sales_strategy_id="s1", company_id=None, effort_prefix="LOOP_o_p_s_1"
    )
    try:
        build_company_finder_stack(
            effort_prefix="LOOP_o_p_s_1",
            loop_context=ctx,
            company_tools=[_Tool("register_company"), _Tool("get_sales_strategy_bundle")],
            browser_tools=[_Tool("navigate"), _Tool("register_company")],
            brain_tools=[_Tool("recall_memory")],
            checkpointer=None,
            strategy_bundle={
                "sales_strategy": {
                    "sales_strategy_form": {
                        "overview": {"target_companies_narrative": "Find SaaS"}
                    }
                },
                "product": {"icp_form": {}},
            },
        )
        raised = False
    except ValueError:
        raised = True
    assert raised


def test_contact_stack_rejects_register_company_on_orchestrator() -> None:
    ctx = LoopAgentToolContext(
        sales_strategy_id="s1", company_id="c1", effort_prefix="LOOP_o_p_s_1_c1_1"
    )
    try:
        build_contact_finder_stack(
            effort_prefix="LOOP_o_p_s_1_c1_1",
            company_id="c1",
            loop_context=ctx,
            contact_tools=[_Tool("register_company"), _Tool("register_contact")],
            browser_tools=[_Tool("navigate")],
            brain_tools=[_Tool("recall_memory")],
            checkpointer=None,
            strategy_bundle={"sales_strategy": {"sales_strategy_form": {"overview": {}}}},
            company_payload={"name": "Acme", "domain": "acme.example"},
        )
        raised = False
    except ValueError:
        raised = True
    assert raised
