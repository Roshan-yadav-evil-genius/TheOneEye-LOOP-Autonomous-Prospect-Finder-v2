# AI Agent Platform Plan

## Objectives and scope

Build the reusable intelligence platform shared by Company Finder and Contact Finder: model routing, tool adapters, prompt registry, Sales-strategy-scoped Brain memory, scratchpads/whiteboards, deep-agent factory, nested checkpointing, effort/thread allocation, and run accounting.

## Functional requirements

- Create all deep agents through `create_loop_deep_agent`.
- Expose role-specific tools backed by application use cases.
- Ensure registration authority stays on orchestrators; Browser never gets `register_*`.
- Persist parent and compiled-child checkpoints and resume interrupted work.
- Allocate GPA threads as `{parent_role_thread}_GPA_n`.
- Track every effort in `AgentRun`, linked or unlinked.
- Recall Brain memory only within the current sales_strategy.
- Render one process whiteboard from active effort scratchpad/sections.
- Attribute tokens, models, costs, tools, errors, and child thread IDs.

## Non-functional requirements

- Idempotent tool calls and deterministic context binding.
- No cross-sales-strategy memory leakage.
- Resume must not duplicate registration or allocate a new child for pending work.
- Summarize/compact before model context exhaustion.
- Prompt and model versions must be observable and reproducible.

## Architecture and design decisions

- Factory receives name, responsibility, tools, middleware, subagents, store, checkpointer, effort prefix, role suffix, and model.
- Browser, Brain, and GPA are separately checkpointed compiled children.
- Parent saves active child thread ID before invocation.
- Scratchpad key is `sales_strategy_id + effort_prefix`; process whiteboard selects active/latest effort.
- Effort sequence increments at start; successful registration counters increment only after register succeeds.
- Contact prefixes use company-frozen `sales_strategy_attempt_at_register`.

## Data models

- `AgentRun`: sales strategy/company/sales-strategy-prospect IDs, role, effort prefix, primary thread ID, effort counters, status, timing, usage/cost.
- Parent checkpoint `active_subagent_threads`: role/tool-call key, child thread ID, status.
- Brain memory: category (`actions`, `failures`, `decisions`, `insights`), sales_strategy scope, content, embedding, evidence.
- Scratchpad/whiteboard: sales_strategy, process role, effort prefix, sections/content, updated timestamp.
- Tool result envelope: status, global entity IDs, strategy-link IDs, created/dedup flags, error code.

## APIs and interfaces

- `create_loop_deep_agent(config)`
- `build_company_finder_stack(...)`, `build_contact_finder_stack(...)`
- `build_role_thread_id`, `allocate_gpa_thread_id`
- `resolve_compiled_child_thread_id`, `invoke_compiled_child_until_idle`
- `get_sales_strategy_bundle`, `get_company`, `is_profile_present`
- `register_company` (Company Finder only), `register_contact` (Contact Finder only)
- `blacklist_company`, `blacklist_prospect`, `set_scratch_pad`
- Threads, snapshots, process whiteboard/status APIs.

Registration contracts:

- `register_company(name, website_url, selection_reason)` → global `company_id` + `sales_strategy_company_id` (strategy from active Company Finder effort).
- `register_contact(full ProspectProfile fields, selection_reason, fit/confidence/evidence)` → runtime supplies `sales_strategy_id` + `company_id` from active Contact Finder effort → `prospect_profile_id` + `company_prospect` + `sales_strategy_prospect_id` (`is_blacklisted = false`).
- `blacklist_prospect(linkedin_url, blacklist_reason, optional sparse name/title)` → runtime supplies strategy + company → if not linked: sparse register + `is_blacklisted = true`; else set flag only.

## Target directory structure

```text
loop/packages/ai/
├── loop_agent_factory.py
├── nested_checkpointing.py
├── subagent_runner.py
├── model_router.py
├── usage.py
└── prompts/
loop/packages/agent-tools/
loop/packages/agent-memory/
loop/apps/agent-runtime/
```

## Milestones and implementation tasks

### M1 — Tools and model foundation

- Implement typed tool context, adapters, errors, model routing, usage accounting, and prompt registry.
- Add registration-authority tests.

### M2 — Memory and whiteboard

- Implement Sales-strategy-scoped Brain storage/search and scratchpad/whiteboard retrieval.
- Add compaction and evidence-retention policies.

### M3 — Factory and checkpoints

- Implement factory, role-specific middleware/subagents, parent-child checkpoint state, GPA max+1 allocation, and resume-until-idle.

### M4 — AgentRun and operational surfaces

- Persist effort lifecycle, usage, links, status, and child delegations.
- Implement Threads/snapshot/process-status integration.
- Add synthetic end-to-end agent harness.

## Dependencies

- Sales Strategy bundle and registration use cases/API.
- PostgreSQL `agent_brain`, AgentRun, object storage.
- Browser runtime for real browsing; fake browser for early tests.
- Observability for traces/costs.

## Testing strategy

- Unit tests for tool permissions, prompt assembly, counters, thread naming, and memory scoping.
- Checkpoint acceptance matrix: fresh child, completed child, interrupted child, pending tool call, multiple children, concurrent GPA allocation.
- Replay/idempotency tests across process restart.
- Golden prompt/tool-schema tests.
- Context compaction and token-budget regression tests.
- Injection tests treating browser content as untrusted.

## Risks and open questions

- Pin compatible LangGraph/deep-agent/checkpointer versions.
- Decide model/provider routing and fallback policy.
- Resolve whiteboard section persistence versus single merged markdown.
- Define memory retention and human correction/deletion.
- Concurrency control for GPA allocation and effort sequences must be database-backed.

## Acceptance criteria

- Synthetic parent/Browser/Brain/GPA graph resumes correctly after forced interruption.
- Browser cannot call registration tools.
- Memory retrieval cannot return another sales strategy's data.
- Linked and unlinked efforts appear correctly in Threads.
- Every sub-agent delegation has a navigable child thread ID.
- Cost/token attribution reconciles with provider usage.

## Related

- [00-architecture.md](00-architecture.md) — topology and workflows
- [03-checkpoints-and-threads.md](03-checkpoints-and-threads.md) — nested checkpoints / GPA
- [04-deep-agent-factory.md](04-deep-agent-factory.md) — `create_loop_deep_agent`
- [02-browser-runtime.md](02-browser-runtime.md) — browser pool consumed by factory stacks
- [prompts/](prompts/README.md) — discovery prompt templates
