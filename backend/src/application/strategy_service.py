from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from application.common import (
    DomainError,
    EventPublisher,
    ReentrantAsyncLock,
)
from application.organization_service import OrganizationService
from application.product_service import ProductService
from contracts.domain import (
    OrganizationRead,
    ProductRead,
    SalesStrategyBundle,
    SalesStrategyCreate,
    SalesStrategyRead,
)
from persistence import models


class StrategyService:
    def __init__(
        self,
        session: AsyncSession,
        request_id: str | None = None,
        lock: ReentrantAsyncLock | None = None,
        organization_service: OrganizationService | None = None,
        product_service: ProductService | None = None,
    ) -> None:
        self.session = session
        self.request_id = request_id
        self._lock = lock or ReentrantAsyncLock()
        self.events = EventPublisher(session, request_id, self._lock)
        self._organization_service = organization_service
        self._product_service = product_service

    @property
    def organization_service(self) -> OrganizationService:
        if self._organization_service is None:
            self._organization_service = OrganizationService(
                self.session, self.request_id, self._lock
            )
        return self._organization_service

    @property
    def product_service(self) -> ProductService:
        if self._product_service is None:
            self._product_service = ProductService(
                self.session,
                self.request_id,
                self._lock,
                organization_service=self.organization_service,
            )
        return self._product_service

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

    async def create_strategy(
        self, product_id: str, data: SalesStrategyCreate
    ) -> models.SalesStrategy:
        product = await self.product_service.get_product(product_id)
        form = data.sales_strategy_form or {}
        if not isinstance(form, dict):
            form = {}
        if "form_version" not in form:
            form["form_version"] = "2.0"

        overview = form.get("overview") if isinstance(form.get("overview"), dict) else {}
        name = data.name or overview.get("name") or "Untitled Sales Strategy"

        targets = form.get("run_targets") if isinstance(form.get("run_targets"), dict) else {}
        target_companies = (
            targets.get("target_companies")
            if isinstance(targets.get("target_companies"), int) and targets.get("target_companies", 0) > 0
            else 10
        )
        contacts_per_company_default = (
            targets.get("contacts_per_company_default")
            if isinstance(targets.get("contacts_per_company_default"), int)
            and targets.get("contacts_per_company_default", 0) >= 0
            else 3
        )

        row = models.SalesStrategy(
            product_id=product.id,
            name=name,
            sales_strategy_form=form,
            target_companies=target_companies,
            contacts_per_company_default=contacts_per_company_default,
            companies=[],
        )
        self.session.add(row)
        await self.session.flush()
        for role in ("company-finder", "contact-finder"):
            self.session.add(models.AgentProcessState(sales_strategy_id=row.id, role=role))
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
        await self.product_service.get_product(product_id)
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
        if (
            "target_companies" in targets
            and isinstance(targets.get("target_companies"), int)
            and targets["target_companies"] > 0
        ):
            row.target_companies = targets["target_companies"]
        if (
            "contacts_per_company_default" in targets
            and isinstance(targets.get("contacts_per_company_default"), int)
            and targets["contacts_per_company_default"] >= 0
        ):
            row.contacts_per_company_default = targets["contacts_per_company_default"]
        await self._commit_event(
            action="SalesStrategyUpdated",
            entity_type="sales_strategy",
            entity_id=row.id,
            after={"name": row.name},
        )
        return row

    async def delete_strategy(self, strategy_id: str) -> None:
        row = await self.get_strategy(strategy_id)
        if row.companies_count > 0:
            raise DomainError(
                "strategy_has_companies",
                "Cannot delete sales strategy that has registered companies.",
                400,
            )
        await self.session.delete(row)
        await self._commit_event(
            action="SalesStrategyDeleted",
            entity_type="sales_strategy",
            entity_id=strategy_id,
            after={},
        )

    async def bundle(self, strategy_id: str) -> SalesStrategyBundle:
        strategy = await self.get_strategy(strategy_id)
        product = await self.product_service.get_product(strategy.product_id)
        organization = await self.organization_service.get_organization(product.organization_id)
        return SalesStrategyBundle(
            organization=OrganizationRead.model_validate(organization),
            product=ProductRead.model_validate(product),
            sales_strategy=SalesStrategyRead.model_validate(strategy),
        )
