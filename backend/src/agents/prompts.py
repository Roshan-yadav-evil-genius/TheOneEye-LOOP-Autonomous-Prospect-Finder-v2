from pathlib import Path
from jinja2 import Environment, FileSystemLoader

PROMPTS_ROOT = Path(__file__).resolve().parent / "prompt_files"

_jinja_env = Environment(
    loader=FileSystemLoader(PROMPTS_ROOT),
    autoescape=False,
    trim_blocks=True,
    lstrip_blocks=True,
)


def load_prompt(filename: str) -> str:
    """Load and render prompt template file using Jinja2 FileSystemLoader."""
    return _jinja_env.get_template(filename).render()


COMPANY_FINDER_PROMPT = load_prompt("company_finder.md")
COMPANY_FINDER_PLANNER_PROMPT = load_prompt("company_finder_planner.md")
PLANNER_V1_PROMPT = COMPANY_FINDER_PLANNER_PROMPT
PLANNER_V2_PROMPT = load_prompt("planner.md")

EVALUATOR_V1_PROMPT = load_prompt("company_finder_planner_evaluator.md")
EVALUATOR_V2_PROMPT = load_prompt("evaluator.md")
EVALUATOR_PROMPT = EVALUATOR_V2_PROMPT
COMPANY_FINDER_PLANNER_EVALUATOR_PROMPT = EVALUATOR_V1_PROMPT
CONTACT_FINDER_PROMPT = load_prompt("contact_finder.md")
BROWSER_AGENT_PROMPT = load_prompt("browser.md")
BRAIN_AGENT_PROMPT = load_prompt("brain.md")
SALES_MANAGER_PROMPT = load_prompt("sales_manager.md")


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

