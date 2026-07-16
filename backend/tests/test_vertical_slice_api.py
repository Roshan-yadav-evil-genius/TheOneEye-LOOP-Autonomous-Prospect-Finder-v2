import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from loop_api.agents.nested_checkpointing import (
    mark_child_completed,
    resolve_compiled_child_thread_id,
)
from loop_api.agents.runtime import validate_registration_authority
from loop_api.main import create_app
from loop_api.persistence import models
from loop_api.persistence.database import Base, get_session
from loop_api.workers.consumers import EventConsumer


@pytest.fixture
async def client(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'slice.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async def override():
        async with factory() as session:
            yield session

    app = create_app()
    app.dependency_overrides[get_session] = override
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as value:
        yield value
    await engine.dispose()


def valid_org_form() -> dict:
    return {
        "company_overview": {
            "description": "We build outreach software.",
            "mission": "Help sellers find fit.",
        },
        "industry": {"primary": "Software"},
        "business_model": {"types": ["B2B", "SaaS"]},
        "target_markets": {"countries": ["US"], "regions": [], "industries": ["SaaS"]},
        "customer_segments": {"primary": ["mid-market"]},
        "deal_constraints": {
            "min_contract_value": "10000",
            "excluded_industries": ["gambling"],
            "geographic_limits": [],
        },
        "delivery_capability": {"geography": ["US"], "support_hours": "9-5 ET"},
    }


def valid_product_form() -> dict:
    return {
        "form_version": "2.0",
        "product_overview": {"summary": "AI prospecting for B2B sellers"},
        "problem_solved": {"primary": "Manual prospecting"},
        "value_proposition": {"primary": "Faster qualified pipelines"},
        "icp": {"industries": {"primary": ["SaaS"]}},
        "buyer_personas": {"primary_titles": ["VP Sales"]},
        "pricing": {"model": "subscription", "min_deal_size": "10000"},
        "differentiators": ["Strategy-scoped automation"],
        "customer_success_stories": [
            {"name": f"Customer {index}", "website": f"https://c{index}.com"}
            for index in range(1, 6)
        ],
    }


def valid_strategy_form() -> dict:
    return {
        "form_version": "2.0",
        "overview": {
            "name": "SaaS CTOs Q3",
            "description": "Focus run",
            "target_companies_narrative": "Series B SaaS companies hiring AEs",
        },
        "priority_industries": {"primary": ["SaaS"]},
        "buying_signals": {"selected": ["Recently funded"]},
        "run_targets": {"target_companies": 1, "contacts_per_company_default": 1},
    }


@pytest.mark.asyncio
async def test_manual_vertical_slice_through_api(client: AsyncClient) -> None:
    org = (
        await client.post(
            "/api/v1/organizations",
            json={
                "name": "TheOneEye",
                "website": "https://theoneeye.example",
                "org_form": valid_org_form(),
            },
        )
    ).json()
    validation = await client.post(f"/api/v1/organizations/{org['id']}/profile/validate")
    assert validation.status_code == 200
    assert validation.json()["valid"] is True

    product = (
        await client.post(
            f"/api/v1/organizations/{org['id']}/products",
            json={
                "name": "LOOP",
                "kind": "product",
                "icp_form": valid_product_form(),
            },
        )
    ).json()
    assert (
        await client.post(f"/api/v1/products/{product['id']}/profile/validate")
    ).json()["valid"] is True

    strategy = (
        await client.post(
            f"/api/v1/products/{product['id']}/sales-strategies",
            json={"sales_strategy_form": valid_strategy_form()},
        )
    ).json()
    immutable = await client.patch(f"/api/v1/sales-strategies/{strategy['id']}/strategy")
    assert immutable.status_code == 409

    company = (
        await client.post(
            f"/api/v1/sales-strategies/{strategy['id']}/companies",
            json={
                "name": "Acme",
                "website_url": "https://www.acme.com/about",
                "selection_reason": "Matches SaaS ICP and funding signal",
            },
        )
    ).json()
    assert company["message"] == "registered"
    company_id = company["company_id"]
    validated = await client.post(
        f"/api/v1/sales-strategies/{strategy['id']}/companies/{company_id}/validate"
    )
    assert validated.status_code == 200
    assert validated.json()["funnel_stage"] == "company_validated"

    prospect = (
        await client.post(
            f"/api/v1/sales-strategies/{strategy['id']}/companies/{company_id}/prospects",
            json={
                "full_name": "Ada Lovelace",
                "job_title": "VP Sales",
                "linkedin_url": "https://www.linkedin.com/in/ada-lovelace",
                "selection_reason": "Owns pipeline",
                "fit_rationale": "Matches decision-maker section",
                "confidence_score": 88,
                "evidence_urls": ["https://www.linkedin.com/in/ada-lovelace"],
            },
        )
    ).json()
    assert prospect["message"] == "registered"

    outreach = await client.patch(
        f"/api/v1/sales-strategies/{strategy['id']}/companies/{company_id}"
        f"/prospects/{prospect['prospect_profile_id']}/outreach",
        json={
            "connection_request_status": "sent",
            "received_response": True,
            "response_sentiment": "positive",
        },
    )
    assert outreach.status_code == 204
    status = await client.post(
        f"/api/v1/sales-strategies/{strategy['id']}/agents/company-finder/start"
    )
    assert status.status_code == 409


def test_nested_checkpoint_reuse_and_completion() -> None:
    thread, state = resolve_compiled_child_thread_id(
        parent_state={},
        invocation_key="General Purpose Agent",
        allocation_mode="gpa",
        effort_prefix="LOOP_p_s_1",
        parent_role_thread="LOOP_p_s_1_company_finder",
        existing_thread_ids=[],
    )
    assert thread.endswith("_GPA_1")
    reused, _ = resolve_compiled_child_thread_id(
        parent_state=state,
        invocation_key="General Purpose Agent",
        allocation_mode="gpa",
        effort_prefix="LOOP_p_s_1",
        parent_role_thread="LOOP_p_s_1_company_finder",
        existing_thread_ids=[thread],
    )
    assert reused == thread
    completed = mark_child_completed(state, "General Purpose Agent")
    assert completed["active_subagent_threads"]["General Purpose Agent"]["status"] == "completed"


def test_registration_authority_matrix() -> None:
    validate_registration_authority("company_finder", {"register_company"})
    with pytest.raises(ValueError):
        validate_registration_authority("browser_agent", {"register_company"})


@pytest.mark.asyncio
async def test_event_consumer_is_idempotent(tmp_path) -> None:
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'inbox.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        event = models.IntegrationEvent(event_type="CompanyRegistered", payload={"ok": True})
        session.add(event)
        await session.commit()
        consumer = EventConsumer(session, "progress")
        assert await consumer.handle(event) is True
        assert await consumer.handle(event) is False
    await engine.dispose()
