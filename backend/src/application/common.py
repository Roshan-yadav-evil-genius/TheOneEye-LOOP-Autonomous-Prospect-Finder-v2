import asyncio
import re
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlparse

from sqlalchemy.ext.asyncio import AsyncSession

from contracts.domain import ValidationResult
from persistence import models


class DomainError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 409) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class ReentrantAsyncLock:
    """Task-reentrant async lock to serialize concurrent operations on a shared AsyncSession."""

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._owner: asyncio.Task | None = None
        self._count = 0

    async def acquire(self) -> None:
        me = asyncio.current_task()
        if self._owner == me:
            self._count += 1
            return
        await self._lock.acquire()
        self._owner = me
        self._count = 1

    def release(self) -> None:
        me = asyncio.current_task()
        if self._owner != me:
            raise RuntimeError("Cannot release un-owned lock")
        self._count -= 1
        if self._count == 0:
            self._owner = None
            self._lock.release()

    async def __aenter__(self) -> "ReentrantAsyncLock":
        await self.acquire()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.release()


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


class EventPublisher:
    """Standardized audit and integration event publisher with task-reentrant session locking."""

    def __init__(
        self,
        session: AsyncSession,
        request_id: str | None = None,
        lock: ReentrantAsyncLock | None = None,
    ) -> None:
        self.session = session
        self.request_id = request_id
        self._lock = lock or ReentrantAsyncLock()

    async def commit_event(
        self,
        *,
        action: str,
        entity_type: str,
        entity_id: str,
        after: dict[str, Any],
        reason: str | None = None,
    ) -> None:
        async with self._lock:
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
