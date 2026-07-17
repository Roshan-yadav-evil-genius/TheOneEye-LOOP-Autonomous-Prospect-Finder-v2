from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from agents.checkpoints import ThreadCheckpointStore
from application.loop_service import LoopService
from application.process_service import ProcessService
from contracts.domain import (
    AgentRole,
    AgentRunSummary,
    BlacklistProspectRequest,
    BlacklistRequest,
    CompanyDetail,
    CompanyProfileUpdate,
    CompanySummary,
    OrganizationCreate,
    OrganizationProfileUpdate,
    OrganizationRead,
    OutreachUpdate,
    ProcessStatus,
    ProductCreate,
    ProductProfileUpdate,
    ProductRead,
    ProgressRead,
    RegisterCompanyRequest,
    RegisterCompanyResult,
    RegisterContactRequest,
    RegistrationResult,
    SalesStrategyBundle,
    SalesStrategyCreate,
    SalesStrategyRead,
    ThreadSnapshot,
    ValidationResult,
    WhiteboardRead,
    WhiteboardUpdate,
)
from persistence.database import get_session

router = APIRouter(prefix="/api/v1", tags=["loop"])
Session = Annotated[AsyncSession, Depends(get_session)]


def service(session: AsyncSession, request: Request) -> LoopService:
    return LoopService(session, getattr(request.state, "request_id", None))


@router.post("/organizations", response_model=OrganizationRead, status_code=status.HTTP_201_CREATED)
async def create_organization(
    data: OrganizationCreate, session: Session, request: Request
) -> object:
    return await service(session, request).create_organization(data)


@router.get("/organizations", response_model=list[OrganizationRead])
async def list_organizations(session: Session, request: Request) -> object:
    return await service(session, request).list_organizations()


@router.get("/organizations/{organization_id}", response_model=OrganizationRead)
async def get_organization(organization_id: str, session: Session, request: Request) -> object:
    return await service(session, request).get_organization(organization_id)


@router.get("/organizations/{organization_id}/profile", response_model=OrganizationRead)
async def get_organization_profile(
    organization_id: str, session: Session, request: Request
) -> object:
    return await service(session, request).get_organization(organization_id)


@router.patch("/organizations/{organization_id}/profile", response_model=OrganizationRead)
async def update_organization_profile(
    organization_id: str, data: OrganizationProfileUpdate, session: Session, request: Request
) -> object:
    return await service(session, request).update_organization_profile(
        organization_id,
        form=data.form,
        name=data.name,
        website=str(data.website) if data.website is not None else None,
        primary_contact_email=data.primary_contact_email,
        thumbnail_url=data.thumbnail_url,
    )


@router.post("/organizations/{organization_id}/profile/validate", response_model=ValidationResult)
async def validate_organization(organization_id: str, session: Session, request: Request) -> object:
    return await service(session, request).validate_organization(organization_id)


@router.post(
    "/organizations/{organization_id}/products",
    response_model=ProductRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_product(
    organization_id: str, data: ProductCreate, session: Session, request: Request
) -> object:
    return await service(session, request).create_product(organization_id, data)


@router.get(
    "/organizations/{organization_id}/products",
    response_model=list[ProductRead],
)
async def list_products(
    organization_id: str, session: Session, request: Request
) -> object:
    return await service(session, request).list_products(organization_id)


@router.get("/products/{product_id}", response_model=ProductRead)
async def get_product(product_id: str, session: Session, request: Request) -> object:
    return await service(session, request).get_product(product_id)


@router.get("/products/{product_id}/profile", response_model=ProductRead)
async def get_product_profile(product_id: str, session: Session, request: Request) -> object:
    return await service(session, request).get_product(product_id)


@router.patch("/products/{product_id}/profile", response_model=ProductRead)
async def update_product_profile(
    product_id: str, data: ProductProfileUpdate, session: Session, request: Request
) -> object:
    return await service(session, request).update_product_profile(
        product_id,
        form=data.form,
        name=data.name,
        kind=data.kind,
        thumbnail_url=data.thumbnail_url,
    )


@router.post("/products/{product_id}/profile/validate", response_model=ValidationResult)
async def validate_product(product_id: str, session: Session, request: Request) -> object:
    return await service(session, request).validate_product(product_id)


@router.post(
    "/products/{product_id}/sales-strategies",
    response_model=SalesStrategyRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_strategy(
    product_id: str, data: SalesStrategyCreate, session: Session, request: Request
) -> object:
    return await service(session, request).create_strategy(product_id, data)


@router.get(
    "/products/{product_id}/sales-strategies",
    response_model=list[SalesStrategyRead],
)
async def list_strategies(
    product_id: str, session: Session, request: Request
) -> object:
    return await service(session, request).list_strategies(product_id)


@router.get("/sales-strategies/{strategy_id}/strategy", response_model=SalesStrategyRead)
async def get_strategy(strategy_id: str, session: Session, request: Request) -> object:
    return await service(session, request).get_strategy(strategy_id)


@router.patch("/sales-strategies/{strategy_id}/strategy", status_code=status.HTTP_409_CONFLICT)
async def immutable_strategy(strategy_id: str) -> None:
    del strategy_id
    from application.loop_service import DomainError

    raise DomainError("strategy_immutable", "Sales strategy forms are immutable after creation.")


@router.get("/sales-strategies/{strategy_id}/bundle", response_model=SalesStrategyBundle)
async def get_bundle(strategy_id: str, session: Session, request: Request) -> object:
    return await service(session, request).bundle(strategy_id)


@router.get("/sales-strategies/{strategy_id}/companies", response_model=list[CompanySummary])
async def records(strategy_id: str, session: Session, request: Request) -> object:
    return await service(session, request).records(strategy_id)


@router.post("/sales-strategies/{strategy_id}/companies", response_model=RegisterCompanyResult)
async def register_company(
    strategy_id: str, data: RegisterCompanyRequest, session: Session, request: Request
) -> object:
    return await service(session, request).register_company(strategy_id, data)


@router.get("/sales-strategies/{strategy_id}/companies/{company_id}", response_model=CompanyDetail)
async def company_detail(
    strategy_id: str, company_id: str, session: Session, request: Request
) -> object:
    return await service(session, request).company_detail(strategy_id, company_id)


@router.patch("/sales-strategies/{strategy_id}/companies/{company_id}/profile", response_model=CompanyDetail)
async def update_company_profile(
    strategy_id: str,
    company_id: str,
    data: CompanyProfileUpdate,
    session: Session,
    request: Request,
) -> object:
    return await service(session, request).update_company_profile(strategy_id, company_id, data)


@router.post(
    "/sales-strategies/{strategy_id}/companies/{company_id}/validate",
    response_model=CompanySummary,
)
async def validate_company(
    strategy_id: str, company_id: str, session: Session, request: Request
) -> object:
    return await service(session, request).validate_company(strategy_id, company_id)


@router.post(
    "/sales-strategies/{strategy_id}/companies/{company_id}/blacklist",
    response_model=CompanySummary,
)
async def blacklist_company(
    strategy_id: str,
    company_id: str,
    data: BlacklistRequest,
    session: Session,
    request: Request,
) -> object:
    return await service(session, request).set_company_blacklist(
        strategy_id, company_id, blacklisted=True, reason=data.blacklist_reason
    )


@router.post(
    "/sales-strategies/{strategy_id}/companies/{company_id}/unblacklist",
    response_model=CompanySummary,
)
async def unblacklist_company(
    strategy_id: str, company_id: str, session: Session, request: Request
) -> object:
    return await service(session, request).set_company_blacklist(
        strategy_id, company_id, blacklisted=False, reason=None
    )


@router.post(
    "/sales-strategies/{strategy_id}/companies/{company_id}/prospects",
    response_model=RegistrationResult,
)
async def register_contact(
    strategy_id: str,
    company_id: str,
    data: RegisterContactRequest,
    session: Session,
    request: Request,
) -> object:
    return await service(session, request).register_contact(strategy_id, company_id, data)


@router.post(
    "/sales-strategies/{strategy_id}/companies/{company_id}/prospects/blacklist",
    response_model=RegistrationResult,
)
async def sparse_blacklist_prospect(
    strategy_id: str,
    company_id: str,
    data: BlacklistProspectRequest,
    session: Session,
    request: Request,
) -> object:
    return await service(session, request).blacklist_prospect(strategy_id, company_id, data)


@router.post(
    "/sales-strategies/{strategy_id}/companies/{company_id}/prospects/{prospect_id}/blacklist",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def blacklist_prospect(
    strategy_id: str,
    company_id: str,
    prospect_id: str,
    data: BlacklistRequest,
    session: Session,
    request: Request,
) -> None:
    await service(session, request).set_prospect_blacklist(
        strategy_id, company_id, prospect_id, blacklisted=True, reason=data.blacklist_reason
    )


@router.post(
    "/sales-strategies/{strategy_id}/companies/{company_id}/prospects/{prospect_id}/unblacklist",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def unblacklist_prospect(
    strategy_id: str,
    company_id: str,
    prospect_id: str,
    session: Session,
    request: Request,
) -> None:
    await service(session, request).set_prospect_blacklist(
        strategy_id, company_id, prospect_id, blacklisted=False, reason=None
    )


@router.patch(
    "/sales-strategies/{strategy_id}/companies/{company_id}/prospects/{prospect_id}/outreach",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def update_outreach(
    strategy_id: str,
    company_id: str,
    prospect_id: str,
    data: OutreachUpdate,
    session: Session,
    request: Request,
) -> None:
    await service(session, request).update_outreach(strategy_id, company_id, prospect_id, data)


@router.get("/sales-strategies/{strategy_id}/progress", response_model=ProgressRead)
async def progress(strategy_id: str, session: Session, request: Request) -> object:
    return await service(session, request).progress(strategy_id)


@router.post("/sales-strategies/{strategy_id}/agents/{role}/start", response_model=ProcessStatus)
async def start_process(strategy_id: str, role: AgentRole, session: Session) -> object:
    return await ProcessService(session).start(strategy_id, role)


@router.post("/sales-strategies/{strategy_id}/agents/{role}/stop", response_model=ProcessStatus)
async def stop_process(strategy_id: str, role: AgentRole, session: Session) -> object:
    return await ProcessService(session).stop(strategy_id, role)


@router.get("/sales-strategies/{strategy_id}/agents/{role}/status", response_model=ProcessStatus)
async def process_status(strategy_id: str, role: AgentRole, session: Session) -> object:
    return await ProcessService(session).status(strategy_id, role)


@router.get(
    "/sales-strategies/{strategy_id}/agents/{role}/whiteboard", response_model=WhiteboardRead
)
async def whiteboard(strategy_id: str, role: AgentRole, session: Session) -> object:
    return await ProcessService(session).whiteboard(strategy_id, role)


@router.patch(
    "/sales-strategies/{strategy_id}/agents/{role}/whiteboard", response_model=WhiteboardRead
)
async def update_whiteboard(
    strategy_id: str, role: AgentRole, data: WhiteboardUpdate, session: Session
) -> object:
    return await ProcessService(session).update_whiteboard(strategy_id, role, data.content)


@router.get("/sales-strategies/{strategy_id}/threads", response_model=list[AgentRunSummary])
async def threads(strategy_id: str, session: Session) -> object:
    return await ProcessService(session).threads(strategy_id)


@router.get(
    "/sales-strategies/{strategy_id}/snapshots/{thread_id:path}", response_model=ThreadSnapshot
)
async def snapshot(strategy_id: str, thread_id: str, session: Session) -> ThreadSnapshot:
    runs = await ProcessService(session).threads(strategy_id)
    run = next(
        (
            item
            for item in runs
            if thread_id == item.primary_thread_id
            or thread_id in item.child_thread_ids
            or thread_id.startswith(f"{item.primary_thread_id}_GPA_")
        ),
        None,
    )
    if not run:
        from application.loop_service import DomainError

        raise DomainError("thread_not_found", "Thread was not found for this strategy.", 404)
    store = ThreadCheckpointStore()
    available = await store.list_threads(run.effort_prefix)
    state = await store.latest(thread_id)
    return ThreadSnapshot(
        thread_id=thread_id,
        effort_prefix=run.effort_prefix,
        available_threads=available,
        state=state,
        checkpoint_backend="postgresql" if store.database_url else "unavailable",
    )
