from loop_api.application.form_markdown import markdown_for_form
from loop_api.main import create_app


def test_form_template_paths_are_published() -> None:
    schema = create_app().openapi()
    paths = schema["paths"]
    assert "/api/v1/forms/organization/template" in paths
    assert "/api/v1/forms/product/template" in paths
    assert "/api/v1/forms/sales-strategy/template" in paths
    assert "/api/v1/sales-strategies/{strategy_id}/companies/{company_id}/profile" in paths


def test_organization_markdown_contains_sections_and_placeholders() -> None:
    filename, content = markdown_for_form("organization")
    assert filename.endswith(".md")
    assert "Organization identity" in content
    assert "Deal constraints" in content
    assert "What NOT to enter" in content
    assert "_Enter your answer here" in content


def test_product_markdown_mentions_success_stories() -> None:
    _, content = markdown_for_form("product")
    assert "Customer success stories" in content
    assert "at least five" in content.lower()


def test_strategy_markdown_includes_run_targets() -> None:
    _, content = markdown_for_form("sales-strategy")
    assert "Run targets" in content
    assert "Target company count" in content
