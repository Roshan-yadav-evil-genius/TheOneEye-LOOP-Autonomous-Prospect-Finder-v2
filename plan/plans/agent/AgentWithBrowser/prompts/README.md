# Agent Prompts Plan

Canonical prompt templates for LOOP AgentWithBrowser agents. Each subfolder holds one prompt spec plus a README explaining scope, placeholders, and what is deliberately excluded.

| Prompt | Agent | Scope |
|--------|-------|--------|
| [company-finder/](company-finder/README.md) | Company Finder | Identify target **companies** from sales strategy — no people, no outreach |
| [contact-finder/](contact-finder/README.md) | Contact Finder | Identify target **people** inside a validated company — no company discovery, no outreach |

Prompts are filled at runtime from [`plans/form/`](../../../form/README.md) payloads via `get_sales_strategy_bundle`. Keep discovery prompts minimal; org/product context enters only where it affects **company fit**, not sales execution.

Parent index: [AgentWithBrowser README](../README.md).
