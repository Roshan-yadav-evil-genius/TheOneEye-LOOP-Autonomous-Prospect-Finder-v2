import copy
from typing import Any

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from application.form_definitions import PRODUCT_FORM, build_agent_profile_dict
from application.loop_service import ReentrantAsyncLock
from agents.setup_chat.common import SetupChatToolContext


@tool
async def get_product_profile(config: RunnableConfig) -> dict[str, Any]:
    """Read the entire product profile including basic info and all form sections."""
    ctx: SetupChatToolContext = config["configurable"]["tool_context"]
    if not ctx.product_id:
        return {"error": "No product context provided."}

    product = await ctx.service.get_product(ctx.product_id)

    icp_data = copy.deepcopy(product.icp_form)
    icp_data["identity"] = {
        "name": product.name,
        "kind": product.kind,
    }

    return build_agent_profile_dict(PRODUCT_FORM, icp_data)



async def _save_product_section(
    config: RunnableConfig, section_key: str, updates: dict[str, Any]
) -> str:
    ctx: SetupChatToolContext = config["configurable"]["tool_context"]
    if ctx.mode == "chat":
        return "Error: Cannot write in chat mode. Ask the user to switch to Agent mode."

    if not ctx.product_id:
        return "Error: No product context provided."

    if not updates:
        return "Error: No field values provided to update. Please pass at least one field value."

    lock = getattr(ctx.service, "_lock", None)
    if isinstance(lock, ReentrantAsyncLock):
        async with lock:
            return await _do_save_product_section(ctx, section_key, updates)
    return await _do_save_product_section(ctx, section_key, updates)


async def _do_save_product_section(
    ctx: SetupChatToolContext, section_key: str, updates: dict[str, Any]
) -> str:
    product = await ctx.service.get_product(ctx.product_id)
    current_form = copy.deepcopy(product.icp_form)

    form_key = "exclusion_rules" if section_key in ("exclusion_rules", "exclusion rules") else section_key

    if form_key == "identity":
        name = updates.get("name", product.name)
        kind = updates.get("kind", product.kind)
        current_form.pop("identity", None)

        await ctx.service.update_product_profile(
            ctx.product_id,
            form=current_form,
            name=name,
            kind=kind,
        )
    else:
        ARRAY_SECTIONS = (
            "customer_success_stories",
            "use_cases",
            "customer_triggers",
            "competitors",
            "differentiators",
            "keywords",
            "signals",
        )
        if form_key in ARRAY_SECTIONS:
            val = updates.get("items")
            current_form[form_key] = val if val is not None else []
        else:
            section_data = current_form.get(form_key, {})
            if not isinstance(section_data, dict):
                section_data = {}
            for field, value in updates.items():
                if isinstance(value, dict) and isinstance(section_data.get(field), dict):
                    section_data[field].update(value)
                else:
                    section_data[field] = value
            current_form[form_key] = section_data

        await ctx.service.update_product_profile(
            ctx.product_id,
            form=current_form,
            name=product.name,
            kind=product.kind,
        )

    return "Saved!"


@tool
async def set_product_identity(
    config: RunnableConfig,
    name: str | None = None,
    kind: str | None = None,
) -> str:
    """Agent mode only. Update the product identity section.

    Args:
        name: Product or service name as prospects recognize it.
        kind: Whether this offering is 'product' or 'service'.
    """
    updates = {}
    if name is not None:
        updates["name"] = name
    if kind is not None:
        updates["kind"] = kind
    return await _save_product_section(config, "identity", updates)


@tool
async def set_product_product_overview(
    config: RunnableConfig,
    summary: str | None = None,
    offering_scope: str | None = None,
) -> str:
    """Agent mode only. Update the product overview section.

    Args:
        summary: One-sentence summary describing the offering.
        offering_scope: What is included and excluded in the offering.
    """
    updates = {}
    if summary is not None:
        updates["summary"] = summary
    if offering_scope is not None:
        updates["offering_scope"] = offering_scope
    return await _save_product_section(config, "product_overview", updates)


@tool
async def set_product_problem_solved(
    config: RunnableConfig,
    primary: str | None = None,
    secondary: list[str] | None = None,
    cost_of_inaction: str | None = None,
) -> str:
    """Agent mode only. Update the problem solved section.

    Args:
        primary: Primary business problem or pain point this offering solves.
        secondary: List of secondary pain points.
        cost_of_inaction: What happens if the buyer does nothing.
    """
    updates = {}
    if primary is not None:
        updates["primary"] = primary
    if secondary is not None:
        updates["secondary"] = secondary
    if cost_of_inaction is not None:
        updates["cost_of_inaction"] = cost_of_inaction
    return await _save_product_section(config, "problem_solved", updates)


@tool
async def set_product_value_proposition(
    config: RunnableConfig,
    primary: str | None = None,
    outcomes: list[str] | None = None,
) -> str:
    """Agent mode only. Update the value proposition section.

    Args:
        primary: Core reason to buy / primary value proposition.
        outcomes: Top measurable outcomes or results achieved.
    """
    updates = {}
    if primary is not None:
        updates["primary"] = primary
    if outcomes is not None:
        updates["outcomes"] = outcomes
    return await _save_product_section(config, "value_proposition", updates)


@tool
async def set_product_icp(
    config: RunnableConfig,
    industries_primary: list[str] | None = None,
    industries_secondary: list[str] | None = None,
    industries_avoid: list[str] | None = None,
    company_size_employees_min: int | None = None,
    company_size_employees_max: int | None = None,
    company_size_revenue_min: int | None = None,
    company_size_revenue_max: int | None = None,
    geography_countries: list[str] | None = None,
    geography_regions: list[str] | None = None,
    geography_exclude_countries: list[str] | None = None,
    company_types: list[str] | None = None,
    maturity: list[str] | None = None,
) -> str:
    """Agent mode only. Update the ideal customer profile (ICP) section.

    Args:
        industries_primary: Best-fit primary industries.
        industries_secondary: Secondary target industries.
        industries_avoid: Poor-fit industries to avoid.
        company_size_employees_min: Minimum employee headcount.
        company_size_employees_max: Maximum employee headcount.
        company_size_revenue_min: Minimum annual revenue.
        company_size_revenue_max: Maximum annual revenue.
        geography_countries: Target countries.
        geography_regions: Target macro regions.
        geography_exclude_countries: Excluded countries.
        company_types: Firm types that fit (e.g. ['SaaS']).
        maturity: Company maturity signals (e.g. ['Series B']).
    """
    updates: dict[str, Any] = {}

    industries: dict[str, Any] = {}
    if industries_primary is not None:
        industries["primary"] = industries_primary
    if industries_secondary is not None:
        industries["secondary"] = industries_secondary
    if industries_avoid is not None:
        industries["avoid"] = industries_avoid
    if industries:
        updates["industries"] = industries

    company_size: dict[str, Any] = {}
    if company_size_employees_min is not None:
        company_size["employees_min"] = company_size_employees_min
    if company_size_employees_max is not None:
        company_size["employees_max"] = company_size_employees_max
    if company_size_revenue_min is not None:
        company_size["revenue_min"] = company_size_revenue_min
    if company_size_revenue_max is not None:
        company_size["revenue_max"] = company_size_revenue_max
    if company_size:
        updates["company_size"] = company_size

    geography: dict[str, Any] = {}
    if geography_countries is not None:
        geography["countries"] = geography_countries
    if geography_regions is not None:
        geography["regions"] = geography_regions
    if geography_exclude_countries is not None:
        geography["exclude_countries"] = geography_exclude_countries
    if geography:
        updates["geography"] = geography

    if company_types is not None:
        updates["company_types"] = company_types
    if maturity is not None:
        updates["maturity"] = maturity
    return await _save_product_section(config, "icp", updates)


@tool
async def set_product_buyer_personas(
    config: RunnableConfig,
    primary_titles: list[str] | None = None,
    economic_buyer: str | None = None,
    technical_evaluator: str | None = None,
    seniority: list[str] | None = None,
) -> str:
    """Agent mode only. Update the buyer personas section.

    Args:
        primary_titles: Job titles that own the purchase.
        economic_buyer: Role that signs or controls budget.
        technical_evaluator: Role that assesses technical fit.
        seniority: Typical seniority levels (e.g. ['VP', 'C-level']).
    """
    updates = {}
    if primary_titles is not None:
        updates["primary_titles"] = primary_titles
    if economic_buyer is not None:
        updates["economic_buyer"] = economic_buyer
    if technical_evaluator is not None:
        updates["technical_evaluator"] = technical_evaluator
    if seniority is not None:
        updates["seniority"] = seniority
    return await _save_product_section(config, "buyer_personas", updates)


@tool
async def set_product_use_cases(
    config: RunnableConfig,
    items: list[dict[str, Any]] | None = None,
) -> str:
    """Agent mode only. Update the product use cases section.

    Args:
        items: List of adoption scenario dicts, each with name, trigger, and outcome.
    """
    updates = {}
    if items is not None:
        updates["items"] = items
    return await _save_product_section(config, "use_cases", updates)


@tool
async def set_product_customer_triggers(
    config: RunnableConfig,
    items: list[str] | None = None,
) -> str:
    """Agent mode only. Update the customer triggers section.

    Args:
        items: List of events indicating a prospect may need this offering now.
    """
    updates = {}
    if items is not None:
        updates["items"] = items
    return await _save_product_section(config, "customer_triggers", updates)


@tool("set_product_exclusion_rules")
async def set_product_exclusion_rules(
    config: RunnableConfig,
    rules: list[str] | None = None,
    free_text: str | None = None,
) -> str:
    """Agent mode only. Update the product exclusion rules (blacklist) section.

    Args:
        rules: List of hard disqualifiers.
        free_text: Additional fit and exclusion notes.
    """
    updates = {}
    if rules is not None:
        updates["rules"] = rules
    if free_text is not None:
        updates["free_text"] = free_text
    return await _save_product_section(config, "exclusion_rules", updates)


@tool
async def set_product_competitors(
    config: RunnableConfig,
    items: list[dict[str, Any]] | None = None,
) -> str:
    """Agent mode only. Update the competitors section.

    Args:
        items: List of competitor dicts, each with name, website, and type ('direct' or 'indirect').
    """
    updates = {}
    if items is not None:
        updates["items"] = items
    return await _save_product_section(config, "competitors", updates)


@tool
async def set_product_differentiators(
    config: RunnableConfig,
    items: list[str] | None = None,
) -> str:
    """Agent mode only. Update the differentiators section.

    Args:
        items: List of reasons customers choose your offering over competitors.
    """
    updates = {}
    if items is not None:
        updates["items"] = items
    return await _save_product_section(config, "differentiators", updates)


@tool
async def set_product_pricing(
    config: RunnableConfig,
    model: str | None = None,
    typical_range: str | None = None,
    min_deal_size: str | None = None,
    sales_cycle: str | None = None,
    engagement_model: str | None = None,
) -> str:
    """Agent mode only. Update the product pricing section.

    Args:
        model: How you charge (e.g. 'subscription', 'per-seat').
        typical_range: Usual price band.
        min_deal_size: Smallest contract accepted.
        sales_cycle: Typical time to signed contract.
        engagement_model: How delivery starts (e.g. 'pilot', 'POC').
    """
    updates = {}
    if model is not None:
        updates["model"] = model
    if typical_range is not None:
        updates["typical_range"] = typical_range
    if min_deal_size is not None:
        updates["min_deal_size"] = min_deal_size
    if sales_cycle is not None:
        updates["sales_cycle"] = sales_cycle
    if engagement_model is not None:
        updates["engagement_model"] = engagement_model
    return await _save_product_section(config, "pricing", updates)


@tool
async def set_product_implementation(
    config: RunnableConfig,
    setup_effort: str | None = None,
    onboarding_duration: str | None = None,
    technical_requirements: list[str] | None = None,
    customer_resources: list[str] | None = None,
) -> str:
    """Agent mode only. Update the implementation section.

    Args:
        setup_effort: Relative effort ('low', 'medium', or 'high').
        onboarding_duration: Typical time until customer goes live.
        technical_requirements: Customer-side technical prerequisites.
        customer_resources: People or systems customer must provide.
    """
    updates = {}
    if setup_effort is not None:
        updates["setup_effort"] = setup_effort
    if onboarding_duration is not None:
        updates["onboarding_duration"] = onboarding_duration
    if technical_requirements is not None:
        updates["technical_requirements"] = technical_requirements
    if customer_resources is not None:
        updates["customer_resources"] = customer_resources
    return await _save_product_section(config, "implementation", updates)


@tool
async def set_product_integrations(
    config: RunnableConfig,
    must_have: list[str] | None = None,
    nice_to_have: list[str] | None = None,
    ecosystems: list[str] | None = None,
) -> str:
    """Agent mode only. Update the product integrations section.

    Args:
        must_have: Must-have integrations required for a viable deal.
        nice_to_have: Nice-to-have integrations that improve fit.
        ecosystems: Marketplaces or partner ecosystems.
    """
    updates = {}
    if must_have is not None:
        updates["must_have"] = must_have
    if nice_to_have is not None:
        updates["nice_to_have"] = nice_to_have
    if ecosystems is not None:
        updates["ecosystems"] = ecosystems
    return await _save_product_section(config, "integrations", updates)


@tool
async def set_product_customer_success_stories(
    config: RunnableConfig,
    items: list[dict[str, Any]] | None = None,
) -> str:
    """Agent mode only. Update the customer success stories section.

    Args:
        items: List of reference customer dicts with name, website, industry, why_they_bought, and outcome.
    """
    updates = {}
    if items is not None:
        updates["items"] = items
    return await _save_product_section(config, "customer_success_stories", updates)


@tool
async def set_product_compliance_restrictions(
    config: RunnableConfig,
    regions_blocked: list[str] | None = None,
    certifications: list[str] | None = None,
    legal_notes: str | None = None,
    technical_limits: list[str] | None = None,
) -> str:
    """Agent mode only. Update the compliance and restrictions section.

    Args:
        regions_blocked: Regions where product cannot be sold or deployed.
        certifications: Certifications this offering satisfies.
        legal_notes: Contract, privacy, or regulatory constraints.
        technical_limits: Hard technical restrictions.
    """
    updates = {}
    if regions_blocked is not None:
        updates["regions_blocked"] = regions_blocked
    if certifications is not None:
        updates["certifications"] = certifications
    if legal_notes is not None:
        updates["legal_notes"] = legal_notes
    if technical_limits is not None:
        updates["technical_limits"] = technical_limits
    return await _save_product_section(config, "compliance_restrictions", updates)


@tool
async def set_product_keywords(
    config: RunnableConfig,
    items: list[str] | None = None,
) -> str:
    """Agent mode only. Update the product keywords section.

    Args:
        items: Search terms prospects use when looking for this offering.
    """
    updates = {}
    if items is not None:
        updates["items"] = items
    return await _save_product_section(config, "keywords", updates)


@tool
async def set_product_signals(
    config: RunnableConfig,
    items: list[str] | None = None,
) -> str:
    """Agent mode only. Update the product signals section.

    Args:
        items: Public indicators of active need.
    """
    updates = {}
    if items is not None:
        updates["items"] = items
    return await _save_product_section(config, "signals", updates)


def get_product_tools() -> list[Any]:
    """Return all product setup chat tools."""
    return [
        get_product_profile,
        set_product_identity,
        set_product_product_overview,
        set_product_problem_solved,
        set_product_value_proposition,
        set_product_icp,
        set_product_buyer_personas,
        set_product_use_cases,
        set_product_customer_triggers,
        set_product_exclusion_rules,
        set_product_competitors,
        set_product_differentiators,
        set_product_pricing,
        set_product_implementation,
        set_product_integrations,
        set_product_customer_success_stories,
        set_product_compliance_restrictions,
        set_product_keywords,
        set_product_signals,
    ]
