import copy
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from application.common import (
    DomainError,
    EventPublisher,
    ReentrantAsyncLock,
    validate_org_form,
)
from contracts.domain import (
    OrganizationCreate,
    ValidationResult,
)
from persistence import models


class OrganizationService:
    def __init__(
        self,
        session: AsyncSession,
        request_id: str | None = None,
        lock: ReentrantAsyncLock | None = None,
    ) -> None:
        self.session = session
        self.request_id = request_id
        self._lock = lock or ReentrantAsyncLock()
        self.events = EventPublisher(session, request_id, self._lock)

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

    async def create_organization(self, data: OrganizationCreate) -> models.Organization:
        org_form = copy.deepcopy(data.org_form) if data.org_form else {}
        org_form.pop("identity", None)
        row = models.Organization(
            name=data.name,
            website=str(data.website),
            primary_contact_email=data.primary_contact_email,
            org_form=org_form,
            products=[],
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
        form = copy.deepcopy(form)
        form.pop("identity", None)
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

    async def delete_organization(self, organization_id: str) -> None:
        row = await self.get_organization(organization_id)
        if row.products_count > 0:
            raise DomainError(
                "organization_has_products", "Cannot delete organization that has products.", 400
            )
        await self.session.delete(row)
        await self._commit_event(
            action="OrganizationDeleted",
            entity_type="organization",
            entity_id=organization_id,
            after={},
        )
