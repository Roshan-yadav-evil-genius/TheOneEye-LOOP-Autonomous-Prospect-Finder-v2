from unittest.mock import AsyncMock, MagicMock

from agents.setup_chat.org_tools import get_all_tools, set_identity, set_brand_positioning, set_unique_strengths
from agents.setup_chat.strategy_tools import get_strategy_tools, set_strategy_overview, set_strategy_company_size
from agents.setup_chat.product_tools import get_product_tools, set_product_identity, set_product_icp
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

    res = await set_brand_positioning.ainvoke({"position": "Premium"}, config=config)
    assert res == {"section": "brand_positioning", "data": {"position": "Premium"}}

    res_strengths = await set_unique_strengths.ainvoke({"items": ["Fast", "Reliable"]}, config=config)
    assert res_strengths == {"section": "unique_strengths", "data": {"items": ["Fast", "Reliable"]}}


async def test_strategy_tools_returns_saved_data():
    mock_service = AsyncMock()
    mock_strategy = MagicMock()
    mock_strategy.sales_strategy_form = {}
    mock_service.get_strategy.return_value = mock_strategy
    mock_service.update_strategy_profile.return_value = None

    ctx = SetupChatToolContext(
        organization_id="org-123", strategy_id="strat-123", mode="agent", service=mock_service
    )
    config = {"configurable": {"tool_context": ctx}}

    res = await set_strategy_overview.ainvoke({"name": "New Strategy"}, config=config)
    assert res == {"section": "overview", "data": {"name": "New Strategy"}}

    # Test empty payload guard on strategy tool
    res_empty = await set_strategy_company_size.ainvoke({}, config=config)
    assert res_empty == "Error: No field values provided to update. Please pass at least one field value."


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
    assert res == {"section": "icp", "data": {"company_size_employees_min": 10}}
