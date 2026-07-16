# API and Contracts Plan

## Objectives and scope

Define and implement the versioned REST/OpenAPI interface used by the React application, agent tools, administrative viewers, and future SDKs. Keep transport mapping separate from business use cases.

## Functional requirements

- Publish OpenAPI 3.1 at `/api/v1/openapi.json`.
- Cover organizations, products/profiles, sales-strategies/strategy/bundle, companies, contacts, outreach, progress, process control, threads, and snapshots.
- Support cursor pagination, filtering, idempotency, and consistent errors.
- Generate strict frontend TypeScript types and optional SDK clients.
- Polling for process/thread status; snapshot viewer embedded in operator web Threads tab.

## Non-functional requirements

- Backward-compatible additive changes inside v1.
- Request/response validation at the boundary.
- Request IDs and trace context on every call.
- Resource scoping by organization/product/sales_strategy via URL path context.
- Documented rate and payload limits.

## Architecture and design decisions

- Resource-oriented REST; commands use POST, partial updates use PATCH.
- API schemas map backend structures directly; frontend must not invent parallel shapes.
- Agent-facing tools invoke application commands directly or through generated API clients, never SQL.
- Stable error envelope with HTTP 409 for quota/state conflicts.
- OpenAPI diff is a required CI gate.

## Data models

Transport DTO groups:

- `OrganizationCreate/Read`, `OrganizationProfileRead/Update/ValidationResult`
- `ProductCreate/Read`, `ProductProfileRead/Update/ValidationResult`
- `SalesStrategyCreate/Read`, `SalesStrategyFormRead`, `SalesStrategyBundle`
- `CompanyRead`, `CompanyProfileRead`, `RegisterCompanyRequest/Result`
- `SalesStrategyCompanyRead/Summary`, `CompanyDetail`, `ContactQuota`
- `ProspectProfileCreate/Read`, `SalesStrategyProspectRead`, `RegisterContactRequest/Result`, `OutreachUpdate`
- `ProcessStatus`, `ProcessLogEntry`, `WhiteboardRead`
- `AgentRunSummary`, `ThreadSnapshot`, `ProgressRead`
- `ApiError`, cursor `Page[T]`

## APIs and interfaces

Primary endpoint groups:

```text
/api/v1/organizations/{id}/profile
/api/v1/organizations/{id}/products
/api/v1/products/{id}/sales-strategies
/api/v1/sales-strategies/{id}/strategy
/api/v1/sales-strategies/{id}/bundle
/api/v1/sales-strategies/{id}/companies
/api/v1/sales-strategies/{id}/companies/{companyId}/validate
/api/v1/sales-strategies/{id}/companies/{companyId}/blacklist
/api/v1/sales-strategies/{id}/companies/{companyId}/unblacklist
/api/v1/companies/{id}                          # global company + optional profile (operator edit)
/api/v1/sales-strategies/{id}/companies/{companyId}/prospects
/api/v1/sales-strategies/{id}/companies/{companyId}/prospects/{prospectProfileId}/validate|outreach|blacklist|unblacklist
/api/v1/sales-strategies/{id}/progress
/api/v1/sales-strategies/{id}/threads
/api/v1/sales-strategies/{id}/agents/{role}/start|stop|status|whiteboard
/api/v1/sales-strategies/{id}/snapshots/threads
/api/v1/sales-strategies/{id}/snapshots/{thread_id}
```

## Target directory structure

```text
loop/apps/api/src/http/
├── dependencies/
├── middleware/
├── errors/
├── routers/
├── schemas/
└── openapi/
loop/packages/contracts/
├── events/
├── api/
└── generated/
loop/packages/shared-types/
└── src/generated/
```

## Milestones and implementation tasks

### M1 — API conventions

- Implement middleware, error mapping, request IDs, pagination primitives, schema/version conventions.
- Add OpenAPI generation and breaking-change CI checks.

### M2 — Core domain endpoints

- Ship organization/product/sales_strategy APIs, global registry APIs, then strategy-company/prospect registration, validation, and outreach APIs.
- Add idempotency keys or natural-key retry semantics for registrations.
- `RegisterCompanyRequest = {name, website_url, selection_reason}` — `website_url` normalized to `Company.domain` at boundary; **200** with message (`registered` | `already_in_db` | `already_in_strategy`); **409** only when `companies_registered` (where `is_blacklisted = false`) `>= target_companies`.
- `RegisterContactRequest` includes full ProspectProfile fields plus selection reason, fit/confidence/evidence; `sales_strategy_id` + `company_id` from request context (active strategy effort).
- `BlacklistProspectRequest` (agent/operator): `linkedin_url`, `blacklist_reason`; optional sparse `full_name` / `job_title`. `sales_strategy_id` + `company_id` from path/context. Upsert sparse registration when not yet linked, then set `is_blacklisted = true`.

### M3 — Operations endpoints

- Add progress, process status/control, whiteboards, threads, and snapshot endpoints.
- 
### M4 — Generated consumers

- Generate TypeScript types and Axios endpoint modules.
- Add optional Python SDK for agent/runtime separation.
- Publish contract changelog and examples.

## Dependencies

- Backend commands/queries and Database repositories.
- Frontend, agent tools, workers, and snapshot viewer depend on these contracts.
- Authentication is not in scope for LOOP v1.

## Testing strategy

- OpenAPI snapshot and breaking-change tests.
- Route-to-use-case mapping tests with dependency overrides.
- Schema validation, error-envelope, pagination, filter, and 409 tests.
- Consumer contract tests for frontend and agent clients.
- SSE disconnect/reconnect and cancellation tests.

## Risks and open questions

- Decide whether registration tools use in-process commands or HTTP in the first deployable.
- Define process log pagination and retention.
- Snapshot payload size may require signed object URLs or pagination.
- Whiteboard: operator `PATCH` allowed (agent + operator co-edit).
- Resolve legacy `connection-sent` alias deprecation timing.

## Acceptance criteria

- Every planned operator/agent action has a documented endpoint or application interface.
- Generated TypeScript compiles without handwritten duplicate domain types.
- OpenAPI CI detects breaking changes.
- Errors and conflicts are consistent across all routers.
- Agent registration retries are demonstrably idempotent.
- Route handlers contain transport mapping only.
