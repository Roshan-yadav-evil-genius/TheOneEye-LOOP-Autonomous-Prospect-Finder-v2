"""Canonical form field definitions for offline markdown templates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

FieldKind = Literal[
    "text",
    "textarea",
    "number",
    "boolean",
    "string-list",
    "select",
    "multi-select",
    "object-list",
]


@dataclass(frozen=True)
class FormFieldDef:
    path: str
    label: str
    kind: FieldKind
    help: str = ""
    required: bool = False
    options: tuple[str, ...] = ()
    item_fields: tuple[FormFieldDef, ...] = ()
    avoid: str = ""


@dataclass(frozen=True)
class FormSectionDef:
    key: str
    title: str
    help: str
    fields: tuple[FormFieldDef, ...]


@dataclass(frozen=True)
class FormTemplateDef:
    form_key: str
    title: str
    filename: str
    purpose: str
    provide_guidance: tuple[str, ...]
    avoid_guidance: tuple[str, ...]
    sections: tuple[FormSectionDef, ...]


def _sl(path: str, label: str, help: str = "", *, required: bool = False, avoid: str = "") -> FormFieldDef:
    return FormFieldDef(path, label, "string-list", help, required, avoid=avoid)


def _txt(path: str, label: str, help: str = "", *, required: bool = False, avoid: str = "") -> FormFieldDef:
    return FormFieldDef(path, label, "text", help, required, avoid=avoid)


def _area(path: str, label: str, help: str = "", *, required: bool = False, avoid: str = "") -> FormFieldDef:
    return FormFieldDef(path, label, "textarea", help, required, avoid=avoid)


def _num(path: str, label: str, help: str = "", *, required: bool = False) -> FormFieldDef:
    return FormFieldDef(path, label, "number", help, required)


ORGANIZATION_FORM = FormTemplateDef(
    form_key="organization",
    title="Organization Profile",
    filename="organization-profile-offline-form.md",
    purpose=(
        "Capture who you represent as a company — mission, market position, delivery capability, "
        "and deal constraints — so agents and operators can judge business fit."
    ),
    provide_guidance=(
        "Accurate facts about your seller organization (the company you work for).",
        "Mission, operating territories, delivery capability, certifications, and macro deal constraints.",
        "Optional sections are still valuable — fill what you know.",
    ),
    avoid_guidance=(
        "Prospect or target-company data — that belongs in sales strategy workflows.",
        "Product-specific ICP details — use the Product/Service form instead.",
        "Passwords, API keys, or confidential credentials.",
        "Internal-only financials beyond revenue ranges you are comfortable sharing.",
    ),
    sections=(
        FormSectionDef(
            "identity",
            "Organization identity",
            "Basic record fields stored on Organization.",
            (
                _txt("name", "Organization name", "Legal or brand name", required=True),
                _txt("website", "Website", "Canonical company website URL", required=True),
                _txt("primary_contact_email", "Primary contact email", "Optional notification contact"),
            ),
        ),
        FormSectionDef(
            "company_overview",
            "Company overview",
            "What the company does and its mission.",
            (
                _area("description", "What the company does", "2–5 sentences", required=True),
                _area("mission", "Mission or vision", "1–2 sentences on purpose or long-term goal", required=True),
                _num("founded_year", "Year founded", "Four-digit year the company was founded"),
                _txt("headquarters", "Headquarters location", "City and country, e.g. San Francisco, US"),
            ),
        ),
        FormSectionDef(
            "operating_territories",
            "Operating territories",
            "Countries and regions where seller can legally and logistically operate and support clients.",
            (
                _sl("countries", "Countries", "Countries you actively operate in — one per line"),
                _sl("regions", "Regions", "Macro regions served — one per line"),
            ),
        ),
        FormSectionDef(
            "delivery_capability",
            "Delivery capability",
            "Geographic coverage and implementation capacity.",
            (
                _sl("geography", "Delivery geography", "Countries or regions where you implement — one per line"),
                _sl("languages", "Languages supported", "One language per line"),
                _txt("support_hours", "Support hours / time zones", "Coverage window, e.g. 9–5 ET"),
                _area("implementation_capacity", "Implementation capacity", "Team size or concurrent project limits"),
            ),
        ),
        FormSectionDef(
            "certifications_compliance",
            "Certifications & compliance",
            "Certifications and frameworks customers require.",
            (
                _sl("certifications", "Certifications", "e.g. ISO 27001 or SOC 2 — one per line"),
                _sl("frameworks", "Compliance frameworks", "e.g. GDPR or HIPAA — one per line"),
                _txt("data_residency", "Data residency / security commitments", "Where customer data is stored"),
            ),
        ),
        FormSectionDef(
            "technology_expertise",
            "Technology expertise",
            "Company-wide technical strengths.",
            (
                _sl("cloud", "Cloud providers", "AWS, Azure, GCP — one per line"),
                _sl("languages", "Languages / frameworks", "One per line"),
                _sl("platforms", "Platforms", "CRM, ERP, or vertical platforms"),
                _sl("tools", "Tools", "Delivery or internal tools"),
            ),
        ),
        FormSectionDef(
            "references",
            "References",
            "Well-known clients and reference industries.",
            (
                FormFieldDef(
                    "clients",
                    "Clients",
                    "object-list",
                    "Logo or name-drop clients prospects may recognize.",
                    item_fields=(
                        _txt("name", "Name", "Client company name"),
                        _txt("website", "Website", "Canonical client website URL"),
                    ),
                ),
                _sl("industries", "Reference industries", "One industry per line"),
            ),
        ),
        FormSectionDef(
            "macro_deal_constraints",
            "Macro deal constraints",
            "Hard rules for business fit and deal breakers.",
            (
                _txt("min_contract_value", "Minimum contract value", "Smallest deal size you will pursue"),
                _sl("geographic_limits", "Geographic limitations", "Regions you cannot serve"),
                _area("other", "Other deal breakers", "Any other hard disqualifiers"),
            ),
        ),
    ),
)

PRODUCT_FORM = FormTemplateDef(
    form_key="product",
    title="Product / Service Profile",
    filename="product-service-offline-form.md",
    purpose=(
        "Define what you sell — problem solved, ICP, buyer personas, pricing, and differentiation — "
        "so agents can match prospects to this specific offering."
    ),
    provide_guidance=(
        "Product or service-specific fit criteria, buyer personas, and proof points.",
        "At least five customer success stories when possible.",
        "Clear minimum deal size and pricing model.",
    ),
    avoid_guidance=(
        "Organization-wide mission or delivery capacity — use the Organization form.",
        "Sales-strategy run targets or prospecting sources — use the Sales Strategy form.",
        "Passwords, API keys, or confidential credentials.",
        "Exact SKU price lists — use ranges and minimum deal size instead.",
    ),
    sections=(
        FormSectionDef(
            "identity",
            "Product identity",
            "Product or service name and kind.",
            (
                _txt("name", "Name", "Product or service name as prospects recognize it", required=True),
                FormFieldDef(
                    "kind",
                    "Kind",
                    "select",
                    "Whether this offering is a product or a service.",
                    required=True,
                    options=("product", "service"),
                ),
            ),
        ),
        FormSectionDef(
            "product_overview",
            "Product overview",
            "What the offering does.",
            (
                _area("summary", "One-sentence summary", "Single sentence describing the offering", required=True),
                _area("offering_scope", "Offering scope", "What is included and excluded"),
            ),
        ),
        FormSectionDef(
            "problem_solved",
            "Problem solved",
            "Business problem or pain point.",
            (
                _area("primary", "Primary problem", "Main business pain this offering solves", required=True),
                _sl("secondary", "Secondary pains", "One pain per line"),
                _area("cost_of_inaction", "Cost of inaction", "What happens if the buyer does nothing"),
            ),
        ),
        FormSectionDef(
            "value_proposition",
            "Value proposition",
            "Why it is better than alternatives.",
            (
                _area("primary", "Primary value proposition", "Core reason to buy", required=True),
                _sl("outcomes", "Top outcomes", "Measurable results — one per line"),
            ),
        ),
        FormSectionDef(
            "icp",
            "Ideal customer profile",
            "General fit profile for this offering.",
            (
                _sl("customer_segments.primary", "Primary customer segments", "Main ICP segments — one per line"),
                _sl("customer_segments.secondary", "Secondary customer segments", "Additional accepted segments"),
                _sl("customer_segments.avoid", "Avoid customer segments", "Segments to decline or deprioritize"),
                _sl("industries.primary", "Primary industries", "Best-fit industries — one per line"),
                _sl("industries.secondary", "Secondary industries", "Lower-priority industries"),
                _sl("industries.avoid", "Industries to avoid", "Poor-fit industries"),
                _num("company_size.employees_min", "Employees min", "Minimum employee count"),
                _num("company_size.employees_max", "Employees max", "Maximum employee count"),
                _num("company_size.revenue_min", "Revenue min", "Minimum annual revenue"),
                _num("company_size.revenue_max", "Revenue max", "Maximum annual revenue"),
                _sl("geography.countries", "Countries", "Target countries — one per line"),
                _sl("geography.regions", "Regions", "Macro regions to include"),
                _sl("geography.exclude_countries", "Excluded countries", "Countries to exclude"),
                _sl("company_types", "Company types", "Firm types that fit, e.g. SaaS"),
                _sl("maturity", "Maturity", "Company maturity signals, e.g. Series B"),
            ),
        ),
        FormSectionDef(
            "buyer_personas",
            "Buyer personas",
            "Who usually buys or champions the deal.",
            (
                _sl("primary_titles", "Primary buyer titles", "Job titles that own the purchase", required=True),
                _txt("economic_buyer", "Economic buyer", "Role that signs or controls budget"),
                _txt("technical_evaluator", "Technical evaluator", "Role that assesses technical fit"),
                _sl("seniority", "Seniority", "Typical seniority levels — one per line"),
            ),
        ),
        FormSectionDef(
            "use_cases",
            "Use cases",
            "Scenarios where customers use the offering.",
            (
                FormFieldDef(
                    ".",
                    "Use cases",
                    "object-list",
                    "Concrete adoption scenarios. Duplicate for each use case.",
                    item_fields=(
                        _txt("name", "Name", "Short label"),
                        _txt("trigger", "Trigger", "Event that starts the need"),
                        _txt("outcome", "Outcome", "Expected result after adoption"),
                    ),
                ),
            ),
        ),
        FormSectionDef(
            "customer_triggers",
            "Customer triggers",
            "Events indicating current need.",
            (_sl(".", "Triggers", "Events indicating a prospect may need this now — one per line"),),
        ),
        FormSectionDef(
            "pricing",
            "Pricing",
            "Model, price band, range, and minimum deal size.",
            (
                _txt("model", "Pricing model", "How you charge, e.g. subscription", required=True),
                _txt("price_band", "Price band", "Relative price position, e.g. mid-market"),
                _txt("typical_range", "Typical price range", "Usual price band"),
                _txt("min_deal_size", "Minimum deal size", "Smallest contract accepted", required=True),
                _txt("sales_cycle", "Sales cycle length", "Typical time to signed contract"),
                _txt("engagement_model", "Engagement model", "How delivery starts, e.g. pilot or POC"),
            ),
        ),
        FormSectionDef(
            "competitors",
            "Competitors",
            "Who prospects use instead.",
            (
                FormFieldDef(
                    ".",
                    "Competitors",
                    "object-list",
                    "Alternatives prospects compare you against.",
                    item_fields=(
                        _txt("name", "Name", "Competitor company name"),
                        _txt("website", "Website", "Competitor website URL"),
                        FormFieldDef(
                            "type",
                            "Type",
                            "select",
                            "Direct rivals solve the same problem; indirect alternatives differ.",
                            options=("direct", "indirect"),
                        ),
                    ),
                ),
            ),
        ),
        FormSectionDef(
            "differentiators",
            "Differentiators",
            "Why customers choose you.",
            (_sl(".", "Differentiators", "Reasons customers pick you — one per line", required=True),),
        ),
        FormSectionDef(
            "implementation",
            "Implementation",
            "Setup effort and technical requirements.",
            (
                _txt("setup_effort", "Setup effort", "Relative effort: low, medium, or high"),
                _txt("onboarding_duration", "Onboarding duration", "Typical time until customer is live"),
                _sl("technical_requirements", "Technical requirements", "Customer-side prerequisites"),
                _sl("customer_resources", "Customer resources required", "People or systems customer must provide"),
            ),
        ),
        FormSectionDef(
            "integrations",
            "Integrations",
            "Software and ecosystems the offering works with.",
            (
                _sl("must_have", "Must-have integrations", "Required for a viable deal"),
                _sl("nice_to_have", "Nice-to-have integrations", "Improve fit but not required"),
                _sl("ecosystems", "Ecosystems", "Marketplaces or partner ecosystems"),
            ),
        ),
        FormSectionDef(
            "customer_success_stories",
            "Customer success stories",
            "Reference companies — provide at least five when possible.",
            (
                FormFieldDef(
                    ".",
                    "Success stories",
                    "object-list",
                    "Reference customers agents can mention. Add at least five entries.",
                    item_fields=(
                        _txt("name", "Company name", "Reference customer name"),
                        _txt("website", "Website", "Reference customer website"),
                        _txt("industry", "Industry", "Customer industry or segment"),
                        _area("why_they_bought", "Why they bought", "Trigger or pain that led to purchase"),
                        _area("outcome", "Outcome", "Result achieved after adoption"),
                    ),
                ),
            ),
        ),
        FormSectionDef(
            "compliance_restrictions",
            "Compliance / restrictions",
            "Regions, certifications, legal, and technical limits.",
            (
                _sl("regions_blocked", "Regions blocked", "Regions where you cannot sell or deploy"),
                _sl("certifications", "Certifications", "Certifications this offering satisfies"),
                _area("legal_notes", "Legal notes", "Contract, privacy, or regulatory constraints"),
                _sl("technical_limits", "Technical limits", "Hard technical restrictions"),
            ),
        ),
        FormSectionDef(
            "keywords",
            "Keywords",
            "Terms prospects use when searching.",
            (_sl(".", "Keywords", "Search terms — one per line"),),
        ),
        FormSectionDef(
            "signals",
            "Signals",
            "Public indicators of active need.",
            (_sl(".", "Signals", "Public indicators of need — one per line"),),
        ),
        FormSectionDef(
            "exclusion_rules",
            "Exclusion rules",
            "Companies that are not a good fit for this offering.",
            (
                _sl("rules", "Exclusion rules", "Hard disqualifiers — one per line"),
                _area("free_text", "Other exclusion rules", "Additional fit rules"),
            ),
        ),
    ),
)

STRATEGY_FORM = FormTemplateDef(
    form_key="sales-strategy",
    title="Sales Strategy",
    filename="sales-strategy-offline-form.md",
    purpose=(
        "Define how to find and approach target companies for one prospecting run — "
        "target profile, signals, outreach approach, and run quotas."
    ),
    provide_guidance=(
        "Concrete targeting criteria for this specific run (industries, geographies, signals).",
        "Run targets: how many companies and contacts per company.",
        "Messaging hooks and qualification rules operators and agents should follow.",
    ),
    avoid_guidance=(
        "Organization-wide seller profile — use the Organization form.",
        "Product ICP details — use the Product/Service form unless run-specific overrides apply.",
        "Individual prospect names or LinkedIn URLs — register those in the portal after companies are found.",
        "Passwords, API keys, or confidential credentials.",
    ),
    sections=(
        FormSectionDef(
            "overview",
            "Sales strategy overview",
            "Name, description, and target narrative.",
            (
                _txt("name", "Sales strategy name", "Short label for this run", required=True),
                _area("description", "Description", "What this strategy is trying to achieve"),
                _area(
                    "target_companies_narrative",
                    "Target companies in your own words",
                    "Describe ideal companies in plain language",
                    required=True,
                ),
            ),
        ),
        FormSectionDef(
            "run_targets",
            "Run targets",
            "Operational quotas for this sales strategy.",
            (
                _num("target_companies", "Target company count", "How many companies to register", required=True),
                _num(
                    "contacts_per_company_default",
                    "Default contacts per company",
                    "How many prospects to find per company",
                    required=True,
                ),
            ),
        ),
        FormSectionDef(
            "target_decision_makers",
            "Target decision makers",
            "Roles to contact first.",
            (
                _sl("primary_titles", "Primary titles", "First-choice job titles"),
                _sl("secondary_titles", "Secondary titles", "Backup titles"),
                FormFieldDef(
                    "seniority_levels",
                    "Seniority levels",
                    "multi-select",
                    "Target seniority tiers to focus on.",
                    options=("C-Suite", "VP", "Director", "Head Of", "Manager"),
                ),
                FormFieldDef(
                    "department_functions",
                    "Department functions",
                    "multi-select",
                    "Department functions to target.",
                    options=("Engineering", "Sales", "Product", "Marketing", "IT", "Finance", "Operations"),
                ),
                _sl("seniority_order", "Seniority order", "Preferred seniority sequence"),
                _sl("contact_buying_signals", "Contact buying signals", "Per-contact readiness signals"),
            ),
        ),
        FormSectionDef(
            "target_company_profile",
            "Target company profile",
            "What kinds of companies to approach now.",
            (
                _sl("company_types", "Company types", "Firm types to pursue — one per line"),
                _sl("characteristics", "Characteristics", "Traits that make a company a strong fit"),
                FormFieldDef(
                    "similar_companies",
                    "Similar companies",
                    "object-list",
                    "Example companies that represent ideal targets.",
                    item_fields=(
                        _txt("name", "Name", "Example company name"),
                        _txt("website_url", "Website URL", "Example company website"),
                    ),
                ),
                _sl("keywords", "Keywords", "Terms to find lookalike companies"),
                _sl("problems_they_should_have", "Problems they should have", "Pains ideal targets should feel"),
            ),
        ),
        FormSectionDef(
            "priority_industries",
            "Priority industries",
            "Industries to focus on this run.",
            (
                _sl("primary", "Primary industries", "Industries to prioritize", required=True),
                _sl("secondary", "Secondary industries", "Include when quota allows"),
                _sl("deprioritized", "Deprioritized industries", "Pursue only if no better matches"),
            ),
        ),
        FormSectionDef(
            "priority_geographies",
            "Priority geographies",
            "Countries, regions, and cities.",
            (
                _sl("countries", "Countries", "Countries to target"),
                _sl("regions", "Regions", "Macro regions to include"),
                _sl("cities", "Cities", "Specific cities to prioritize"),
                FormFieldDef(
                    "remote_only",
                    "Remote-only companies",
                    "boolean",
                    "Limit targeting to fully remote or distributed companies only.",
                ),
                _sl("exclude_countries", "Exclude countries", "Countries to skip"),
            ),
        ),
        FormSectionDef(
            "company_size",
            "Company size",
            "Employee and revenue ranges for target companies.",
            (
                _num("employees_min", "Employees min", "Minimum employee count"),
                _num("employees_max", "Employees max", "Maximum employee count"),
                _num("revenue_min", "Revenue min", "Minimum annual revenue"),
                _num("revenue_max", "Revenue max", "Maximum annual revenue"),
                _sl("segments", "Segment tags", "Size or stage bands, e.g. mid-market"),
            ),
        ),
        FormSectionDef(
            "buying_signals",
            "Buying signals",
            "Events indicating readiness now.",
            (
                FormFieldDef(
                    "selected",
                    "Selected signals",
                    "multi-select",
                    "Select all that apply (list chosen signals on separate lines).",
                    options=(
                        "Hiring engineers / AI engineers / specific roles",
                        "Recently funded / acquisition / IPO",
                        "New office / international expansion",
                        "New product launch / digital transformation / cloud migration",
                        "Automation or AI initiative signals",
                        "Growing engineering team / building AI products",
                    ),
                ),
                _sl("custom", "Custom signals", "Additional buying signals"),
            ),
        ),
        FormSectionDef(
            "prospecting_strategy",
            "Prospecting strategy",
            "How Company Finder should discover companies.",
            (
                FormFieldDef(
                    "sources",
                    "Sources",
                    "multi-select",
                    "Where Company Finder should look (list chosen sources on separate lines).",
                    options=(
                        "LinkedIn",
                        "Crunchbase",
                        "Product Hunt",
                        "YC",
                        "App stores",
                        "VC portfolios",
                        "Careers pages",
                        "GitHub",
                        "News",
                        "AngelList / Wellfound",
                        "Google",
                        "Apollo",
                    ),
                ),
                _sl("excluded_domain_types", "Excluded domain types", "Types of sites to skip during discovery"),
            ),
        ),
        FormSectionDef(
            "competitor_targeting",
            "Competitor targeting",
            "Incumbents that make good targets.",
            (
                _sl("incumbents_to_target", "Incumbents to target", "Competitor products to displace"),
                _sl("switch_triggers", "Switch triggers", "Events that push buyers to switch"),
                _sl("avoid_unless_scaling", "Avoid unless scaling", "Incumbents to skip unless growing fast"),
            ),
        ),
        FormSectionDef(
            "qualification_criteria",
            "Qualification criteria",
            "What makes a company worth pursuing.",
            (
                _sl("must_have", "Must-have attributes", "Traits a company must have"),
                _sl("nice_to_have", "Nice-to-have attributes", "Traits that improve priority"),
                _num("min_confidence_hint", "Minimum confidence hint", "Lowest agent confidence to keep a company"),
            ),
        ),
        FormSectionDef(
            "prioritization_rules",
            "Prioritization rules",
            "Who to contact or validate first.",
            (_sl("rules", "Rules", "How to rank companies or contacts when quota is tight"),),
        ),
        FormSectionDef(
            "exclusion_rules",
            "Exclusion rules",
            "Hard avoids for this strategy.",
            (
                _sl("rules", "Exclusion rules", "Conditions that disqualify a company"),
                _sl("companies", "Companies", "Named companies to never contact"),
                _sl("domains", "Domains", "Email or web domains to block"),
                _sl("industries", "Industries", "Industries to exclude from this run"),
                _sl("regions", "Regions", "Regions to exclude from this run"),
            ),
        ),
        FormSectionDef(
            "experiments",
            "Experiments",
            "What the team is actively testing.",
            (
                FormFieldDef(
                    ".",
                    "Experiments",
                    "object-list",
                    "Active tests for agents and operators. Duplicate for each experiment.",
                    item_fields=(
                        _txt("hypothesis", "Hypothesis", "What you are trying to learn"),
                        _txt("variant", "Variant", "What is different in this test"),
                        _txt("success_criteria", "Success criteria", "How you will judge success"),
                        _area("notes", "Notes", "Setup details or constraints"),
                    ),
                ),
            ),
        ),
        FormSectionDef(
            "success_metrics",
            "Success metrics",
            "Operator-defined run targets.",
            (_sl("targets", "Targets", "Measurable goals, e.g. meetings booked"),),
        ),
    ),
)

FORM_TEMPLATES: dict[str, FormTemplateDef] = {
    "organization": ORGANIZATION_FORM,
    "product": PRODUCT_FORM,
    "sales-strategy": STRATEGY_FORM,
}


def _clean_value(val: Any) -> Any:
    if val is None:
        return None
    if val == "" or val == [] or val == {}:
        return None
    if isinstance(val, str) and not val.strip():
        return None
    return val


def _extract_field_value(section_data: Any, path: str) -> Any:
    if section_data is None:
        return None

    if path == ".":
        if isinstance(section_data, dict) and "items" in section_data:
            return section_data["items"]
        return section_data

    if not isinstance(section_data, dict):
        return None

    if path in section_data:
        return section_data[path]

    parts = path.split(".")
    curr = section_data
    for part in parts:
        if isinstance(curr, dict) and part in curr:
            curr = curr[part]
        else:
            return None
    return curr


def build_agent_profile_dict(
    template: FormTemplateDef,
    form_data: dict[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    """Transform canonical form template definition and form data into agent profile dictionary.

    Returns a dict mapping section keys to lists of field dicts:
    {
        section_key: [
            {
                "name": field.label,
                "description": field.help,
                "value": extracted_value_or_None,
            }
        ]
    }
    Empty values ("", [], {}) are normalized to None.
    """
    from typing import Any

    result: dict[str, list[dict[str, Any]]] = {}

    for section in template.sections:
        section_key = section.key
        section_data = form_data.get(section_key)
        if section_data is None:
            if section_key == "exclusion rules":
                section_data = form_data.get("exclusion_rules")
            elif section_key == "exclusion_rules":
                section_data = form_data.get("exclusion rules")

        field_list: list[dict[str, Any]] = []

        for field in section.fields:
            raw_value = _extract_field_value(section_data, field.path)
            clean_val = _clean_value(raw_value)

            field_list.append(
                {
                    "name": field.label,
                    "description": field.help,
                    "value": clean_val,
                }
            )

        result[section_key] = field_list

    return result

