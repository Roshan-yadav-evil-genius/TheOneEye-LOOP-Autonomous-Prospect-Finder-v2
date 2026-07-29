from core.config import get_settings
import psycopg
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from agents.checkpoints import ThreadCheckpointStore
from application.loop_service import LoopService
from application.process_service import ProcessService
from application.chat_history_service import ThreadChatHistoryService
from contracts.domain import (
    ChatHistoryRead,
    SalesStrategyProfileUpdate,
    AgentRole,
    AgentRunSummary,
    BlacklistProspectRequest,
    BlacklistRequest,
    CompanyDetail,
    CompanyProfileUpdate,
    CompanySummary,
    EffortDetailRead,
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
    ValidationResult,
)
from persistence.database import get_session
import shutil
import uuid
import os
from fastapi import File, UploadFile, HTTPException

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


@router.delete("/organizations/{organization_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organization(organization_id: str, session: Session, request: Request) -> None:
    await service(session, request).delete_organization(organization_id)


@router.post("/orgs/{org_id}/thumbnail")
async def upload_org_thumbnail(
    org_id: str,
    file: UploadFile = File(...),
    session: Session = None,
    request: Request = None,
) -> dict[str, str]:
    svc = service(session, request)
    org = await svc.get_organization(org_id)
    
    settings = get_settings()
    upload_dir = settings.resolved_upload_dir
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    if org.thumbnail_url and org.thumbnail_url.startswith("/static/uploads/"):
        old_filename = org.thumbnail_url.split("/")[-1]
        old_file_path = upload_dir / old_filename
        if old_file_path.exists():
            old_file_path.unlink()
            
    extension = file.filename.split(".")[-1] if "." in file.filename else "bin"
    unique_filename = f"{uuid.uuid4().hex}.{extension}"
    file_path = upload_dir / unique_filename
    
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    org.thumbnail_url = f"/static/uploads/{unique_filename}"
    await session.commit()
    
    return {"url": org.thumbnail_url}


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


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(product_id: str, session: Session, request: Request) -> None:
    await service(session, request).delete_product(product_id)


@router.post("/orgs/{org_id}/products/{product_id}/thumbnail")
async def upload_product_thumbnail(
    org_id: str,
    product_id: str,
    file: UploadFile = File(...),
    session: Session = None,
    request: Request = None,
) -> dict[str, str]:
    svc = service(session, request)
    product = await svc.get_product(product_id)
    
    if product.organization_id != org_id:
        raise HTTPException(status_code=400, detail="Product does not belong to this organization")
    
    settings = get_settings()
    upload_dir = settings.resolved_upload_dir
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    if product.thumbnail_url and product.thumbnail_url.startswith("/static/uploads/"):
        old_filename = product.thumbnail_url.split("/")[-1]
        old_file_path = upload_dir / old_filename
        if old_file_path.exists():
            old_file_path.unlink()
            
    extension = file.filename.split(".")[-1] if "." in file.filename else "bin"
    unique_filename = f"{uuid.uuid4().hex}.{extension}"
    file_path = upload_dir / unique_filename
    
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    product.thumbnail_url = f"/static/uploads/{unique_filename}"
    await session.commit()
    
    return {"url": product.thumbnail_url}


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


@router.patch("/sales-strategies/{strategy_id}/strategy", response_model=SalesStrategyRead)
async def update_strategy(
    strategy_id: str, data: SalesStrategyProfileUpdate, session: Session, request: Request
) -> object:
    return await service(session, request).update_strategy_profile(
        strategy_id, form=data.form, name=data.name
    )


@router.delete("/sales-strategies/{strategy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_strategy(strategy_id: str, session: Session, request: Request) -> None:
    await service(session, request).delete_strategy(strategy_id)


@router.post("/orgs/{org_id}/products/{product_id}/sales-strategies/{strategy_id}/thumbnail")
async def upload_strategy_thumbnail(
    org_id: str,
    product_id: str,
    strategy_id: str,
    file: UploadFile = File(...),
    session: Session = None,
    request: Request = None,
) -> dict[str, str]:
    svc = service(session, request)
    strategy = await svc.get_strategy(strategy_id)
    
    if strategy.product_id != product_id:
        raise HTTPException(status_code=400, detail="Strategy does not belong to this product")
        
    product = await svc.get_product(product_id)
    if product.organization_id != org_id:
        raise HTTPException(status_code=400, detail="Product does not belong to this organization")
    
    settings = get_settings()
    upload_dir = settings.resolved_upload_dir
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    if strategy.thumbnail_url and strategy.thumbnail_url.startswith("/static/uploads/"):
        old_filename = strategy.thumbnail_url.split("/")[-1]
        old_file_path = upload_dir / old_filename
        if old_file_path.exists():
            old_file_path.unlink()
            
    extension = file.filename.split(".")[-1] if "." in file.filename else "bin"
    unique_filename = f"{uuid.uuid4().hex}.{extension}"
    file_path = upload_dir / unique_filename
    
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    strategy.thumbnail_url = f"/static/uploads/{unique_filename}"
    await session.commit()
    
    return {"url": strategy.thumbnail_url}


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





@router.get("/sales-strategies/{strategy_id}/agents/company-finder/threads", response_model=list[str])
async def company_finder_threads(strategy_id: str) -> list[str]:
    store = ThreadCheckpointStore()
    return await store.search_threads(contains=f"_{strategy_id}_", suffix="company_finder")


@router.get("/sales-strategies/{strategy_id}/agents/contact-finder/threads", response_model=list[str])
async def contact_finder_threads(strategy_id: str) -> list[str]:
    store = ThreadCheckpointStore()
    return await store.search_threads(contains=f"_{strategy_id}_", suffix="contact_finder")





@router.get("/threads", response_model=list[str])
async def global_threads() -> list[str]:
    settings = get_settings()
    conn_string = settings.resolved_threads_database_url
    
    if not conn_string:
        return []
        
    async with await psycopg.AsyncConnection.connect(conn_string) as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT DISTINCT thread_id
                FROM checkpoints
                """
            )
            rows = await cur.fetchall()
            
    return [row[0] for row in rows]

@router.get("/threads/{thread_id:path}/chat/history", response_model=ChatHistoryRead)
async def chat_history(thread_id: str) -> object:
    return await ThreadChatHistoryService.get_history(thread_id)


@router.get("/loop/strategies/{sales_strategy_id}/efforts", response_model=list[AgentRunSummary])
@router.get("/sales-strategies/{sales_strategy_id}/efforts", response_model=list[AgentRunSummary])
async def list_company_finder_efforts(
    sales_strategy_id: str, session: Session, role: str | None = None
) -> object:
    return await ProcessService(session).list_efforts(
        sales_strategy_id, role=role or "company-finder"
    )


@router.get(
    "/loop/strategies/{sales_strategy_id}/companies/{company_id}/efforts",
    response_model=list[AgentRunSummary],
)
@router.get(
    "/sales-strategies/{sales_strategy_id}/companies/{company_id}/efforts",
    response_model=list[AgentRunSummary],
)
async def list_contact_finder_efforts(
    sales_strategy_id: str, company_id: str, session: Session
) -> object:
    return await ProcessService(session).list_efforts(
        sales_strategy_id, role="contact-finder", company_id=company_id
    )


@router.get("/loop/efforts/{effort_prefix:path}", response_model=EffortDetailRead)
@router.get("/efforts/{effort_prefix:path}", response_model=EffortDetailRead)
async def get_effort_detail(effort_prefix: str, session: Session) -> object:
    return await ProcessService(session).effort_detail(effort_prefix)

