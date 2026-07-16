# Observability and Operations Plan

## Objectives and scope

Make operator requests, domain transitions, background jobs, browser sessions, model calls, agent efforts, child threads, and costs traceable through structured logs, metrics, traces, audit records, dashboards, alerts, and runbooks.

## Functional requirements

- Correlate UI request → API use case → outbox → worker → agent → browser/model.
- Record immutable audit events for registrations and funnel/outreach transitions.
- Track AgentRun model/token/cost/tool/browser usage.
- Expose process logs and statuses to sales strategy Process tabs.
- Dashboard API health, queues, projections, browser health, agent success, quotas, and cost.
- Alert on SLO burn, DLQ depth, stale processes, quota conflicts, browser failure, and abnormal spend.

## Non-functional requirements

- Structured JSON logs in production.
- W3C trace context propagated across HTTP, queue, agent, model, and browser boundaries.
- Logs exclude secrets, cookies, raw tokens, and unnecessary PII.
- Business metrics use bounded-cardinality labels.
- Telemetry failure must not fail business transactions.

## Architecture and design decisions

- OpenTelemetry instrumentation with vendor-neutral exporters.
- Prometheus-style metrics and centralized log/trace backend.
- Audit history is domain data in PostgreSQL, not inferred from logs.
- `AgentRun` is the unit for usage/cost attribution.
- Thread snapshot viewer is operational inspection, not a replacement for traces/logs.
- Sampling keeps errors and agent efforts while reducing routine health traffic.

## Data models

- `AuditEvent`: actor, action, entity, before/after summary, reason, timestamp, request/trace IDs.
- `AgentRun`: timing, status, prompt/completion tokens, model, estimated cost, tool/snapshot counts.
- `ProcessLogEntry`: process/run, level, event code, safe message, timestamp, trace ID.
- SLO definitions and alert metadata.

## APIs and interfaces

- `get_logger()` with contextual fields.
- `tracer` and span helpers for use cases, tools, models, browser tasks.
- Metrics such as registered totals, API latency, queue age, effort duration/outcome, token/cost totals, browser recovery.
- Audit query/export interface.
- Process status/log APIs.

## Target directory structure

```text
loop/packages/logging/
loop/packages/telemetry/
loop/apps/api/src/audit/
loop/deployment/observability/
├── dashboards/
├── alerts/
└── collectors/
loop/docs/runbooks/
```

## Milestones and implementation tasks

### M1 — Telemetry baseline

- Add request IDs, JSON logging, trace propagation, API/DB/HTTP spans, build metadata, and redaction.

### M2 — Domain and asynchronous visibility

- Add audit events, outbox/queue spans, process logs, projection lag, and DLQ metrics.

### M3 — Agent/browser visibility

- Add AgentRun usage/cost, tool and child-thread spans, browser lease/recovery/snapshot metrics, and prompt/model version tags.

### M4 — SLOs and operations

- Build dashboards, alerts, on-call runbooks, synthetic checks, cost budgets, and telemetry retention.

## Dependencies

- Foundation hooks first; every component integrates incrementally.
- Database for audit/AgentRun/process logs.
- Infrastructure for collectors and telemetry backends.

## Testing strategy

- Assert trace context through API→outbox→worker paths.
- Redaction tests with synthetic cookies/tokens/PII.
- Metric cardinality and expected-label tests.
- Audit completeness tests for each mutation.
- Alert rule tests and runbook game days.
- Cost reconciliation against provider statements.

## Risks and open questions

- Choose telemetry backend and retention based on budget.
- Decide whether detailed agent messages are logs, snapshots, or artifacts.
- High-cardinality sales_strategy/thread IDs should stay in traces/logs, not metrics.
- Define operator access to audit and snapshots before auth.
- Set cost thresholds after baseline measurements.

## Acceptance criteria

- A registration can be traced end-to-end from operator/process trigger to entity/event.
- Every required mutation has an audit record.
- Process pages show safe, useful logs and current state.
- Alerts fire in simulated queue, browser, API, and cost incidents.
- Secret/PII redaction tests pass.
- Runbooks identify owner, diagnosis, mitigation, and recovery verification.
