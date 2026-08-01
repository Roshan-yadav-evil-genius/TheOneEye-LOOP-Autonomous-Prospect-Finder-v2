import copy
from typing import Any

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from application.form_definitions import ORGANIZATION_FORM, build_agent_profile_dict
from application.loop_service import ReentrantAsyncLock
from agents.setup_chat.common import SetupChatToolContext


@tool
async def get_organization_profile(config: RunnableConfig) -> dict[str, Any]:
    """Read the entire organization profile including identity and all form sections."""
    ctx: SetupChatToolContext = config["configurable"]["tool_context"]
    org = await ctx.service.get_organization(ctx.organization_id)

    org_data = copy.deepcopy(org.org_form)
    org_data["identity"] = {
        "name": org.name,
        "website": org.website,
        "primary_contact_email": org.primary_contact_email,
    }

    return build_agent_profile_dict(ORGANIZATION_FORM, org_data)



async def _save_org_section(
    config: RunnableConfig, section_key: str, updates: dict[str, Any]
) -> str:
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
) -> str:
    org = await ctx.service.get_organization(ctx.organization_id)
    current_form = copy.deepcopy(org.org_form)

    if section_key == "identity":
        name = updates.get("name", org.name)
        website = updates.get("website", org.website)
        email = updates.get("primary_contact_email", org.primary_contact_email)
        current_form.pop("identity", None)

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

    return "Saved!"


@tool
async def set_identity(
    config: RunnableConfig,
    name: str | None = None,
    website: str | None = None,
    primary_contact_email: str | None = None,
) -> str:
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
) -> str:
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
async def set_operating_territories(
    config: RunnableConfig,
    countries: list[str] | None = None,
    regions: list[str] | None = None,
) -> str:
    """Agent mode only. Update operating territories.

    Args:
        countries: Countries where seller operates and supports clients.
        regions: Macro regions served.
    """
    updates = {}
    if countries is not None:
        updates["countries"] = countries
    if regions is not None:
        updates["regions"] = regions
    return await _save_org_section(config, "operating_territories", updates)


@tool
async def set_delivery_capability(
    config: RunnableConfig,
    geography: list[str] | None = None,
    languages: list[str] | None = None,
    support_hours: str | None = None,
    implementation_capacity: str | None = None,
) -> str:
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
) -> str:
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
) -> str:
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
async def set_references(
    config: RunnableConfig,
    clients: list[dict[str, Any]] | None = None,
    industries: list[str] | None = None,
) -> str:
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
async def set_macro_deal_constraints(
    config: RunnableConfig,
    min_contract_value: str | None = None,
    geographic_limits: list[str] | None = None,
    other: str | None = None,
) -> str:
    """Agent mode only. Update the macro deal constraints section.

    Args:
        min_contract_value: Smallest deal size pursued.
        geographic_limits: Geographic limitations or unsupported regions.
        other: Other hard deal disqualifiers.
    """
    updates = {}
    if min_contract_value is not None:
        updates["min_contract_value"] = min_contract_value
    if geographic_limits is not None:
        updates["geographic_limits"] = geographic_limits
    if other is not None:
        updates["other"] = other
    return await _save_org_section(config, "macro_deal_constraints", updates)


def get_all_tools() -> list[Any]:
    """Return all organization setup chat tools."""
    return [
        get_organization_profile,
        set_identity,
        set_company_overview,
        set_operating_territories,
        set_delivery_capability,
        set_certifications_compliance,
        set_technology_expertise,
        set_references,
        set_macro_deal_constraints,
    ]
