from pathlib import Path

PROMPTS_ROOT = Path(__file__).resolve().parent / "prompt_files"

COMPANY_FINDER_PROMPT = (PROMPTS_ROOT / "company_finder.md").read_text(encoding="utf-8")
COMPANY_FINDER_PLANNER_PROMPT = (PROMPTS_ROOT / "company_finder_planner.md").read_text(
    encoding="utf-8"
)
PLANNER_V1_PROMPT = COMPANY_FINDER_PLANNER_PROMPT
PLANNER_V2_PROMPT = (PROMPTS_ROOT / "planner.md").read_text(encoding="utf-8")

EVALUATOR_V1_PROMPT = (PROMPTS_ROOT / "company_finder_planner_evaluator.md").read_text(
    encoding="utf-8"
)
EVALUATOR_V2_PROMPT = (PROMPTS_ROOT / "evaluator.md").read_text(encoding="utf-8")
EVALUATOR_PROMPT = EVALUATOR_V2_PROMPT
COMPANY_FINDER_PLANNER_EVALUATOR_PROMPT = EVALUATOR_V1_PROMPT
CONTACT_FINDER_PROMPT = (PROMPTS_ROOT / "contact_finder.md").read_text(encoding="utf-8")
BROWSER_AGENT_PROMPT = (PROMPTS_ROOT / "browser.md").read_text(encoding="utf-8")
BRAIN_AGENT_PROMPT = (PROMPTS_ROOT / "brain.md").read_text(encoding="utf-8")
SALES_MANAGER_PROMPT = (PROMPTS_ROOT / "sales_manager.md").read_text(encoding="utf-8")


def get_planner_prompt(version: str | None = None) -> str:
    """Return planner prompt string based on specified version ('v1' or 'v2') or config setting."""
    if not version:
        from core.config import get_settings
        version = get_settings().planner_prompt_version
    if str(version).lower() == "v1":
        return PLANNER_V1_PROMPT
    return PLANNER_V2_PROMPT


def get_evaluator_prompt(version: str | None = None) -> str:
    """Return evaluator prompt string based on specified version ('v1' or 'v2') or config setting."""
    if not version:
        from core.config import get_settings
        version = get_settings().planner_prompt_version
    if str(version).lower() == "v1":
        return EVALUATOR_V1_PROMPT
    return EVALUATOR_V2_PROMPT


def render_prompt(template: str, values: dict[str, str]) -> str:
    result = template
    for key, value in values.items():
        result = result.replace(f"{{{{{key}}}}}", value)
    return result

