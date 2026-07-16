# Product / Service Form

> **Architecture reference:** Canonical `ProductProfile` schema for production LOOP.  
> See JSON persistence block below and [database plan](../02-database.md).  
> **Organization context:** [organization_form.md](organization_form.md) (seller company — business fit).  
> **Sales Strategy targeting:** [sales_strategy_form.md](sales_strategy_form.md) (Sales Strategy — per-run playbook).  
> **Planning index:** [form/README.md](README.md)

Fill this form **once per product or service** under an **Organization** (after the [Organization Form](organization_form.md) is complete). It captures **offering-level** context — what you sell, who buys it, and product fit. Reuse it across all sales strategies for that offering.

**Hierarchy:**

```text
Organization (organization_form.md → OrganizationProfile.org_form)
  └── Product / Service (this form → ProductProfile.icp_form)
        └── SalesStrategy (sales_strategy_form.md → SalesStrategy.sales_strategy_form)
              └── SalesStrategyCompany / SalesStrategyProspect

Global registry: Company / CompanyProfile / ProspectProfile / CompanyProspect
```

Four knowledge areas: [knowledge-model.md](../knowledge/knowledge-model.md).

---

## Knowledge pillars (Product/Service)

| Pillar | Form sections |
|--------|---------------|
| **Features** | §2 Product Overview (scope), §14 Integrations, §13 Implementation |
| **Benefits** | §4 Value Proposition, §11 Differentiators |
| **Pain points solved** | §3 Problem Solved |
| **ICP** | §5 Ideal Customer Profile, §6 Buyer Personas, §7 Use Cases |
| **Pricing** | §12 Pricing |
| **Competitors** | §10 Competitors |
| **Buying triggers** | §8 Customer Triggers, §18 Signals |

SalesStrategy [Sales Strategy form](sales_strategy_form.md) narrows ICP, signals, and playbook **per run** — do not duplicate sales-strategy-only targeting here.

---

## Category overview

| Category | What the operator should provide |
|----------|----------------------------------|
| **Product Overview** | What the product/service does in one sentence |
| **Problem Solved** | Business problem or pain point it solves |
| **Value Proposition** | Why it is better than alternatives |
| **Ideal Customer Profile (ICP)** | Company size, industry, geography, revenue, employee count, maturity, etc. |
| **Buyer Personas** | Who usually buys (CEO, CTO, HR, Sales Head, Marketing, etc.) |
| **Use Cases** | Scenarios where customers use it |
| **Customer Triggers** | Events indicating a company may need it (funding, hiring, expansion, compliance, tech migration, acquisitions, …) |
| **Blacklist** | Companies that are **not** a good fit |
| **Competitors** | Who prospects use instead |
| **Differentiators** | Why customers switch from competitors |
| **Pricing** | Price range, pricing model, minimum deal size |
| **Implementation** | Setup effort, onboarding time, technical requirements |
| **Integrations** | Software, platforms, or ecosystems it works with |
| **Customer Success Stories** | Industries and companies already using it |
| **Compliance / Restrictions** | Region, security, legal, or technical limitations |
| **Keywords** | Terms prospects use when describing the problem |
| **Signals** | Public indicators of need (job postings, tech stack, press, funding, hiring, website changes, …) |

---

## 1. Product identity

Record fields on `Product` (seller company name/website live on **Organization**):

| Field | Description |
|-------|-------------|
| **Name** | Product or service name |
| **Kind** | `product` or `service` |

---

## 2. Product Overview

* **One-sentence summary** — what the product/service does
* **Offering scope** — what is included in this product/service line (modules, tiers, packages)

---

## 3. Problem Solved

* Primary business problem or pain point
* Secondary pains it addresses
* What happens if the problem is **not** solved (cost of inaction)

---

## 4. Value Proposition

* Primary value proposition (2–3 sentences)
* Top outcomes customers achieve (measurable if possible)
* Why it is better than doing nothing or building in-house

---

## 5. Ideal Customer Profile (ICP)

General fit profile for this offering (sales strategies **narrow** this per run):

| Dimension | Examples |
|-----------|----------|
| **Industry** | Primary and secondary industries; industries to avoid |
| **Company size** | Employee count range; revenue range |
| **Geography** | Countries, regions; remote-only or on-site requirements |
| **Company type** | B2B, B2C, SaaS, marketplace, agency, enterprise, SMB, … |
| **Maturity** | Startup, growth, mature, PE-backed, public, … |
| **Technology profile** | Cloud-first, legacy stack, AI-adopting, regulated, … |

---

## 6. Buyer Personas

Who usually buys or champions the deal:

| Field | Examples |
|-------|----------|
| **Primary buyer titles** | CEO, CTO, VP Engineering, Head of Ops, HR Director, Sales Head, Marketing Director |
| **Economic buyer** | Who signs the contract |
| **Technical evaluator** | Who validates fit (if different) |
| **User personas** | Day-to-day users |
| **Seniority** | Founder, C-level, VP, director, manager |

---

## 7. Use Cases

List distinct scenarios where customers use the offering:

* Use case name
* Trigger situation
* Expected outcome
* Example customer type (optional)

Agents use these to judge company/contact relevance beyond checkbox ICP filters.

---

## 8. Customer Triggers

Events that suggest a company may need the offering **now**:

* Recently funded
* Hiring spree (roles relevant to your product)
* Expansion / new office / new market
* Compliance or regulatory change
* Technology migration (cloud, ERP, CRM, AI adoption)
* Acquisition or merger
* New product launch
* Leadership change
* Public statements about pain you solve

---

## 9. Blacklist

Companies that are **not** a good fit (product-level, always apply):

* Wrong industry or business model
* Too small / too large
* Wrong geography or regulatory block
* Uses incompatible tech stack
* Agency, reseller, or competitor types (if applicable)
* Budget below minimum deal size
* Free-text **other exclusion rules**

Sales Strategy form may add **additional** exclusions for a specific run.

---

## 10. Competitors

* Direct competitors (names + websites)
* Indirect alternatives (spreadsheets, manual process, in-house build)
* Who you most often lose deals to
* Common objection: “We already use X”

---

## 11. Differentiators

* Why customers switch **from** competitors **to** you
* Why existing customers chose you over alternatives
* Unique capabilities competitors lack
* Proof points (awards, certifications, benchmarks — optional)

---

## 12. Pricing

| Field | Description |
|-------|-------------|
| **Pricing model** | Subscription, one-time, retainer, usage-based, licensing, … |
| **Typical price range** | Average deal size |
| **Minimum deal size** | Do not pursue below this |
| **Sales cycle length** | Typical time to close |
| **Engagement model** | Project, subscription, retainer, hybrid |

---

## 13. Implementation

* Setup effort (self-serve vs assisted vs enterprise onboarding)
* Typical onboarding duration
* Technical requirements (SSO, API access, data migration, integrations mandatory at go-live)
* Internal resources customer must provide (IT, engineering, ops)

---

## 14. Integrations

Software, platforms, and ecosystems the offering works with:

* CRM, ERP, HRIS, data warehouse, cloud providers
* Must-have integrations for a successful deployment
* Nice-to-have integrations
* Ecosystems where your ideal customers already live (Salesforce, HubSpot, AWS, …)

---

## 15. Customer Success Stories

Reference customers agents can use for lookalike reasoning:

| Field | Description |
|-------|-------------|
| **Company name** | Customer or logo account |
| **Website** | Canonical URL |
| **Industry** | If known |
| **Why they bought** | Short fit rationale |
| **Outcome** | Result achieved (optional) |

**Minimum:** 5–20 reference companies (names or websites). More is better for pattern inference.

---

## 16. Compliance / Restrictions

* Regions you cannot sell or support
* Security certifications required or offered (SOC 2, ISO, HIPAA, …)
* Legal or contractual limitations
* Technical restrictions (on-prem only, air-gapped, data residency)
* Industries you cannot serve

---

## 17. Keywords

Terms prospects use when describing the problem or searching for solutions:

* Problem keywords
* Solution category keywords
* Technology keywords
* Role/title keywords (optional overlap with buyer personas)

---

## 18. Signals

Public indicators that suggest active need (observable during research):

* Job postings (roles, skills, volume)
* Tech stack changes (BuiltWith, careers page, GitHub)
* Press releases and news
* Funding announcements
* Hiring velocity
* Website copy changes (new product pages, pricing page, “we’re hiring”)
* Leadership posts on LinkedIn about relevant pain

---

## Required fields (minimum to create a sales strategy)

Before starting any sales strategy under this product/service, validation must pass on:

1. **Product Overview** — one-sentence summary (§2)
2. **Problem Solved** and **Value Proposition** (§3–4)
3. **ICP** — at least industry **or** company size **or** geography (§5)
4. **Buyer Personas** — at least one primary buyer title (§6)
5. **Pricing** — model and minimum deal size (§12)
6. **Customer Success Stories** — at least **5** reference companies (§15)
7. **Differentiators** — why customers choose you over alternatives (§11)

Optional but strongly recommended: Customer Triggers, Blacklist, Signals, Keywords, Integrations, Implementation, Compliance.

---

## What belongs in the Organization Form instead

See [organization_form.md](organization_form.md) for seller-company fields: mission, org industry, business model, org size, target markets, customer segments, brand positioning, delivery capability, org-level deal constraints, case studies at company level, etc.

---

## What belongs in the Sales Strategy Form instead

The **[Sales Strategy Form](sales_strategy_form.md)** operationalizes **this** product context for one run — see [knowledge-model.md §3](../knowledge/knowledge-model.md#3-sales-strategy-knowledge--who-to-target-now--how):

| Product form (stable) | Sales Strategy form (per sales strategy) |
|-----------------------|-------------------------------------|
| General ICP, personas, triggers, signals | **Priority** industries, geographies, size bands for **now** |
| Product-level exclusion rules | SalesStrategy qualification / blacklist / exclusion rules |
| General keywords and signals | SalesStrategy buying signals, prospecting sources, experiments |
| Competitors (who prospects use) | **Competitor targeting** — which incumbents make good targets this run |
| Value prop and differentiators | **Messaging hypotheses**, outreach strategy, lessons learned |
| — | Target decision makers, prioritization rules, success metrics, run targets |

---

## Persistence (`ProductProfile.icp_form`)

Payload stored as JSONB on `product_profile.icp_form`:

```json
{
  "form_version": "2.0",
  "product_overview": { "summary": "", "offering_scope": "" },
  "problem_solved": { "primary": "", "secondary": [], "cost_of_inaction": "" },
  "value_proposition": { "primary": "", "outcomes": [] },
  "icp": {
    "industries": { "primary": [], "secondary": [], "avoid": [] },
    "company_size": { "employees_min": null, "employees_max": null, "revenue_min": null, "revenue_max": null },
    "geography": { "countries": [], "regions": [], "exclude_countries": [] },
    "company_types": [],
    "maturity": []
  },
  "buyer_personas": { "primary_titles": [], "economic_buyer": "", "technical_evaluator": "", "seniority": [] },
  "use_cases": [{ "name": "", "trigger": "", "outcome": "" }],
  "customer_triggers": [],
  "exclusion rules": { "rules": [], "free_text": "" },
  "competitors": [{ "name": "", "website": "", "type": "direct|indirect" }],
  "differentiators": [],
  "pricing": { "model": "", "typical_range": "", "min_deal_size": "", "sales_cycle": "", "engagement_model": "" },
  "implementation": { "setup_effort": "", "onboarding_duration": "", "technical_requirements": [], "customer_resources": [] },
  "integrations": { "must_have": [], "nice_to_have": [], "ecosystems": [] },
  "customer_success_stories": [{ "name": "", "website": "", "industry": "", "why_they_bought": "", "outcome": "" }],
  "compliance_restrictions": { "regions_blocked": [], "certifications": [], "legal_notes": "", "technical_limits": [] },
  "keywords": [],
  "signals": []
}
```

`Product.kind`, `Product.name`, and seller company name/website may also live on the `Product` row; the wizard should keep them in sync with profile submission.

---

## Agent consumption

| Consumer | Reads from product form |
|----------|-------------------------|
| **Company Finder** | ICP, triggers, signals, exclusion rules, keywords, success stories (lookalikes), competitors/differentiators for fit rationale |
| **Contact Finder** | Buyer personas, use cases, signals |
| **
`get_sales_strategy_bundle` includes a compressed **`icp_form` excerpt** plus full sales strategy `sales_strategy_form`.

---

## API

| Method | Path |
|--------|------|
| GET/PATCH | `/api/v1/products/{id}/profile` |
| POST | `/api/v1/products/{id}/profile/validate` |

Validation returns missing required sections and `completion_pct`.
