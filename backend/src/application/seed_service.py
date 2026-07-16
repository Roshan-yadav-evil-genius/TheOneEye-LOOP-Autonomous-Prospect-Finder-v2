"""SQLite OLTP seed orchestration for local / E2E happy-path testing.

Uses ``LoopService`` / ``ProcessService`` for domain writes so invariants,
audit rows, and junction counters match production API behavior. Does not
touch PostgreSQL LangChain thread tables.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pydantic import HttpUrl
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from application.loop_service import LoopService, normalize_domain, utcnow
from application.process_service import ProcessService
from application.seed_fixtures import (
    DISTRIBUTOR_COMPANIES,
    LIGHT_COMPANIES,
    PARTIAL_COMPANIES,
    PARTIAL_CONTACTS,
    PRIMARY_COMPANIES,
    PRIMARY_COMPANY_PROFILES,
    PRIMARY_CONTACTS,
    SEED_ORG_WEBSITES,
    contacts_by_domain,
    generate_companies,
    organization_form,
    product_icp_form,
    sales_strategy_form,
)
from contracts.domain import (
    OrganizationCreate,
    OutreachUpdate,
    ProductCreate,
    RegisterCompanyRequest,
    RegisterContactRequest,
    SalesStrategyCreate,
)
from persistence import models
from persistence.database import Base, create_schema, engine


async def wipe_oltp_data() -> None:
    """Drop and recreate SQLite OLTP tables so seed matches current models."""
    from persistence import models  # noqa: F401

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)


@dataclass
class SeedSummary:
    organizations: list[dict[str, str]] = field(default_factory=list)
    products: list[dict[str, str]] = field(default_factory=list)
    strategies: list[dict[str, str]] = field(default_factory=list)
    companies: int = 0
    prospects: int = 0
    agent_runs: int = 0
    wiped: bool = False
    skipped: bool = False
    primary_strategy_id: str | None = None
    primary_org_id: str | None = None

    def as_lines(self) -> list[str]:
        lines = [
            f"wiped={self.wiped} skipped={self.skipped}",
            f"organizations={len(self.organizations)} products={len(self.products)} "
            f"strategies={len(self.strategies)}",
            f"companies={self.companies} prospects={self.prospects} agent_runs={self.agent_runs}",
        ]
        for org in self.organizations:
            lines.append(f"org {org['name']} id={org['id']}")
        for strategy in self.strategies:
            lines.append(
                f"strategy {strategy['name']} id={strategy['id']} "
                f"product={strategy['product_id']} org={strategy['organization_id']}"
            )
        if self.primary_org_id and self.primary_strategy_id:
            lines.append(
                "primary_workspace="
                f"/orgs/{self.primary_org_id}/sales-strategies/{self.primary_strategy_id}/records"
            )
        return lines


class SeedService:
    """Populate a realistic Organization → Product → Strategy hierarchy."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.loop = LoopService(session, request_id="seed")
        self.process = ProcessService(session)

    async def already_seeded(self) -> bool:
        websites = {site.rstrip("/") for site in SEED_ORG_WEBSITES}
        websites |= {f"{site}/" for site in websites}
        count = await self.session.scalar(
            select(func.count())
            .select_from(models.Organization)
            .where(models.Organization.website.in_(tuple(websites) + SEED_ORG_WEBSITES))
        )
        return int(count or 0) >= 1

    async def seed(self, *, wiped: bool = False) -> SeedSummary:
        """Populate demo data. Callers that wipe must do so before opening this session."""
        await create_schema()
        summary = SeedSummary(wiped=wiped)

        if not wiped and await self.already_seeded():
            summary.skipped = True
            await self._apply_company_profiles()
            await self._fill_existing_summary(summary)
            return summary

        northstar = await self._create_org(
            name="Northstar Analytics",
            website="https://northstar-analytics.example",
            email="ops@northstar-analytics.example",
            form=organization_form(
                company_overview={
                    "description": "Operator-led B2B prospecting software vendor",
                    "mission": "Make ICP-qualified outreach repeatable",
                }
            ),
        )
        helix = await self._create_org(
            name="Helix Robotics",
            website="https://helix-robotics.example",
            email="growth@helix-robotics.example",
            form=organization_form(
                industry={"primary": "Industrial Automation"},
                company_overview={
                    "description": "Warehouse robotics and fleet software seller",
                    "mission": "Automate mid-market fulfillment operations",
                },
            ),
        )
        summary.organizations = [
            {"id": northstar.id, "name": northstar.name},
            {"id": helix.id, "name": helix.name},
        ]
        summary.primary_org_id = northstar.id

        signal_desk = await self._create_product(
            northstar.id,
            name="Signal Desk",
            kind="product",
            form=product_icp_form(
                product_overview={"summary": "LinkedIn operator console for sales teams"}
            ),
        )
        pipeline_advisory = await self._create_product(
            northstar.id,
            name="Pipeline Advisory",
            kind="service",
            form=product_icp_form(
                product_overview={"summary": "Hands-on ICP and outreach advisory retainers"},
                pricing={"model": "retainer", "min_deal_size": "15000"},
            ),
        )
        fleet_os = await self._create_product(
            helix.id,
            name="Fleet OS",
            kind="product",
            form=product_icp_form(
                product_overview={"summary": "Fleet orchestration for warehouse robots"},
                icp={"industries": {"primary": ["Logistics", "Warehousing"]}},
                buyer_personas={"primary_titles": ["VP Operations", "Director of Automation"]},
            ),
        )
        field_kit = await self._create_product(
            helix.id,
            name="Field Service Kit",
            kind="product",
            form=product_icp_form(
                product_overview={"summary": "Field technician enablement for robot fleets"},
                buyer_personas={"primary_titles": ["Service Director", "COO"]},
            ),
        )
        summary.products = [
            {"id": p.id, "name": p.name, "organization_id": p.organization_id}
            for p in (signal_desk, pipeline_advisory, fleet_os, field_kit)
        ]

        primary = await self._create_strategy(
            signal_desk.id,
            sales_strategy_form(
                name="Mid-market SaaS CTOs Q3",
                narrative="Series B SaaS companies hiring AEs and RevOps leaders",
                target_companies=40,
                contacts_per_company_default=3,
            ),
            organization_id=northstar.id,
            summary=summary,
        )
        summary.primary_strategy_id = primary.id

        light = await self._create_strategy(
            pipeline_advisory.id,
            sales_strategy_form(
                name="Enterprise Ops Leaders",
                narrative="Ops leaders evaluating advisory retainers",
                target_companies=15,
                contacts_per_company_default=2,
            ),
            organization_id=northstar.id,
            summary=summary,
        )
        partial = await self._create_strategy(
            fleet_os.id,
            sales_strategy_form(
                name="Warehouse Automation Buyers",
                narrative="Multi-site 3PLs evaluating fleet software",
                target_companies=20,
                contacts_per_company_default=2,
                priority_industries={"primary": ["Logistics", "Warehousing"]},
            ),
            organization_id=helix.id,
            summary=summary,
        )
        distributors = await self._create_strategy(
            field_kit.id,
            sales_strategy_form(
                name="Regional Distributors",
                narrative="Regional robot distributors needing field service kits",
                target_companies=12,
                contacts_per_company_default=2,
            ),
            organization_id=helix.id,
            summary=summary,
        )

        domain_to_company = await self._seed_primary_strategy(primary.id)
        await self._seed_light_strategy(light.id)
        await self._seed_partial_strategy(partial.id)
        await self._seed_distributor_strategy(distributors.id)
        await self._apply_company_profiles()
        await self._seed_process_artifacts(primary, signal_desk, domain_to_company)
        await self._recount(summary)
        return summary

    async def _recount(self, summary: SeedSummary) -> None:
        summary.companies = int(
            await self.session.scalar(select(func.count()).select_from(models.Company)) or 0
        )
        summary.prospects = int(
            await self.session.scalar(select(func.count()).select_from(models.ProspectProfile))
            or 0
        )
        summary.agent_runs = int(
            await self.session.scalar(select(func.count()).select_from(models.AgentRun)) or 0
        )

    async def _fill_existing_summary(self, summary: SeedSummary) -> None:
        orgs = list(
            (
                await self.session.scalars(
                    select(models.Organization).order_by(models.Organization.created_at)
                )
            ).all()
        )
        summary.organizations = [{"id": org.id, "name": org.name} for org in orgs]
        products = list((await self.session.scalars(select(models.Product))).all())
        summary.products = [
            {"id": p.id, "name": p.name, "organization_id": p.organization_id} for p in products
        ]
        strategies = list((await self.session.scalars(select(models.SalesStrategy))).all())
        product_org = {p.id: p.organization_id for p in products}
        summary.strategies = [
            {
                "id": s.id,
                "name": s.name,
                "product_id": s.product_id,
                "organization_id": product_org.get(s.product_id, ""),
            }
            for s in strategies
        ]
        summary.companies = int(
            await self.session.scalar(select(func.count()).select_from(models.Company)) or 0
        )
        summary.prospects = int(
            await self.session.scalar(select(func.count()).select_from(models.ProspectProfile))
            or 0
        )
        summary.agent_runs = int(
            await self.session.scalar(select(func.count()).select_from(models.AgentRun)) or 0
        )
        if orgs and strategies:
            summary.primary_org_id = orgs[0].id
            summary.primary_strategy_id = strategies[0].id

    async def _create_org(
        self, *, name: str, website: str, email: str, form: dict[str, Any]
    ) -> models.Organization:
        org = await self.loop.create_organization(
            OrganizationCreate(
                name=name,
                website=HttpUrl(website),
                primary_contact_email=email,
                org_form=form,
            )
        )
        await self.loop.validate_organization(org.id)
        return await self.loop.get_organization(org.id)

    async def _create_product(
        self, organization_id: str, *, name: str, kind: str, form: dict[str, Any]
    ) -> models.Product:
        product = await self.loop.create_product(
            organization_id,
            ProductCreate(name=name, kind=kind, icp_form=form),  # type: ignore[arg-type]
        )
        await self.loop.validate_product(product.id)
        return await self.loop.get_product(product.id)

    async def _create_strategy(
        self,
        product_id: str,
        form: dict[str, Any],
        *,
        organization_id: str,
        summary: SeedSummary,
    ) -> models.SalesStrategy:
        strategy = await self.loop.create_strategy(
            product_id, SalesStrategyCreate(sales_strategy_form=form)
        )
        summary.strategies.append(
            {
                "id": strategy.id,
                "name": strategy.name,
                "product_id": product_id,
                "organization_id": organization_id,
            }
        )
        return strategy

    async def _apply_company_profiles(self) -> None:
        """Attach curated CompanyProfile JSON for demoable enriched company detail."""
        for domain, profile in PRIMARY_COMPANY_PROFILES.items():
            company = await self.session.scalar(
                select(models.Company).where(models.Company.domain == domain)
            )
            if company is None:
                continue
            if company.profile:
                continue
            company.profile = dict(profile)
        await self.session.commit()

    async def _register_companies(
        self, strategy_id: str, payloads: list[dict[str, str]]
    ) -> dict[str, str]:
        domain_to_id: dict[str, str] = {}
        for payload in payloads:
            result = await self.loop.register_company(
                strategy_id,
                RegisterCompanyRequest(
                    name=payload["name"],
                    website_url=payload["website_url"],
                    selection_reason=payload["selection_reason"],
                ),
            )
            domain = normalize_domain(payload["website_url"])
            domain_to_id[domain] = result.company_id
        return domain_to_id

    async def _register_contacts(
        self,
        strategy_id: str,
        company_id: str,
        contacts: list[dict[str, Any]],
    ) -> list[str]:
        prospect_ids: list[str] = []
        for contact in contacts:
            result = await self.loop.register_contact(
                strategy_id,
                company_id,
                RegisterContactRequest(**contact),
            )
            prospect_ids.append(result.prospect_profile_id)
        return prospect_ids

    async def _seed_company_cohort(
        self,
        strategy_id: str,
        companies: list[dict[str, str]],
        contacts: dict[str, list[dict[str, Any]]],
        *,
        validate_domains: set[str] | None = None,
        blacklist: dict[str, str] | None = None,
        contacts_for_domains: set[str] | None = None,
        max_contacts_per_company: int | None = None,
    ) -> dict[str, str]:
        """Register companies, optionally validate / blacklist / attach contacts."""
        domains = await self._register_companies(strategy_id, companies)
        validate_set = validate_domains if validate_domains is not None else set(domains)
        contact_set = contacts_for_domains if contacts_for_domains is not None else validate_set
        blacklist = blacklist or {}

        for domain, reason in blacklist.items():
            company_id = domains.get(domain)
            if company_id:
                await self.loop.set_company_blacklist(
                    strategy_id, company_id, blacklisted=True, reason=reason
                )

        for domain in validate_set:
            company_id = domains.get(domain)
            if not company_id or domain in blacklist:
                continue
            await self.loop.validate_company(strategy_id, company_id)

        for domain in contact_set:
            company_id = domains.get(domain)
            if not company_id or domain in blacklist:
                continue
            payload = contacts.get(domain, [])
            if max_contacts_per_company is not None:
                payload = payload[:max_contacts_per_company]
            if payload:
                await self._register_contacts(strategy_id, company_id, payload)
        return domains

    async def _seed_primary_strategy(self, strategy_id: str) -> dict[str, str]:
        curated = list(PRIMARY_COMPANIES)
        generated = generate_companies(
            28,
            prefix="saas-mid",
            reason="Generated mid-market SaaS ICP match",
        )
        all_companies = curated + generated
        generated_contacts = contacts_by_domain(
            generated, contacts_per_company=3, slug_prefix="saas-mid"
        )
        contacts = {**PRIMARY_CONTACTS, **generated_contacts}

        curated_domains = {normalize_domain(item["website_url"]) for item in curated}
        generated_domains = {normalize_domain(item["website_url"]) for item in generated}
        # Leave a few registered-only; blacklist one curated + a few generated.
        registered_only = {
            "cobalt-analytics.example",
            *sorted(generated_domains)[-3:],
        }
        blacklist = {
            "drift-commerce.example": "Wrong ICP motion after operator review",
            sorted(generated_domains)[0]: "Duplicate buying committee / already customer",
            sorted(generated_domains)[1]: "Out of geo after operator review",
        }
        validate_domains = (curated_domains | generated_domains) - registered_only - set(blacklist)
        contact_domains = validate_domains - {"cobalt-analytics.example"}

        domains = await self._seed_company_cohort(
            strategy_id,
            all_companies,
            contacts,
            validate_domains=validate_domains,
            blacklist=blacklist,
            contacts_for_domains=contact_domains,
            max_contacts_per_company=3,
        )

        acme_id = domains["acme-robotics.example"]
        acme_linkedin = PRIMARY_CONTACTS["acme-robotics.example"][0]["linkedin_url"]
        prospect = await self.session.scalar(
            select(models.ProspectProfile).where(
                models.ProspectProfile.linkedin_url == acme_linkedin
            )
        )
        if prospect:
            await self.loop.update_outreach(
                strategy_id,
                acme_id,
                prospect.id,
                OutreachUpdate(
                    connection_request_status="accepted",
                    received_response=True,
                    response_sentiment="positive",
                ),
            )
        return domains

    async def _seed_light_strategy(self, strategy_id: str) -> None:
        curated = list(LIGHT_COMPANIES)
        generated = generate_companies(
            12,
            prefix="ops-adv",
            reason="Generated enterprise ops advisory fit",
        )
        all_companies = curated + generated
        contacts = contacts_by_domain(all_companies, contacts_per_company=2, slug_prefix="ops-adv")
        domains = {normalize_domain(item["website_url"]) for item in all_companies}
        registered_only = set(sorted(domains)[-4:])
        blacklist = {sorted(domains)[0]: "Advisory conflict / competitor adjacency"}
        validate_domains = domains - registered_only - set(blacklist)
        await self._seed_company_cohort(
            strategy_id,
            all_companies,
            contacts,
            validate_domains=validate_domains,
            blacklist=blacklist,
            contacts_for_domains=validate_domains,
            max_contacts_per_company=2,
        )

    async def _seed_partial_strategy(self, strategy_id: str) -> None:
        curated = list(PARTIAL_COMPANIES)
        generated = generate_companies(
            14,
            prefix="wh-auto",
            reason="Generated warehouse automation buyer",
        )
        all_companies = curated + generated
        generated_contacts = contacts_by_domain(
            generated, contacts_per_company=2, slug_prefix="wh-auto"
        )
        contacts = {**PARTIAL_CONTACTS, **generated_contacts}
        domains = {normalize_domain(item["website_url"]) for item in all_companies}
        registered_only = {"summit-fulfillment.example", *sorted(domains)[-2:]}
        warehouse_domains = sorted(domain for domain in domains if domain.startswith("wh-auto"))
        blacklist = {warehouse_domains[0]: "Wrong facility size"}
        validate_domains = domains - registered_only - set(blacklist)
        await self._seed_company_cohort(
            strategy_id,
            all_companies,
            contacts,
            validate_domains=validate_domains,
            blacklist=blacklist,
            contacts_for_domains=validate_domains,
            max_contacts_per_company=2,
        )

    async def _seed_distributor_strategy(self, strategy_id: str) -> None:
        """Populate Field Service Kit / Regional Distributors (common Helix demo path)."""
        curated = list(DISTRIBUTOR_COMPANIES)
        generated = generate_companies(
            10,
            prefix="reg-dist",
            reason="Generated regional robot distributor ICP match",
        )
        all_companies = curated + generated
        contacts = contacts_by_domain(
            all_companies, contacts_per_company=2, slug_prefix="reg-dist"
        )
        domains = {normalize_domain(item["website_url"]) for item in all_companies}
        registered_only = set(sorted(domains)[-2:])
        blacklist = {sorted(domains)[0]: "Already exclusive for competing OEM"}
        validate_domains = domains - registered_only - set(blacklist)
        await self._seed_company_cohort(
            strategy_id,
            all_companies,
            contacts,
            validate_domains=validate_domains,
            blacklist=blacklist,
            contacts_for_domains=validate_domains,
            max_contacts_per_company=2,
        )

    async def _seed_process_artifacts(
        self,
        strategy: models.SalesStrategy,
        product: models.Product,
        domain_to_company: dict[str, str],
    ) -> None:
        acme_id = domain_to_company["acme-robotics.example"]
        await self.process.update_whiteboard(
            strategy.id,
            "company-finder",
            "Seed whiteboard: prioritize Series B SaaS with AE hiring signals.",
        )
        await self.process.update_whiteboard(
            strategy.id,
            "contact-finder",
            "Seed whiteboard: prefer CTO / VP Sales titles with budget ownership.",
        )
        self.session.add_all(
            [
                models.ProcessLog(
                    sales_strategy_id=strategy.id,
                    role="company-finder",
                    event_code="seed_ready",
                    message="Seeded company finder workspace for E2E.",
                ),
                models.ProcessLog(
                    sales_strategy_id=strategy.id,
                    role="contact-finder",
                    event_code="seed_ready",
                    message="Seeded contact finder workspace for E2E.",
                ),
                models.AgentRun(
                    product_id=product.id,
                    sales_strategy_id=strategy.id,
                    company_id=None,
                    agent_role="company_finder",
                    effort_prefix=f"LOOP_{product.id[:8]}_{strategy.id[:8]}_1",
                    primary_thread_id=f"LOOP_{product.id[:8]}_{strategy.id[:8]}_1_company_finder",
                    attempt_iteration=1,
                    status="completed",
                    completed_at=utcnow(),
                    prompt_tokens=1200,
                    completion_tokens=400,
                    estimated_cost=0.02,
                    child_thread_ids=[],
                ),
                models.AgentRun(
                    product_id=product.id,
                    sales_strategy_id=strategy.id,
                    company_id=acme_id,
                    agent_role="contact_finder",
                    effort_prefix=f"LOOP_{product.id[:8]}_{strategy.id[:8]}_{acme_id[:8]}_1",
                    primary_thread_id=(
                        f"LOOP_{product.id[:8]}_{strategy.id[:8]}_{acme_id[:8]}_1_contact_finder"
                    ),
                    attempt_iteration=1,
                    contact_attempt_iteration=1,
                    status="completed",
                    completed_at=utcnow(),
                    prompt_tokens=900,
                    completion_tokens=350,
                    estimated_cost=0.015,
                    child_thread_ids=[],
                ),
                models.BrainMemory(
                    sales_strategy_id=strategy.id,
                    agent_type="company_finder",
                    category="learning",
                    content=(
                        "Mid-market SaaS with AE hiring converts better than "
                        "pure keyword matches."
                    ),
                    terms=["saas", "ae hiring", "series b"],
                    embedding=[],
                    evidence_urls=["https://brightpath-soft.example"],
                ),
            ]
        )
        await self.session.commit()
