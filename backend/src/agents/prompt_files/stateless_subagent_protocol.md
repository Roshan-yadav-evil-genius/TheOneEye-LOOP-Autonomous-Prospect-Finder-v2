### 🚫 STATELESS SUBAGENT PROTOCOL — CONTEXT-ENRICHED PROMPTS REQUIRED

- All subagents are invoked via delegation tools (such as the `task` tool) and are **STATELESS**—they receive NO parent conversation history or prior workspace state automatically.
- Any call to a subagent via the `task` tool **MUST pass a fully self-contained, context-enriched task prompt** that explicitly embeds all necessary background context, parameters, goals, and constraints required for execution.
- **NEVER** pass vague, ambiguous, or generic task prompts when invoking subagents without embedding all exact required context and concrete details directly into the prompt.
