# Testing and Quality Plan

## Objectives and scope

Create the test infrastructure, quality gates, fixtures, evaluation datasets, and release evidence needed for backend, frontend, data, agents, browser runtime, workers, security, performance, and recovery.

## Functional requirements

- Unit, integration, contract, component, E2E, load, security, chaos, and AI evaluation suites.
- Production-like PostgreSQL/Redis/object-storage test environments.
- Deterministic test factories for the full domain hierarchy.
- Fake model/browser/tool implementations for fast agent tests.
- OpenAPI-generated frontend mocks and contract fixtures.
- CI reports, flaky-test handling, coverage, and release gate summaries.

## Non-functional requirements

- Fast unit suite on every commit; bounded full-pipeline duration.
- Domain logic target coverage of at least 90%.
- Tests isolated, repeatable, parallel-safe, and free of real secrets.
- Real LinkedIn tests are limited, approved, and excluded from normal CI.
- Failure artifacts are useful but sanitized.

## Architecture and design decisions

- Test pyramid: domain unit tests dominate; integration tests use real infrastructure; few high-value E2E flows.
- Testcontainers PostgreSQL rather than SQLite.
- OpenAPI contract tests prevent backend/frontend drift.
- Agent evaluation separates deterministic orchestration correctness from probabilistic output quality.
- Chaos/recovery tests are required for browser, queues, checkpoints, and backups.
- Acceptance criteria in every component plan map to executable test evidence.

## Data models

Testing owns no production entities. It defines:

- Scenario builders for SalesStrategy → global Company → SalesStrategyCompany → ProspectProfile → CompanyProspect → SalesStrategyProspect.
- Golden cases for global domain/LinkedIn normalization, junction deduplication, strategy forms, and agent decisions.
- `EvalCase`, expected constraints, grader result, model/prompt version.
- Load profiles and recovery experiment records.

## APIs and interfaces

- Shared `packages/testing` factories/fixtures.
- Fake repository, queue, model, browser, checkpointer, clock, and ID generator ports.
- Contract fixture generator from OpenAPI.
- `pytest` markers and frontend test projects.
- Eval/benchmark CLI with reproducible seeds and version output.

## Target directory structure

```text
loop/packages/testing/
loop/tests/
├── integration/
├── contract/
├── e2e/
├── performance/
├── security/
├── chaos/
└── evals/
loop/apps/web/src/**/*.test.tsx
loop/apps/*/tests/
```

## Milestones and implementation tasks

### M1 — Quality baseline

- Configure lint/type/format/coverage, shared fixtures, Testcontainers, CI sharding, and deterministic clocks/IDs.

### M2 — Manual vertical slice tests

- Cover forms, domain transitions, migrations, REST contracts, frontend components, and operator E2E.

### M3 — Asynchronous and agent tests

- Add outbox/queue failure tests, nested checkpoint acceptance matrix, tool authority, memory isolation, thread linking, and process restart.

### M4 — Production readiness

- Add browser chaos, load/SLO, backup restore, security scans/tests, accessibility, cost/token regression, soak and rollback tests.

## Dependencies

- Begins with Foundation and evolves alongside all components.
- Requires canonical OpenAPI, database migrations, and testable ports.
- Infrastructure supplies ephemeral CI services.

## Testing strategy

Required suites:

- **Domain:** transitions, quotas, dedup, forms, value objects.
- **Persistence:** migrations, transactions, indexes, concurrency.
- **API/contracts:** schemas, errors, pagination, idempotency.
- **Frontend:** stores, components, accessibility, E2E, visual regression on [UI theme](15-ui-theme-and-design-system.md) screens.
- **Agents:** permissions, prompts, counters, nested resume, memory scope, eval quality.
- **Browser:** compaction, recovery, injection, rate limits.
- **Workers:** duplicate delivery, retries, DLQ, scheduler overlap.
- **Security:** network isolation, secrets, PII redaction, dependency/image scans (no application auth in v1).
- **Performance/recovery:** API load, queue lag, browser soak, PITR.

## Risks and open questions

- Probabilistic eval thresholds require baseline collection.
- Real browser UI changes can make tests brittle; fake sites should cover mechanics.
- Define quarantine policy and maximum flaky-test age.
- Determine coverage exclusions for generated code.
- Production-like agent tests may incur cost; enforce budgets.

## Acceptance criteria

- CI runs appropriate quality gates for every changed component.
- Critical domain and checkpoint behaviors have deterministic tests.
- Manual and automated vertical slices pass E2E.
- Contract drift fails CI before merge.
- Browser/worker/database recovery exercises meet targets.
- Release evidence includes test, scan, migration, load, and rollback results.
