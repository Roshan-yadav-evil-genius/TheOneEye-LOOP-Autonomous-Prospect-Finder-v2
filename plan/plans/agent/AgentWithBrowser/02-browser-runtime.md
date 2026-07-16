# Browser Runtime Plan

## Objectives and scope

Provide a production browser-pool service for LinkedIn/company research through Playwright MCP. Isolate sessions, compact snapshots, recover dead browsers, enforce navigation/rate guardrails, and expose a stable browser sub-agent interface.

## Functional requirements

- Acquire/release browser sessions for agent efforts.
- Connect to validated LinkedIn Chrome profiles through CDP/MCP.
- Navigate, inspect, click, type, and extract evidence.
- Compact repetitive browser snapshots before agent context storage.
- Detect session death and rebuild/reconnect within the recovery target.
- Store evidence references and sanitized artifacts.
- Support distinct company-research and contact-research tool sets.

## Non-functional requirements

- Browser session recovery under 30 seconds.
- Target 95% task completion under injected session death.
- No cookies/tokens in logs, checkpoints, or artifacts.
- Configurable per-account and per-domain rate limits.
- Browser content is untrusted and cannot override system/tool policies.
- Sessions are isolated and disposable.

## Architecture and design decisions

- Separate `browser-pool` runtime from agent orchestration.
- Playwright MCP gateway is the browser contract.
- Browser sub-agent receives navigation/presence tools, never registration tools.
- Snapshot compaction is middleware with fixture-based regression tests.
- Object storage keeps artifacts; checkpoints keep references and compact state.
- Start with one validated LinkedIn profile; design lease API for multiple profiles later.

## Data models

- `BrowserSession`: ID, profile ID, state, lease owner, timestamps, health.
- `BrowserTask`: effort/thread ID, task type, allowed domains, timeout.
- `BrowserEvidence`: URL, title, snapshot/artifact reference, captured timestamp.
- `BrowserFailure`: category, retryable flag, recovery action, sanitized details.

## APIs and interfaces

- `acquire_session(effort_id, task_type)`
- `execute_browser_task(session_id, instructions, policy)`
- `health_check(session_id)`
- `release_session(session_id)`
- MCP tools for browser interaction.
- Metrics/events for leases, recovery, throttling, navigation failures, and snapshot size.

## Target directory structure

```text
loop/apps/browser-pool/
├── src/
│   ├── leases/
│   ├── sessions/
│   ├── mcp_gateway/
│   ├── policies/
│   ├── recovery/
│   └── telemetry/
├── tests/
└── Dockerfile
loop/packages/ai/browser/
├── snapshot_compaction.py
└── evidence.py
```

## Milestones and implementation tasks

### M1 — Gateway and local session

- Package the POC Chrome/CDP/MCP workflow behind a health-checked service.
- Define task, lease, evidence, and sanitized error contracts.

### M2 — Isolation and policy

- Add exclusive leases, timeouts, domain allowlists, action throttles, and safe teardown.
- Implement company/contact browser profiles.

### M3 — Compaction and evidence

- Port snapshot compaction with real fixtures.
- Store sanitized evidence artifacts and references.
- Add maximum payload/context budgets.

### M4 — Recovery and scale

- Add dead-session detection, restart/reconnect, lease recovery, and load shedding.
- Exercise multiple workers and future multiple-profile routing.

## Dependencies

- Foundation runtime/configuration.
- Infrastructure for browser-capable nodes and encrypted profile volume.
- AI platform consumes the browser interface.
- Observability and object storage.

## Testing strategy

- Unit fixtures for compaction and secret redaction.
- Fake-site integration tests for navigation, forms, dialogs, and rate limits.
- Session-death chaos tests and lease-expiration tests.
- Prompt-injection fixtures.
- Limited manual/staging LinkedIn validation under approved account policy.
- Performance tests for snapshot size and concurrent leases.

## Risks and open questions

- LinkedIn UI/account restrictions are external reliability risks.
- Define legal/policy limits and account-safe request rates.
- Determine encrypted profile provisioning and rotation procedure.
- MCP version changes may alter snapshot shape.
- Decide browser-node sandboxing and outbound network policy.

## Acceptance criteria

- Agent can complete representative company/contact research through the gateway.
- Forced browser death recovers within target without duplicate lease ownership.
- Compaction preserves actionable elements and materially reduces payload.
- No registration tool is present in browser configuration.
- Secret scanning finds no session material in logs/artifacts.
- Rate-limit and allowed-domain policies are enforced.
