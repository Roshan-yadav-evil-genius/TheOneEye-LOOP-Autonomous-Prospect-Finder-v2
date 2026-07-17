# Checkpoints, Effort Threads, and Snapshot Viewer

> Canonical source for nested checkpointing, effort thread naming, GPA allocation, and the snapshot viewer.

This plan owns nested checkpointing, effort thread naming, GPA allocation, `AgentRun` linking, and the snapshot viewer for the AgentWithBrowser pattern.

### 9.12 Agent effort threads and snapshot viewer

Production replaces the POC flat thread list (`LangChainStateSnapShotViewer`) with **effort-linked threads** operators open from company and contact rows.

#### Design principles

| Rule | Detail |
|------|--------|
| Link **main thread only** | Store orchestrator `thread_id` on entity — not browser/brain sub-threads |
| Shared prefix | All sub-agents for one effort share the same prefix; suffix distinguishes role |
| Link on register | Thread exists before registration with strategy link IDs null on `AgentRun`; linked atomically in `register_company` / `register_contact` |
| Sub-agent picker | Snapshot viewer dropdown lists `thread_id LIKE '{effort_prefix}_%'` |

#### Thread naming

**Company Finder** — sales-strategy-level effort (unique `effort_seq` per attempt start):

```text
Prefix:  LOOP_<org_id>_<product_id>_<sales_strategy_id>_<effort_seq>

Threads:
  LOOP_<org_id>_<product_id>_<sales_strategy_id>_<effort_seq>_company_finder    ← linked on register_company
  LOOP_<org_id>_<product_id>_<sales_strategy_id>_<effort_seq>_browser_agent
  LOOP_<org_id>_<product_id>_<sales_strategy_id>_<effort_seq>_company_finder_brain
  LOOP_<org_id>_<product_id>_<sales_strategy_id>_<effort_seq>_browser_agent_brain
```

**Contact Finder** — uses **`sales_strategy_attempt_at_register`** frozen on the company (not the live sales_strategy counter) + company + contact effort:

```text
Prefix:  LOOP_<org_id>_<product_id>_<sales_strategy_id>_<sales_strategy_attempt_at_register>_<company_id>_<contact_effort_seq>

Threads:
  LOOP_..._<contact_effort_seq>_contact_finder    ← linked on register_contact
  LOOP_..._<contact_effort_seq>_browser_agent
  LOOP_..._<contact_effort_seq>_contact_finder_brain
  LOOP_..._<contact_effort_seq>_browser_agent_brain
```

**GPA (General Purpose Agent) invocations** — numbered checkpoint per call inside a parent role thread:

```text
{parent_role_thread}_GPA_1     ← first GPA invoke in this effort for that role
{parent_role_thread}_GPA_2     ← second invoke in same effort
{parent_role_thread}_GPA_n
```

Examples:

```text
LOOP_org1_prod_camp_7_company_finder_GPA_1
LOOP_org1_prod_camp_7_company_finder_GPA_2
LOOP_org1_prod_camp_7_browser_agent_GPA_1
```

#### GPA thread allocation (DB max + 1)

Before each GPA run, the factory **does not** reuse the parent role thread. It allocates a new checkpoint thread:

1. Build search prefix: `{parent_role_thread}_GPA_`
2. Query checkpoints: `SELECT DISTINCT thread_id FROM agent_brain.checkpoints WHERE thread_id LIKE '{parent_role_thread}_GPA_%'`
3. Parse each id with regex `_GPA_(\d+)$` — take **max** (default `0` if none)
4. Next thread: `{parent_role_thread}_GPA_{max + 1}`

| Rule | Detail |
|------|--------|
| Scope | Counter is **per parent role thread** within one effort (resets on new `effort_seq` / new effort prefix) |
| Concurrency | Use advisory lock on `(effort_prefix, parent_role_suffix)` or retry if two workers race |
| Viewer | Sub-agent dropdown `LIKE '{effort_prefix}_%'` includes all `_GPA_n` rows for traceability |

Implementation: `packages/ai/loop_agent_factory.py` → `allocate_gpa_thread_id(parent_role_thread)`.

#### Nested checkpointing for compiled sub-agents

`create_deep_agent` manages parent-child checkpoint wiring for sub-agents it creates internally. LOOP also uses custom `CompiledSubAgent` wrappers around independently compiled graphs, such as Browser, Brain, and the custom GPA. Those wrappers are generic runnables from LangGraph's point of view, so the parent graph must explicitly preserve the child's checkpoint thread id.

The production implementation must use a nested checkpoint architecture:

| Layer | Checkpointer | Thread id owner | Example |
|-------|--------------|-----------------|---------|
| Parent role agent | Parent graph checkpointer | Company Finder / Contact Finder / Browser role | `LOOP_org1_prod_camp_7_company_finder` |
| Compiled child agent | Child graph checkpointer | Wrapped `CompiledSubAgent` graph | `LOOP_org1_prod_camp_7_company_finder_GPA_3` |
| Role child agent | Child graph checkpointer | Stable role child such as Browser or Brain | `LOOP_org1_prod_camp_7_browser_agent` |

The checkpointer may be the same physical `PostgresSaver`, but parent and child state must be isolated by different `thread_id` values. Never invoke a compiled sub-agent on the parent role thread.

##### Parent checkpoint state

The parent role checkpoint must store the child thread currently assigned to every in-flight compiled sub-agent invocation. Use a small explicit state field so the child thread survives process crashes, retries, and resume operations:

```python
active_subagent_threads: dict[str, dict]
```

Recommended value shape:

```python
{
    "General Purpose Agent": {
        "thread_id": "LOOP_org1_prod_camp_7_company_finder_GPA_3",
        "status": "running",
        "allocation_mode": "gpa",
        "task_fingerprint": "optional stable hash of the delegated task"
    },
    "Browser Agent": {
        "thread_id": "LOOP_org1_prod_camp_7_browser_agent",
        "status": "running",
        "allocation_mode": "role"
    }
}
```

If the same compiled sub-agent can run concurrently, key the map by a stable invocation key instead of only the sub-agent name, for example `{subagent_name}:{tool_call_id}`. The key must be recreated exactly on resume.

##### Thread resolution rules

Before invoking any custom compiled sub-agent, resolve the child thread id in this order:

1. Load the parent checkpoint using the parent `thread_id`.
2. Look for an existing `active_subagent_threads[invocation_key]` entry with `status = running`.
3. If found, reuse that stored child `thread_id`.
4. If not found, create a new child `thread_id` using the sub-agent allocation mode.
5. Store the new child `thread_id` in the parent checkpoint before invoking the child graph.
6. Invoke the compiled sub-agent using `config={"configurable": {"thread_id": child_thread_id}}`.
7. After the child graph reaches an idle/completed state, mark the parent entry as `completed` or remove it.

Allocation modes:

| Mode | Use case | Thread id rule |
|------|----------|----------------|
| `role` | Long-lived role child such as Browser or Brain | `{effort_prefix}_{role_suffix}` |
| `gpa` | Numbered GPA delegation inside a parent role | `{parent_role_thread}_GPA_{n}` |
| `named` | Generic reusable worker where role suffix is enough | `{parent_thread_id}:{child_suffix}` |

##### GPA resume versus allocation rule

GPA allocation is only for a brand-new GPA delegation. It must not run during resume of an interrupted GPA.

| Parent state | Child checkpoint | Required action |
|--------------|------------------|-----------------|
| No active GPA entry | No matching child checkpoint | Allocate next `_GPA_n` |
| No active GPA entry | Previous GPA is completed | Allocate next `_GPA_n` |
| Active GPA entry points to `_GPA_3` | `_GPA_3` has pending or mid-turn state | Reuse `_GPA_3` |
| Active GPA entry points to `_GPA_3` | `_GPA_3` is completed | Mark completed, then next delegation allocates `_GPA_4` |

Example:

```text
Parent role thread: LOOP_org1_prod_camp_7_company_finder
First GPA call:     LOOP_org1_prod_camp_7_company_finder_GPA_1
Second GPA call:    LOOP_org1_prod_camp_7_company_finder_GPA_2
Third GPA call:     LOOP_org1_prod_camp_7_company_finder_GPA_3
```

If `_GPA_3` stops after tool step 3:

1. Parent checkpoint contains `active_subagent_threads["General Purpose Agent"].thread_id = "LOOP_org1_prod_camp_7_company_finder_GPA_3"`.
2. Child checkpoint exists for `LOOP_org1_prod_camp_7_company_finder_GPA_3`.
3. Resume parent on `LOOP_org1_prod_camp_7_company_finder`.
4. Parent reads the stored child thread id.
5. Parent invokes GPA with `thread_id = LOOP_org1_prod_camp_7_company_finder_GPA_3`.
6. GPA graph restores its own checkpoint and continues from the last saved step.
7. The system must not allocate `LOOP_org1_prod_camp_7_company_finder_GPA_4` until `_GPA_3` has completed and a new GPA task is requested.

##### Child graph resume input

Every compiled sub-agent wrapper must use the same checkpoint-aware input resolution pattern:

```python
invoke_input = await resolve_subagent_input(child_graph, child_config, task)
```

`resolve_subagent_input(...)` returns:

| Return value | Meaning | Invocation |
|--------------|---------|------------|
| `task` | Fresh thread or prior turn completed | Invoke child with the delegated task |
| `None` | Child is mid-turn or has pending graph nodes | Invoke child with `None` to resume |

After invoking the child, the wrapper must drain pending child graph nodes until `snapshot.next` is empty. This preserves normal LangGraph checkpoint behavior for pending tool calls and interrupted turns.

##### Required reusable helpers

Production code should centralize this in one helper module instead of hand-writing thread logic in every sub-agent wrapper:

```python
def build_role_thread_id(*, effort_prefix: str, role_suffix: str) -> str: ...
def build_named_child_thread_id(parent_thread_id: str, child_suffix: str) -> str: ...
def allocate_gpa_thread_id(conn, parent_role_thread: str) -> str: ...
def resolve_compiled_child_thread_id(...): ...
async def invoke_compiled_child_until_idle(...): ...
def to_checkpointed_compiled_subagent(...): ...
```

Suggested package location:

```text
packages/ai/
├── loop_agent_factory.py
├── nested_checkpointing.py
└── subagent_runner.py
```

Responsibilities:

| Helper | Responsibility |
|--------|----------------|
| `resolve_compiled_child_thread_id` | Read parent checkpoint state, reuse active child id on resume, allocate only for new work |
| `invoke_compiled_child_until_idle` | Invoke child graph with `task` or `None`, then drain pending nodes |
| `to_checkpointed_compiled_subagent` | Wrap any compiled child graph as a `CompiledSubAgent` with transparent nested checkpointing |
| `allocate_gpa_thread_id` | Allocate the next numbered GPA thread for new GPA work only |

##### Implementation requirements for developers

- Use `create_deep_agent` for parent and child agents.
- Give every compiled sub-agent its own child `thread_id`; never share the parent's thread id.
- Persist the child `thread_id` in the parent checkpoint before child invocation starts.
- Reuse the persisted child `thread_id` on retries and parent resume.
- Allocate `_GPA_n` only when there is no active running GPA entry in parent state.
- Mark active child entries completed only after the child graph has no pending `snapshot.next`.
- Preserve existing role threads for Browser and Brain.
- Preserve current checkpoint viewer behavior by keeping child thread ids under the effort prefix where possible.
- Do not modify LangChain or deepagents internals unless the public runnable wrapper API cannot support this.
- Avoid random UUID child threads for resumable compiled sub-agents; random ids break resume unless they are persisted in the parent checkpoint before invocation.

##### Acceptance tests

Developers must prove these cases:

| Case | Expected result |
|------|-----------------|
| Fresh GPA call | Parent allocates `_GPA_1` and stores it in parent state |
| Second completed GPA call | Parent allocates `_GPA_2` |
| Interrupted `_GPA_3` | Parent state stores `_GPA_3` with `status = running` |
| Resume parent after `_GPA_3` interruption | Parent invokes child with `_GPA_3`, not `_GPA_4` |
| Child has pending tool call | Child is invoked with `None` and continues pending graph nodes |
| Child completed | Parent marks child entry completed, then future GPA call allocates next number |
| Multiple compiled children | Browser, Brain, and GPA each get separate thread ids and separate checkpoints |
| Snapshot viewer | Dropdown lists parent role thread plus Browser, Brain, and `_GPA_n` child threads |

| Counter | Scope | Increments when |
|---------|-------|-----------------|
| `effort_seq` (`AgentRun.attempt_iteration`) | Per sales strategy (company efforts) | Each Company Finder effort **starts** (unique prefix; includes failed/unlinked) |
| `company_finder_attempt` (`sales_strategy.company_finder_attempt`) | SalesStrategy | Each **successful** `register_company` |
| `sales_strategy_attempt_at_register` | Per company | Set once at first successful `register_company` for that company (= `company_finder_attempt` at link time) |
| `contact_effort_seq` (`AgentRun.contact_attempt_iteration`) | Per company contact effort | Each Contact Finder effort **starts** at that company |
| `contact_finder_attempt` (`sales_strategy_company.contact_finder_attempt`) | Per strategy-company | Each successful new `SalesStrategyProspect` |

`<product_id>`, `<sales_strategy_id>`, `<company_id>` use stable UUID strings (no slashes).

#### `AgentRun` record (OLTP)

One row per effort start (orchestrator); sub-threads share `effort_prefix`:

```text
agent_run
├── id                      PK
├── product_id, sales_strategy_id FK
├── company_id              FK nullable  # set at Contact Finder start; set on register for Company Finder
├── sales_strategy_prospect_id FK nullable  # set on register_contact
├── agent_role              company_finder | contact_finder
├── effort_prefix           text         # prefix for LIKE query
├── primary_thread_id       text         # orchestrator checkpoint thread_id
├── attempt_iteration       int          # sales-strategy-level
├── contact_attempt_iteration int nullable
├── status                  running | completed | stopped | failed
├── started_at, completed_at
└── prompt_tokens, ...      # usage fields
```

#### Entity links (denormalized for UI)

| Entity | Column | Value |
|--------|--------|-------|
| `SalesStrategyCompany` | `discovery_thread_id` | `{prefix}_company_finder` |
| `SalesStrategyProspect` | `discovery_thread_id` | `{prefix}_contact_finder` |

#### Snapshot viewer (`apps/admin` or embedded route)

Evolves POC `LangChainStateSnapShotViewer` — reads `agent_brain.checkpoints`.

| Entry point | Opens with |
|-------------|------------|
| **Threads** tab → click row | `AgentRun.primary_thread_id` (linked or unlinked) |
| Company detail → linked effort shortcut | `SalesStrategyCompany.discovery_thread_id` or `SalesStrategyProspect.discovery_thread_id` |
| Orchestrator chat — sub-agent tool call link | Child `thread_id` stored on delegation row |

**Viewer UX:**

1. Load checkpoint state for `primary_thread_id` (default: orchestrator).
2. Derive `effort_prefix` from `AgentRun` or strip known suffix (`_company_finder` / `_contact_finder`).
3. **Sub-agent dropdown:** `SELECT DISTINCT thread_id FROM checkpoints WHERE thread_id LIKE '{effort_prefix}_%' ORDER BY thread_id` (includes `_company_finder`, `_browser_agent`, `_GPA_1`, `_GPA_2`, …).
4. Switching dropdown reloads snapshot for selected sub-agent (browser, brain, etc.).

Route: `/sales-strategies/{id}/threads/snapshots?thread_id={primary_thread_id}` (embedded in **Threads** tab or deep-linked from company detail).

#### Package helpers (`packages/ai` + `packages/agent-memory`)

```python
def build_role_thread_id(*, effort_prefix: str, role_suffix: str) -> str: ...
def allocate_gpa_thread_id(conn, parent_role_thread: str) -> str: ...  # DB max + 1
def list_effort_threads(effort_prefix: str) -> list[str]: ...  # checkpoints LIKE query
def resolve_compiled_child_thread_id(...): ...  # reuse active child id, allocate only for new work
async def invoke_compiled_child_until_idle(...): ...  # resume child checkpoints and drain pending nodes
```

---
