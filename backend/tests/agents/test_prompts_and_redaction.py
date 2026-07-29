from agents.prompt_context import company_finder_prompt_values, contact_finder_prompt_values
from agents.prompts import COMPANY_FINDER_PROMPT, CONTACT_FINDER_PROMPT, render_prompt
from agents.redaction import redact_payload, redact_text


def test_company_prompt_placeholders_filled() -> None:
    bundle = {
        "sales_strategy": {
            "sales_strategy_form": {
                "overview": {"target_companies_narrative": "Find logistics SaaS"},
                "priority_industries": {"primary": ["Logistics"]},
            }
        },
        "product": {"icp_form": {"icp": {"industries": {"primary": ["Software"]}}}},
    }
    rendered = render_prompt(COMPANY_FINDER_PROMPT, company_finder_prompt_values(bundle))
    assert "{{sales_objective}}" not in rendered
    assert "Find logistics SaaS" in rendered
    assert "Logistics" in rendered


def test_contact_prompt_placeholders_filled() -> None:
    bundle = {
        "sales_strategy": {
            "sales_strategy_form": {
                "overview": {"description": "Sell ops automation"},
                "target_decision_makers": {"primary_titles": ["CTO", "VP Eng"]},
            }
        },
        "product": {"icp_form": {"product_overview": {"summary": "Ops platform"}}, "kind": "product"},
    }
    company = {"name": "Acme", "domain": "acme.example", "profile": {"industry": "SaaS"}}
    rendered = render_prompt(
        CONTACT_FINDER_PROMPT, contact_finder_prompt_values(bundle, company)
    )
    assert "{{company_name}}" not in rendered
    assert "Acme" in rendered
    assert "CTO" in rendered


def test_redaction_strips_cookies_and_tokens() -> None:
    text = "Cookie: li_at=abc123; Authorization: Bearer secret-token"
    assert "abc123" not in redact_text(text)
    assert "secret-token" not in redact_text(text)
    payload = redact_payload({"cookie": "li_at=abc", "ok": "safe", "nested": {"access_token": "x"}})
    assert payload["cookie"] == "[REDACTED]"
    assert payload["ok"] == "safe"
    assert payload["nested"]["access_token"] == "[REDACTED]"


def test_render_organization_setup_prompt() -> None:
    from agents.setup_chat.prompts import render_setup_prompt
    rendered = render_setup_prompt("organization")
    assert "You are the Organization Setup Assistant." in rendered
    assert "mission, vision, business model" in rendered
    assert "Ask only for the next missing field" in rendered


def test_render_product_setup_prompt() -> None:
    from agents.setup_chat.prompts import render_setup_prompt
    rendered = render_setup_prompt("product")
    assert "You are the Product Setup Assistant." in rendered
    assert "value proposition, target customers, customer pain points" in rendered
    assert "Ask only for the next missing field" in rendered


def test_render_strategy_setup_prompt() -> None:
    from agents.setup_chat.prompts import render_setup_prompt
    rendered = render_setup_prompt("strategy")
    assert "You are the Strategy Setup Assistant." in rendered
    assert "prospect discovery strategy" in rendered
    assert "Ask only for the next missing field" in rendered


def test_setup_assistant_thread_ids() -> None:
    from agents.runtime import (
        build_org_setup_thread_id,
        build_product_setup_thread_id,
        build_strategy_setup_thread_id,
    )
    assert build_org_setup_thread_id("org123") == "LOOP_org123_org_setup_chat"
    assert build_product_setup_thread_id("org123", "prod456") == "LOOP_org123_prod456_product_setup_chat"
    assert build_strategy_setup_thread_id("org123", "prod456", "strat789") == "LOOP_org123_prod456_strat789_strategy_setup_chat"


