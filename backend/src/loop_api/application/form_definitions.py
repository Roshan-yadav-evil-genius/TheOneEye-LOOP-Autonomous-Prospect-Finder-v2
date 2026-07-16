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
        "Mission, industries served, target markets, customer segments, and deal constraints.",
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
            "industry",
            "Industry",
            "Industries the seller organization operates in.",
            (
                _txt("primary", "Primary industry", "Main industry label, e.g. Software", required=True),
                _sl("secondary", "Secondary industries", "One industry per line"),
                _sl("sub_verticals", "Sub-verticals or niches", "One niche per line"),
            ),
        ),
        FormSectionDef(
            "business_model",
            "Business model",
            "How the company makes money.",
            (
                _sl("types", "Model types", "B2B, B2C, B2G, SaaS, agency, etc. — one per line", required=True),
                _area("description", "How the company makes money", "Revenue streams and delivery model"),
            ),
        ),
        FormSectionDef(
            "company_size",
            "Company size",
            "Employees, revenue, and years in business.",
            (
                _txt("employees", "Employee count / range", "Headcount or band, e.g. 51–200"),
                _txt("revenue_range", "Annual revenue range", "Typical annual revenue band"),
                _num("years_in_business", "Years in business", "Years operating under current brand"),
            ),
        ),
        FormSectionDef(
            "target_markets",
            "Target markets",
            "Where and who the organization serves.",
            (
                _sl("countries", "Countries", "Countries you actively sell into — one per line"),
                _sl("regions", "Regions", "Macro regions served — one per line"),
                _sl("industries", "Industries served", "Industry verticals you target — one per line"),
                _sl("excluded", "Markets not served", "Regions or segments you do not pursue"),
            ),
        ),
        FormSectionDef(
            "existing_customers",
            "Existing customers",
            "Patterns of companies already served.",
            (
                _area("typical_profile", "Typical customer profile", "Size, industry, and traits of best-fit customers"),
                _sl("strong_industries", "Industries with strongest traction", "One industry per line"),
            ),
        ),
        FormSectionDef(
            "customer_segments",
            "Customer segments",
            "Segments the organization sells into.",
            (
                _sl("primary", "Primary segments", "Main ICP segments — one per line", required=True),
                _sl("secondary", "Secondary segments", "Additional segments you accept"),
                _sl("avoid", "Segments to avoid", "Segments you decline or deprioritize"),
            ),
        ),
        FormSectionDef(
            "brand_positioning",
            "Brand positioning",
            "How the market perceives the company.",
            (
                _txt("position", "Position", "Market tier or stance, e.g. premium niche"),
                _area("statement", "Positioning statement", "2–4 sentences on who you serve and why you win"),
            ),
        ),
        FormSectionDef(
            "unique_strengths",
            "Unique strengths",
            "Company-level competitive advantages.",
            (_sl(".", "Strengths", "Distinct competitive advantages — one per line"),),
        ),
        FormSectionDef(
            "competitive_landscape",
            "Competitive landscape",
            "Main competitors and differentiators.",
            (
                _sl("competitors", "Main competitors", "Direct competitors by name — one per line"),
                _sl("differentiators", "Differentiators", "Why customers choose you — one per line"),
                _area("win_loss_notes", "Common win/loss reasons", "Recurring patterns when you win or lose"),
            ),
        ),
        FormSectionDef(
            "sales_goals",
            "Sales goals",
            "Current commercial priorities.",
            (
                _txt("revenue_targets", "Revenue or pipeline targets", "Quarterly or annual goals"),
                _sl("strategic_industries", "Strategic industries", "One industry per line"),
                _sl("expansion_markets", "Expansion markets", "New geographies or verticals"),
            ),
        ),
        FormSectionDef(
            "partnership_strategy",
            "Partnership strategy",
            "Direct, partner, or reseller model.",
            (
                _txt("model", "Partnership model", "GTM motion: direct, reseller, referral, or hybrid"),
                _txt("regions", "Partner-led regions", "Territories sold primarily through partners"),
                _area("notes", "Constraints / notes", "Partner restrictions or exclusivity terms"),
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
            "case_studies",
            "Case studies",
            "Notable projects and outcomes.",
            (
                FormFieldDef(
                    ".",
                    "Case studies",
                    "object-list",
                    "Notable customer projects agents can cite. Duplicate the block for each case study.",
                    item_fields=(
                        _txt("title", "Title", "Short project or customer name"),
                        _txt("customer_type", "Customer type", "Segment or industry"),
                        _area("challenge", "Challenge", "Problem before working with you"),
                        _area("outcome", "Outcome", "Measurable result achieved"),
                        _txt("link", "Link", "URL to public case study"),
                    ),
                ),
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
            "pricing_position",
            "Pricing position",
            "Organization-level price band.",
            (
                _txt("band", "Price band", "Relative price position, e.g. mid-market"),
                _txt("typical_contract_size", "Typical contract size", "Usual deal size or ACV band"),
                _area("positioning_notes", "Positioning notes", "How you justify pricing vs alternatives"),
            ),
        ),
        FormSectionDef(
            "sales_process",
            "Sales process",
            "Typical stages from first touch to contract.",
            (
                _sl("stages", "Stages", "Sales stages — one per line"),
                _txt("cycle_length", "Average cycle length", "Typical days or weeks to close"),
                _sl("stakeholders", "Required stakeholders", "Roles that must be involved — one per line"),
            ),
        ),
        FormSectionDef(
            "deal_constraints",
            "Deal constraints",
            "Hard rules for business fit.",
            (
                _txt("min_contract_value", "Minimum contract value", "Smallest deal size you will pursue"),
                _sl("preferred_industries", "Preferred industries", "One industry per line"),
                _sl("excluded_industries", "Excluded industries", "Industries you will not sell into"),
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
            "exclusion rules",
            "Blacklist",
            "Companies that are not a good fit for this offering.",
            (
                _sl("rules", "Exclusion rules", "Hard disqualifiers — one per line"),
                _area("free_text", "Other exclusion rules", "Additional fit rules"),
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
            "pricing",
            "Pricing",
            "Model, range, and minimum deal size.",
            (
                _txt("model", "Pricing model", "How you charge, e.g. subscription", required=True),
                _txt("typical_range", "Typical price range", "Usual price band"),
                _txt("min_deal_size", "Minimum deal size", "Smallest contract accepted", required=True),
                _txt("sales_cycle", "Sales cycle length", "Typical time to signed contract"),
                _txt("engagement_model", "Engagement model", "How delivery starts, e.g. pilot or POC"),
            ),
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
            "target_decision_makers",
            "Target decision makers",
            "Roles to contact first.",
            (
                _sl("primary_titles", "Primary titles", "First-choice job titles"),
                _sl("secondary_titles", "Secondary titles", "Backup titles"),
                _sl("seniority_order", "Seniority order", "Preferred seniority sequence"),
                _sl("contact_buying_signals", "Contact buying signals", "Per-contact readiness signals"),
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
            ),
        ),
        FormSectionDef(
            "outreach_strategy",
            "Outreach strategy",
            "How operators approach contacts.",
            (
                FormFieldDef(
                    "primary_channel",
                    "Primary channel",
                    "select",
                    "Default first-touch channel for this strategy.",
                    options=(
                        "LinkedIn connection",
                        "InMail",
                        "email",
                        "phone",
                        "referral",
                        "partner intro",
                    ),
                ),
                _sl("channels", "Channels", "All channels operators may use"),
                _area("sequence_notes", "Sequence notes", "Cadence and follow-up guidance"),
                _sl("do_not_contact_rules", "Do-not-contact rules", "People or situations to avoid"),
            ),
        ),
        FormSectionDef(
            "messaging_hypotheses",
            "Messaging hypotheses",
            "Angles to test in outreach.",
            (
                _area("primary_hook", "Primary hook", "Main angle for first-touch messages"),
                _sl("secondary_hooks", "Secondary hooks", "Backup angles to test"),
                _sl("proof_points", "Proof points", "Evidence to cite in outreach"),
                _txt("tone", "Tone", "Voice for messages, e.g. consultative"),
                _area("message_guidance", "Message guidance", "Do and do-not phrasing guidance"),
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
            "blacklist_criteria",
            "Blacklist criteria",
            "When to skip a company.",
            (_sl("rules", "Rules", "Conditions that disqualify a company"),),
        ),
        FormSectionDef(
            "prioritization_rules",
            "Prioritization rules",
            "Who to contact or validate first.",
            (_sl("rules", "Rules", "How to rank companies or contacts when quota is tight"),),
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
            "exclusion_rules",
            "Exclusion rules",
            "Hard avoids for this strategy.",
            (
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
        FormSectionDef(
            "lessons_learned",
            "Lessons learned",
            "What worked and what did not.",
            (
                _sl("worked", "What worked", "Tactics that produced good results"),
                _sl("did_not_work", "What did not work", "Tactics to avoid repeating"),
            ),
        ),
        FormSectionDef(
            "best_practices",
            "Best practices",
            "Repeatable tactics.",
            (_sl(".", "Best practices", "Repeatable tactics — one per line"),),
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
    ),
)

FORM_TEMPLATES: dict[str, FormTemplateDef] = {
    "organization": ORGANIZATION_FORM,
    "product": PRODUCT_FORM,
    "sales-strategy": STRATEGY_FORM,
}
