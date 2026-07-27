from pathlib import Path
from jinja2 import Environment, FileSystemLoader

PROMPTS_DIR = Path(__file__).parent

def render_setup_prompt(form_name: str) -> str:
    """Render the unified LOOP setup chatbot prompt for a given form_name using Jinja2."""
    env = Environment(loader=FileSystemLoader(PROMPTS_DIR))
    template = env.get_template("LOOP_chatbot.jinja")
    return template.render(form_name=form_name)
