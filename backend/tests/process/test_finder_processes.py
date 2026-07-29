import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from application.loop_service import DomainError, LoopService
from application.process_service import ProcessService
from application.seed_fixtures import (
    organization_form,
    product_icp_form,
    sales_strategy_form,
)
from contracts.domain import (
    OrganizationCreate,
    ProductCreate,
    RegisterCompanyRequest,
    SalesStrategyCreate,
)
from persistence import models


async def _seed_strategy(session: AsyncSession, *, target: int = 2, contacts: int = 2) -> str:
    service = LoopService(session)
    org = await service.create_organization(
        OrganizationCreate(
            name="Test Org",
            website="https://test-org.example",
            org_form=organization_form(),
        )
    )
    row = await session.get(models.Organization, org.id)
    assert row
    row.profile_validated = True
    product = await service.create_product(
        org.id,
        ProductCreate(
            name="Test Product",
            kind="product",
            icp_form=product_icp_form(),
        ),
    )
    prod = await session.get(models.Product, product.id)
    assert prod
    prod.profile_validated = True
    strategy = await service.create_strategy(
        product.id,
        SalesStrategyCreate(
            sales_strategy_form=sales_strategy_form(
                name="Test Strategy",
                narrative="Find SaaS buyers",
                target_companies=target,
                contacts_per_company_default=contacts,
            ),
        ),
    )
    await session.commit()
    return strategy.id


@pytest.mark.asyncio
async def test_company_finder_fills_to_target_and_stops(session: AsyncSession) -> None:
    from agents.model_provider import DeterministicDiscoveryModel
    from agents.orchestration import CompanyFinderEffort

    strategy_id = await _seed_strategy(session, target=2)
    model = DeterministicDiscoveryModel(
        responses=[
            {
                "action": "register_company",
                "company": {
                    "name": "Alpha Co",
                    "website_url": "https://alpha-co.example",
                    "selection_reason": "fit",
                },
            },
            {
                "action": "register_company",
                "company": {
                    "name": "Beta Co",
                    "website_url": "https://beta-co.example",
                    "selection_reason": "fit",
                },
            },
        ]
    )

    process = ProcessService(session)
    await process.start(strategy_id, "company-finder")
    run1 = await CompanyFinderEffort(session, model).execute(strategy_id)
    run2 = await CompanyFinderEffort(session, model).execute(strategy_id)
    assert run1.company_id
    assert run2.company_id
    status = await process.status(strategy_id, "company-finder")
    assert status.desired_state == "stopped"
    assert status.actual_state == "stopped"
    progress = await LoopService(session).progress(strategy_id)
    assert progress.companies_registered == 2


@pytest.mark.asyncio
async def test_failed_effort_stays_unlinked(session: AsyncSession) -> None:
    from agents.model_provider import DeterministicDiscoveryModel
    from agents.orchestration import CompanyFinderEffort

    strategy_id = await _seed_strategy(session, target=3)
    model = DeterministicDiscoveryModel(responses=[{"action": "no_candidate"}])
    run = await CompanyFinderEffort(session, model).execute(strategy_id)
    assert run.company_id is None
    assert run.status == "completed"


@pytest.mark.asyncio
async def test_contact_finder_requires_positive_n(session: AsyncSession) -> None:
    strategy_id = await _seed_strategy(session, contacts=0)
    with pytest.raises(DomainError) as exc:
        await ProcessService(session).start(strategy_id, "contact-finder")
    assert exc.value.code == "contacts_disabled"


@pytest.mark.asyncio
async def test_contact_finder_sets_active_company_and_auto_stops(
    session: AsyncSession,
) -> None:
    from agents.model_provider import DeterministicDiscoveryModel
    from agents.orchestration import ContactFinderEffort
    from application.loop_service import utcnow

    strategy_id = await _seed_strategy(session, target=1, contacts=1)
    service = LoopService(session)
    registered = await service.register_company(
        strategy_id,
        RegisterCompanyRequest(
            name="Validated Co",
            website_url="https://validated-co.example",
            selection_reason="seed",
        ),
        thread_id="manual_thread",
    )
    link = await session.get(models.SalesStrategyCompany, registered.sales_strategy_company_id)
    assert link
    link.funnel_stage = "company_validated"
    link.validated_at = utcnow()
    link.contacts_target = 1
    await session.commit()

    model = DeterministicDiscoveryModel(
        responses=[
            {
                "action": "register_contact",
                "contact": {
                    "full_name": "Pat Buyer",
                    "job_title": "CTO",
                    "linkedin_url": "https://www.linkedin.com/in/pat-buyer",
                    "selection_reason": "decision maker",
                    "fit_rationale": "owns problem",
                    "confidence_score": 0.9,
                    "evidence_urls": ["https://www.linkedin.com/in/pat-buyer"],
                },
            }
        ]
    )
    await ProcessService(session).start(strategy_id, "contact-finder")
    run = await ContactFinderEffort(session, model).execute(strategy_id)
    assert run is not None
    assert run.sales_strategy_prospect_id
    status = await ProcessService(session).status(strategy_id, "contact-finder")
    assert status.desired_state == "stopped"
    assert status.active_company_id is None


@pytest.mark.asyncio
async def test_contact_queue_empty_auto_stops_without_error(session: AsyncSession) -> None:
    from agents.model_provider import DeterministicDiscoveryModel
    from agents.orchestration import ContactFinderEffort

    strategy_id = await _seed_strategy(session, contacts=2)
    await ProcessService(session).start(strategy_id, "contact-finder")
    result = await ContactFinderEffort(session, DeterministicDiscoveryModel()).execute(strategy_id)
    assert result is None
    status = await ProcessService(session).status(strategy_id, "contact-finder")
    assert status.desired_state == "stopped"
    assert status.actual_state == "stopped"


@pytest.mark.asyncio
async def test_effort_listing_and_detail(session: AsyncSession) -> None:
    from agents.model_provider import DeterministicDiscoveryModel
    from agents.orchestration import CompanyFinderEffort

    strategy_id = await _seed_strategy(session, target=1)
    model = DeterministicDiscoveryModel(responses=[{"action": "no_candidate"}])
    process = ProcessService(session)
    await process.start(strategy_id, "company-finder")
    run = await CompanyFinderEffort(session, model).execute(strategy_id)
    assert run is not None

    efforts = await process.list_efforts(strategy_id, role="company-finder")
    assert len(efforts) == 1
    assert efforts[0].effort_prefix == run.effort_prefix

    detail = await process.effort_detail(run.effort_prefix)
    assert detail.effort_prefix == run.effort_prefix
    assert detail.primary_thread_id == run.primary_thread_id

