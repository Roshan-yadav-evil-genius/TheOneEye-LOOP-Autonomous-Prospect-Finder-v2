# Events and Background Workers Plan

## Objectives and scope

Implement reliable asynchronous processing through a transactional outbox, versioned integration events, queue adapters, generic consumers, scheduler, agent process control, retries, dead-letter queues, and projection workers.

## Functional requirements

- Persist integration events in the same transaction as business changes.
- Publish unpublished outbox rows and safely retry.
- Consume global company/prospect, strategy-selection, outreach, and agent events idempotently.
- Run Company Finder and Contact Finder as independently controlled processes.
- Schedule recurring tasks with overlap policy (`skip` or `queue`) and run-now.
- Expose process execution history, logs, retry, replay, and DLQ administration.
- Rebuild/reconcile progress projections.

## Non-functional requirements

- At-least-once delivery with idempotent consumers.
- No lost events after acknowledged business writes.
- Bounded retries, exponential backoff, visibility timeout, and poison-message isolation.
- Trace/correlation context propagated end-to-end.
- Agent work never blocks HTTP request threads.

## Architecture and design decisions

- PostgreSQL transactional outbox is authoritative.
- Redis Streams initially; queue port permits SQS/Kafka later.
- Domain events stay internal; only versioned integration events cross contexts.
- Company Finder → Contact Finder is not an auto-chained saga; operators control each process.
- Start with durable worker loops; Temporal migration is until complexity justifies it.
- Scheduler stores definitions and run history in PostgreSQL.

## Data models

- `IntegrationEvent`: ID, type/version, occurred/published timestamps, producer, correlation ID, payload, attempts.
- `ConsumerCheckpoint/Inbox`: consumer, event ID, status, processed timestamp.
- `ScheduledTask`: key, schedule, enabled, overlap policy, payload.
- `JobRun`: task/process, status, attempts, timing, error, trace ID.
- `DeadLetter`: queue, payload reference, reason, attempts, replay state.
- `AgentProcessState`: role/sales_strategy desired and actual state, lease/heartbeat.

## APIs and interfaces

- `OutboxPublisher.publish_batch()`
- `Queue.enqueue/dequeue/ack/nack`
- `EventConsumer.handle(event)`
- Scheduler `tick`, `run_now`, enable/disable.
- `GET/PATCH /api/v1/processes/{key}`
- Agent start/stop/status endpoints.
- Admin DLQ list/replay/discard interfaces.

## Target directory structure

```text
loop/packages/events/
loop/packages/queue/
loop/apps/worker/src/
├── outbox/
├── consumers/
├── projections/
└── dlq/
loop/apps/scheduler/src/
├── schedules/
├── leases/
└── runs/
```

## Milestones and implementation tasks

### M1 — Outbox and contracts

- Implement event envelope/catalog, outbox append/publisher, queue port, and Redis adapter.
- Add inbox/idempotency records.

### M2 — Consumers and projections

- Implement audit, metrics/progress, UI-refresh/SSE hooks, and agent-run usage consumers.
- Add reconciliation commands.

### M3 — Scheduler and process control

- Implement task definitions, overlap policy, run-now, durable agent desired state, worker lease, and execution history.

### M4 — Failure operations

- Implement retry taxonomy, DLQs, replay/discard API/UI, alerts, backpressure, and graceful shutdown/recovery.

## Dependencies

- Database outbox/process schema.
- Backend domain events and contracts.
- Agent runtimes for process workers.
- Observability and Infrastructure Redis.

## Testing strategy

- Atomicity test: rollback business transaction means no event.
- Duplicate delivery and consumer-crash-before-ack tests.
- Queue visibility timeout, backoff, poison message, and DLQ replay tests.
- Scheduler overlap, lease expiry, clock boundary, and restart tests.
- Projection reconciliation against OLTP.
- End-to-end trace propagation assertions.

## Risks and open questions

- Keep global identity events (`CompanyRegistered`, `ProspectRegistered`) distinct from strategy selection events so projections do not double-count reused records.
- Select Redis Streams consumer-group conventions and retention.
- Define process heartbeat/lease intervals separately from agent effort counters.
- Determine DLQ payload privacy/redaction.
- Temporal adoption criteria need an ADR.

## Acceptance criteria

- Outbox events survive publisher/queue outages and publish once recovery occurs.
- Every consumer is idempotent under duplicate delivery.
- Company and Contact Finder can run, stop, restart, and recover leases independently; projections distinguish global identity creation from strategy selection.
- Operators can inspect execution history and replay/discard DLQ items.
- Progress projections reconcile with source tables.
- HTTP requests never execute long-running agent work inline.
