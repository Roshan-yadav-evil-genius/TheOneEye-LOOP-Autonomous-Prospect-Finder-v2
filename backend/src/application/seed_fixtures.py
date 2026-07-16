"""Deterministic fixture definitions for local SQLite OLTP seeding.

Forms mirror ``loop_testing.factories`` so seeded rows pass the same validation
gates used by the setup wizards and vertical-slice API tests.
"""

from __future__ import annotations

from typing import Any

SEED_ORG_WEBSITES = (
    "https://northstar-analytics.example/",
    "https://helix-robotics.example/",
)


def organization_form(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "company_overview": {
            "description": "B2B seller operating an operator-led prospecting console",
            "mission": "Turn ICP fit into qualified pipeline faster",
        },
        "industry": {"primary": "Software"},
        "business_model": {"types": ["B2B", "SaaS"]},
        "target_markets": {
            "countries": ["US"],
            "regions": ["North America"],
            "industries": ["SaaS"],
        },
        "customer_segments": {"primary": ["mid-market"]},
        "deal_constraints": {
            "min_contract_value": "10000",
            "excluded_industries": ["gambling"],
            "geographic_limits": [],
        },
        "delivery_capability": {"geography": ["US"], "support_hours": "9-5 ET"},
    }
    base.update(overrides)
    return base


def product_icp_form(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "form_version": "2.0",
        "product_overview": {"summary": "Operator console for LinkedIn prospecting"},
        "problem_solved": {"primary": "Manual prospecting waste"},
        "value_proposition": {"primary": "Faster qualified pipeline"},
        "icp": {"industries": {"primary": ["Software", "SaaS"]}},
        "buyer_personas": {"primary_titles": ["CTO", "VP Sales"]},
        "pricing": {"model": "subscription", "min_deal_size": "10000"},
        "customer_success_stories": [
            {"name": f"Reference {index}", "website": f"https://ref{index}.example"}
            for index in range(1, 6)
        ],
        "differentiators": ["Operator-first workflows", "Strategy-scoped quotas"],
    }
    base.update(overrides)
    return base


def sales_strategy_form(
    *,
    name: str,
    narrative: str,
    target_companies: int = 5,
    contacts_per_company_default: int = 2,
    description: str = "Seeded local E2E strategy",
    **overrides: Any,
) -> dict[str, Any]:
    base: dict[str, Any] = {
        "form_version": "2.0",
        "overview": {
            "name": name,
            "description": description,
            "target_companies_narrative": narrative,
        },
        "priority_industries": {"primary": ["Software", "SaaS"]},
        "buying_signals": {"selected": ["Recently funded", "Hiring AEs"]},
        "run_targets": {
            "target_companies": target_companies,
            "contacts_per_company_default": contacts_per_company_default,
        },
    }
    base.update(overrides)
    return base


# Primary happy-path strategy companies (domain keys must stay unique globally).
PRIMARY_COMPANIES: list[dict[str, str]] = [
    {
        "name": "Acme Robotics",
        "website_url": "https://www.acme-robotics.example/about",
        "selection_reason": "Series B robotics firm hiring RevOps; strong ICP fit",
    },
    {
        "name": "BrightPath Soft",
        "website_url": "https://brightpath-soft.example",
        "selection_reason": "Mid-market SaaS with active AE hiring signals",
    },
    {
        "name": "Cobalt Analytics",
        "website_url": "https://cobalt-analytics.example",
        "selection_reason": "Data platform overlapping buyer personas",
    },
    {
        "name": "Drift Commerce",
        "website_url": "https://drift-commerce.example",
        "selection_reason": "Initially matched keywords but wrong buyer motion",
    },
]


def company_profile(**overrides: Any) -> dict[str, Any]:
    """Optional CompanyProfile payload stored on ``Company.profile`` JSON."""
    base: dict[str, Any] = {
        "linkedin_company_url": "https://www.linkedin.com/company/example",
        "industry": "Software",
        "sub_industry": "B2B SaaS",
        "headquarters": "San Francisco, CA",
        "operating_countries": ["US"],
        "employee_count": "201-500",
        "revenue_range": "$25M-$50M",
        "founded_year": 2016,
        "ownership": "Private",
        "business_model": "B2B SaaS",
        "description": "Seeded firmographic enrichment for operator demos.",
    }
    base.update(overrides)
    return base


# Domain → CompanyProfile. Cobalt intentionally omitted so null-profile UX is demoable.
PRIMARY_COMPANY_PROFILES: dict[str, dict[str, Any]] = {
    "acme-robotics.example": company_profile(
        linkedin_company_url="https://www.linkedin.com/company/acme-robotics-seed",
        industry="Industrial Automation",
        sub_industry="Robotics software",
        headquarters="San Francisco, CA",
        operating_countries=["US", "CA", "DE"],
        employee_count="501-1000",
        revenue_range="$50M-$100M",
        founded_year=2014,
        ownership="Private — Series B",
        business_model="Hardware + software subscription",
        description=(
            "Warehouse and field robotics platform selling fleet software to mid-market "
            "manufacturers and 3PLs."
        ),
    ),
    "brightpath-soft.example": company_profile(
        linkedin_company_url="https://www.linkedin.com/company/brightpath-soft-seed",
        industry="Software",
        sub_industry="Revenue operations SaaS",
        headquarters="Austin, TX",
        operating_countries=["US"],
        employee_count="51-200",
        revenue_range="$10M-$25M",
        founded_year=2018,
        ownership="Private — Series A",
        business_model="B2B SaaS",
        description="Mid-market sales engagement platform with active AE hiring.",
    ),
    "nova-warehousing.example": company_profile(
        linkedin_company_url="https://www.linkedin.com/company/nova-warehousing-seed",
        industry="Logistics",
        sub_industry="3PL warehousing",
        headquarters="Chicago, IL",
        operating_countries=["US"],
        employee_count="1001-5000",
        revenue_range="$100M-$250M",
        founded_year=2009,
        ownership="Private",
        business_model="3PL services",
        description="Multi-site fulfillment operator evaluating fleet automation software.",
    ),
}


PRIMARY_CONTACTS: dict[str, list[dict[str, Any]]] = {
    "acme-robotics.example": [
        {
            "full_name": "Ada Lovelace",
            "job_title": "CTO",
            "department": "Engineering",
            "seniority": "C-level",
            "linkedin_url": "https://www.linkedin.com/in/ada-lovelace-seed",
            "location": "San Francisco, CA",
            "selection_reason": "Owns tooling budget and vendor shortlist",
            "fit_rationale": "Primary economic buyer for operator console",
            "confidence_score": 92.0,
            "evidence_urls": ["https://www.linkedin.com/in/ada-lovelace-seed"],
        },
        {
            "full_name": "Grace Hopper",
            "job_title": "VP Sales",
            "department": "Sales",
            "seniority": "VP",
            "linkedin_url": "https://www.linkedin.com/in/grace-hopper-seed",
            "location": "Austin, TX",
            "selection_reason": "Owns outbound pipeline targets",
            "fit_rationale": "Champions prospecting workflow changes",
            "confidence_score": 86.0,
            "evidence_urls": ["https://www.linkedin.com/in/grace-hopper-seed"],
        },
    ],
    "brightpath-soft.example": [
        {
            "full_name": "Katherine Johnson",
            "job_title": "Head of Revenue Operations",
            "department": "RevOps",
            "seniority": "Director",
            "linkedin_url": "https://www.linkedin.com/in/katherine-johnson-seed",
            "location": "New York, NY",
            "selection_reason": "Owns CRM + sequencing stack",
            "fit_rationale": "Evaluates operator tooling for AE teams",
            "confidence_score": 81.0,
            "evidence_urls": ["https://www.linkedin.com/in/katherine-johnson-seed"],
        },
    ],
}

LIGHT_COMPANIES: list[dict[str, str]] = [
    {
        "name": "Orbit Logistics",
        "website_url": "https://orbit-logistics.example",
        "selection_reason": "Warehouse ops buyer motion for advisory services",
    }
]

PARTIAL_COMPANIES: list[dict[str, str]] = [
    {
        "name": "Nova Warehousing",
        "website_url": "https://nova-warehousing.example",
        "selection_reason": "Multi-site warehouse automation buyer",
    },
    {
        "name": "Summit Fulfillment",
        "website_url": "https://summit-fulfillment.example",
        "selection_reason": "Regional 3PL expanding fleet software",
    },
]

DISTRIBUTOR_COMPANIES: list[dict[str, str]] = [
    {
        "name": "Prairie Robot Supply",
        "website_url": "https://prairie-robot-supply.example",
        "selection_reason": "Midwest distributor stocking field service kits",
    },
    {
        "name": "Coastline Automation Partners",
        "website_url": "https://coastline-automation.example",
        "selection_reason": "Regional partner network for robot fleet service",
    },
]

PARTIAL_CONTACTS: dict[str, list[dict[str, Any]]] = {
    "nova-warehousing.example": [
        {
            "full_name": "Alan Turing",
            "job_title": "VP Operations",
            "department": "Operations",
            "seniority": "VP",
            "linkedin_url": "https://www.linkedin.com/in/alan-turing-seed",
            "location": "Chicago, IL",
            "selection_reason": "Owns warehouse automation roadmap",
            "fit_rationale": "Budget owner for fleet OS evaluation",
            "confidence_score": 84.0,
            "evidence_urls": ["https://www.linkedin.com/in/alan-turing-seed"],
        },
        {
            "full_name": "Dorothy Vaughan",
            "job_title": "Director of Automation",
            "department": "Engineering",
            "seniority": "Director",
            "linkedin_url": "https://www.linkedin.com/in/dorothy-vaughan-seed",
            "location": "Chicago, IL",
            "selection_reason": "Technical evaluator for fleet software",
            "fit_rationale": "Runs RFP scoring for ops tooling",
            "confidence_score": 79.0,
            "evidence_urls": ["https://www.linkedin.com/in/dorothy-vaughan-seed"],
        },
    ],
}

_FIRST_NAMES = (
    "Ada",
    "Grace",
    "Katherine",
    "Alan",
    "Dorothy",
    "Margaret",
    "Claude",
    "Barbara",
    "Dennis",
    "Frances",
    "Linus",
    "Radia",
    "Tim",
    "Anita",
    "Ken",
)
_LAST_NAMES = (
    "Lovelace",
    "Hopper",
    "Johnson",
    "Turing",
    "Vaughan",
    "Hamilton",
    "Shannon",
    "Liskov",
    "Ritchie",
    "Allen",
    "Torvalds",
    "Perlman",
    "Berners",
    "Borg",
    "Thompson",
)
_TITLES = (
    ("CTO", "Engineering", "C-level"),
    ("VP Sales", "Sales", "VP"),
    ("Head of Revenue Operations", "RevOps", "Director"),
    ("VP Operations", "Operations", "VP"),
    ("Director of Automation", "Engineering", "Director"),
    ("Chief Revenue Officer", "Sales", "C-level"),
    ("Director of Procurement", "Finance", "Director"),
    ("VP Engineering", "Engineering", "VP"),
)
_LOCATIONS = (
    "San Francisco, CA",
    "Austin, TX",
    "New York, NY",
    "Chicago, IL",
    "Seattle, WA",
    "Boston, MA",
    "Denver, CO",
    "Atlanta, GA",
)


def generate_companies(
    count: int,
    *,
    prefix: str,
    reason: str,
) -> list[dict[str, str]]:
    """Build unique website/domain companies for a strategy cohort."""
    companies: list[dict[str, str]] = []
    for index in range(1, count + 1):
        slug = f"{prefix}-{index:02d}"
        companies.append(
            {
                "name": f"{prefix.replace('-', ' ').title()} {index:02d}",
                "website_url": f"https://{slug}.example",
                "selection_reason": f"{reason} (seed cohort {prefix} #{index})",
            }
        )
    return companies


def generate_contacts_for_domain(
    domain: str,
    count: int,
    *,
    slug_prefix: str,
) -> list[dict[str, Any]]:
    """Build unique LinkedIn contacts for a company domain."""
    contacts: list[dict[str, Any]] = []
    for index in range(count):
        first = _FIRST_NAMES[index % len(_FIRST_NAMES)]
        last = _LAST_NAMES[(index * 3) % len(_LAST_NAMES)]
        title, department, seniority = _TITLES[index % len(_TITLES)]
        linkedin_slug = f"{slug_prefix}-{index + 1:02d}-{first}-{last}".lower()
        linkedin_url = f"https://www.linkedin.com/in/{linkedin_slug}-seed"
        contacts.append(
            {
                "full_name": f"{first} {last}",
                "job_title": title,
                "department": department,
                "seniority": seniority,
                "linkedin_url": linkedin_url,
                "location": _LOCATIONS[index % len(_LOCATIONS)],
                "selection_reason": f"Seed contact #{index + 1} for {domain}",
                "fit_rationale": f"Matches buyer persona ({title}) for seeded ICP",
                "confidence_score": float(70 + (index % 25)),
                "evidence_urls": [linkedin_url],
            }
        )
    return contacts


def _fixture_domain(website_url: str) -> str:
    host = website_url.removeprefix("https://").removeprefix("http://")
    host = host.removeprefix("www.").split("/", 1)[0].lower()
    return host


def contacts_by_domain(
    companies: list[dict[str, str]],
    *,
    contacts_per_company: int,
    slug_prefix: str,
) -> dict[str, list[dict[str, Any]]]:
    """Map normalized ``*.example`` domains to generated contact payloads."""
    mapping: dict[str, list[dict[str, Any]]] = {}
    for offset, company in enumerate(companies):
        domain = _fixture_domain(company["website_url"])
        mapping[domain] = generate_contacts_for_domain(
            domain,
            contacts_per_company,
            slug_prefix=f"{slug_prefix}-{offset + 1:02d}",
        )
    return mapping
