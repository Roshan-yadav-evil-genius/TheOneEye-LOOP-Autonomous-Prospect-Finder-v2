# Organization Form

> **Architecture reference:** Canonical `OrganizationProfile` schema for production LOOP.  
> See JSON persistence block below and [database plan](../02-database.md).  
> **Product/service context** is defined separately in [service_form.md](service_form.md).  
> **Planning index:** [form/README.md](README.md)

Fill this form **once per organization** when the salesperson (or operator) creates the organization record. It captures **who you represent as a company** — mission, market position, delivery capability, and deal constraints — so agents and operators can judge **business fit**, not just product fit.

**Hierarchy:**

```text
Organization (this form → OrganizationProfile.org_form)
  └── Product / Service (service_form.md → ProductProfile.icp_form)
        └── SalesStrategy (sales_strategy_form.md → SalesStrategy.sales_strategy_form)
              └── SalesStrategyCompany / SalesStrategyProspect

Global registry: Company / CompanyProfile / ProspectProfile / CompanyProspect
```

Four knowledge areas: [knowledge-model.md](../knowledge/knowledge-model.md).

---

## Knowledge pillars (Organization)

| Pillar | Form sections |
|--------|---------------|
| **Mission** | §2 Company Overview |
| **Industry** | §3 Industry, §4 Business Model |
| **Strengths** | §9 Brand Positioning, §10 Unique Strengths, §11 Competitive Landscape |
| **Capabilities** | §14 Delivery Capability, §15 Certifications, §16 Technology Expertise |
| **Markets** | §6 Target Markets, §8 Customer Segments |
| **Customers** | §7 Existing Customers, §17 Case Studies, §18 References |
| **Strategy** | §12 Sales Goals, §13 Partnership Strategy, §19 Pricing Position, §20 Sales Process, §21 Deal Constraints |

---

## Why this form exists

A prospect can match a **product** on paper but still be wrong for the **organization** (wrong geography, segment, deal size, compliance, delivery capacity, or strategic focus). This form gives Company Finder and operators the seller-company context needed alongside product-level ICP.

---

## Category overview

| Category | What the salesperson should provide |
|----------|-------------------------------------|
| **Company Overview** | What the company does and its mission |
| **Industry** | Which industry the company operates in |
| **Business Model** | B2B, B2C, SaaS, Agency, Manufacturing, Services, etc. |
| **Company Size** | Employees, revenue, years in business |
| **Target Markets** | Countries, regions, or industries served |
| **Existing Customers** | Types of companies already served |
| **Customer Segments** | Enterprise, Mid-market, SMB, Startups, Government, etc. |
| **Brand Positioning** | Premium, affordable, enterprise-grade, niche, etc. |
| **Unique Strengths** | Core capabilities and competitive advantages |
| **Competitive Landscape** | Main competitors and differentiators |
| **Sales Goals** | Revenue targets, strategic industries, expansion markets |
| **Partnership Strategy** | Partners, resellers, or direct sales |
| **Delivery Capability** | Geographic coverage, languages, support hours, implementation capacity |
| **Certifications & Compliance** | ISO, SOC 2, GDPR, HIPAA, PCI DSS, etc. |
| **Technology Expertise** | Platforms, languages, cloud providers, frameworks, tools |
| **Case Studies** | Notable projects and successful customer outcomes |
| **References** | Well-known clients or industries served |
| **Pricing Position** | Budget, mid-market, premium, enterprise |
| **Sales Process** | Discovery → Demo → Proposal → POC → Contract, etc. |
| **Deal Constraints** | Minimum contract value, preferred/excluded industries, geographic limits |

---

## 1. Organization identity

Basic record fields (stored on `Organization`, synced with profile wizard):

| Field | Description |
|-------|-------------|
| **Organization name** | Legal or brand name |
| **Website** | Canonical company website |
| **Primary contact email** | Optional; for notifications later |

---

## 2. Company Overview

* What the company does (2–5 sentences)
* Mission or vision statement
* Year founded (optional)
* Headquarters location (optional)

---

## 3. Industry

* Primary industry
* Secondary industries (if any)
* Sub-verticals or niches

---

## 4. Business Model

Select all that apply:

* B2B, B2C, B2G (government)
* SaaS, marketplace, agency, consulting, manufacturing, services, hardware, other

Brief description of how the company makes money.

---

## 5. Company Size

| Field | Description |
|-------|-------------|
| **Employee count** | Current approximate headcount or range |
| **Annual revenue** | Range or order of magnitude (optional) |
| **Years in business** | How long operating |

---

## 6. Target Markets

* Countries and regions actively served
* Industries or verticals prioritized
* Markets explicitly **not** served

---

## 7. Existing Customers

Types of companies already served (patterns, not only logos):

* Typical customer profile (size, industry, maturity)
* Industries with strongest traction
* Customer concentration notes (optional)

---

## 8. Customer Segments

Segments the organization sells into:

* Enterprise, mid-market, SMB, startup, government, non-profit, etc.
* Primary segment vs secondary
* Segments to avoid

---

## 9. Brand Positioning

How the market perceives the company:

* Premium, affordable, enterprise-grade, niche specialist, fast-moving, white-glove, etc.
* Positioning statement (1–2 sentences)

---

## 10. Unique Strengths

Core capabilities and competitive advantages at the **company** level:

* Delivery speed, domain expertise, proprietary IP, team credentials, global footprint, support quality, etc.

---

## 11. Competitive Landscape

* Main competitors (company-level, not product-specific only)
* How the organization is generally differentiated in the market
* Common reasons deals are won or lost

---

## 12. Sales Goals

Current commercial priorities:

* Revenue or pipeline targets (optional)
* Strategic industries to win this quarter/year
* Expansion markets (new geos or verticals)
* Accounts or logo types prioritized

---

## 13. Partnership Strategy

* Direct sales only, or partners/resellers/MSPs/system integrators
* Partner-led vs direct-led regions
* Constraints on who can resell or co-sell

---

## 14. Delivery Capability

* Geographic coverage for delivery and support
* Languages supported
* Support hours / time zones
* Implementation capacity (concurrent projects, team size, lead time)

---

## 15. Certifications & Compliance

* Certifications held: ISO, SOC 2, GDPR readiness, HIPAA, PCI DSS, etc.
* Compliance frameworks customers often require
* Data residency or security commitments

---

## 16. Technology Expertise

Company-wide technical strengths (broader than a single product):

* Cloud providers (AWS, Azure, GCP, …)
* Languages, frameworks, platforms
* Tools and ecosystems the team specializes in

---

## 17. Case Studies

Notable projects and outcomes at the organization level:

| Field | Description |
|-------|-------------|
| **Title** | Project or program name |
| **Customer type** | Industry, size |
| **Challenge** | Problem addressed |
| **Outcome** | Measurable result |
| **Link** | URL or document reference (optional) |

---

## 18. References

Well-known clients or reference industries:

* Logo clients (names + websites)
* Reference industries where the org is strongest
* Testimonial themes (optional)

---

## 19. Pricing Position

Organization-level price band (not SKU-level pricing):

* Budget / mid-market / premium / enterprise
* Typical contract sizes the org pursues
* How pricing is generally positioned vs competitors

---

## 20. Sales Process

Typical stages from first touch to contract:

* Example: Discovery → Qualification → Demo → Proposal → POC → Security review → Contract
* Average cycle length
* Required stakeholders in a standard deal

---

## 21. Deal Constraints

Hard rules for **business fit** (org-level; product form may add product-specific limits):

| Constraint | Examples |
|------------|----------|
| **Minimum contract value** | Do not pursue below $X |
| **Preferred industries** | Prioritize fintech, healthcare, … |
| **Excluded industries** | No gambling, no agencies, … |
| **Geographic limitations** | No APAC without partner; US/Canada only |
| **Other** | Free-text deal breakers |

Agents and operators use these to blacklist prospects that match the product but not the seller organization.

---

## Required fields (minimum to create a product/service)

Before registering a **product or service** under this organization:

1. **Company Overview** — what the company does + mission (§2)
2. **Industry** and **Business Model** (§3–4)
3. **Target Markets** — at least one region or industry served (§6)
4. **Customer Segments** — at least one segment (§8)
5. **Deal Constraints** — minimum contract value **or** excluded industries/geographies (§21)
6. **Delivery Capability** — geographic coverage or support scope (§14)

Optional but strongly recommended: Sales Goals, Competitive Landscape, Certifications, Case Studies, References, Pricing Position, Sales Process.

---

## What belongs in the Product/Service Form instead

| Organization form (seller company) | Product/Service form (offering) |
|-----------------------------------|----------------------------------|
| Company mission, industry, business model | Product overview, problem solved, value prop |
| Org-wide target markets and segments | Product ICP and buyer personas |
| Delivery capability, certifications (company) | Product implementation, integrations, compliance |
| Org competitive landscape, brand positioning | Product competitors and differentiators |
| Deal constraints (org-level) | Product pricing, min deal size, product exclusion rules |
| Case studies and references (company) | Customer success stories (product-specific) |

---

## Persistence (`OrganizationProfile.org_form`)

```json
{
  "form_version": "1.0",
  "company_overview": { "description": "", "mission": "", "founded_year": null, "headquarters": "" },
  "industry": { "primary": "", "secondary": [], "sub_verticals": [] },
  "business_model": { "types": [], "description": "" },
  "company_size": { "employees": "", "revenue_range": "", "years_in_business": null },
  "target_markets": { "countries": [], "regions": [], "industries": [], "excluded": [] },
  "existing_customers": { "typical_profile": "", "strong_industries": [] },
  "customer_segments": { "primary": [], "secondary": [], "avoid": [] },
  "brand_positioning": { "position": "", "statement": "" },
  "unique_strengths": [],
  "competitive_landscape": { "competitors": [], "differentiators": [], "win_loss_notes": "" },
  "sales_goals": { "revenue_targets": "", "strategic_industries": [], "expansion_markets": [] },
  "partnership_strategy": { "model": "", "regions": "", "notes": "" },
  "delivery_capability": { "geography": [], "languages": [], "support_hours": "", "implementation_capacity": "" },
  "certifications_compliance": { "certifications": [], "frameworks": [], "data_residency": "" },
  "technology_expertise": { "cloud": [], "languages": [], "platforms": [], "tools": [] },
  "case_studies": [{ "title": "", "customer_type": "", "challenge": "", "outcome": "", "link": "" }],
  "references": { "clients": [{ "name": "", "website": "" }], "industries": [] },
  "pricing_position": { "band": "", "typical_contract_size": "", "positioning_notes": "" },
  "sales_process": { "stages": [], "cycle_length": "", "stakeholders": [] },
  "deal_constraints": {
    "min_contract_value": "",
    "preferred_industries": [],
    "excluded_industries": [],
    "geographic_limits": [],
    "other": ""
  }
}
```

---

## Agent consumption

| Consumer | Reads from organization form |
|----------|------------------------------|
| **Company Finder** | Deal constraints, target markets, segments, delivery capability, org exclusion rules vs prospect |
| **Contact Finder** | Buyer personas (with product form), sales process stages |
| **`get_sales_strategy_bundle`** | Compressed **`org_form` excerpt** plus product `icp_form` excerpt and full sales strategy `sales_strategy_form` |

Fit rationale on `register_company` should consider **both** organization business fit and product/sales strategy fit.

---

## API

| Method | Path |
|--------|------|
| GET/PATCH | `/api/v1/organizations/{id}/profile` |
| POST | `/api/v1/organizations/{id}/profile/validate` |

Validation returns missing required sections and `completion_pct`. Product creation returns **409** if organization profile is incomplete.
