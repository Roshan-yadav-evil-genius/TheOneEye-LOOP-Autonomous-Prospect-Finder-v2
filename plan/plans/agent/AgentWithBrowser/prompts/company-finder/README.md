# Company Finder Prompt

> **Purpose:** Minimum sufficient context for the **Company Finder** agent to identify target **companies** — not people, not outreach, not product selling.

## What this file is

[`prompt.md`](prompt.md) is the canonical **Company Prospect Identification** prompt template for production LOOP. At runtime, placeholders (e.g. `{{sales_objective}}`, `{{buying_signals}}`) are filled from the active sales strategy’s [`sales_strategy_form.md`](../../../../form/sales_strategy_form.md) and compressed excerpts from organization/product forms when needed for fit checks — but the prompt itself stays focused on **company discovery only**.

## Intention

At the prospect discovery stage, the agent answers one question:

> **Does this company fit the sales strategy and deserve to enter the pipeline?**

This prompt deliberately includes only what supports that decision:

| Included | Why |
|----------|-----|
| Sales objective | Anchors what “good” looks like for this run |
| Target ICP (industry, size, geo, characteristics) | Firmographic fit |
| Qualification criteria | Must-have / nice-to-have for registration |
| Buying signals | Readiness indicators to prioritize |
| Exclusion rules | Hard skips |
| Priority rules | Rank when multiple candidates qualify |
| Search constraints | Source and quality guardrails |
| Expected output + instructions | Rich research result used to choose a company |

## What is intentionally excluded

The following belong in other layers — not in this discovery prompt:

| Excluded | Lives in |
|----------|----------|
| Organization history, mission, values | [organization_form.md](../../../../form/organization_form.md) |
| Product features, pricing, implementation | [service_form.md](../../../../form/service_form.md) |
| Case studies, competitive positioning, sales process | Org / product forms |
| Decision makers, outreach, messaging | Contact Finder + operator workflow |
| Technical architecture, internal team info | N/A at discovery |

Those details help during **qualification review, outreach, and selling**; they add little to **finding companies**.

## Runtime mapping

| Prompt placeholder | Typical source |
|--------------------|----------------|
| `{{sales_objective}}` | `sales_strategy_form.overview` + target narrative |
| `{{target_industries}}` | `priority_industries` |
| `{{company_size}}` | `company_size` |
| `{{target_regions}}` | `priority_geographies` |
| `{{business_characteristics}}` | `target_company_profile.characteristics`, `company_types` |
| `{{qualification_criteria}}` | `qualification_criteria` |
| `{{buying_signals}}` | `buying_signals` |
| `{{exclusion_rules}}` | `exclusion_rules` + `blacklist_criteria` |
| `{{priority_rules}}` | `prioritization_rules` |
| `{{search_constraints}}` | `prospecting_strategy` |

Full bundle assembly: `get_sales_strategy_bundle` — see [Company Finder plan](../../05-company-finder.md) and [§9.10](../../00-architecture.md#910-multi-agent-workflows).

## Research output vs registration contract

The prompt asks for rich research (industry, headquarters, size, revenue, signals, confidence) so the agent can make a good decision. That research is **not** the persistence shape.

Only these values enter `register_company`:

| Field | Storage |
|-------|---------|
| Company name | global `Company.name` |
| Website URL (input) | Normalized to global `Company.domain` |
| Selection reason | `SalesStrategyCompany.selection_reason` |

`register_company` get-or-creates the global company and creates the active strategy link. Optional firmographics are reserved for the future `CompanyProfile` enricher; technology and current vendors are not part of the planned profile.

## Related plans

- [Knowledge forms](../../../../form/README.md) — where strategy fields are defined
- [Company Finder](../../05-company-finder.md) — process, quota, registration authority
- [AI agent platform](../../01-platform.md) — prompt registry, injection, versioning
