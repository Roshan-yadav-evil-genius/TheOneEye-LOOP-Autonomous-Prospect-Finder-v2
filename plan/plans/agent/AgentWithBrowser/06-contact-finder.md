# Contact Finder Plan

## Objectives and scope

Implement the separate Contact Finder process that selects one validated, non-blacklisted company at a time, finds role-matching contacts until each company reaches its **fixed** N, and exposes independent process controls, logs, whiteboard, and effort threads.

**Discovery prompt:** [prompts/contact-finder/prompt.md](prompts/contact-finder/prompt.md) — minimum sufficient context for prospect identification inside a company (see [README](prompts/contact-finder/README.md)).

## Functional requirements

- Start only when `contacts_per_company_default > 0`.
- Queue **mark-valid, non-blacklisted** `SalesStrategyCompany` rows where `contacts_registered < contacts_target`.
- Process one company at a time in `validated_at` order.
- One effort equals one contact try.
- Use a new contact-specific Browser sub-agent per effort stack.
- `register_contact` (Contact Finder only): agent sends **full** ProspectProfile + selection/fit/evidence; runtime links to **active** `sales_strategy_id` + `company_id`.
- `blacklist_prospect` (Contact Finder only): agent sends **minimal** input (`linkedin_url`, `blacklist_reason`); if not linked in this strategy+company, sparse register + link + `is_blacklisted = true`; else set flag only.
- Require validated company context, canonical LinkedIn URL, and dedup/blacklist checks.
- Increment successful contact counter and link thread only after successful `register_contact` (`is_blacklisted = false`).
- Use company-frozen `sales_strategy_attempt_at_register` in effort prefix.
- Continue independently/parallel with Company Finder.

## Non-functional requirements

- Never exceed per-company N under concurrency/retries.
- Stop/restart without skipping or duplicating contacts.
- Sales-strategy-scoped memory and no cross-company context confusion.
- Configurable pacing and LinkedIn-safe rate limits.
- `contacts_registered` counts prospects where `is_blacklisted = false` toward `contacts_target`.

## Architecture and design decisions

- Durable queue query is derived from company state, not a `needs_more_contacts` stage.
- Company-level locking prevents two efforts on the same company.
- Browser researches profiles; orchestrator registers in strategy+company context (agent passes contact fields only).
- Human operator performs contact validation, blacklist/unblacklist, and outreach.
- Whiteboard is editable by agent and operator; one per Contact Finder process.
- **Stop** aborts the current effort immediately.

## Data models

- `SalesStrategyCompany` / `SalesStrategyProspect`: validated state, N/count, queue, `is_blacklisted`, `blacklist_reason`, frozen strategy attempt, contact success counter.
- Global `ProspectProfile`: full name, title, department, seniority, LinkedIn URL, public email/phone, location.
- Global `CompanyProspect`: company/person association.
- `SalesStrategyProspect`: strategy + company + profile selection, fit/confidence/evidence, funnel, thread, outreach.
- `AgentProcessState`, `AgentRun`, contact whiteboard/Brain memory.

## APIs and interfaces

- `POST /sales-strategies/{id}/agents/contact-finder/start`
- `POST /sales-strategies/{id}/agents/contact-finder/stop`
- `GET /sales-strategies/{id}/agents/contact-finder/status`
- `GET /sales-strategies/{id}/agents/contact-finder/whiteboard`
- `POST /sales-strategies/{strategyId}/companies/{companyId}/blacklist|unblacklist`
- Tools: `get_sales_strategy_bundle`, `get_company`, `is_profile_present`, `blacklist_prospect`, `register_contact`, `set_scratch_pad`.

## Target directory structure

```text
loop/apps/agent-runtime/src/contact_finder/
├── process.py
├── queue.py
├── effort.py
├── policies.py
├── status.py
└── errors.py
loop/packages/ai/prompts/contact_finder/
loop/packages/agent-tools/contact/
```

## Milestones and implementation tasks

### M1 — Queue and registration

- Implement queue query, company lock, quota checks, global profile/company-prospect upserts, strategy-prospect insert, dedup/blacklist, counters, and thread linking.

### M2 — Durable process

- Implement start/stop/status, active-company state, pacing, safe resume, logs, and queue transitions.
- Add N change behavior while running.

### M3 — Browser-backed contact research

- Build contact Browser tools/prompts and evidence validation.
- Enforce job-title fit and profile presence checks.

### M4 — Operator integration

- Connect Process page UI using themed **Control | Whiteboard** layout; show active company in header metrics ([UI theme](../../15-ui-theme-and-design-system.md)).
- Connect Records Viewer N controls, Company detail prospects/outreach, Threads/snapshots, metrics, and rollout flag.

## Dependencies

- Validated company workflow and contact registration APIs.
- Company Finder thread/counter patterns.
- [AI platform](01-platform.md), [Browser runtime](02-browser-runtime.md), events/workers, frontend.
- [Deep-agent factory](04-deep-agent-factory.md) and [checkpoints/threads](03-checkpoints-and-threads.md).

## Testing strategy

- Queue ordering and eligibility matrix tests.
- Concurrent company lock and N boundary tests.
- Global LinkedIn normalization, CompanyProspect dedup, strategy triple dedup, blacklist, and title-fit tests.
- Restart at every checkpoint and stop during active company.
- N blacklist/unblacklist while queued/in-progress/completed.
- Parallel Company Finder + Contact Finder integration test.
- Human validation/outreach E2E after registration.

## Risks and open questions

- Define behavior when operator blacklists active company: **immediate abort**, release company lock, set `is_blacklisted = true` on junction row.
- Decide fairness when many companies repeatedly increase N.
- Define failure threshold before moving to next company.
- Confirm required evidence fields for a contact.
- Decide whether ignored connection status affects future search; current design says only N controls requeue.

## Acceptance criteria

- Process cannot start with zero/missing default N.
- Prospects only register under validated, non-blacklist strategy-company links with open quota.
- One company is active per process and locks prevent duplicate work.
- Thread prefixes use frozen company sales_strategy attempt.
- UI accurately shows active company, counts, logs, whiteboard, and all effort threads.
