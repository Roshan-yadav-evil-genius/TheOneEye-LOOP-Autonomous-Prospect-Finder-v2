import copy
from typing import Any

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from application.form_definitions import STRATEGY_FORM, build_agent_profile_dict
from application.loop_service import ReentrantAsyncLock
from agents.setup_chat.common import SetupChatToolContext


@tool
async def get_strategy_profile(config: RunnableConfig) -> dict[str, Any]:
    """Read the entire strategy profile including basic info and all form sections."""
    ctx: SetupChatToolContext = config["configurable"]["tool_context"]
    if not ctx.strategy_id:
        return {"error": "No strategy context provided."}

    strategy = await ctx.service.get_strategy(ctx.strategy_id)

    strategy_data = copy.deepcopy(strategy.sales_strategy_form)

    overview = strategy_data.get("overview")
    if not isinstance(overview, dict):
        overview = {}
    if not overview.get("name") and strategy.name:
        overview["name"] = strategy.name
    strategy_data["overview"] = overview

    run_targets = strategy_data.get("run_targets")
    if not isinstance(run_targets, dict):
        run_targets = {}
    if run_targets.get("target_companies") is None and strategy.target_companies is not None:
        run_targets["target_companies"] = strategy.target_companies
    if run_targets.get("contacts_per_company_default") is None and strategy.contacts_per_company_default is not None:
        run_targets["contacts_per_company_default"] = strategy.contacts_per_company_default
    strategy_data["run_targets"] = run_targets

    return build_agent_profile_dict(STRATEGY_FORM, strategy_data)



async def _save_strategy_section(
    config: RunnableConfig, section_key: str, updates: dict[str, Any]
) -> str:
    ctx: SetupChatToolContext = config["configurable"]["tool_context"]
    if ctx.mode == "chat":
        return "Error: Cannot write in chat mode. Ask the user to switch to Agent mode."

    if not ctx.strategy_id:
        return "Error: No strategy context provided."

    if not updates:
        return "Error: No field values provided to update. Please pass at least one field value."

    lock = getattr(ctx.service, "_lock", None)
    if isinstance(lock, ReentrantAsyncLock):
        async with lock:
            return await _do_save_strategy_section(ctx, section_key, updates)
    return await _do_save_strategy_section(ctx, section_key, updates)


async def _do_save_strategy_section(
    ctx: SetupChatToolContext, section_key: str, updates: dict[str, Any]
) -> str:
    strategy = await ctx.service.get_strategy(ctx.strategy_id)
    current_form = copy.deepcopy(strategy.sales_strategy_form)

    ARRAY_SECTIONS = ("best_practices", "experiments")

    if section_key in ARRAY_SECTIONS:
        val = updates.get("items")
        current_form[section_key] = val if val is not None else []
    else:
        section_data = current_form.get(section_key, {})
        if not isinstance(section_data, dict):
            section_data = {}
        for field, value in updates.items():
            section_data[field] = value
        current_form[section_key] = section_data

    name = updates.get("name") if section_key == "overview" else None

    await ctx.service.update_strategy_profile(
        ctx.strategy_id,
        form=current_form,
        name=name,
    )

    return "Saved!"


@tool
async def set_strategy_overview(
    config: RunnableConfig,
    name: str | None = None,
    description: str | None = None,
    target_companies_narrative: str | None = None,
) -> str:
    """Agent mode only. Update the strategy overview section.

    Args:
        name: Short label/name for this sales strategy.
        description: Description of what this strategy aims to achieve.
        target_companies_narrative: Description of ideal target companies in plain language.
    """
    updates = {}
    if name is not None:
        updates["name"] = name
    if description is not None:
        updates["description"] = description
    if target_companies_narrative is not None:
        updates["target_companies_narrative"] = target_companies_narrative
    return await _save_strategy_section(config, "overview", updates)


@tool
async def set_strategy_run_targets(
    config: RunnableConfig,
    target_companies: int | None = None,
    contacts_per_company_default: int | None = None,
) -> str:
    """Agent mode only. Update the strategy run targets section.

    Args:
        target_companies: Total number of companies to target in this strategy run.
        contacts_per_company_default: Default number of prospects/contacts per company.
    """
    updates = {}
    if target_companies is not None:
        updates["target_companies"] = target_companies
    if contacts_per_company_default is not None:
        updates["contacts_per_company_default"] = contacts_per_company_default
    return await _save_strategy_section(config, "run_targets", updates)


@tool
async def set_strategy_target_company_profile(
    config: RunnableConfig,
    company_types: list[str] | None = None,
    characteristics: list[str] | None = None,
    similar_companies: list[dict[str, Any]] | None = None,
    keywords: list[str] | None = None,
    problems_they_should_have: list[str] | None = None,
) -> str:
    """Agent mode only. Update the strategy target company profile section.

    Args:
        company_types: List of firm types to pursue (e.g. ['B2B SaaS']).
        characteristics: Traits making a company a strong fit.
        similar_companies: Example companies that represent ideal targets (list of dicts with name and website_url).
        keywords: Search terms to find lookalike target companies.
        problems_they_should_have: Pains ideal target companies feel.
    """
    updates = {}
    if company_types is not None:
        updates["company_types"] = company_types
    if characteristics is not None:
        updates["characteristics"] = characteristics
    if similar_companies is not None:
        updates["similar_companies"] = similar_companies
    if keywords is not None:
        updates["keywords"] = keywords
    if problems_they_should_have is not None:
        updates["problems_they_should_have"] = problems_they_should_have
    return await _save_strategy_section(config, "target_company_profile", updates)


@tool
async def set_strategy_target_decision_makers(
    config: RunnableConfig,
    primary_titles: list[str] | None = None,
    secondary_titles: list[str] | None = None,
    seniority_levels: list[str] | None = None,
    department_functions: list[str] | None = None,
    seniority_order: list[str] | None = None,
    contact_buying_signals: list[str] | None = None,
) -> str:
    """Agent mode only. Update the strategy target decision makers section.

    Args:
        primary_titles: First-choice job titles to target.
        secondary_titles: Backup job titles.
        seniority_levels: Target seniority tiers (e.g. ['C-Suite', 'VP', 'Director']).
        department_functions: Target department functions (e.g. ['Engineering', 'Sales']).
        seniority_order: Preferred seniority hierarchy sequence.
        contact_buying_signals: Per-contact readiness signals.
    """
    updates = {}
    if primary_titles is not None:
        updates["primary_titles"] = primary_titles
    if secondary_titles is not None:
        updates["secondary_titles"] = secondary_titles
    if seniority_levels is not None:
        updates["seniority_levels"] = seniority_levels
    if department_functions is not None:
        updates["department_functions"] = department_functions
    if seniority_order is not None:
        updates["seniority_order"] = seniority_order
    if contact_buying_signals is not None:
        updates["contact_buying_signals"] = contact_buying_signals
    return await _save_strategy_section(config, "target_decision_makers", updates)


@tool
async def set_strategy_priority_industries(
    config: RunnableConfig,
    primary: list[str] | None = None,
    secondary: list[str] | None = None,
    deprioritized: list[str] | None = None,
) -> str:
    """Agent mode only. Update the strategy priority industries section.

    Args:
        primary: First priority industries to target.
        secondary: Secondary industries to target when quota allows.
        deprioritized: Industries to pursue only if no better matches exist.
    """
    updates = {}
    if primary is not None:
        updates["primary"] = primary
    if secondary is not None:
        updates["secondary"] = secondary
    if deprioritized is not None:
        updates["deprioritized"] = deprioritized
    return await _save_strategy_section(config, "priority_industries", updates)


@tool
async def set_strategy_priority_geographies(
    config: RunnableConfig,
    countries: list[str] | None = None,
    regions: list[str] | None = None,
    cities: list[str] | None = None,
    remote_only: bool | None = None,
    exclude_countries: list[str] | None = None,
) -> str:
    """Agent mode only. Update the strategy priority geographies section.

    Args:
        countries: Target countries.
        regions: Target macro regions.
        cities: Specific cities to prioritize.
        remote_only: Whether to target fully remote companies only.
        exclude_countries: Countries to skip.
    """
    updates = {}
    if countries is not None:
        updates["countries"] = countries
    if regions is not None:
        updates["regions"] = regions
    if cities is not None:
        updates["cities"] = cities
    if remote_only is not None:
        updates["remote_only"] = remote_only
    if exclude_countries is not None:
        updates["exclude_countries"] = exclude_countries
    return await _save_strategy_section(config, "priority_geographies", updates)


@tool
async def set_strategy_company_size(
    config: RunnableConfig,
    employees_min: int | None = None,
    employees_max: int | None = None,
    revenue_min: int | None = None,
    revenue_max: int | None = None,
    segments: list[str] | None = None,
) -> str:
    """Agent mode only. Update the strategy company size section.

    Args:
        employees_min: Minimum employee count.
        employees_max: Maximum employee count.
        revenue_min: Minimum annual revenue.
        revenue_max: Maximum annual revenue.
        segments: Size or stage bands (e.g. ['mid-market']).
    """
    updates = {}
    if employees_min is not None:
        updates["employees_min"] = employees_min
    if employees_max is not None:
        updates["employees_max"] = employees_max
    if revenue_min is not None:
        updates["revenue_min"] = revenue_min
    if revenue_max is not None:
        updates["revenue_max"] = revenue_max
    if segments is not None:
        updates["segments"] = segments
    return await _save_strategy_section(config, "company_size", updates)


@tool
async def set_strategy_buying_signals(
    config: RunnableConfig,
    selected: list[str] | None = None,
    custom: list[str] | None = None,
) -> str:
    """Agent mode only. Update the strategy buying signals section.

    Args:
        selected: Selected predefined signals (e.g. ['Recently funded', 'Hiring AEs']).
        custom: Custom buying signal descriptions.
    """
    updates = {}
    if selected is not None:
        updates["selected"] = selected
    if custom is not None:
        updates["custom"] = custom
    return await _save_strategy_section(config, "buying_signals", updates)


@tool
async def set_strategy_prospecting_strategy(
    config: RunnableConfig,
    sources: list[str] | None = None,
    excluded_domain_types: list[str] | None = None,
) -> str:
    """Agent mode only. Update the strategy prospecting sources section.

    Args:
        sources: Where to discover target companies (e.g. ['LinkedIn', 'Crunchbase']).
        excluded_domain_types: Types of sites to skip during discovery (e.g. ['Job boards']).
    """
    updates = {}
    if sources is not None:
        updates["sources"] = sources
    if excluded_domain_types is not None:
        updates["excluded_domain_types"] = excluded_domain_types
    return await _save_strategy_section(config, "prospecting_strategy", updates)





@tool
async def set_strategy_prioritization_rules(
    config: RunnableConfig,
    rules: list[str] | None = None,
) -> str:
    """Agent mode only. Update the strategy prioritization rules section.

    Args:
        rules: Ranking rules for companies or contacts when quota is limited.
    """
    updates = {}
    if rules is not None:
        updates["rules"] = rules
    return await _save_strategy_section(config, "prioritization_rules", updates)


@tool
async def set_strategy_competitor_targeting(
    config: RunnableConfig,
    incumbents_to_target: list[str] | None = None,
    switch_triggers: list[str] | None = None,
    avoid_unless_scaling: list[str] | None = None,
) -> str:
    """Agent mode only. Update the strategy competitor targeting section.

    Args:
        incumbents_to_target: Competitor products to displace.
        switch_triggers: Events that encourage prospects to switch.
        avoid_unless_scaling: Incumbents to skip unless target is growing fast.
    """
    updates = {}
    if incumbents_to_target is not None:
        updates["incumbents_to_target"] = incumbents_to_target
    if switch_triggers is not None:
        updates["switch_triggers"] = switch_triggers
    if avoid_unless_scaling is not None:
        updates["avoid_unless_scaling"] = avoid_unless_scaling
    return await _save_strategy_section(config, "competitor_targeting", updates)


@tool
async def set_strategy_exclusion_rules(
    config: RunnableConfig,
    rules: list[str] | None = None,
    companies: list[str] | None = None,
    domains: list[str] | None = None,
    industries: list[str] | None = None,
    regions: list[str] | None = None,
) -> str:
    """Agent mode only. Update the strategy exclusion rules section.

    Args:
        rules: Conditions that disqualify a company from outreach.
        companies: Named companies to never contact.
        domains: Email or web domains to block.
        industries: Industries excluded from this run.
        regions: Regions excluded from this run.
    """
    updates = {}
    if rules is not None:
        updates["rules"] = rules
    if companies is not None:
        updates["companies"] = companies
    if domains is not None:
        updates["domains"] = domains
    if industries is not None:
        updates["industries"] = industries
    if regions is not None:
        updates["regions"] = regions
    return await _save_strategy_section(config, "exclusion_rules", updates)


@tool
async def set_strategy_experiments(
    config: RunnableConfig,
    items: list[dict[str, Any]] | None = None,
) -> str:
    """Agent mode only. Update the strategy experiments section.

    Args:
        items: List of active test dicts with hypothesis, variant, success_criteria, notes.
    """
    updates = {}
    if items is not None:
        updates["items"] = items
    return await _save_strategy_section(config, "experiments", updates)


@tool
async def set_strategy_success_metrics(
    config: RunnableConfig,
    targets: list[str] | None = None,
) -> str:
    """Agent mode only. Update the strategy success metrics section.

    Args:
        targets: Measurable operational goals (e.g. ['10 meetings booked']).
    """
    updates = {}
    if targets is not None:
        updates["targets"] = targets
    return await _save_strategy_section(config, "success_metrics", updates)


@tool
async def set_strategy_qualification_criteria(
    config: RunnableConfig,
    must_have: list[str] | None = None,
    nice_to_have: list[str] | None = None,
    min_confidence_hint: int | None = None,
) -> str:
    """Agent mode only. Update the strategy qualification criteria section.

    Args:
        must_have: Mandatory attributes a company must possess.
        nice_to_have: Attributes that improve target priority.
        min_confidence_hint: Lowest agent confidence score to retain a company.
    """
    updates = {}
    if must_have is not None:
        updates["must_have"] = must_have
    if nice_to_have is not None:
        updates["nice_to_have"] = nice_to_have
    if min_confidence_hint is not None:
        updates["min_confidence_hint"] = min_confidence_hint
    return await _save_strategy_section(config, "qualification_criteria", updates)


def get_strategy_tools() -> list[Any]:
    """Return all sales strategy setup chat tools."""
    return [
        get_strategy_profile,
        set_strategy_overview,
        set_strategy_run_targets,
        set_strategy_target_decision_makers,
        set_strategy_target_company_profile,
        set_strategy_priority_industries,
        set_strategy_priority_geographies,
        set_strategy_company_size,
        set_strategy_buying_signals,
        set_strategy_prospecting_strategy,
        set_strategy_competitor_targeting,
        set_strategy_qualification_criteria,
        set_strategy_prioritization_rules,
        set_strategy_exclusion_rules,
        set_strategy_experiments,
        set_strategy_success_metrics,
    ]
