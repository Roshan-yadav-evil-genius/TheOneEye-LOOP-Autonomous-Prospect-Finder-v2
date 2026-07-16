# recreationDocs — LOOP production specification

Canonical documentation for the **greenfield LOOP** product. Implementation sequencing and subsystem work plans live in [`plans/README.md`](plans/README.md).

UI theme: [plans/15-ui-theme-and-design-system.md](plans/15-ui-theme-and-design-system.md).

## Documents

| File | Purpose |
|------|---------|
| [plans/README.md](plans/README.md) | **Single source of truth** — roadmap, planning principles, component index |
| [plans/knowledge/knowledge-model.md](plans/knowledge/knowledge-model.md) | **Four knowledge areas** — Organization, Product, Sales Strategy, Prospect |
| [plans/knowledge/README.md](plans/knowledge/README.md) | Knowledge model plan index |
| [plans/form/README.md](plans/form/README.md) | **Knowledge forms plan** — gates, schemas, implementation checklist |
| [plans/form/organization_form.md](plans/form/organization_form.md) | Organization form → `OrganizationProfile.org_form` |
| [plans/form/service_form.md](plans/form/service_form.md) | Product/Service form → `ProductProfile.icp_form` |
| [plans/form/sales_strategy_form.md](plans/form/sales_strategy_form.md) | Sales Strategy form → `SalesStrategy.sales_strategy_form` |

## Key production topics

- **Four knowledge areas** — [knowledge-model.md](plans/knowledge/knowledge-model.md#four-knowledge-areas)
- **Core model** — Organization → Product/Service → Sales Strategy; global Company/Prospect registries linked through `SalesStrategyCompany` / `SalesStrategyProspect` ([database plan](plans/02-database.md#data-models))
- **Sales Strategy workspace** — Strategy / Records Viewer / Company Finder Process / Contact Finder Process / Threads + Company detail ([frontend plan](plans/05-frontend.md))
- **Agent runtime** — effort threads, `create_loop_deep_agent`, registration authority, browser tool matrix ([AgentWithBrowser](plans/agent/AgentWithBrowser/README.md))
- **Operator workflow** — Mark valid / blacklist on Records Viewer; outreach on Company detail; whiteboard per process tab ([database plan](plans/02-database.md#operator-workflow-company--contact))
- **Form persistence** — global `Company`/`ProspectProfile`; strategy links with `is_blacklisted` on junction rows; sales strategy **immutable after create** ([database plan](plans/02-database.md#strategy-scoped-blacklist-junction-columns))
- **API** — threads, whiteboard, process status, outreach endpoints ([API plan](plans/04-api-and-contracts.md))
- **Operator model** — single trusted operator, multi-org URL routes, no authentication ([infra plan](plans/14-infrastructure-deployment.md#operational-security))

## Implementation plans (`plans/`)

- [Master roadmap](plans/README.md)
- [Knowledge model plan](plans/knowledge/README.md)
- [Knowledge forms plan](plans/form/README.md)
- [AgentWithBrowser plans](plans/agent/AgentWithBrowser/README.md)
- [UI theme and design system](plans/15-ui-theme-and-design-system.md)
