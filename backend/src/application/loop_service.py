from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from application.common import (
    DomainError,
    EventPublisher,
    ReentrantAsyncLock,
    normalize_domain,
    normalize_linkedin_url,
    utcnow,
    validate_org_form,
    validate_product_form,
    validate_strategy_form,
)
from application.company_service import CompanyService
from application.organization_service import OrganizationService
from application.product_service import ProductService
from application.prospect_service import ProspectService
from application.strategy_service import StrategyService
from contracts.domain import (
    BlacklistProspectRequest,
    CompanyDetail,
    CompanyProfileUpdate,
    CompanySummary,
    OrganizationCreate,
    OutreachUpdate,
    ProductCreate,
    ProgressRead,
    ProspectRead,
    RegisterCompanyRequest,
    RegisterCompanyResult,
    RegisterContactRequest,
    RegistrationResult,
    SalesStrategyBundle,
    SalesStrategyCreate,
    ValidationResult,
)
from persistence import models


__all__ = [
    "DomainError",
    "ReentrantAsyncLock",
    "utcnow",
    "normalize_domain",
    "normalize_linkedin_url",
    "validate_org_form",
    "validate_product_form",
    "validate_strategy_form",
    "EventPublisher",
    "OrganizationService",
    "ProductService",
    "StrategyService",
    "CompanyService",
    "ProspectService",
    "LoopService",
]


class LoopService:
    """Facade delegating domain operations to specialized domain services."""

    def __init__(self, session: AsyncSession, request_id: str | None = None) -> None:
        self.session = session
        self.request_id = request_id
        self._lock = ReentrantAsyncLock()

        self.organization_service = OrganizationService(session, request_id, self._lock)
        self.product_service = ProductService(
            session, request_id, self._lock, organization_service=self.organization_service
        )
        self.strategy_service = StrategyService(
            session,
            request_id,
            self._lock,
            organization_service=self.organization_service,
            product_service=self.product_service,
        )
        self.prospect_service = ProspectService(session, request_id, self._lock)
        self.company_service = CompanyService(
            session,
            request_id,
            self._lock,
            prospect_service=self.prospect_service,
            strategy_service=self.strategy_service,
        )
        self.prospect_service._company_service = self.company_service

    # Organization operations
    async def create_organization(self, data: OrganizationCreate) -> models.Organization:
        return await self.organization_service.create_organization(data)

    async def get_organization(self, organization_id: str) -> models.Organization:
        return await self.organization_service.get_organization(organization_id)

    async def list_organizations(self) -> list[models.Organization]:
        return await self.organization_service.list_organizations()

    async def validate_organization(self, organization_id: str) -> ValidationResult:
        return await self.organization_service.validate_organization(organization_id)

    async def update_organization_profile(
        self,
        organization_id: str,
        *,
        form: dict[str, Any],
        name: str | None = None,
        website: str | None = None,
        primary_contact_email: str | None = None,
        thumbnail_url: str | None = None,
    ) -> models.Organization:
        return await self.organization_service.update_organization_profile(
            organization_id,
            form=form,
            name=name,
            website=website,
            primary_contact_email=primary_contact_email,
            thumbnail_url=thumbnail_url,
        )

    async def delete_organization(self, organization_id: str) -> None:
        return await self.organization_service.delete_organization(organization_id)

    # Product operations
    async def create_product(self, organization_id: str, data: ProductCreate) -> models.Product:
        return await self.product_service.create_product(organization_id, data)

    async def get_product(self, product_id: str) -> models.Product:
        return await self.product_service.get_product(product_id)

    async def list_products(self, organization_id: str) -> list[models.Product]:
        return await self.product_service.list_products(organization_id)

    async def validate_product(self, product_id: str) -> ValidationResult:
        return await self.product_service.validate_product(product_id)

    async def update_product_profile(
        self,
        product_id: str,
        *,
        form: dict[str, Any],
        name: str | None = None,
        kind: str | None = None,
        thumbnail_url: str | None = None,
    ) -> models.Product:
        return await self.product_service.update_product_profile(
            product_id, form=form, name=name, kind=kind, thumbnail_url=thumbnail_url
        )

    async def delete_product(self, product_id: str) -> None:
        return await self.product_service.delete_product(product_id)

    # Strategy operations
    async def create_strategy(
        self, product_id: str, data: SalesStrategyCreate
    ) -> models.SalesStrategy:
        return await self.strategy_service.create_strategy(product_id, data)

    async def get_strategy(self, strategy_id: str) -> models.SalesStrategy:
        return await self.strategy_service.get_strategy(strategy_id)

    async def list_strategies(self, product_id: str) -> list[models.SalesStrategy]:
        return await self.strategy_service.list_strategies(product_id)

    async def update_strategy_profile(
        self,
        strategy_id: str,
        *,
        form: dict[str, Any],
        name: str | None = None,
    ) -> models.SalesStrategy:
        return await self.strategy_service.update_strategy_profile(
            strategy_id, form=form, name=name
        )

    async def delete_strategy(self, strategy_id: str) -> None:
        return await self.strategy_service.delete_strategy(strategy_id)

    async def bundle(self, strategy_id: str) -> SalesStrategyBundle:
        return await self.strategy_service.bundle(strategy_id)

    # Company operations
    async def _company_count(self, strategy_id: str) -> int:
        return await self.company_service._company_count(strategy_id)

    async def register_company(
        self, strategy_id: str, data: RegisterCompanyRequest, thread_id: str | None = None
    ) -> RegisterCompanyResult:
        return await self.company_service.register_company(strategy_id, data, thread_id)

    async def _company_link(self, strategy_id: str, company_id: str) -> models.SalesStrategyCompany:
        return await self.company_service._company_link(strategy_id, company_id)

    async def validate_company(self, strategy_id: str, company_id: str) -> CompanySummary:
        return await self.company_service.validate_company(strategy_id, company_id)

    async def set_company_blacklist(
        self, strategy_id: str, company_id: str, *, blacklisted: bool, reason: str | None
    ) -> CompanySummary:
        return await self.company_service.set_company_blacklist(
            strategy_id, company_id, blacklisted=blacklisted, reason=reason
        )

    async def companies_registered(self, strategy_id: str) -> int:
        return await self.company_service.companies_registered(strategy_id)

    async def company_summary(self, link: models.SalesStrategyCompany) -> CompanySummary:
        return await self.company_service.company_summary(link)

    async def records(self, strategy_id: str) -> list[CompanySummary]:
        return await self.company_service.records(strategy_id)

    async def company_detail(self, strategy_id: str, company_id: str) -> CompanyDetail:
        return await self.company_service.company_detail(strategy_id, company_id)

    async def update_company_profile(
        self, strategy_id: str, company_id: str, data: CompanyProfileUpdate
    ) -> CompanyDetail:
        return await self.company_service.update_company_profile(strategy_id, company_id, data)

    async def progress(self, strategy_id: str) -> ProgressRead:
        return await self.company_service.progress(strategy_id)

    # Prospect operations
    async def contacts_registered(self, strategy_id: str, company_id: str) -> int:
        return await self.prospect_service.contacts_registered(strategy_id, company_id)

    async def profile_presence(
        self, strategy_id: str, linkedin_profile_url: str
    ) -> dict[str, Any]:
        return await self.prospect_service.profile_presence(strategy_id, linkedin_profile_url)

    async def register_contact(
        self,
        strategy_id: str,
        company_id: str,
        data: RegisterContactRequest,
        thread_id: str | None = None,
    ) -> RegistrationResult:
        return await self.prospect_service.register_contact(strategy_id, company_id, data, thread_id)

    async def blacklist_prospect(
        self, strategy_id: str, company_id: str, data: BlacklistProspectRequest
    ) -> RegistrationResult:
        return await self.prospect_service.blacklist_prospect(strategy_id, company_id, data)

    async def set_prospect_blacklist(
        self,
        strategy_id: str,
        company_id: str,
        prospect_id: str,
        *,
        blacklisted: bool,
        reason: str | None,
    ) -> None:
        return await self.prospect_service.set_prospect_blacklist(
            strategy_id, company_id, prospect_id, blacklisted=blacklisted, reason=reason
        )

    async def update_outreach(
        self, strategy_id: str, company_id: str, prospect_id: str, data: OutreachUpdate
    ) -> None:
        return await self.prospect_service.update_outreach(strategy_id, company_id, prospect_id, data)

    async def prospects(self, strategy_id: str, company_id: str) -> list[ProspectRead]:
        return await self.prospect_service.prospects(strategy_id, company_id)
