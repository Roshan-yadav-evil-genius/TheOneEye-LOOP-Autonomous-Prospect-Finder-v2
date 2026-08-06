from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from application.common import (
    DomainError,
    EventPublisher,
    ReentrantAsyncLock,
    normalize_linkedin_url,
    utcnow,
)
from contracts.domain import (
    BlacklistProspectRequest,
    OutreachUpdate,
    ProspectRead,
    RegisterContactRequest,
    RegistrationResult,
)
from persistence import models


class ProspectService:
    def __init__(
        self,
        session: AsyncSession,
        request_id: str | None = None,
        lock: ReentrantAsyncLock | None = None,
        company_service: Any | None = None,
    ) -> None:
        self.session = session
        self.request_id = request_id
        self._lock = lock or ReentrantAsyncLock()
        self.events = EventPublisher(session, request_id, self._lock)
        self._company_service = company_service

    @property
    def company_service(self) -> Any:
        if self._company_service is None:
            from application.company_service import CompanyService

            self._company_service = CompanyService(
                self.session, self.request_id, self._lock, prospect_service=self
            )
        return self._company_service

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

    async def contacts_registered(self, strategy_id: str, company_id: str) -> int:
        return int(
            await self.session.scalar(
                select(func.count())
                .select_from(models.SalesStrategyProspect)
                .where(
                    models.SalesStrategyProspect.sales_strategy_id == strategy_id,
                    models.SalesStrategyProspect.company_id == company_id,
                    models.SalesStrategyProspect.is_blacklisted.is_(False),
                )
            )
            or 0
        )

    async def profile_presence(
        self, strategy_id: str, linkedin_profile_url: str
    ) -> dict[str, Any]:
        canonical = normalize_linkedin_url(linkedin_profile_url)
        prospect = await self.session.scalar(
            select(models.SalesStrategyProspect)
            .join(
                models.ProspectProfile,
                models.ProspectProfile.id
                == models.SalesStrategyProspect.prospect_profile_id,
            )
            .where(
                models.SalesStrategyProspect.sales_strategy_id == strategy_id,
                models.ProspectProfile.linkedin_url == canonical,
            )
        )
        if prospect:
            return {
                "found": True,
                "source": "blacklist" if prospect.is_blacklisted else "prospect",
                "sales_strategy_prospect_id": prospect.id,
                "is_blacklisted": prospect.is_blacklisted,
                "reason": prospect.blacklist_reason,
            }
        return {"found": False, "profile_url": canonical}

    async def register_contact(
        self,
        strategy_id: str,
        company_id: str,
        data: RegisterContactRequest,
        thread_id: str | None = None,
    ) -> RegistrationResult:
        link = await self.company_service._company_link(strategy_id, company_id)
        if link.is_blacklisted or link.funnel_stage not in {
            "company_validated",
            "finding_contacts",
            "contacts_batch_done",
        }:
            raise DomainError(
                "company_not_contact_eligible", "The company must be validated and not blacklisted."
            )
        if await self.contacts_registered(strategy_id, company_id) >= link.contacts_target:
            raise DomainError(
                "contact_quota_reached", "The company contact quota has been reached."
            )
        linkedin_url = normalize_linkedin_url(data.linkedin_url)
        profile = await self.session.scalar(
            select(models.ProspectProfile).where(
                models.ProspectProfile.linkedin_url == linkedin_url
            )
        )
        global_exists = profile is not None
        if not profile:
            profile = models.ProspectProfile(
                **data.model_dump(
                    include={
                        "full_name",
                        "job_title",
                        "department",
                        "seniority",
                        "public_email",
                        "public_phone",
                        "location",
                    }
                ),
                linkedin_url=linkedin_url,
            )
            self.session.add(profile)
            await self.session.flush()
        association = await self.session.scalar(
            select(models.CompanyProspect).where(
                models.CompanyProspect.prospect_profile_id == profile.id
            )
        )
        if association:
            association.company_id = company_id
            association.active = True
        else:
            self.session.add(
                models.CompanyProspect(company_id=company_id, prospect_profile_id=profile.id)
            )
        selected = await self.session.scalar(
            select(models.SalesStrategyProspect).where(
                models.SalesStrategyProspect.sales_strategy_id == strategy_id,
                models.SalesStrategyProspect.company_id == company_id,
                models.SalesStrategyProspect.prospect_profile_id == profile.id,
            )
        )
        if selected:
            return RegistrationResult(
                prospect_profile_id=profile.id,
                sales_strategy_prospect_id=selected.id,
                message="already_in_strategy",
            )
        selected = models.SalesStrategyProspect(
            sales_strategy_id=strategy_id,
            company_id=company_id,
            prospect_profile_id=profile.id,
            selection_reason=data.selection_reason,
            fit_rationale=data.fit_rationale,
            confidence_score=data.confidence_score,
            evidence_urls=data.evidence_urls,
            discovery_thread_id=thread_id,
        )
        self.session.add(selected)
        link.contact_finder_attempt += 1
        await self.session.flush()
        count = await self.contacts_registered(strategy_id, company_id)
        link.funnel_stage = (
            "contacts_batch_done" if count >= link.contacts_target else "finding_contacts"
        )
        link.prospect_queue_status = (
            "batch_done" if count >= link.contacts_target else "in_progress"
        )
        await self._commit_event(
            action="SalesStrategyProspectSelected",
            entity_type="sales_strategy_prospect",
            entity_id=selected.id,
            after={"prospect_profile_id": profile.id, "company_id": company_id},
        )
        return RegistrationResult(
            prospect_profile_id=profile.id,
            sales_strategy_prospect_id=selected.id,
            message="already_in_db" if global_exists else "registered",
        )

    async def blacklist_prospect(
        self, strategy_id: str, company_id: str, data: BlacklistProspectRequest
    ) -> RegistrationResult:
        await self.company_service._company_link(strategy_id, company_id)
        linkedin_url = normalize_linkedin_url(data.linkedin_url)
        profile = await self.session.scalar(
            select(models.ProspectProfile).where(
                models.ProspectProfile.linkedin_url == linkedin_url
            )
        )
        if not profile:
            profile = models.ProspectProfile(
                linkedin_url=linkedin_url, full_name=data.full_name, job_title=data.job_title
            )
            self.session.add(profile)
            await self.session.flush()
        association = await self.session.scalar(
            select(models.CompanyProspect).where(
                models.CompanyProspect.prospect_profile_id == profile.id
            )
        )
        if not association:
            self.session.add(
                models.CompanyProspect(company_id=company_id, prospect_profile_id=profile.id)
            )
        selected = await self.session.scalar(
            select(models.SalesStrategyProspect).where(
                models.SalesStrategyProspect.sales_strategy_id == strategy_id,
                models.SalesStrategyProspect.company_id == company_id,
                models.SalesStrategyProspect.prospect_profile_id == profile.id,
            )
        )
        if not selected:
            selected = models.SalesStrategyProspect(
                sales_strategy_id=strategy_id,
                company_id=company_id,
                prospect_profile_id=profile.id,
                is_blacklisted=True,
                blacklist_reason=data.blacklist_reason,
                blacklisted_at=utcnow(),
                blacklisted_by="operator",
            )
            self.session.add(selected)
            await self.session.flush()
        else:
            selected.is_blacklisted = True
            selected.blacklist_reason = data.blacklist_reason
            selected.blacklisted_at = utcnow()
            selected.blacklisted_by = "operator"
        await self._commit_event(
            action="ProspectBlacklisted",
            entity_type="sales_strategy_prospect",
            entity_id=selected.id,
            after={"prospect_profile_id": profile.id},
            reason=data.blacklist_reason,
        )
        return RegistrationResult(
            prospect_profile_id=profile.id,
            sales_strategy_prospect_id=selected.id,
            message="blacklisted",
        )

    async def set_prospect_blacklist(
        self,
        strategy_id: str,
        company_id: str,
        prospect_id: str,
        *,
        blacklisted: bool,
        reason: str | None,
    ) -> None:
        row = await self.session.scalar(
            select(models.SalesStrategyProspect).where(
                models.SalesStrategyProspect.sales_strategy_id == strategy_id,
                models.SalesStrategyProspect.company_id == company_id,
                models.SalesStrategyProspect.prospect_profile_id == prospect_id,
            )
        )
        if not row:
            raise DomainError("strategy_prospect_not_found", "Prospect was not found.", 404)
        if blacklisted and not reason:
            raise DomainError("blacklist_reason_required", "A blacklist reason is required.", 422)
        row.is_blacklisted = blacklisted
        row.blacklist_reason = reason if blacklisted else None
        row.blacklisted_at = utcnow() if blacklisted else None
        row.blacklisted_by = "operator" if blacklisted else None
        await self._commit_event(
            action="ProspectBlacklisted" if blacklisted else "ProspectUnblacklisted",
            entity_type="sales_strategy_prospect",
            entity_id=row.id,
            after={"is_blacklisted": blacklisted},
            reason=reason,
        )

    async def update_outreach(
        self, strategy_id: str, company_id: str, prospect_id: str, data: OutreachUpdate
    ) -> None:
        row = await self.session.scalar(
            select(models.SalesStrategyProspect).where(
                models.SalesStrategyProspect.sales_strategy_id == strategy_id,
                models.SalesStrategyProspect.company_id == company_id,
                models.SalesStrategyProspect.prospect_profile_id == prospect_id,
            )
        )
        if not row:
            raise DomainError("strategy_prospect_not_found", "Prospect was not found.", 404)
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(row, key, value)
        row.outreach_validated_at = utcnow()
        await self._commit_event(
            action="OutreachUpdated",
            entity_type="sales_strategy_prospect",
            entity_id=row.id,
            after=data.model_dump(exclude_unset=True),
        )

    async def prospects(self, strategy_id: str, company_id: str) -> list[ProspectRead]:
        rows = (
            await self.session.execute(
                select(models.SalesStrategyProspect, models.ProspectProfile)
                .join(
                    models.ProspectProfile,
                    models.ProspectProfile.id == models.SalesStrategyProspect.prospect_profile_id,
                )
                .where(
                    models.SalesStrategyProspect.sales_strategy_id == strategy_id,
                    models.SalesStrategyProspect.company_id == company_id,
                )
            )
        ).all()
        return [
            ProspectRead(
                id=selected.id,
                prospect_profile_id=profile.id,
                full_name=profile.full_name,
                job_title=profile.job_title,
                linkedin_url=profile.linkedin_url,
                selection_reason=selected.selection_reason,
                fit_rationale=selected.fit_rationale,
                confidence_score=selected.confidence_score,
                is_blacklisted=selected.is_blacklisted,
                blacklist_reason=selected.blacklist_reason,
                connection_request_status=selected.connection_request_status,
                received_response=selected.received_response,
                response_sentiment=selected.response_sentiment,
                response_negative_reason=selected.response_negative_reason,
                discovery_thread_id=selected.discovery_thread_id,
            )
            for selected, profile in rows
        ]
