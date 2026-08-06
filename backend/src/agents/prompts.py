from pathlib import Path

PROMPTS_ROOT = Path(__file__).resolve().parent / "prompt_files"

COMPANY_FINDER_PROMPT = (PROMPTS_ROOT / "company_finder.md").read_text(encoding="utf-8")
COMPANY_FINDER_PLANNER_PROMPT = (PROMPTS_ROOT / "company_finder_planner.md").read_text(
    encoding="utf-8"
)
COMPANY_FINDER_PLANNER_EVALUATOR_PROMPT = (
    PROMPTS_ROOT / "company_finder_planner_evaluator.md"
).read_text(encoding="utf-8")
CONTACT_FINDER_PROMPT = (PROMPTS_ROOT / "contact_finder.md").read_text(encoding="utf-8")
BROWSER_AGENT_PROMPT = (PROMPTS_ROOT / "browser.md").read_text(encoding="utf-8")
BRAIN_AGENT_PROMPT = (PROMPTS_ROOT / "brain.md").read_text(encoding="utf-8")
SALES_MANAGER_PROMPT = (PROMPTS_ROOT / "sales_manager.md").read_text(encoding="utf-8")



def render_prompt(template: str, values: dict[str, str]) -> str:
    result = template
    for key, value in values.items():
        result = result.replace(f"{{{{{key}}}}}", value)
    return result
