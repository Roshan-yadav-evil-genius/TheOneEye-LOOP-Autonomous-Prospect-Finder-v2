from typing import Any, Literal

from langchain_core.tools import BaseTool, StructuredTool, tool
from sqlalchemy.ext.asyncio import AsyncSession

from application.loop_service import LoopService
from contracts.domain import (
    BlacklistProspectRequest,
    RegisterCompanyRequest,
    RegisterContactRequest,
)

# Note: Tool permissions across modes (plan, evaluate, execute, record) are enforced dynamically
# by PlannerModeMiddleware rather than static wrapper functions.




def _sanitize_sales_strategy_dict(data: dict[str, Any]) -> dict[str, Any]:
    for key in (
        "run_targets",
        "target_companies",
        "contacts_per_company_default",
        "company_finder_attempt",
        "companies_count",
    ):
        data.pop(key, None)
    if "sales_strategy_form" in data and isinstance(data["sales_strategy_form"], dict):
        data["sales_strategy_form"].pop("run_targets", None)
    return data


def get_register_company_tool(
    session: AsyncSession, strategy_id: str, thread_id: str
) -> list[BaseTool]:
    service = LoopService(session)

    @tool
    async def register_company(
        name: str,
        website_url: str,
        selection_reason: str,
    ) -> dict[str, Any]:
        """Register one evidence-backed company; Company Finder is sole authority."""
        from urllib.parse import urlparse

        host = urlparse(
            website_url if "://" in website_url else f"https://{website_url}"
        ).hostname
        if not host:
            raise ValueError("website_url must be a real observed company URL.")
        result = await service.register_company(
            strategy_id,
            RegisterCompanyRequest(
                name=name,
                website_url=website_url,
                selection_reason=selection_reason,
            ),
            thread_id=thread_id,
        )
        return result.model_dump(mode="json")

    return [register_company]


from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional
from persistence.database import SessionFactory


@asynccontextmanager
async def _get_db_session(provided_session: Optional[AsyncSession]) -> AsyncIterator[AsyncSession]:
    if provided_session is not None:
        yield provided_session
    else:
        async with SessionFactory() as db_session:
            yield db_session


def sales_manager_tools(
    session: Optional[AsyncSession], strategy_id: str
) -> list[BaseTool]:
    @tool
    async def get_org() -> dict[str, Any]:
        """Read the organization overview, mission, business model, and deal constraints."""
        async with _get_db_session(session) as db_session:
            service = LoopService(db_session)
            bundle = await service.bundle(strategy_id)
            return bundle.organization.model_dump(mode="json")

    @tool
    async def get_product() -> dict[str, Any]:
        """Read product details, value proposition, pricing, and ICP forms."""
        async with _get_db_session(session) as db_session:
            service = LoopService(db_session)
            bundle = await service.bundle(strategy_id)
            return bundle.product.model_dump(mode="json")

    @tool
    async def get_sales_strategy() -> dict[str, Any]:
        """Read active sales strategy targeting rules, narratives, and target quotas."""
        async with _get_db_session(session) as db_session:
            service = LoopService(db_session)
            bundle = await service.bundle(strategy_id)
            return _sanitize_sales_strategy_dict(bundle.sales_strategy.model_dump(mode="json"))

    return [get_org, get_product, get_sales_strategy]




def contact_finder_tools(
    session: AsyncSession, strategy_id: str, company_id: str, thread_id: str
) -> list[BaseTool]:
    service = LoopService(session)

    @tool
    async def get_sales_strategy_bundle() -> dict[str, Any]:
        """Read immutable sales context and targeting rules."""
        return (await service.bundle(strategy_id)).model_dump(mode="json")

    @tool
    async def get_company() -> dict[str, Any]:
        """Read the assigned company and its current contact queue."""
        return (await service.company_detail(strategy_id, company_id)).model_dump(
            mode="json"
        )

    @tool
    async def is_profile_present(linkedin_url: str) -> dict[str, Any]:
        """Check canonical profile presence before visiting or registering."""
        return await service.profile_presence(strategy_id, linkedin_url)

    @tool
    async def register_contact(
        full_name: str,
        job_title: str,
        linkedin_url: str,
        selection_reason: str,
        fit_rationale: str,
        confidence_score: float,
        department: str | None = None,
        seniority: str | None = None,
        public_email: str | None = None,
        public_phone: str | None = None,
        location: str | None = None,
        evidence_urls: list[str] | None = None,
    ) -> dict[str, Any]:
        """Register one verified decision maker; Contact Finder is sole authority."""
        from urllib.parse import urlparse

        urls = evidence_urls or []
        for url in [linkedin_url, *urls]:
            host = urlparse(url if "://" in url else f"https://{url}").hostname
            if not host:
                raise ValueError("Invented or invalid URLs are rejected; use observed evidence only.")
        result = await service.register_contact(
            strategy_id,
            company_id,
            RegisterContactRequest(
                full_name=full_name,
                job_title=job_title,
                linkedin_url=linkedin_url,
                selection_reason=selection_reason,
                fit_rationale=fit_rationale,
                confidence_score=confidence_score,
                department=department,
                seniority=seniority,
                public_email=public_email,
                public_phone=public_phone,
                location=location,
                evidence_urls=evidence_urls or [],
            ),
            thread_id=thread_id,
        )
        return result.model_dump(mode="json")

    @tool
    async def blacklist_prospect(
        linkedin_url: str,
        blacklist_reason: str,
        full_name: str | None = None,
        job_title: str | None = None,
    ) -> dict[str, Any]:
        """Persist a wrong-fit observed profile so future efforts skip it."""
        result = await service.blacklist_prospect(
            strategy_id,
            company_id,
            BlacklistProspectRequest(
                linkedin_url=linkedin_url,
                blacklist_reason=blacklist_reason,
                full_name=full_name,
                job_title=job_title,
            ),
        )
        return result.model_dump(mode="json")

    return [
        get_sales_strategy_bundle,
        get_company,
        is_profile_present,
        register_contact,
        blacklist_prospect,
    ]
