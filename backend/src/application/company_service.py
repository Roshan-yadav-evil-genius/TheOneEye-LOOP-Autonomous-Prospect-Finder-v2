from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from application.common import (
    DomainError,
    EventPublisher,
    ReentrantAsyncLock,
    normalize_domain,
    utcnow,
)
from application.prospect_service import ProspectService
from application.strategy_service import StrategyService
from contracts.domain import (
    CompanyDetail,
    CompanyProfileUpdate,
    CompanySummary,
    ProgressRead,
    RegisterCompanyRequest,
    RegisterCompanyResult,
)
from persistence import models


class CompanyService:
    def __init__(
        self,
        session: AsyncSession,
        request_id: str | None = None,
        lock: ReentrantAsyncLock | None = None,
        prospect_service: ProspectService | None = None,
        strategy_service: StrategyService | None = None,
    ) -> None:
        self.session = session
        self.request_id = request_id
        self._lock = lock or ReentrantAsyncLock()
        self.events = EventPublisher(session, request_id, self._lock)
        self._prospect_service = prospect_service
        self._strategy_service = strategy_service

    @property
    def prospect_service(self) -> ProspectService:
        if self._prospect_service is None:
            self._prospect_service = ProspectService(
                self.session, self.request_id, self._lock, company_service=self
            )
        return self._prospect_service

    @property
    def strategy_service(self) -> StrategyService:
        if self._strategy_service is None:
            self._strategy_service = StrategyService(
                self.session, self.request_id, self._lock
            )
        return self._strategy_service

    async def _commit_event(
        self,
        *,
        action: str,
        entity_type: str,
        entity_id: str,
        after: dict[str, Any],
        reason: str | None = None,
    ) -> None:
        await self.events.commit_event(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            after=after,
            reason=reason,
        )

    async def _company_count(self, strategy_id: str) -> int:
        return int(
            await self.session.scalar(
                select(func.count())
                .select_from(models.SalesStrategyCompany)
                .where(
                    models.SalesStrategyCompany.sales_strategy_id == strategy_id,
                    models.SalesStrategyCompany.is_blacklisted.is_(False),
                )
            )
            or 0
        )

    async def register_company(
        self, strategy_id: str, data: RegisterCompanyRequest, thread_id: str | None = None
    ) -> RegisterCompanyResult:
        strategy = await self.strategy_service.get_strategy(strategy_id)
        domain = normalize_domain(data.website_url)
        company = await self.session.scalar(
            select(models.Company).where(models.Company.domain == domain)
        )
        global_exists = company is not None
        if not company:
            company = models.Company(name=data.name, domain=domain)
            self.session.add(company)
            await self.session.flush()
        link = await self.session.scalar(
            select(models.SalesStrategyCompany).where(
                models.SalesStrategyCompany.sales_strategy_id == strategy_id,
                models.SalesStrategyCompany.company_id == company.id,
            )
        )
        if link:
            return RegisterCompanyResult(
                company_id=company.id,
                sales_strategy_company_id=link.id,
                message="already_in_strategy",
            )
        if await self._company_count(strategy_id) >= strategy.target_companies:
            raise DomainError(
                "company_quota_reached", "The strategy company target has been reached."
            )
        strategy.company_finder_attempt += 1
        link = models.SalesStrategyCompany(
            sales_strategy_id=strategy_id,
            company_id=company.id,
            selection_reason=data.selection_reason,
            sales_strategy_attempt_at_register=strategy.company_finder_attempt,
            discovery_thread_id=thread_id,
        )
        self.session.add(link)
        await self.session.flush()
        await self._commit_event(
            action="SalesStrategyCompanySelected",
            entity_type="sales_strategy_company",
            entity_id=link.id,
            after={"company_id": company.id, "domain": domain},
        )
        return RegisterCompanyResult(
            company_id=company.id,
            sales_strategy_company_id=link.id,
            message="already_in_db" if global_exists else "registered",
        )

    async def _company_link(
        self, strategy_id: str, company_id: str
    ) -> models.SalesStrategyCompany:
        link = await self.session.scalar(
            select(models.SalesStrategyCompany).where(
                models.SalesStrategyCompany.sales_strategy_id == strategy_id,
                models.SalesStrategyCompany.company_id == company_id,
            )
        )
        if not link:
            raise DomainError(
                "strategy_company_not_found", "Company is not linked to this strategy.", 404
            )
        return link

    async def validate_company(self, strategy_id: str, company_id: str) -> CompanySummary:
        strategy = await self.strategy_service.get_strategy(strategy_id)
        link = await self._company_link(strategy_id, company_id)
        if link.is_blacklisted:
            raise DomainError(
                "company_blacklisted", "Unblacklist the company before validating it."
            )
        if strategy.contacts_per_company_default <= 0:
            raise DomainError("contacts_disabled", "This strategy has no contact quota.")
        link.funnel_stage = "company_validated"
        link.contacts_target = strategy.contacts_per_company_default
        link.prospect_queue_status = "queued"
        link.validated_at = utcnow()
        await self._commit_event(
            action="CompanyValidated",
            entity_type="sales_strategy_company",
            entity_id=link.id,
            after={},
        )
        return await self.company_summary(link)

    async def set_company_blacklist(
        self, strategy_id: str, company_id: str, *, blacklisted: bool, reason: str | None
    ) -> CompanySummary:
        link = await self._company_link(strategy_id, company_id)
        if blacklisted and not reason:
            raise DomainError("blacklist_reason_required", "A blacklist reason is required.", 422)
        link.is_blacklisted = blacklisted
        link.blacklist_reason = reason if blacklisted else None
        link.blacklisted_at = utcnow() if blacklisted else None
        link.blacklisted_by = "operator" if blacklisted else None
        await self._commit_event(
            action="CompanyBlacklisted" if blacklisted else "CompanyUnblacklisted",
            entity_type="sales_strategy_company",
            entity_id=link.id,
            after={"is_blacklisted": blacklisted},
            reason=reason,
        )
        return await self.company_summary(link)

    async def companies_registered(self, strategy_id: str) -> int:
        return int(
            await self.session.scalar(
                select(func.count())
                .select_from(models.SalesStrategyCompany)
                .where(
                    models.SalesStrategyCompany.sales_strategy_id == strategy_id,
                    models.SalesStrategyCompany.is_blacklisted.is_(False),
                )
            )
            or 0
        )

    async def company_summary(self, link: models.SalesStrategyCompany) -> CompanySummary:
        company = await self.session.get(models.Company, link.company_id)
        assert company
        return CompanySummary(
            id=link.id,
            company_id=company.id,
            name=company.name,
            domain=company.domain,
            selection_reason=link.selection_reason,
            funnel_stage=link.funnel_stage,
            prospect_queue_status=link.prospect_queue_status,
            contacts_target=link.contacts_target,
            contacts_registered=await self.prospect_service.contacts_registered(
                link.sales_strategy_id, company.id
            ),
            is_blacklisted=link.is_blacklisted,
            blacklist_reason=link.blacklist_reason,
            discovery_thread_id=link.discovery_thread_id,
        )

    async def records(self, strategy_id: str) -> list[CompanySummary]:
        links = (
            await self.session.scalars(
                select(models.SalesStrategyCompany)
                .where(models.SalesStrategyCompany.sales_strategy_id == strategy_id)
                .order_by(models.SalesStrategyCompany.created_at.desc())
            )
        ).all()
        return [await self.company_summary(link) for link in links]

    async def company_detail(self, strategy_id: str, company_id: str) -> CompanyDetail:
        link = await self._company_link(strategy_id, company_id)
        company = await self.session.get(models.Company, company_id)
        assert company
        return CompanyDetail(
            company=await self.company_summary(link),
            profile=company.profile,
            prospects=await self.prospect_service.prospects(strategy_id, company_id),
        )

    async def update_company_profile(
        self, strategy_id: str, company_id: str, data: CompanyProfileUpdate
    ) -> CompanyDetail:
        await self._company_link(strategy_id, company_id)
        company = await self.session.get(models.Company, company_id)
        if not company:
            raise DomainError("company_not_found", "Company was not found.", 404)
        company.profile = data.profile
        await self._commit_event(
            action="CompanyProfileUpdated",
            entity_type="company",
            entity_id=company.id,
            after={"profile_keys": sorted(data.profile.keys())},
        )
        return await self.company_detail(strategy_id, company_id)

    async def progress(self, strategy_id: str) -> ProgressRead:
        strategy = await self.strategy_service.get_strategy(strategy_id)
        records = await self.records(strategy_id)
        return ProgressRead(
            companies_registered=sum(not item.is_blacklisted for item in records),
            target_companies=strategy.target_companies,
            companies_validated=sum(
                item.funnel_stage != "registered" and not item.is_blacklisted for item in records
            ),
            contacts_registered=sum(item.contacts_registered for item in records),
            contacts_target=sum(
                item.contacts_target for item in records if not item.is_blacklisted
            ),
        )
