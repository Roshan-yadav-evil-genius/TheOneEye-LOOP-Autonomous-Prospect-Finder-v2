# Contact Finder Prompt (Prospect Discovery)

> **Purpose:** Minimum sufficient context for the **Contact Finder** agent to identify **people** inside a validated target company — not companies, not outreach, not product selling.

## What this file is

[`prompt.md`](prompt.md) is the canonical **Prospect Discovery** prompt template for production LOOP. At runtime, placeholders are filled from:

- The selected global **Company** (`name` + normalized `domain`) and optional `CompanyProfile` when future enrichment exists
- The sales strategy’s [`sales_strategy_form.md`](../../../../form/sales_strategy_form.md) (decision makers, qualification, exclusions, prioritization)
- Compressed product context only where needed for **solution category** and **sales objective** (from [`service_form.md`](../../../../form/service_form.md) excerpts in the bundle)

The prompt stays focused on **who to contact inside this company**, not rediscovering the company or drafting messages.

## Intention

At contact discovery stage, the agent answers one question:

> **Given this company and this sales objective, who is most likely to own the problem, influence the decision, or approve the purchase?**

| Included | Why |
|----------|-----|
| Target company context | Grounds search to one validated company |
| Sales objective | What we are trying to sell / solve for this run |
| Solution category | Frames role relevance without full product spec |
| Buying committee + preferred titles | Who to find first |
| Department priority | Where to search inside the org |
| Qualification + exclusion rules | Filter noise (recruiters, interns, …) |
| Prioritization rules | Rank when multiple people qualify |
| Search constraints | LinkedIn-first, current employees, public evidence |
| Expected output + decision guidelines | Stable `register_contact` contract |

## What is intentionally excluded

For **prospect discovery**, the agent does **not** need:

| Excluded | Lives in |
|----------|----------|
| Organization history, mission, values | [organization_form.md](../../../../form/organization_form.md) |
| Product features, pricing, competitors | [service_form.md](../../../../form/service_form.md) |
| Case studies, implementation, sales process | Org / product forms |
| Messaging hypotheses, outreach strategy | Sales strategy form §9–10 (operator/outreach phase) |
| Company discovery / ICP matching | [Company Finder prompt](../company-finder/README.md) |

Product knowledge is already distilled into **sales objective**, **solution category**, **target roles**, and **qualification criteria** — keeping the prompt reusable across products and sales strategies.

## Runtime mapping

| Prompt placeholder | Typical source |
|--------------------|----------------|
| `{{company_name}}`, `{{company_website}}` | global `Company` |
| `{{company_summary}}`, `{{industry}}`, `{{employee_count}}` | optional `CompanyProfile`; use unknown when absent |
| `{{sales_objective}}` | `sales_strategy_form.overview` + messaging / problem narrative |
| `{{solution_category}}` | Product `icp_form` excerpt or `service_form` kind + category |
| `{{target_roles}}` | `target_decision_makers` + product buyer personas excerpt |
| `{{preferred_job_titles}}` | `target_decision_makers.primary_titles`, `secondary_titles` |
| `{{target_departments}}` | Derived from titles / product personas |
| `{{prospect_qualification_criteria}}` | `qualification_criteria` (contact-relevant subset) |
| `{{prospect_exclusion_rules}}` | `blacklist_criteria` + contact-level rules |
| `{{prioritization_rules}}` | `prioritization_rules` |
| `{{search_constraints}}` | `prospecting_strategy` + LinkedIn-first policy |

Full bundle: `get_sales_strategy_bundle` + `get_company` — see [Contact Finder plan](../../06-contact-finder.md).

## Output contract

**`register_contact`** — full payload; runtime links to active strategy + company. Align with [sales_strategy_form.md § Agent output (register_contact)](../../../../form/sales_strategy_form.md):

- Full `ProspectProfile`: full name, job title, department, seniority, LinkedIn URL, public email, public phone, location
- Global `CompanyProspect` link for this person at this company
- Strategy-specific `SalesStrategyProspect`: selection reason, fit/confidence/evidence (`is_blacklisted = false`)
- Unique strategy identity: `(sales_strategy_id, company_id, prospect_profile_id)`

**`blacklist_prospect`** — minimal payload. See [sales_strategy_form.md § Agent output (blacklist_prospect)](../../../../form/sales_strategy_form.md):

- Required: canonical LinkedIn URL, `blacklist_reason`
- Optional sparse name/title when creating a new global profile
- If not yet linked: sparse register + `is_blacklisted = true` in one step; does **not** count toward N

`SalesStrategyCompany.contacts_registered` counts prospects where `is_blacklisted = false` toward per-company **N**.

## Related plans

- [Company Finder prompt](../company-finder/README.md) — company identification (upstream)
- [Knowledge forms](../../../../form/README.md) — strategy and product field definitions
- [Contact Finder](../../06-contact-finder.md) — queue, frozen attempt, one-company-at-a-time
- [AI agent platform](../../01-platform.md) — prompt registry and injection
