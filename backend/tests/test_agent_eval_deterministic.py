"""Deterministic agent evaluation cases (RecreationDocs 13 — local/no-credential)."""

from __future__ import annotations

import pytest

from loop_api.agents.model_provider import DeterministicDiscoveryModel
from loop_api.agents.runtime import validate_registration_authority

EVAL_CASES = [
    {
        "id": "company-register",
        "decision": {
            "action": "register_company",
            "company": {
                "name": "Acme Robotics",
                "website_url": "https://acme.example",
                "selection_reason": "Hiring AI engineers after Series B",
            },
        },
        "expects_action": "register_company",
    },
    {
        "id": "company-none",
        "decision": {"action": "no_candidate", "reason": "No public signal"},
        "expects_action": "no_candidate",
    },
    {
        "id": "contact-register",
        "decision": {
            "action": "register_contact",
            "contact": {
                "full_name": "Ada Lovelace",
                "job_title": "CTO",
                "linkedin_url": "https://www.linkedin.com/in/ada",
                "selection_reason": "Economic buyer",
                "fit_rationale": "Owns toolchain budget",
                "confidence_score": 88,
                "evidence_urls": ["https://www.linkedin.com/in/ada"],
            },
        },
        "expects_action": "register_contact",
    },
]


@pytest.mark.asyncio
async def test_deterministic_eval_cases_and_authority() -> None:
    validate_registration_authority("company_finder", {"register_company", "set_scratch_pad"})
    validate_registration_authority(
        "contact_finder", {"register_contact", "blacklist_prospect", "get_company"}
    )
    with pytest.raises(ValueError):
        validate_registration_authority("browser_agent", {"register_company"})

    model = DeterministicDiscoveryModel([case["decision"] for case in EVAL_CASES])
    for case in EVAL_CASES:
        decision = await model.decide(case["id"])
        assert decision["action"] == case["expects_action"]
        if case["expects_action"] == "register_company":
            assert "website_url" in decision["company"]
        if case["expects_action"] == "register_contact":
            assert 0 <= float(decision["contact"]["confidence_score"]) <= 100
