"""Map sales-strategy bundles into AgentWithBrowser prompt placeholders."""

from __future__ import annotations

import json
from typing import Any


def _as_text(value: Any, fallback: str = "Not specified") -> str:
    if value is None:
        return fallback
    if isinstance(value, str):
        return value.strip() or fallback
    if isinstance(value, (list, tuple)):
        return ", ".join(str(item) for item in value) if value else fallback
    if isinstance(value, dict):
        return json.dumps(value, indent=2, default=str)
    return str(value)


def _dig(data: dict[str, Any], *path: str, default: Any = None) -> Any:
    current: Any = data
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def company_finder_prompt_values(bundle: dict[str, Any]) -> dict[str, str]:
    strategy = bundle.get("sales_strategy") or {}
    form = strategy.get("sales_strategy_form") or {}
    product = bundle.get("product") or {}
    icp = product.get("icp_form") or {}
    overview = form.get("overview") or {}
    return {
        "sales_objective": _as_text(
            overview.get("target_companies_narrative") or overview.get("description")
        ),
        "target_industries": _as_text(
            _dig(form, "priority_industries", "primary")
            or _dig(icp, "icp", "industries", "primary")
        ),
        "company_size": _as_text(form.get("company_size") or _dig(icp, "icp", "company_size")),
        "target_regions": _as_text(
            form.get("priority_geographies") or _dig(icp, "icp", "geographies")
        ),
        "business_characteristics": _as_text(
            form.get("target_company_profile") or form.get("business_characteristics")
        ),
        "qualification_criteria": _as_text(form.get("qualification_criteria")),
        "buying_signals": _as_text(
            _dig(form, "buying_signals", "selected") or form.get("buying_signals")
        ),
        "exclusion_rules": _as_text(form.get("exclusion_rules") or form.get("blacklist_criteria")),
        "priority_rules": _as_text(form.get("prioritization_rules")),
        "search_constraints": _as_text(form.get("prospecting_strategy") or form.get("search_constraints")),
    }


def contact_finder_prompt_values(
    bundle: dict[str, Any], company: dict[str, Any] | None = None
) -> dict[str, str]:
    strategy = bundle.get("sales_strategy") or {}
    form = strategy.get("sales_strategy_form") or {}
    product = bundle.get("product") or {}
    icp = product.get("icp_form") or {}
    overview = form.get("overview") or {}
    company = company or {}
    profile = company.get("profile") or {}
    return {
        "company_name": _as_text(company.get("name")),
        "company_website": _as_text(company.get("domain") or company.get("website")),
        "company_summary": _as_text(profile.get("summary") or company.get("selection_reason")),
        "industry": _as_text(profile.get("industry") or _dig(form, "priority_industries", "primary")),
        "employee_count": _as_text(profile.get("employee_count") or profile.get("headcount")),
        "sales_objective": _as_text(
            overview.get("target_companies_narrative") or overview.get("description")
        ),
        "solution_category": _as_text(
            _dig(icp, "product_overview", "summary") or product.get("kind")
        ),
        "target_roles": _as_text(
            _dig(form, "target_decision_makers", "primary_titles")
            or _dig(icp, "buyer_personas", "primary_titles")
        ),
        "preferred_job_titles": _as_text(
            _dig(form, "target_decision_makers", "preferred_titles")
            or _dig(form, "target_decision_makers", "primary_titles")
            or _dig(icp, "buyer_personas", "primary_titles")
        ),
        "target_departments": _as_text(
            _dig(form, "target_decision_makers", "departments")
        ),
        "prospect_qualification_criteria": _as_text(
            form.get("prospect_qualification_criteria") or form.get("qualification_criteria")
        ),
        "prospect_exclusion_rules": _as_text(
            form.get("prospect_exclusion_rules") or form.get("exclusion_rules")
        ),
        "prioritization_rules": _as_text(form.get("prioritization_rules")),
        "search_constraints": _as_text(form.get("prospecting_strategy") or form.get("search_constraints")),
    }


def brain_prompt_values() -> dict[str, str]:
    return {}


def browser_prompt_values() -> dict[str, str]:
    return {}


def sales_manager_prompt_values() -> dict[str, str]:
    return {}
