# AgentWithBrowser

Everything needed to develop LOOP deep agents that compose an **orchestrator**, a **Browser sub-agent** (Playwright MCP), **Brain memory**, and nested **GPA** checkpoints.

```text
Orchestrator (Company Finder / Contact Finder)
  ├── Browser sub-agent   ← navigation/evidence only; never register_*
  ├── Brain sub-agent     ← sales-strategy-scoped memory
  └── GPA (nested)        ← numbered _GPA_n child threads
```

Built through `create_loop_deep_agent` / `build_*_finder_stack()`.

## Reading order

| Order | Doc | Purpose |
|------:|-----|---------|
| 0 | [00-architecture.md](00-architecture.md) | Topology, tools, memory, workflows, guardrails (§9.1–9.11) |
| 1 | [01-platform.md](01-platform.md) | Shared AI platform: tools, memory, AgentRun, factory milestones |
| 2 | [02-browser-runtime.md](02-browser-runtime.md) | Browser pool, MCP gateway, compaction, recovery |
| 3 | [03-checkpoints-and-threads.md](03-checkpoints-and-threads.md) | Effort prefixes, nested checkpoints, GPA, snapshot viewer (§9.12) |
| 4 | [04-deep-agent-factory.md](04-deep-agent-factory.md) | `create_loop_deep_agent`, stack builders, registration authority (§9.13) |
| 5 | [05-company-finder.md](05-company-finder.md) | Company Finder process, quota, registration |
| 6 | [06-contact-finder.md](06-contact-finder.md) | Contact Finder process, queue, per-company N |
| — | [prompts/](prompts/README.md) | Discovery prompt templates |

## Canonical design

This folder is the **single source of truth** for the LOOP AI architecture.

| Topic | Canonical doc |
|-------|---------------|
| AI architecture | [00-architecture.md](00-architecture.md) |
| Effort threads / checkpoints | [03-checkpoints-and-threads.md](03-checkpoints-and-threads.md) |
| Deep-agent factory | [04-deep-agent-factory.md](04-deep-agent-factory.md) |

## Depends on

- [Knowledge forms](../../form/README.md) — sales strategy / product / org payloads
- Backend registration APIs (`register_company`, `register_contact`)
- Database + events/workers for durable process control

## Stage mapping

See [plans/README.md](../../README.md) Stages 3–5:

- **Stage 3** — platform + factory + checkpoints (`01`, `03`, `04`)
- **Stage 4** — browser runtime + Company Finder (`02`, `05`)
- **Stage 5** — Contact Finder (`06`)
