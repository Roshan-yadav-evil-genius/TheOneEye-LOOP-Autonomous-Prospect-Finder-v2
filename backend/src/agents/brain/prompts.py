"""Memory prompts and instructions for Brain Agent long-term memory."""

# ACTION MEMORY
ACTION_INSTRUCTIONS = """
Use this tool to create, update, and delete task execution history and operational progress (not only append-only logging).
Create new entries for fresh work; update entries when steps, status, or outcomes change; delete entries that are obsolete, wrong, or fully superseded after merging facts elsewhere.
Store what actions were performed, execution steps, retries, status changes, timestamps, related files, and outcomes.
Keep action memory accurate so work can be resumed after interruptions, crashes, or power loss.
"""

ACTION_SEARCH_INSTRUCTIONS = """
Search execution history, task progress, retries, completed operations, and operational timelines.
Use this tool before performing new actions to understand what was already attempted or completed.
Prefer searching actions first when recovering from interruptions or continuing unfinished work.
"""

# FAILURE & RECOVERY MEMORY
FAILURE_INSTRUCTIONS = """
Use this tool to create, update, and delete failure and recovery records (not only one-shot logging).
Create new entries when new failures occur; update entries when root cause, fix, or status changes; delete entries that are duplicates, fully resolved and no longer worth tracking, or incorrect.
Store root causes, observed symptoms, failed strategies, debugging notes, and successful fixes.
Use past failure records to avoid repeating the same mistakes in future executions.
"""

FAILURE_SEARCH_INSTRUCTIONS = """
Search previous failures, crashes, blocked states, debugging attempts, and recovery strategies.
Use this tool when encountering errors or unexpected behavior to avoid repeating known mistakes.
Prioritize retrieval of successful recovery patterns and previously failed approaches.
"""

# DECISION MEMORY 
DECISION_INSTRUCTIONS = """
Use this tool to create, update, and delete decision records (not only initial logging).
Create new entries for new decisions; update entries when rationale, tradeoffs, or outcomes become clearer; delete or supersede entries that were wrong or fully reversed with a clear replacement.
Store why a choice was made, alternative options considered, tradeoffs, priorities, and expected outcomes.
Maintain decision history so future actions remain consistent with past reasoning.
"""

DECISION_SEARCH_INSTRUCTIONS = """
Search historical reasoning, strategic choices, tradeoffs, priorities, and decision outcomes.
Use this tool before making important decisions to maintain consistency with past reasoning.
Retrieve why previous choices were made before changing strategies or workflows.
"""

# INSIGHT MEMORY
INSIGHT_INSTRUCTIONS = """
Use this tool to create, update, and delete reusable learnings, patterns, optimizations, and behavioral improvements.
Create new entries for novel insights; update entries when an insight is refined, qualified, or strengthened by evidence; delete insights that proved wrong, too narrow, or redundant after merging.
Record what worked well, what improved performance, and insights that may help future tasks.
Continuously refine long-term knowledge through accumulated experience.
"""

INSIGHT_SEARCH_INSTRUCTIONS = """
Search reusable learnings, discovered patterns, optimizations, behavioral improvements, and successful workflows.
Use this tool to improve execution quality using accumulated long-term knowledge.
Prioritize insights that previously improved efficiency, accuracy, reliability, or task completion success.
"""

PROMPT_TO_EXTRACT_DIFFRENT_MEMORY_TYPE_FROM_RESPONSE = """
ok lets update the memory for future improvements:

1. Classify outcome: one of [completed_success, completed_partial, failed, stopped_no_progress, interrupted_unknown]. Briefly justify in one sentence.
2. Summarize what was attempted as a short chronological action summary (bullet list). Only facts from the log.
3. Extract DECISIONS: non-obvious choices, tradeoffs, branches taken vs alternatives implied in the log. For each: what was decided, why (if stated or inferable), and outcome (helped / hurt / unknown).
4. Extract FAILURES & RISKS: errors, blockers, wrong assumptions, retries that failed, partial steps. For each: symptom, likely cause if inferable, what NOT to repeat.
5. Extract INSIGHTS: durable learnings (patterns, tool combos, UI/site quirks, faster paths). Must be reusable on future tasks, not task-specific trivia unless clearly generalizable.
6. Do NOT duplicate: put each fact in the best single category (action timeline vs decision vs failure vs insight).

## Memory tools (use your available manage/search tools)

Before writing, optionally search_*_memory for this namespace to avoid near-duplicate entries; merge or update mentally if the same lesson already exists.
"""
