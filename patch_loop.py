from typing import Any
from backend.src.persistence import models

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

