# Backend Domains Plan

## Objectives and scope

Implement LOOP as a FastAPI-hosted modular monolith with strict domain, application, infrastructure, and HTTP boundaries. Cover Organization, Product, SalesStrategy, Discovery, Validation, Outreach, Analytics, Intelligence metadata, and Automation control.

**Form contracts:** [form/README.md](form/README.md) — organization, product/service, and sales strategy payloads.

## Functional requirements

- Create organizations with **[Organization Form](form/organization_form.md)** profile and product/service profiles.
- Validate organization profile before product creation; product profile before sales strategy creation.
- Create sales strategies with one immutable **Sales Strategy** form ([sales_strategy_form.md](form/sales_strategy_form.md) — v2.0) and quota settings.
- Register/deduplicate global companies and prospect profiles; create strategy-specific selection links.
- Enforce company/contact funnel transitions and quota rules.
- Support human validation, blacklist, and outreach updates.
- Expose progress, Records Viewer, Company detail, Threads, and process-state queries.
- Emit audit/domain/integration events from application use cases.

## Non-functional requirements

- HTTP controllers contain no business logic.
- Domain services are unit-testable without HTTP, DB, queues, or LLMs.
- Commands are idempotent where agents may retry.
- Read p95 under 300 ms and write p95 under 800 ms excluding AI.
- All errors use stable machine-readable codes and request IDs.

## Architecture and design decisions

- Bounded-context modules inside one deployable API.
- Command/query separation without a heavy framework.
- Domain entities enforce local invariants; application services coordinate repositories/events.
- Infrastructure implements ports defined by application/domain packages.
- Registration tools call the same use cases as REST endpoints.
- No source-channel allocation, hypothesis entity, maturity analytics, or autonomous validation.

## Data models

| Context | Aggregate/data |
|---------|----------------|
| Organization | `Organization`, `OrganizationProfile.org_form` |
| Product | `Product`, `ProductProfile.icp_form` |
| SalesStrategy | `SalesStrategy.sales_strategy_form` (v2.0 Sales Strategy), target counts, successful-attempt counters |
| Discovery | Global `Company`, optional `CompanyProfile`, `ProspectProfile`, `CompanyProspect`; strategy `SalesStrategyCompany`, `SalesStrategyProspect` ([knowledge-model.md](knowledge/knowledge-model.md)) |
| Validation | funnel transitions; blacklist via junction `is_blacklisted` + `blacklist_reason` |
| Outreach | `SalesStrategyProspect` outreach status + immutable `OutreachEvent` |
| Analytics | progress/funnel read models |
| Intelligence | `AgentRun`, process state, whiteboard/scratchpad references |

Critical policies:

- Strategy cannot be edited after submit (immutable `sales_strategy_form`).
- `register_company`: if global `domain` exists, reuse `Company`; always ensure `SalesStrategyCompany` link for active strategy unless already linked (**200** + message). Count toward `target_companies` only when a **new** strategy link is created and `is_blacklisted = false`. **409** only when `companies_registered >= target_companies`.
- `Company.domain` normalized registrable domain (e.g. `acme.com`); globally unique; **operator-only** edits to company fields.
- Mark-valid sets fixed `contacts_target` from `contacts_per_company_default`; blocked when default is **0**.
- `register_contact`: agent sends **full** ProspectProfile + selection/fit/evidence; runtime binds `sales_strategy_id` + `company_id` from the active Contact Finder effort; creates global + strategy links with `is_blacklisted = false`; counts toward N when successful.
- `blacklist_prospect` (agent): **minimal** input (`linkedin_url`, `blacklist_reason`; optional sparse identity fields). If prospect not yet linked in this strategy+company: register sparse global/strategy rows and set `is_blacklisted = true` in one transaction. If already linked: set `is_blacklisted = true` only. Does not count toward `contacts_registered`.
- `linkedin_url` validated as canonical LinkedIn **profile** URL (`/in/<id>`); dedup returns **200** if already registered.
- `contacts_registered` counts `SalesStrategyProspect` rows where `is_blacklisted = false` toward N.
- `companies_registered` counts `SalesStrategyCompany` rows where `is_blacklisted = false` toward `target_companies`.
- **Blacklist** sets `is_blacklisted = true` and required `blacklist_reason` on the junction row (company or prospect); Contact Finder skips blacklisted links.
- **Unblacklist** sets `is_blacklisted = false`, clears `blacklist_reason`; prior reasons retained in audit log (operator and agent tools).
- `CompanyProspect`: at most **one active** company association per `ProspectProfile` (replace on company change).
- Stop agent process: **abort immediately**.

## APIs and interfaces

Application commands/queries include:

- `CreateOrganization`, `UpdateOrganizationProfile`, `ValidateOrganizationProfile`
- `CreateProduct`, `UpdateProductProfile`, `ValidateProductProfile`
- `CreateSalesStrategy`, `GetSalesStrategyBundle`
- `RegisterCompany`, `ValidateCompany`, `BlacklistCompany`, `UnblacklistCompany`
- `RegisterContact`, `ValidateContact`, `BlacklistProspect`, `UnblacklistProspect`, `UpdateOutreach`
- `GetRecordsViewer`, `GetCompanyDetail`, `GetSalesStrategyProgress`
- `StartAgentProcess`, `StopAgentProcess`, `GetProcessStatus`, `GetSalesStrategyThreads`

Domain events remain private; integration events are translated into versioned public contracts.

## Target directory structure

```text
loop/apps/api/src/
├── organization/{domain,application,infrastructure,api}/
├── product/{domain,application,infrastructure,api}/
├── sales-strategy/{domain,application,infrastructure,api}/
├── discovery/{domain,application,infrastructure,api}/
├── validation/{domain,application,infrastructure,api}/
├── outreach/{domain,application,infrastructure,api}/
├── analytics/{application,infrastructure,api}/
├── intelligence/{application,infrastructure,api}/
└── automation/{application,infrastructure,api}/
```

## Milestones and implementation tasks

### M1 — Organization, Product, Sales Strategy

- Implement Organization + OrganizationProfile entities, org form schemas, org validation gate.
- Implement Product entities, product form schemas, profile gate, sales strategy creation, and bundle query.
- Add immutable strategy policy and stable error codes.

### M2 — Company discovery

- Implement globally unique `domain` Company upsert plus strategy-company selection transaction.
- Persist name + normalized `domain` globally and `selection_reason` on `SalesStrategyCompany`; keep enrichment out of registration.
- Implement quota transaction, dedup response, mark-valid/blacklist/unblacklist on junction columns (fixed N at mark-valid).
- Build Records Viewer and company-detail read models.

### M3 — Contact discovery and outreach

- Implement full ProspectProfile registration (name, role, department, seniority, LinkedIn, public contact fields, location).
- Upsert global `CompanyProspect`, create unique `SalesStrategyProspect`, enforce validated-company gate/dedup/blacklist/counters, and store outreach history.

### M4 — Progress and process metadata

- Implement progress queries/projections, AgentRun/process state, Threads query, and whiteboard retrieval.
- Add reconciliation and export use cases.

## Dependencies

- Foundation and Database.
- API plan maps these use cases to HTTP/OpenAPI.
- Agent tools consume registration and query use cases.
- Events/workers publish resulting integration events.

## Testing strategy

- Domain unit tests for every state transition and invariant.
- Application tests with in-memory/fake ports.
- PostgreSQL integration tests for concurrent quotas and dedup.
- Property tests for URL/domain normalization and transition matrices.
- Audit/outbox assertions for every mutating use case.
- Regression tests for removed POC semantics.

## Risks and open questions

- Define exact contact funnel stage names versus outreach field statuses before coding.
- Decide whether manual company registration counts as a successful agent attempt (recommended: no agent counter).
- Determine editability of non-strategy SalesStrategy metadata such as name/status.
- Define export fields and retention/redaction rules.

## Acceptance criteria

- Manual vertical slice works without agents.
- Invalid transitions and quota violations fail with deterministic errors.
- Concurrent retries never duplicate global identities or strategy links and never exceed targets.
- Every mutation produces audit data and the required outbox event.
- Domain/application tests run without FastAPI.
- No route handler directly accesses SQLAlchemy models.
