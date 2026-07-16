# Sales Strategy Form

> **Knowledge area:** **Sales Strategy Knowledge** — *Who should we target right now, how should we approach them, and what are we testing?*  
> **Architecture reference:** Canonical `SalesStrategy.sales_strategy_form` schema for production LOOP.  
> See [knowledge-model.md §3](../knowledge/knowledge-model.md#3-sales-strategy-knowledge--who-to-target-now--how) and JSON persistence below.  
> **Upstream context:** [organization_form.md](organization_form.md) (business fit) and [service_form.md](service_form.md) (product fit). This form **narrows and operationalizes** that context for **one run**.  
> **Planning index:** [form/README.md](README.md)

Fill this form **once per sales strategy** at **creation time**. Each sales strategy is **one playbook snapshot** — who to find, how to find them, how to approach them, and what the team is currently testing. **`sales_strategy_form` is immutable after create** — to evolve the playbook, create a **new sales strategy** (pre-fill from a prior sales strategy or template).

Unlike Organization and Product/Service knowledge, Sales Strategy is **experiential and time-bound**. Examples that belong here:

* “We’re focusing on logistics companies this quarter.”
* “Target CTOs before Engineering Managers.”
* “Mention SOC 2 in the first email — it increases reply rates.”
* “Healthcare companies under 100 employees aren’t converting.”
* “Avoid Competitor X unless they’re rapidly scaling.”

---

## Knowledge pillars (Sales Strategy)

| Category | What should be defined |
|----------|------------------------|
| **Target Company Profile** | What kinds of companies we want to approach **now** |
| **Target Decision Makers** | Which roles should be contacted first |
| **Priority Industries** | Industries to focus on this run |
| **Priority Geographies** | Countries, regions, or cities to target |
| **Company Size** | Employee and revenue ranges |
| **Buying Signals** | Events indicating a company may be ready to buy (funding, hiring, expansion, …) |
| **Prospecting Strategy** | How prospects will be found (LinkedIn, Apollo, Crunchbase, Google, …) |
| **Outreach Strategy** | Cold email, LinkedIn, calls, referrals, partners, … |
| **Messaging Hypotheses** | Value propositions or angles to test |
| **Qualification Criteria** | What makes a company worth pursuing |
| **Blacklist Criteria** | When to skip a company |
| **Prioritization Rules** | Which prospects should be contacted first |
| **Competitor Targeting** | Customers using which competitors are good targets |
| **Exclusion Rules** | Companies, industries, or regions to avoid |
| **Experiments** | New ICPs, industries, messaging, or channels being tested |
| **Success Metrics** | Meetings booked, reply rate, conversions, pipeline, … |
| **Lessons Learned** | What has worked and what hasn’t (from prior runs) |
| **Best Practices** | Repeatable tactics discovered by the team |
| **Run Targets** | `target_companies`, default contacts per company, optional message guidance |

---

## 1. Sales strategy overview

| Field | Description |
|-------|-------------|
| **Sales strategy name** | Short label for this strategy run |
| **Description** | 1–2 sentences — what this sales strategy is testing or focusing on |
| **Target companies in your own words** | Free-text ICP for this run (operator + agent anchor) |

---

## 2. Target company profile

What kinds of companies to approach **in this sales strategy** (narrows product ICP):

* Company type — B2B, B2C, SaaS, marketplace, manufacturing, healthcare, agency, …
* Characteristics — cloud-first, AI-adopter, venture-backed, PE-backed, digital transformation, …
* Similar companies — example URLs of companies you would love to find
* Keywords — terms that describe ideal targets (AI, logistics, FinTech, …)
* Problems they should have — pains that indicate need **for this sales strategy’s angle**

---

## 3. Target decision makers

Roles and seniority to contact first inside each validated company:

* Primary titles (e.g. CTO, VP Engineering, Head of Ops)
* Secondary titles
* Seniority order — founder → C-level → VP → manager
* Contact-level buying signals (e.g. posted about automation pain)

---

## 4. Priority industries

* Primary industries
* Secondary industries
* Industries to deprioritize (not necessarily hard exclusions — see §15)

---

## 5. Priority geographies

* Countries / regions / cities
* Remote-only companies?
* Exclude countries or regions

---

## 6. Company size

* Employees (min / max)
* Revenue (min / max)
* Segment tags — startup, SMB, mid-market, enterprise

---

## 7. Buying signals

Events indicating readiness **now** (select all that apply):

* Hiring engineers / AI engineers / specific roles
* Recently funded / acquisition / IPO
* New office / international expansion
* New product launch / digital transformation / cloud migration
* Automation or AI initiative signals
* Growing engineering team / building AI products

Observed signals inform `SalesStrategyCompany.selection_reason`; they are not persisted as company firmographics by `register_company`.

---

## 8. Prospecting strategy

How Company Finder should discover companies (source-agnostic — quota is total companies found, not per channel):

* LinkedIn, Crunchbase, Product Hunt, YC, app stores, VC portfolios
* Careers pages, GitHub, news, AngelList / Wellfound, Google, Apollo, …
* Search keywords or query hints per source (optional)

---

## 9. Outreach strategy

How humans (and future automation) should approach contacts after discovery:

* Primary channel — LinkedIn connection, InMail, email, phone, referral, partner intro (v1: human records on Company detail)
* Sequence notes — timing, follow-up cadence
* Do-not-contact rules for this sales strategy

---

## 10. Messaging hypotheses

Value propositions and angles to test in outreach:

* Primary hook / angle
* Secondary hooks
* Proof points to mention (case study, certification, metric)
* Tone — consultative, direct, technical, …

Optional **message guidance** for operators when a contact is found.

---

## 11. Qualification criteria

What makes a registered company **worth pursuing** for this run:

* Must-have attributes (industry band, size, tech, signal, …)
* Nice-to-have attributes
* Minimum confidence threshold guidance for agents (optional)

Used by operators on **Records Viewer** and by Company Finder when writing `SalesStrategyCompany.selection_reason`.

---

## 12. Blacklist criteria

When to **skip** a company (operator blacklist or agent should not register):

* Firmographic rules — too small / too large, wrong segment
* Wrong industry, geography, or company type
* Missing required tech or using forbidden stack
* Agency, government, consulting (if applicable)

Maps to `SalesStrategyCompany.blacklist_reason` when operator blacklists the company for this strategy.

---

## 13. Prioritization rules

Which prospects to contact or validate first within the sales strategy:

* Order by signal strength, funding recency, hiring velocity, …
* Prefer companies matching experiment cohort A vs B
* Tie-break rules for Contact Finder queue

---

## 14. Competitor targeting

Customers using which incumbents are **good targets** for this run:

* Competitor products / vendors to look for in stack or job posts
* Switch triggers — why they might leave incumbent
* When **not** to target incumbent users (unless scaling fast — see exclusion)

Product-level competitors live in [service_form.md](service_form.md); this section is **sales-strategy-specific targeting**.

---

## 15. Exclusion rules

Hard avoids for this sales strategy:

* Named companies or domains
* Industries, regions, or segments to never register
* Competitor users to avoid (unless exception in §14)

---

## 16. Experiments

What the team is **actively testing** in this sales strategy:

* Hypothesis statement
* Variant — industry focus, messaging angle, channel, ICP slice
* Success criteria for the experiment
* Control vs test notes (optional)

---

## 17. Success metrics

How the team will judge this strategy run (operator-defined; not auto-computed):

* Target meetings booked, reply rate, positive sentiment rate
* Pipeline or SQL targets (optional)
* Company registration quality bar

---

## 18. Lessons learned

Institutional memory **copied forward** from prior sales strategies or filled at create:

* What worked — industries, titles, messaging, signals
* What didn’t — segments that wasted time, low reply angles
* Dated notes optional (“Q2 2026: healthcare &lt;100 FTE didn’t convert”)

---

## 19. Best practices

Repeatable tactics for agents and operators:

* Playbook bullets — e.g. “Mention SOC 2 in first touch,” “Validate funding within 12 months”
* Source-specific tips
* Operator checklist items

---

## 20. Run targets

Operational quotas for this sales strategy:

| Field | Description |
|-------|-------------|
| **Target company count** (required) | How many companies Company Finder should register before the **company phase** completes |
| **Default contacts per company** (required for Contact Finder) | Initial **N** when operator marks valid on **Records Viewer**; adjust per company via **Blacklist** |
| **Message guidance** (optional) | Short default angle for outreach when a contact is found |

> **Per-company N:** `SalesStrategy.contacts_per_company_default` seeds `SalesStrategyCompany.contacts_target` at mark-valid and is **fixed** (no increment UI). To pursue more contacts per company, create a **new sales strategy**. Contact Finder runs until `contacts_registered >= contacts_target`. See [operator workflow](../02-database.md#operator-workflow-company--contact).

---

## Required fields (minimum to start agents)

1. **Sales strategy overview** — name + target companies in your own words (§1)
2. **Run targets** — `target_companies` + `contacts_per_company_default` (§20)
3. At least one targeting dimension: **priority industries** (§4), **buying signals** (§7), or **keywords** in target company profile (§2)

---

## `sales_strategy_form` JSON (v2.0)

Stored on `SalesStrategy.sales_strategy_form`. Denormalized columns: `target_companies`, `contacts_per_company_default`.

```json
{
  "form_version": "2.0",
  "overview": {
    "name": "",
    "description": "",
    "target_companies_narrative": ""
  },
  "target_company_profile": {
    "company_types": [],
    "characteristics": [],
    "similar_companies": [{ "name": "", "website_url": "" }],
    "keywords": [],
    "problems_they_should_have": []
  },
  "target_decision_makers": {
    "primary_titles": [],
    "secondary_titles": [],
    "seniority_order": [],
    "contact_buying_signals": []
  },
  "priority_industries": {
    "primary": [],
    "secondary": [],
    "deprioritized": []
  },
  "priority_geographies": {
    "countries": [],
    "regions": [],
    "cities": [],
    "remote_only": false,
    "exclude_countries": []
  },
  "company_size": {
    "employees_min": null,
    "employees_max": null,
    "revenue_min": null,
    "revenue_max": null,
    "segments": []
  },
  "buying_signals": {
    "selected": [],
    "custom": []
  },
  "prospecting_strategy": {
    "sources": [],
    "source_hints": {}
  },
  "outreach_strategy": {
    "primary_channel": "",
    "channels": [],
    "sequence_notes": "",
    "do_not_contact_rules": []
  },
  "messaging_hypotheses": {
    "primary_hook": "",
    "secondary_hooks": [],
    "proof_points": [],
    "tone": "",
    "message_guidance": ""
  },
  "qualification_criteria": {
    "must_have": [],
    "nice_to_have": [],
    "min_confidence_hint": null
  },
  "blacklist_criteria": {
    "rules": []
  },
  "prioritization_rules": {
    "rules": []
  },
  "competitor_targeting": {
    "incumbents_to_target": [],
    "switch_triggers": [],
    "avoid_unless_scaling": []
  },
  "exclusion_rules": {
    "companies": [],
    "domains": [],
    "industries": [],
    "regions": []
  },
  "experiments": [
    {
      "hypothesis": "",
      "variant": "",
      "success_criteria": "",
      "notes": ""
    }
  ],
  "success_metrics": {
    "targets": []
  },
  "lessons_learned": {
    "worked": [],
    "did_not_work": []
  },
  "best_practices": [],
  "run_targets": {
    "target_companies": 0,
    "contacts_per_company_default": 0
  }
}
```

Legacy v1 payloads (12-section form) may be migrated to v2.0 at read time; new sales strategies use v2.0 only.

---

## What happens after the form

| Phase | Where in UI | Agent | Completion |
|-------|-------------|-------|------------|
| Company discovery | **Records Viewer** + **Company Finder Process** | Company Finder (start/stop on Process tab) | `target_companies` reached |
| Contact discovery | **Records Viewer** / **Company detail** + **Contact Finder Process** | Contact Finder (start/stop; requires `contacts_per_company_default > 0`) | Per company: `contacts_registered / contacts_target` |
| All efforts | **Threads** tab | — | Linked + unlinked threads → snapshot viewer |

Operator flow: companies appear on **Records Viewer** → **mark valid** or **blacklist** (reason) → open **Company detail** for prospects, prospect blacklist/unblacklist, and outreach → start agents on **Process** tabs.

Contact Finder may run **in parallel** with Company Finder once companies are validated.

---

## Agent output (register_company)

Company Finder may research richer evidence, but the persisted command is intentionally minimal:

| Field | Description |
|-------|-------------|
| Company name | Legal or brand name |
| Website domain | Normalized registrable domain (e.g. `acme.com`) — persisted on `Company.domain` |
| Selection reason | Why the global company should be linked to this sales strategy |

`register_company(name, website_url, selection_reason)` normalizes URL to `domain`, get-or-creates global `Company`, then creates `SalesStrategyCompany`. It does not write industry, size, revenue, technology, vendors, scores, or evidence. Those details belong to optional future `CompanyProfile` enrichment.

See [database plan](../02-database.md#strategy-scoped-blacklist-junction-columns) for blacklist and quota rules.

---

## Agent output (register_contact)

`register_contact` uses the full ProspectProfile payload and creates both global and strategy links:

| Field | Description |
|-------|-------------|
| Full name | Identity as shown publicly |
| Job title | **Required** — must match §3 target decision makers |
| Department | Organization area |
| Seniority | Influence level |
| LinkedIn profile URL | Canonical profile URL |
| Public email | Only if publicly available |
| Public phone | Only if publicly available |
| Location | Regional outreach context |
| Company ID | Must match validated `SalesStrategyCompany` |
| Selection reason | Why this prospect is selected inside this company for this strategy |
| Fit rationale | Fit vs §3 + product buyer personas + org sales process |
| Confidence score | 0–100 |
| Source URLs | Where evidence was observed |

The command get-or-creates global `ProspectProfile`, get-or-creates `CompanyProspect`, and inserts `SalesStrategyProspect` (`is_blacklisted = false`). `sales_strategy_id` and `company_id` are supplied by the agent runtime (active Contact Finder effort), not repeated in every agent field. `contacts_registered` counts prospects where `is_blacklisted = false`.

---

## Agent output (blacklist_prospect)

Contact Finder may exclude a profile without a full discovery register. Agent passes **minimal** input; runtime binds strategy + company.

| Field | Required | Description |
|-------|----------|-------------|
| LinkedIn profile URL | Yes | Canonical `/in/` URL — lookup key |
| Blacklist reason | Yes | Why this prospect is excluded for this strategy+company |
| Full name | No | Sparse identity when creating a new global profile |
| Job title | No | Sparse identity when creating a new global profile |

**Tool behavior:**

1. Resolve `sales_strategy_id` + `company_id` from the active Contact Finder effort.
2. If `SalesStrategyProspect` already exists → set `is_blacklisted = true`, `blacklist_reason`.
3. If not linked → get-or-create sparse `ProspectProfile` (LinkedIn URL required; other fields optional), `CompanyProspect`, `SalesStrategyProspect` with `is_blacklisted = true` in one transaction.
4. Does **not** increment successful contact quota fill (`contacts_registered` excludes blacklisted rows).

Operator `POST .../blacklist` uses the same use case (may include `prospect_profile_id` when the row already exists).

---

## Operator outreach (human — v1)

After Contact Finder registers a prospect, the operator records outreach on the strategy-specific `SalesStrategyProspect` row:

| Field | Values |
|-------|--------|
| Connection request | **sent** / **ignored** / **accepted** |
| Received response? | yes / no |
| If yes — sentiment | **positive** / **negative** |
| If negative — what happened | Free text (required) |

API: `PATCH /api/v1/sales-strategies/{strategyId}/companies/{companyId}/prospects/{prospectProfileId}/outreach` — see [API plan](../04-api-and-contracts.md).

Outcomes inform the **next** sales strategy’s §18–19 (lessons learned / best practices), not this sales strategy’s frozen `sales_strategy_form`.
