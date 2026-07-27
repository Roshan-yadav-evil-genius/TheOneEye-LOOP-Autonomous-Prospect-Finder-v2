import copy
from typing import Any

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from application.form_definitions import ORGANIZATION_FORM
from application.loop_service import ReentrantAsyncLock
from agents.setup_chat.common import SetupChatToolContext


@tool
async def get_organization_profile(config: RunnableConfig) -> dict[str, Any]:
    """Read the entire organization profile including identity and all form sections."""
    ctx: SetupChatToolContext = config["configurable"]["tool_context"]
    org = await ctx.service.get_organization(ctx.organization_id)

    full_org_form = {}
    for section in ORGANIZATION_FORM.sections:
        val = org.org_form.get(section.key)
        if val is None:
            if section.key in ("unique_strengths", "case_studies"):
                val = []
            else:
                val = {}
        elif isinstance(val, dict) and "items" in val:
            val = val["items"]
        full_org_form[section.key] = val

    return {
        "identity": {
            "name": org.name,
            "website": org.website,
            "primary_contact_email": org.primary_contact_email,
        },
        "org_form": full_org_form,
    }


async def _save_org_section(
    config: RunnableConfig, section_key: str, updates: dict[str, Any]
) -> dict[str, Any] | str:
    ctx: SetupChatToolContext = config["configurable"]["tool_context"]
    if ctx.mode == "chat":
        return "Error: Cannot write in chat mode. Ask the user to switch to Agent mode."

    if not updates:
        return "Error: No field values provided to update. Please pass at least one field value."

    lock = getattr(ctx.service, "_lock", None)
    if isinstance(lock, ReentrantAsyncLock):
        async with lock:
            return await _do_save_org_section(ctx, section_key, updates)
    return await _do_save_org_section(ctx, section_key, updates)


async def _do_save_org_section(
    ctx: SetupChatToolContext, section_key: str, updates: dict[str, Any]
) -> dict[str, Any]:
    org = await ctx.service.get_organization(ctx.organization_id)
    current_form = copy.deepcopy(org.org_form)

    if section_key == "identity":
        name = updates.get("name", org.name)
        website = updates.get("website", org.website)
        email = updates.get("primary_contact_email", org.primary_contact_email)

        await ctx.service.update_organization_profile(
            ctx.organization_id,
            form=current_form,
            name=name,
            website=str(website) if website else None,
            primary_contact_email=email,
        )
    else:
        section_data = current_form.get(section_key, {})
        if not isinstance(section_data, dict):
            section_data = {}

        if section_key in ("unique_strengths", "case_studies"):
            val = (
                updates.get("items")
                if updates.get("items") is not None
                else updates.get("strengths")
            )
            current_form[section_key] = val if val is not None else []
        else:
            for field, value in updates.items():
                section_data[field] = value
            current_form[section_key] = section_data

        await ctx.service.update_organization_profile(
            ctx.organization_id,
            form=current_form,
            name=org.name,
            website=org.website,
            primary_contact_email=org.primary_contact_email,
        )

    return {"section": section_key, "data": updates}


@tool
async def set_identity(
    config: RunnableConfig,
    name: str | None = None,
    website: str | None = None,
    primary_contact_email: str | None = None,
) -> dict[str, Any] | str:
    """Agent mode only. Update the identity section of the organization profile.

    Args:
        name: Legal or brand name of the organization.
        website: Canonical company website URL.
        primary_contact_email: Optional contact email for notifications.
    """
    updates = {}
    if name is not None:
        updates["name"] = name
    if website is not None:
        updates["website"] = website
    if primary_contact_email is not None:
        updates["primary_contact_email"] = primary_contact_email
    return await _save_org_section(config, "identity", updates)


@tool
async def set_company_overview(
    config: RunnableConfig,
    description: str | None = None,
    mission: str | None = None,
    founded_year: int | None = None,
    headquarters: str | None = None,
) -> dict[str, Any] | str:
    """Agent mode only. Update the company overview section.

    Args:
        description: 2-5 sentences describing what the company does.
        mission: 1-2 sentences on company purpose or long-term vision.
        founded_year: Four-digit year the company was founded.
        headquarters: City and country of headquarters (e.g. 'San Francisco, US').
    """
    updates = {}
    if description is not None:
        updates["description"] = description
    if mission is not None:
        updates["mission"] = mission
    if founded_year is not None:
        updates["founded_year"] = founded_year
    if headquarters is not None:
        updates["headquarters"] = headquarters
    return await _save_org_section(config, "company_overview", updates)


@tool
async def set_industry(
    config: RunnableConfig,
    primary: str | None = None,
    secondary: list[str] | None = None,
    sub_verticals: list[str] | None = None,
) -> dict[str, Any] | str:
    """Agent mode only. Update the industry section.

    Args:
        primary: Main industry label (e.g. 'Software').
        secondary: List of secondary industry labels.
        sub_verticals: List of sub-verticals or niches served.
    """
    updates = {}
    if primary is not None:
        updates["primary"] = primary
    if secondary is not None:
        updates["secondary"] = secondary
    if sub_verticals is not None:
        updates["sub_verticals"] = sub_verticals
    return await _save_org_section(config, "industry", updates)


@tool
async def set_business_model(
    config: RunnableConfig,
    types: list[str] | None = None,
    description: str | None = None,
) -> dict[str, Any] | str:
    """Agent mode only. Update the business model section.

    Args:
        types: List of model types (e.g. ['B2B', 'SaaS']).
        description: Description of revenue streams and delivery model.
    """
    updates = {}
    if types is not None:
        updates["types"] = types
    if description is not None:
        updates["description"] = description
    return await _save_org_section(config, "business_model", updates)


@tool
async def set_company_size(
    config: RunnableConfig,
    employees: str | None = None,
    revenue_range: str | None = None,
    years_in_business: int | None = None,
) -> dict[str, Any] | str:
    """Agent mode only. Update the company size section.

    Args:
        employees: Employee headcount or range (e.g. '51-200').
        revenue_range: Annual revenue range.
        years_in_business: Years operating under current brand.
    """
    updates = {}
    if employees is not None:
        updates["employees"] = employees
    if revenue_range is not None:
        updates["revenue_range"] = revenue_range
    if years_in_business is not None:
        updates["years_in_business"] = years_in_business
    return await _save_org_section(config, "company_size", updates)


@tool
async def set_target_markets(
    config: RunnableConfig,
    countries: list[str] | None = None,
    regions: list[str] | None = None,
    industries: list[str] | None = None,
    excluded: list[str] | None = None,
) -> dict[str, Any] | str:
    """Agent mode only. Update the target markets section.

    Args:
        countries: List of target countries.
        regions: List of target macro regions.
        industries: List of target industry verticals.
        excluded: List of markets/regions not pursued.
    """
    updates = {}
    if countries is not None:
        updates["countries"] = countries
    if regions is not None:
        updates["regions"] = regions
    if industries is not None:
        updates["industries"] = industries
    if excluded is not None:
        updates["excluded"] = excluded
    return await _save_org_section(config, "target_markets", updates)


@tool
async def set_existing_customers(
    config: RunnableConfig,
    typical_profile: str | None = None,
    strong_industries: list[str] | None = None,
) -> dict[str, Any] | str:
    """Agent mode only. Update the existing customers section.

    Args:
        typical_profile: Typical customer profile (size, industry, traits).
        strong_industries: List of industries with strongest traction.
    """
    updates = {}
    if typical_profile is not None:
        updates["typical_profile"] = typical_profile
    if strong_industries is not None:
        updates["strong_industries"] = strong_industries
    return await _save_org_section(config, "existing_customers", updates)


@tool
async def set_customer_segments(
    config: RunnableConfig,
    primary: list[str] | None = None,
    secondary: list[str] | None = None,
    avoid: list[str] | None = None,
) -> dict[str, Any] | str:
    """Agent mode only. Update the customer segments section.

    Args:
        primary: List of primary ideal customer profile segments.
        secondary: List of secondary segments accepted.
        avoid: List of segments to decline or deprioritize.
    """
    updates = {}
    if primary is not None:
        updates["primary"] = primary
    if secondary is not None:
        updates["secondary"] = secondary
    if avoid is not None:
        updates["avoid"] = avoid
    return await _save_org_section(config, "customer_segments", updates)


@tool
async def set_brand_positioning(
    config: RunnableConfig,
    position: str | None = None,
    statement: str | None = None,
) -> dict[str, Any] | str:
    """Agent mode only. Update the brand positioning section.

    Args:
        position: Market tier or stance (e.g. 'premium niche').
        statement: 2-4 sentences on who you serve and why you win.
    """
    updates = {}
    if position is not None:
        updates["position"] = position
    if statement is not None:
        updates["statement"] = statement
    return await _save_org_section(config, "brand_positioning", updates)


@tool
async def set_unique_strengths(
    config: RunnableConfig,
    items: list[str] | None = None,
    strengths: list[str] | None = None,
) -> dict[str, Any] | str:
    """Agent mode only. Update the unique strengths section.

    Args:
        items: List of distinct competitive advantages.
        strengths: Alias for items (list of competitive advantages).
    """
    updates = {}
    if items is not None:
        updates["items"] = items
    if strengths is not None:
        updates["strengths"] = strengths
    return await _save_org_section(config, "unique_strengths", updates)


@tool
async def set_competitive_landscape(
    config: RunnableConfig,
    competitors: list[str] | None = None,
    differentiators: list[str] | None = None,
    win_loss_notes: str | None = None,
) -> dict[str, Any] | str:
    """Agent mode only. Update the competitive landscape section.

    Args:
        competitors: List of direct competitor names.
        differentiators: List of reasons customers choose your organization.
        win_loss_notes: Common win/loss reasons.
    """
    updates = {}
    if competitors is not None:
        updates["competitors"] = competitors
    if differentiators is not None:
        updates["differentiators"] = differentiators
    if win_loss_notes is not None:
        updates["win_loss_notes"] = win_loss_notes
    return await _save_org_section(config, "competitive_landscape", updates)


@tool
async def set_sales_goals(
    config: RunnableConfig,
    revenue_targets: str | None = None,
    strategic_industries: list[str] | None = None,
    expansion_markets: list[str] | None = None,
) -> dict[str, Any] | str:
    """Agent mode only. Update the sales goals section.

    Args:
        revenue_targets: Quarterly or annual revenue/pipeline targets.
        strategic_industries: List of strategic priority industries.
        expansion_markets: List of expansion markets or geographies.
    """
    updates = {}
    if revenue_targets is not None:
        updates["revenue_targets"] = revenue_targets
    if strategic_industries is not None:
        updates["strategic_industries"] = strategic_industries
    if expansion_markets is not None:
        updates["expansion_markets"] = expansion_markets
    return await _save_org_section(config, "sales_goals", updates)


@tool
async def set_partnership_strategy(
    config: RunnableConfig,
    model: str | None = None,
    regions: str | None = None,
    notes: str | None = None,
) -> dict[str, Any] | str:
    """Agent mode only. Update the partnership strategy section.

    Args:
        model: GTM motion (e.g. 'direct', 'reseller', 'referral', 'hybrid').
        regions: Territories sold primarily through partners.
        notes: Partner restrictions or exclusivity terms.
    """
    updates = {}
    if model is not None:
        updates["model"] = model
    if regions is not None:
        updates["regions"] = regions
    if notes is not None:
        updates["notes"] = notes
    return await _save_org_section(config, "partnership_strategy", updates)


@tool
async def set_delivery_capability(
    config: RunnableConfig,
    geography: list[str] | None = None,
    languages: list[str] | None = None,
    support_hours: str | None = None,
    implementation_capacity: str | None = None,
) -> dict[str, Any] | str:
    """Agent mode only. Update the delivery capability section.

    Args:
        geography: Countries or regions where implementation occurs.
        languages: Languages supported.
        support_hours: Coverage window (e.g. '9-5 ET').
        implementation_capacity: Team size or concurrent project limits.
    """
    updates = {}
    if geography is not None:
        updates["geography"] = geography
    if languages is not None:
        updates["languages"] = languages
    if support_hours is not None:
        updates["support_hours"] = support_hours
    if implementation_capacity is not None:
        updates["implementation_capacity"] = implementation_capacity
    return await _save_org_section(config, "delivery_capability", updates)


@tool
async def set_certifications_compliance(
    config: RunnableConfig,
    certifications: list[str] | None = None,
    frameworks: list[str] | None = None,
    data_residency: str | None = None,
) -> dict[str, Any] | str:
    """Agent mode only. Update the certifications and compliance section.

    Args:
        certifications: List of certifications (e.g. ISO 27001, SOC 2).
        frameworks: List of compliance frameworks (e.g. GDPR, HIPAA).
        data_residency: Data residency and security commitments.
    """
    updates = {}
    if certifications is not None:
        updates["certifications"] = certifications
    if frameworks is not None:
        updates["frameworks"] = frameworks
    if data_residency is not None:
        updates["data_residency"] = data_residency
    return await _save_org_section(config, "certifications_compliance", updates)


@tool
async def set_technology_expertise(
    config: RunnableConfig,
    cloud: list[str] | None = None,
    languages: list[str] | None = None,
    platforms: list[str] | None = None,
    tools: list[str] | None = None,
) -> dict[str, Any] | str:
    """Agent mode only. Update the technology expertise section.

    Args:
        cloud: Cloud providers (AWS, Azure, GCP).
        languages: Languages or frameworks supported.
        platforms: CRM, ERP, or vertical platforms.
        tools: Delivery or internal tools.
    """
    updates = {}
    if cloud is not None:
        updates["cloud"] = cloud
    if languages is not None:
        updates["languages"] = languages
    if platforms is not None:
        updates["platforms"] = platforms
    if tools is not None:
        updates["tools"] = tools
    return await _save_org_section(config, "technology_expertise", updates)


@tool
async def set_case_studies(
    config: RunnableConfig,
    items: list[dict[str, Any]] | None = None,
) -> dict[str, Any] | str:
    """Agent mode only. Update the case studies section.

    Args:
        items: List of case study dicts, each with keys title, customer_type, challenge, outcome, link.
    """
    updates = {}
    if items is not None:
        updates["items"] = items
    return await _save_org_section(config, "case_studies", updates)


@tool
async def set_references(
    config: RunnableConfig,
    clients: list[dict[str, Any]] | None = None,
    industries: list[str] | None = None,
) -> dict[str, Any] | str:
    """Agent mode only. Update the references section.

    Args:
        clients: List of client dicts with name and website.
        industries: List of reference industries.
    """
    updates = {}
    if clients is not None:
        updates["clients"] = clients
    if industries is not None:
        updates["industries"] = industries
    return await _save_org_section(config, "references", updates)


@tool
async def set_pricing_position(
    config: RunnableConfig,
    band: str | None = None,
    typical_contract_size: str | None = None,
    positioning_notes: str | None = None,
) -> dict[str, Any] | str:
    """Agent mode only. Update the pricing position section.

    Args:
        band: Price band (e.g. 'mid-market').
        typical_contract_size: Usual deal size or ACV band.
        positioning_notes: Notes on how pricing is justified against alternatives.
    """
    updates = {}
    if band is not None:
        updates["band"] = band
    if typical_contract_size is not None:
        updates["typical_contract_size"] = typical_contract_size
    if positioning_notes is not None:
        updates["positioning_notes"] = positioning_notes
    return await _save_org_section(config, "pricing_position", updates)


@tool
async def set_sales_process(
    config: RunnableConfig,
    stages: list[str] | None = None,
    cycle_length: str | None = None,
    stakeholders: list[str] | None = None,
) -> dict[str, Any] | str:
    """Agent mode only. Update the sales process section.

    Args:
        stages: List of sales stages from first touch to contract.
        cycle_length: Typical days or weeks to close a deal.
        stakeholders: List of roles that must be involved.
    """
    updates = {}
    if stages is not None:
        updates["stages"] = stages
    if cycle_length is not None:
        updates["cycle_length"] = cycle_length
    if stakeholders is not None:
        updates["stakeholders"] = stakeholders
    return await _save_org_section(config, "sales_process", updates)


@tool
async def set_deal_constraints(
    config: RunnableConfig,
    min_contract_value: str | None = None,
    preferred_industries: list[str] | None = None,
    excluded_industries: list[str] | None = None,
    geographic_limits: list[str] | None = None,
    other: str | None = None,
) -> dict[str, Any] | str:
    """Agent mode only. Update the deal constraints section.

    Args:
        min_contract_value: Smallest deal size pursued.
        preferred_industries: List of preferred target industries.
        excluded_industries: List of industries to avoid.
        geographic_limits: Geographic limitations or unsupported regions.
        other: Other hard deal disqualifiers.
    """
    updates = {}
    if min_contract_value is not None:
        updates["min_contract_value"] = min_contract_value
    if preferred_industries is not None:
        updates["preferred_industries"] = preferred_industries
    if excluded_industries is not None:
        updates["excluded_industries"] = excluded_industries
    if geographic_limits is not None:
        updates["geographic_limits"] = geographic_limits
    if other is not None:
        updates["other"] = other
    return await _save_org_section(config, "deal_constraints", updates)


def get_all_tools() -> list[Any]:
    """Return all organization setup chat tools."""
    return [
        get_organization_profile,
        set_identity,
        set_company_overview,
        set_industry,
        set_business_model,
        set_company_size,
        set_target_markets,
        set_existing_customers,
        set_customer_segments,
        set_brand_positioning,
        set_unique_strengths,
        set_competitive_landscape,
        set_sales_goals,
        set_partnership_strategy,
        set_delivery_capability,
        set_certifications_compliance,
        set_technology_expertise,
        set_case_studies,
        set_references,
        set_pricing_position,
        set_sales_process,
        set_deal_constraints,
    ]
