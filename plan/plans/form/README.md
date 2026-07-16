# Knowledge Forms Plan

Canonical operator and agent form specifications for LOOP. These define **what data to collect**, **validation gates**, and **JSON payloads** stored on domain entities.

**Architecture model:** [knowledge-model.md](../knowledge/knowledge-model.md) — four knowledge areas.  
**Persistence and API:** form JSON blocks in each form spec; [database plan](../02-database.md#strategy-scoped-blacklist-junction-columns) for junction blacklist columns and shapes.

## Form index

| Order | Knowledge area | Form | Stored as | Gate |
|------:|----------------|------|-----------|------|
| 1 | Organization — *Who we are* | [organization_form.md](organization_form.md) | `OrganizationProfile.org_form` | Required before creating a Product/Service |
| 2 | Product/Service — *What we sell* | [service_form.md](service_form.md) | `ProductProfile.icp_form` | Required before creating a Sales Strategy |
| 3 | Sales Strategy — *Who to target now & how* | [sales_strategy_form.md](sales_strategy_form.md) | `SalesStrategy.sales_strategy_form` | Required at sales strategy create; **immutable after create** |
| 4 | Prospect — *Global identities + strategy selection* | [knowledge-model.md §4](../knowledge/knowledge-model.md#4-prospect-knowledge--global-identity--strategy-selection) | `Company`/`CompanyProfile`, `ProspectProfile`/`CompanyProspect`, `SalesStrategyCompany`/`SalesStrategyProspect` | Accumulated during discovery — not a fill-once wizard |

## Hierarchy

```text
Organization (organization_form.md)
  └── Product / Service (service_form.md)
        └── Sales Strategy (sales_strategy_form.md)
              └── SalesStrategyCompany / SalesStrategyProspect

Global registry (not owned by org/product):
Company ── optional CompanyProfile
Company ── CompanyProspect ── ProspectProfile
```

## Implementation ownership

| Workstream | Delivers |
|------------|----------|
| [Backend domains](../03-backend-domains.md) | Profile entities, validation use cases, `get_sales_strategy_bundle` |
| [API and contracts](../04-api-and-contracts.md) | OpenAPI schemas generated from these forms |
| [Frontend](../05-frontend.md) | Multi-step wizards + read-only Strategy tab |
| [Company Finder](../agent/AgentWithBrowser/05-company-finder.md) | Consumes org + product excerpts + full `sales_strategy_form` |
| [Contact Finder](../agent/AgentWithBrowser/06-contact-finder.md) | Consumes decision-maker + outreach sections from form |

## Stage 1 checklist (forms)

- [ ] Organization wizard — 21 sections, `org_form` v1+
- [ ] Product/Service wizard — 18 sections, `icp_form` v2.0
- [ ] Sales Strategy create wizard — 20 sections + run targets, `sales_strategy_form` v2.0
- [ ] Validation gates block downstream create until prior form passes
- [ ] Sales Strategy form read-only on Strategy tab after create (PATCH → 409)
- [ ] OpenAPI types regenerated; frontend Zod matches backend shapes exactly

## Versioning

| Form | Current schema version | Notes |
|------|------------------------|-------|
| Organization | per `organization_form.md` | Stable seller context |
| Product/Service | `icp_form` v2.0 | Seller name/website on org form |
| Sales Strategy | `sales_strategy_form` v2.0 | Legacy v1 campaign payloads migrate at read time |

When form schemas change, update this folder first, then [database](../02-database.md) / [backend](../03-backend-domains.md) / [API](../04-api-and-contracts.md) plans, then regenerate API contracts.
