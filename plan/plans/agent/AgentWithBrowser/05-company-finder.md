# Company Finder Plan

## Objectives and scope

Implement the sales-strategy-level Company Finder process that repeatedly attempts one company at a time, registers qualified companies until the sales strategy target is reached, exposes play/pause/status/logs/whiteboard, and preserves all linked or unlinked effort threads.

**Discovery prompt:** [prompts/company-finder/prompt.md](prompts/company-finder/prompt.md) — minimum sufficient context for company identification (see [README](prompts/company-finder/README.md)).

## Functional requirements

- Start/stop independently per sales strategy.
- Refuse start/register when `companies_registered >= target_companies`.
- One effort equals one company try.
- Research one candidate through a dedicated Browser sub-agent.
- `register_company` is available only to the Company Finder orchestrator.
- Deduplicate `Company` globally by website URL; create a new strategy link only when `(sales_strategy_id, company_id)` is absent.
- On successful registration: increment success counter, freeze `sales_strategy_attempt_at_register`, link orchestrator thread, emit event.
- On failure: retain unlinked AgentRun/thread for inspection.
- Persist Sales-strategy-scoped Brain learning and Company Finder whiteboard.

## Non-functional requirements

- Restart-safe, idempotent, and observable.
- Configurable 5–15 minute pacing with policy/rate limits.
- Never exceed sales strategy target under concurrent/retried work.
- Stop request takes effect immediately.
- Browser/session failures do not corrupt sales_strategy counters.

## Architecture and design decisions

- Background process owns the loop; each iteration creates a new effort sequence.
- Process state and AgentRun are persisted, not held only in memory.
- Quota is checked before research and transactionally inside registration.
- Browser gathers evidence; orchestrator decides and registers.
- Contact Finder may operate in parallel on already-validated companies.
- Operator remains responsible for mark-valid/blacklist.

## Data models

- `SalesStrategy`: target, registered count/read projection, `company_finder_attempt`.
- `AgentProcessState`: sales_strategy, role, desired/actual state, timestamps, last error.
- `AgentRun`: effort sequence/prefix, primary thread, status, usage.
- Global `Company`: name + globally unique normalized `domain`.
- `SalesStrategyCompany`: selection reason, funnel/quota state, frozen attempt, linked thread.
- Optional `CompanyProfile`: future enricher output; not written or required by Company Finder.
- Company Finder whiteboard/scratchpad and Brain memory.

## APIs and interfaces

- `POST /sales-strategies/{id}/agents/company-finder/start`
- `POST /sales-strategies/{id}/agents/company-finder/stop`
- `GET /sales-strategies/{id}/agents/company-finder/status`
- `GET /sales-strategies/{id}/agents/company-finder/whiteboard`
- Tools: `get_sales_strategy_bundle`, `register_company`, `set_scratch_pad`.
- Browser child interface and process-control queue command.

## Target directory structure

```text
loop/apps/agent-runtime/src/company_finder/
├── process.py
├── effort.py
├── policies.py
├── status.py
└── errors.py
loop/packages/ai/prompts/company_finder/
loop/packages/agent-tools/company/
```

## Milestones and implementation tasks

### M1 — Deterministic effort runner

- Implement state machine with fake browser/model.
- Add effort sequence, AgentRun lifecycle, quota checks, registration, and linking.

### M2 — Process control

- Implement start/stop/status, durable desired state, leases/locks, pacing, retry classes, and logs.
- Add whiteboard/Brain close step.

### M3 — Browser-backed discovery

- Build company Browser sub-agent and prompts.
- Enforce evidence and no-invented-URL rules.
- Add recovery and duplicate candidate handling.

### M4 — Operator integration

- Connect Process tab UI using themed **Control | Whiteboard** layout ([UI theme](../../15-ui-theme-and-design-system.md): play/pause amber primary, MetricTiles, log DataTable, markdown whiteboard).
- Connect Records Viewer refresh/events, Threads/snapshots, progress, alerts, and feature flag.

## Dependencies

- SalesStrategy, global Company, and SalesStrategyCompany domains/APIs.
- [AI agent platform](01-platform.md) and [Browser runtime](02-browser-runtime.md).
- [Deep-agent factory](04-deep-agent-factory.md) and [checkpoints/threads](03-checkpoints-and-threads.md).
- Events/workers for durable process execution.
- Observability, Threads viewer, and process frontend.

## Testing strategy

- Unit tests for process/effort states and quota policy.
- Concurrent quota and duplicate registration integration tests.
- Forced stop/restart at every checkpoint boundary.
- Browser failure, malformed evidence, model timeout, and 409 tests.
- Golden discovery scenarios against fake websites.
- Staging soak test with conservative approved pacing.

## Risks and open questions

- Reusing global Company is expected; increment strategy quota/counter only when a new `SalesStrategyCompany` link is created.
- Establish maximum consecutive failures before pause/alert.
- Define operator restart behavior after target is changed.
- Model quality and LinkedIn variability require measurable eval sets.
- Decide whether a running effort is cancelled immediately or finishes after stop. **Locked:** immediate abort (see backend plan).

## Acceptance criteria

- Process fills sales_strategy to target and stops without overshoot.
- Every effort appears in Threads; only a successful new strategy-company link counts and links the effort.
- Failed/restarted efforts do not increment success counters.
- Browser cannot register companies.
- Operator can play/pause and observe status, counts, logs, whiteboard, and snapshots.
- Parallel Contact Finder operation does not block or corrupt Company Finder.
