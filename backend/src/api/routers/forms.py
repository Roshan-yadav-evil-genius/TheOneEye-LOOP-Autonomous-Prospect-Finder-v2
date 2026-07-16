from fastapi import APIRouter, HTTPException

from application.form_definitions import FORM_TEMPLATES
from application.form_markdown import markdown_for_form
from contracts.domain import FormMarkdownTemplate

router = APIRouter(prefix="/api/v1/forms", tags=["forms"])


@router.get("/organization/template", response_model=FormMarkdownTemplate)
async def organization_form_template() -> FormMarkdownTemplate:
    filename, content = markdown_for_form("organization")
    return FormMarkdownTemplate(filename=filename, content=content)


@router.get("/product/template", response_model=FormMarkdownTemplate)
async def product_form_template() -> FormMarkdownTemplate:
    filename, content = markdown_for_form("product")
    return FormMarkdownTemplate(filename=filename, content=content)


@router.get("/sales-strategy/template", response_model=FormMarkdownTemplate)
async def sales_strategy_form_template() -> FormMarkdownTemplate:
    filename, content = markdown_for_form("sales-strategy")
    return FormMarkdownTemplate(filename=filename, content=content)


@router.get("/{form_key}/template", response_model=FormMarkdownTemplate, include_in_schema=False)
async def form_template_by_key(form_key: str) -> FormMarkdownTemplate:
    if form_key not in FORM_TEMPLATES:
        raise HTTPException(status_code=404, detail="Unknown form template.")
    filename, content = markdown_for_form(form_key)
    return FormMarkdownTemplate(filename=filename, content=content)
