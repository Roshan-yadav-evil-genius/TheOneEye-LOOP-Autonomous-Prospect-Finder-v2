import pytest

from loop_api.agents.runtime import (
    allocate_gpa_thread_id,
    build_company_effort_prefix,
    build_contact_effort_prefix,
    validate_registration_authority,
)
from loop_api.application.loop_service import (
    DomainError,
    normalize_domain,
    normalize_linkedin_url,
    validate_org_form,
    validate_product_form,
)


def test_identity_normalization_is_canonical() -> None:
    assert normalize_domain("https://www.Example.com/path") == "example.com"
    assert (
        normalize_linkedin_url("https://www.linkedin.com/in/Jane-Doe/?trk=public")
        == "https://www.linkedin.com/in/jane-doe"
    )


def test_linkedin_company_pages_are_rejected() -> None:
    with pytest.raises(DomainError) as error:
        normalize_linkedin_url("https://linkedin.com/company/acme")
    assert error.value.code == "invalid_linkedin_url"


def test_form_gates_report_missing_sections() -> None:
    organization = validate_org_form({})
    product = validate_product_form({})
    assert not organization.valid
    assert "deal_constraints" in organization.missing_sections
    assert not product.valid
    assert "customer_success_stories" in product.missing_sections


def test_effort_thread_names_follow_frozen_strategy_attempt() -> None:
    assert build_company_effort_prefix("p", "s", 3) == "LOOP_p_s_3"
    assert build_contact_effort_prefix("p", "s", 3, "c", 2) == "LOOP_p_s_3_c_2"


def test_gpa_allocator_uses_max_plus_one() -> None:
    parent = "LOOP_p_s_1_company_finder"
    assert allocate_gpa_thread_id(parent, [f"{parent}_GPA_1", f"{parent}_GPA_4"]) == (
        f"{parent}_GPA_5"
    )


def test_browser_cannot_receive_registration_authority() -> None:
    with pytest.raises(ValueError, match="Browser agents"):
        validate_registration_authority("browser_agent", {"navigate", "register_company"})
