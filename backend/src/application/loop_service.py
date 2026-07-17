import re
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlparse

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from contracts.domain import (
    BlacklistProspectRequest,
    CompanyDetail,
    CompanyProfileUpdate,
    CompanySummary,
    OrganizationCreate,
    OrganizationRead,
    OutreachUpdate,
    ProductCreate,
    ProductRead,
    ProgressRead,
    ProspectRead,
    RegisterCompanyRequest,
    RegisterCompanyResult,
    RegisterContactRequest,
    RegistrationResult,
    SalesStrategyBundle,
    SalesStrategyCreate,
    SalesStrategyRead,
    ValidationResult,
)
from persistence import models


class DomainError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 409) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def utcnow() -> datetime:
    return datetime.now(UTC)


def normalize_domain(value: str) -> str:
    candidate = value.strip().lower()
    parsed = urlparse(candidate if "://" in candidate else f"https://{candidate}")
    host = (parsed.hostname or "").removeprefix("www.").rstrip(".")
    if not host or "." not in host or not re.fullmatch(r"[a-z0-9.-]+", host):
        raise DomainError("invalid_company_url", "A valid company website URL is required.", 422)
    parts = host.split(".")
    return ".".join(parts[-2:])


def normalize_linkedin_url(value: str) -> str:
    parsed = urlparse(value.strip())
    host = (parsed.hostname or "").lower().removeprefix("www.")
    parts = [part for part in parsed.path.split("/") if part]
    if host != "linkedin.com" or len(parts) < 2 or parts[0] != "in":
        raise DomainError(
            "invalid_linkedin_url", "A canonical LinkedIn /in/ profile URL is required.", 422
        )
    return f"https://www.linkedin.com/in/{parts[1].lower()}"


def _present(value: Any) -> bool:
    return value not in (None, "", [], {})


def validate_org_form(form: dict[str, Any]) -> ValidationResult:
    checks = {
        "company_overview": _present(form.get("company_overview", {}).get("description"))
        and _present(form.get("company_overview", {}).get("mission")),
        "industry": _present(form.get("industry", {}).get("primary")),
        "business_model": _present(form.get("business_model", {}).get("types")),
        "target_markets": any(
            _present(form.get("target_markets", {}).get(key))
            for key in ("countries", "regions", "industries")
        ),
        "customer_segments": _present(form.get("customer_segments", {}).get("primary")),
        "deal_constraints": any(
            _present(form.get("deal_constraints", {}).get(key))
            for key in ("min_contract_value", "excluded_industries", "geographic_limits")
        ),
        "delivery_capability": any(
            _present(form.get("delivery_capability", {}).get(key))
            for key in ("geography", "support_hours")
        ),
    }
    missing = [key for key, valid in checks.items() if not valid]
    return ValidationResult(
        valid=not missing,
        missing_sections=missing,
        completion_pct=round((len(checks) - len(missing)) / len(checks) * 100),
    )


def validate_product_form(form: dict[str, Any]) -> ValidationResult:
    icp = form.get("icp", {})
    checks = {
        "product_overview": _present(form.get("product_overview", {}).get("summary")),
        "problem_solved": _present(form.get("problem_solved", {}).get("primary")),
        "value_proposition": _present(form.get("value_proposition", {}).get("primary")),
        "icp": any(
            (
                _present(icp.get("industries", {}).get("primary")),
                _present(icp.get("company_size", {}).get("employees_min")),
                _present(icp.get("geography", {}).get("countries")),
            )
        ),
        "buyer_personas": _present(form.get("buyer_personas", {}).get("primary_titles")),
        "pricing": _present(form.get("pricing", {}).get("model"))
        and _present(form.get("pricing", {}).get("min_deal_size")),
        "customer_success_stories": len(
            [
                story
                for story in form.get("customer_success_stories", [])
                if story.get("name") or story.get("website")
            ]
        )
        >= 5,
        "differentiators": _present(form.get("differentiators")),
    }
    missing = [key for key, valid in checks.items() if not valid]
    return ValidationResult(
        valid=not missing,
        missing_sections=missing,
        completion_pct=round((len(checks) - len(missing)) / len(checks) * 100),
    )


def validate_strategy_form(form: dict[str, Any]) -> tuple[str, int, int]:
    if form.get("form_version") != "2.0":
        raise DomainError(
            "invalid_strategy_form", "New sales strategies require form_version 2.0.", 422
        )
    overview = form.get("overview", {})
    targets = form.get("run_targets", {})
    target_companies = targets.get("target_companies")
    contacts_default = targets.get("contacts_per_company_default")
    targeting = any(
        (
            form.get("priority_industries", {}).get("primary"),
            form.get("buying_signals", {}).get("selected"),
            form.get("target_company_profile", {}).get("keywords"),
        )
    )
    if not overview.get("name") or not overview.get("target_companies_narrative"):
        raise DomainError(
            "invalid_strategy_form", "Strategy name and target narrative are required.", 422
        )
    if not isinstance(target_companies, int) or target_companies <= 0:
        raise DomainError(
            "invalid_strategy_form", "target_companies must be greater than zero.", 422
        )
    if not isinstance(contacts_default, int) or contacts_default < 0:
        raise DomainError(
            "invalid_strategy_form", "contacts_per_company_default cannot be negative.", 422
        )
    if not targeting:
        raise DomainError(
            "invalid_strategy_form", "At least one targeting dimension is required.", 422
        )
    return overview["name"], target_companies, contacts_default


class LoopService:
    def __init__(self, session: AsyncSession, request_id: str | None = None) -> None:
        self.session = session
        self.request_id = request_id

    async def _commit_event(
        self,
        *,
        action: str,
        entity_type: str,
        entity_id: str,
        after: dict[str, Any],
        reason: str | None = None,
    ) -> None:
        self.session.add(
            models.AuditEvent(
                actor="operator",
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                after=after,
                reason=reason,
                request_id=self.request_id,
            )
        )
        self.session.add(
            models.IntegrationEvent(
                event_type=action,
                correlation_id=self.request_id,
                payload={"entity_type": entity_type, "entity_id": entity_id, **after},
            )
        )
        await self.session.commit()

    async def create_organization(self, data: OrganizationCreate) -> models.Organization:
        row = models.Organization(
            name=data.name,
            website=str(data.website),
            primary_contact_email=data.primary_contact_email,
            org_form=data.org_form,
        )
        self.session.add(row)
        await self.session.flush()
        await self._commit_event(
            action="OrganizationCreated",
            entity_type="organization",
            entity_id=row.id,
            after={"name": row.name},
        )
        return row

    async def get_organization(self, organization_id: str) -> models.Organization:
        row = await self.session.get(models.Organization, organization_id)
        if not row:
            raise DomainError("organization_not_found", "Organization was not found.", 404)
        return row

    async def list_organizations(self) -> list[models.Organization]:
        return list(
            (
                await self.session.scalars(
                    select(models.Organization).order_by(models.Organization.created_at.desc())
                )
            ).all()
        )

    async def validate_organization(self, organization_id: str) -> ValidationResult:
        row = await self.get_organization(organization_id)
        result = validate_org_form(row.org_form)
        row.profile_validated = result.valid
        await self._commit_event(
            action="OrganizationProfileValidated",
            entity_type="organization",
            entity_id=row.id,
            after=result.model_dump(),
        )
        return result

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
        row = await self.get_organization(organization_id)
        row.org_form = form
        row.profile_validated = False
        if name is not None:
            row.name = name
        if website is not None:
            row.website = website
        if primary_contact_email is not None:
            row.primary_contact_email = primary_contact_email or None
        if thumbnail_url is not None:
            row.thumbnail_url = thumbnail_url
        await self._commit_event(
            action="OrganizationProfileUpdated",
            entity_type="organization",
            entity_id=row.id,
            after={"name": row.name, "website": row.website},
        )
        return row

    async def create_product(self, organization_id: str, data: ProductCreate) -> models.Product:
        organization = await self.get_organization(organization_id)
        if not organization.profile_validated:
            raise DomainError(
                "organization_profile_incomplete", "Validate the organization profile first."
            )
        row = models.Product(
            organization_id=organization_id, name=data.name, kind=data.kind, icp_form=data.icp_form
        )
        self.session.add(row)
        await self.session.flush()
        await self._commit_event(
            action="ProductCreated",
            entity_type="product",
            entity_id=row.id,
            after={"name": row.name},
        )
        return row

    async def get_product(self, product_id: str) -> models.Product:
        row = await self.session.get(models.Product, product_id)
        if not row:
            raise DomainError("product_not_found", "Product was not found.", 404)
        return row

    async def list_products(self, organization_id: str) -> list[models.Product]:
        await self.get_organization(organization_id)
        return list(
            (
                await self.session.scalars(
                    select(models.Product)
                    .where(models.Product.organization_id == organization_id)
                    .order_by(models.Product.created_at.desc())
                )
            ).all()
        )

    async def validate_product(self, product_id: str) -> ValidationResult:
        row = await self.get_product(product_id)
        result = validate_product_form(row.icp_form)
        row.profile_validated = result.valid
        await self._commit_event(
            action="ProductProfileValidated",
            entity_type="product",
            entity_id=row.id,
            after=result.model_dump(),
        )
        return result

    async def update_product_profile(
        self,
        product_id: str,
        *,
        form: dict[str, Any],
        name: str | None = None,
        kind: str | None = None,
        thumbnail_url: str | None = None,
    ) -> models.Product:
        row = await self.get_product(product_id)
        row.icp_form = form
        row.profile_validated = False
        if name is not None:
            row.name = name
        if kind is not None:
            row.kind = kind
        if thumbnail_url is not None:
            row.thumbnail_url = thumbnail_url
        await self._commit_event(
            action="ProductProfileUpdated",
            entity_type="product",
            entity_id=row.id,
            after={"name": row.name, "kind": row.kind},
        )
        return row

    async def create_strategy(
        self, product_id: str, data: SalesStrategyCreate
    ) -> models.SalesStrategy:
        product = await self.get_product(product_id)
        if not product.profile_validated:
            raise DomainError("product_profile_incomplete", "Validate the product profile first.")
        name, target, contacts = validate_strategy_form(data.sales_strategy_form)
        row = models.SalesStrategy(
            product_id=product_id,
            name=name,
            sales_strategy_form=data.sales_strategy_form,
            target_companies=target,
            contacts_per_company_default=contacts,
        )
        self.session.add(row)
        await self.session.flush()
        for role in ("company-finder", "contact-finder"):
            self.session.add(models.AgentProcessState(sales_strategy_id=row.id, role=role))
            self.session.add(models.Whiteboard(sales_strategy_id=row.id, role=role))
        await self._commit_event(
            action="SalesStrategyCreated",
            entity_type="sales_strategy",
            entity_id=row.id,
            after={"name": name},
        )
        return row

    async def get_strategy(self, strategy_id: str) -> models.SalesStrategy:
        row = await self.session.get(models.SalesStrategy, strategy_id)
        if not row:
            raise DomainError("sales_strategy_not_found", "Sales strategy was not found.", 404)
        return row

    async def list_strategies(self, product_id: str) -> list[models.SalesStrategy]:
        await self.get_product(product_id)
        return list(
            (
                await self.session.scalars(
                    select(models.SalesStrategy)
                    .where(models.SalesStrategy.product_id == product_id)
                    .order_by(models.SalesStrategy.created_at.desc())
                )
            ).all()
        )

    async def update_strategy_profile(
        self,
        strategy_id: str,
        *,
        form: dict[str, Any],
        name: str | None = None,
    ) -> models.SalesStrategy:
        row = await self.get_strategy(strategy_id)
        row.sales_strategy_form = form
        if name is not None:
            row.name = name
        targets = form.get("run_targets", {})
        if "target_companies" in targets and isinstance(targets.get("target_companies"), int) and targets["target_companies"] > 0:
            row.target_companies = targets["target_companies"]
        if "contacts_per_company_default" in targets and isinstance(targets.get("contacts_per_company_default"), int) and targets["contacts_per_company_default"] >= 0:
            row.contacts_per_company_default = targets["contacts_per_company_default"]
        await self._commit_event(
            action="SalesStrategyUpdated",
            entity_type="sales_strategy",
            entity_id=row.id,
            after={"name": row.name},
        )
        return row

    async def bundle(self, strategy_id: str) -> SalesStrategyBundle:
        strategy = await self.get_strategy(strategy_id)
        product = await self.get_product(strategy.product_id)
        organization = await self.get_organization(product.organization_id)
        return SalesStrategyBundle(
            organization=OrganizationRead.model_validate(organization),
            product=ProductRead.model_validate(product),
            sales_strategy=SalesStrategyRead.model_validate(strategy),
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
        strategy = await self.get_strategy(strategy_id)
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

    async def _company_link(self, strategy_id: str, company_id: str) -> models.SalesStrategyCompany:
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
        strategy = await self.get_strategy(strategy_id)
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
        link = await self._company_link(strategy_id, company_id)
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
        await self._company_link(strategy_id, company_id)
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
            contacts_registered=await self.contacts_registered(link.sales_strategy_id, company.id),
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

    async def company_detail(self, strategy_id: str, company_id: str) -> CompanyDetail:
        link = await self._company_link(strategy_id, company_id)
        company = await self.session.get(models.Company, company_id)
        assert company
        return CompanyDetail(
            company=await self.company_summary(link),
            profile=company.profile,
            prospects=await self.prospects(strategy_id, company_id),
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
        strategy = await self.get_strategy(strategy_id)
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
