import copy
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from application.common import (
    DomainError,
    EventPublisher,
    ReentrantAsyncLock,
    validate_product_form,
)
from application.organization_service import OrganizationService
from contracts.domain import (
    ProductCreate,
    ValidationResult,
)
from persistence import models


class ProductService:
    def __init__(
        self,
        session: AsyncSession,
        request_id: str | None = None,
        lock: ReentrantAsyncLock | None = None,
        organization_service: OrganizationService | None = None,
    ) -> None:
        self.session = session
        self.request_id = request_id
        self._lock = lock or ReentrantAsyncLock()
        self.events = EventPublisher(session, request_id, self._lock)
        self._organization_service = organization_service

    @property
    def organization_service(self) -> OrganizationService:
        if self._organization_service is None:
            self._organization_service = OrganizationService(
                self.session, self.request_id, self._lock
            )
        return self._organization_service

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

    async def create_product(self, organization_id: str, data: ProductCreate) -> models.Product:
        organization = await self.organization_service.get_organization(organization_id)
        icp_form = copy.deepcopy(data.icp_form) if data.icp_form else {}
        icp_form.pop("identity", None)
        row = models.Product(
            organization_id=organization.id,
            name=data.name,
            kind=data.kind,
            icp_form=icp_form,
            sales_strategies=[],
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
        await self.organization_service.get_organization(organization_id)
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
        form = copy.deepcopy(form)
        form.pop("identity", None)
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

    async def delete_product(self, product_id: str) -> None:
        row = await self.get_product(product_id)
        if row.strategies_count > 0:
            raise DomainError(
                "product_has_strategies", "Cannot delete product that has sales strategies.", 400
            )
        await self.session.delete(row)
        await self._commit_event(
            action="ProductDeleted",
            entity_type="product",
            entity_id=product_id,
            after={},
        )
