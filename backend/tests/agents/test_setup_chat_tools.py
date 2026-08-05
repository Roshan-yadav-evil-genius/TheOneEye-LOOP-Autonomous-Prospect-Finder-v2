from unittest.mock import AsyncMock, MagicMock

from agents.setup_chat.org_tools import (
    get_all_tools,
    get_organization_profile,
    set_identity,
    set_operating_territories,
    set_macro_deal_constraints,
)
from agents.setup_chat.strategy_tools import (
    get_strategy_tools,
    get_strategy_profile,
    set_strategy_overview,
    set_strategy_run_targets,
    set_strategy_company_size,
    set_strategy_experiments,
)
from agents.setup_chat.product_tools import (
    get_product_tools,
    get_product_profile,
    set_product_identity,
    set_product_icp,
    set_product_use_cases,
    set_product_competitors,
)
from agents.setup_chat.common import SetupChatToolContext


async def test_org_tools_empty_payload_validation():
    mock_service = AsyncMock()
    ctx = SetupChatToolContext(organization_id="org-123", mode="agent", service=mock_service)
    config = {"configurable": {"tool_context": ctx}}

    # Call with empty payload
    res = await set_identity.ainvoke({}, config=config)
    assert res == "Error: No field values provided to update. Please pass at least one field value."


async def test_org_tools_chat_mode_guard():
    mock_service = AsyncMock()
    ctx = SetupChatToolContext(organization_id="org-123", mode="chat", service=mock_service)
    config = {"configurable": {"tool_context": ctx}}

    res = await set_identity.ainvoke({"name": "Acme Corp"}, config=config)
    assert res == "Error: Cannot write in chat mode. Ask the user to switch to Agent mode."


async def test_org_tools_successful_update_returns_saved_data():
    mock_service = AsyncMock()
    mock_org = MagicMock()
    mock_org.name = "Old Name"
    mock_org.website = "https://old.com"
    mock_org.primary_contact_email = "old@example.com"
    mock_org.org_form = {}
    mock_service.get_organization.return_value = mock_org
    mock_service.update_organization_profile.return_value = None

    ctx = SetupChatToolContext(organization_id="org-123", mode="agent", service=mock_service)
    config = {"configurable": {"tool_context": ctx}}

    res = await set_operating_territories.ainvoke({"countries": ["US"]}, config=config)
    assert res == "Saved!"

    res_constraints = await set_macro_deal_constraints.ainvoke({"min_contract_value": "10000"}, config=config)
    assert res_constraints == "Saved!"


async def test_strategy_tools_returns_saved_data():
    mock_service = AsyncMock()
    mock_strategy = MagicMock()
    mock_strategy.name = "Outbound Run 1"
    mock_strategy.target_companies = 100
    mock_strategy.contacts_per_company_default = 5
    mock_strategy.sales_strategy_form = {}
    mock_service.get_strategy.return_value = mock_strategy
    mock_service.update_strategy_profile.return_value = None

    ctx = SetupChatToolContext(
        organization_id="org-123", strategy_id="strat-123", mode="agent", service=mock_service
    )
    config = {"configurable": {"tool_context": ctx}}

    res = await set_strategy_overview.ainvoke({"name": "New Strategy"}, config=config)
    assert res == "Saved!"

    res_targets = await set_strategy_run_targets.ainvoke({"target_companies": 50}, config=config)
    assert res_targets == "Saved!"

    # Verify get_strategy_tools() returns valid tools list
    tools = get_strategy_tools()
    assert set_strategy_run_targets in tools
    assert len(tools) == 16

    # Test empty payload guard on strategy tool
    res_empty = await set_strategy_company_size.ainvoke({}, config=config)
    assert res_empty == "Error: No field values provided to update. Please pass at least one field value."

    # Test get_strategy_profile transformer output
    strategy_profile = await get_strategy_profile.ainvoke({}, config=config)
    assert strategy_profile["overview"][0]["value"] == "Outbound Run 1"
    assert strategy_profile["run_targets"][0]["value"] == 100
    assert strategy_profile["run_targets"][1]["value"] == 5


async def test_strategy_experiments_saved_as_direct_list():
    mock_service = AsyncMock()
    mock_strategy = MagicMock()
    mock_strategy.name = "Strat"
    mock_strategy.target_companies = 10
    mock_strategy.contacts_per_company_default = 2
    mock_strategy.sales_strategy_form = {}
    mock_service.get_strategy.return_value = mock_strategy

    ctx = SetupChatToolContext(
        organization_id="org-123", strategy_id="strat-123", mode="agent", service=mock_service
    )
    config = {"configurable": {"tool_context": ctx}}

    exp_items = [{"hypothesis": "Test H1", "variant": "Var A"}]
    res = await set_strategy_experiments.ainvoke({"items": exp_items}, config=config)
    assert res == "Saved!"

    mock_service.update_strategy_profile.assert_called_once()
    saved_form = mock_service.update_strategy_profile.call_args.kwargs["form"]
    assert saved_form["experiments"] == exp_items
    assert isinstance(saved_form["experiments"], list)


async def test_product_tools_returns_saved_data():
    mock_service = AsyncMock()
    mock_product = MagicMock()
    mock_product.name = "Product X"
    mock_product.kind = "product"
    mock_product.icp_form = {}
    mock_service.get_product.return_value = mock_product
    mock_service.update_product_profile.return_value = None

    ctx = SetupChatToolContext(
        organization_id="org-123", product_id="prod-123", mode="agent", service=mock_service
    )
    config = {"configurable": {"tool_context": ctx}}

    res = await set_product_icp.ainvoke({"company_size_employees_min": 10}, config=config)
    assert res == "Saved!"


async def test_product_use_cases_and_competitors_saved_as_direct_list():
    mock_service = AsyncMock()
    mock_product = MagicMock()
    mock_product.name = "Product Y"
    mock_product.kind = "product"
    mock_product.icp_form = {}
    mock_service.get_product.return_value = mock_product

    ctx = SetupChatToolContext(
        organization_id="org-123", product_id="prod-123", mode="agent", service=mock_service
    )
    config = {"configurable": {"tool_context": ctx}}

    uc_items = [{"name": "UC1", "trigger": "T1", "outcome": "O1"}]
    res_uc = await set_product_use_cases.ainvoke({"items": uc_items}, config=config)
    assert res_uc == "Saved!"
    saved_form = mock_service.update_product_profile.call_args.kwargs["form"]
    assert saved_form["use_cases"] == uc_items
    assert isinstance(saved_form["use_cases"], list)

    comp_items = [{"name": "Comp A", "website": "https://compa.com", "type": "direct"}]
    res_comp = await set_product_competitors.ainvoke({"items": comp_items}, config=config)
    assert res_comp == "Saved!"
    saved_form_comp = mock_service.update_product_profile.call_args.kwargs["form"]
    assert saved_form_comp["competitors"] == comp_items
    assert isinstance(saved_form_comp["competitors"], list)


async def test_product_icp_nested_storage_and_retrieval():
    mock_service = AsyncMock()
    mock_product = MagicMock()
    mock_product.name = "Product Z"
    mock_product.kind = "product"
    mock_product.icp_form = {
        "icp": {
            "industries": {"primary": ["Software & SaaS"]},
            "company_size": {"employees_min": 50},
            "geography": {"countries": ["United States"]},
        }
    }
    mock_service.get_product.return_value = mock_product

    ctx = SetupChatToolContext(
        organization_id="org-123", product_id="prod-123", mode="agent", service=mock_service
    )
    config = {"configurable": {"tool_context": ctx}}

    profile = await get_product_profile.ainvoke({}, config=config)
    assert profile["identity"][0]["value"] == "Product Z"
    assert profile["identity"][1]["value"] == "product"

    icp_fields = {f["name"]: f["value"] for f in profile["icp"]}
    assert icp_fields["Primary industries"] == ["Software & SaaS"]
    assert icp_fields["Employees min"] == 50
    assert icp_fields["Countries"] == ["United States"]


async def test_identity_stripped_from_form_json():
    mock_service = AsyncMock()
    mock_product = MagicMock()
    mock_product.name = "Product A"
    mock_product.kind = "product"
    mock_product.icp_form = {"identity": {"name": "Old Name"}}
    mock_service.get_product.return_value = mock_product

    ctx = SetupChatToolContext(
        organization_id="org-123", product_id="prod-123", mode="agent", service=mock_service
    )
    config = {"configurable": {"tool_context": ctx}}

    await set_product_identity.ainvoke({"name": "New Name"}, config=config)
    mock_service.update_product_profile.assert_called_once()
    saved_form = mock_service.update_product_profile.call_args.kwargs["form"]
    assert "identity" not in saved_form


def test_build_agent_profile_dict_normalization():
    from application.form_definitions import ORGANIZATION_FORM, build_agent_profile_dict

    form_data = {
        "identity": {
            "name": "Acme Inc",
            "website": "",
            "primary_contact_email": None,
        },
        "company_overview": {
            "description": "   ",
            "mission": [],
            "founded_year": 0,
        },
        "operating_territories": [],
    }

    result = build_agent_profile_dict(ORGANIZATION_FORM, form_data)

    identity_fields = {f["name"]: f["value"] for f in result["identity"]}
    assert identity_fields["Organization name"] == "Acme Inc"
    assert identity_fields["Website"] is None
    assert identity_fields["Primary contact email"] is None

    overview_fields = {f["name"]: f["value"] for f in result["company_overview"]}
    assert overview_fields["What the company does"] is None
    assert overview_fields["Mission or vision"] is None
    assert overview_fields["Year founded"] == 0

    territories_fields = {f["name"]: f["value"] for f in result["operating_territories"]}
    assert territories_fields["Countries"] is None





