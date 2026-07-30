from typing import Any, Literal

from agents.planner_tools import company_planner_tools

from langchain_core.tools import BaseTool, tool
from sqlalchemy.ext.asyncio import AsyncSession

from agents.brain import BrainMemoryService
from application.loop_service import LoopService
from contracts.domain import (
    BlacklistProspectRequest,
    RegisterCompanyRequest,
    RegisterContactRequest,
)


def company_finder_tools(
    session: AsyncSession, strategy_id: str, thread_id: str
) -> list[BaseTool]:
    service = LoopService(session)

    @tool
    async def get_sales_strategy_bundle() -> dict[str, Any]:
        """Read the immutable organization, product, and strategy context."""
        return (await service.bundle(strategy_id)).model_dump(mode="json")

    @tool
    async def get_sales_strategy() -> dict[str, Any]:
        """Read the active sales strategy targeting rules, narratives, and targets."""
        bundle = await service.bundle(strategy_id)
        return bundle.sales_strategy.model_dump(mode="json")

    @tool
    async def register_company(
        name: str,
        website_url: str,
        selection_reason: str,
    ) -> dict[str, Any]:
        """Register one evidence-backed company; Company Finder is sole authority."""
        from urllib.parse import urlparse

        host = urlparse(
            website_url if "://" in website_url else f"https://{website_url}"
        ).hostname
        if not host:
            raise ValueError("website_url must be a real observed company URL.")
        result = await service.register_company(
            strategy_id,
            RegisterCompanyRequest(
                name=name,
                website_url=website_url,
                selection_reason=selection_reason,
            ),
            thread_id=thread_id,
        )
        return result.model_dump(mode="json")

    return [get_sales_strategy_bundle, get_sales_strategy, register_company]


def sales_manager_tools(
    session: AsyncSession, strategy_id: str
) -> list[BaseTool]:
    service = LoopService(session)

    @tool
    async def get_org() -> dict[str, Any]:
        """Read the organization overview, mission, business model, and deal constraints."""
        bundle = await service.bundle(strategy_id)
        return bundle.organization.model_dump(mode="json")

    @tool
    async def get_product() -> dict[str, Any]:
        """Read product details, value proposition, pricing, and ICP forms."""
        bundle = await service.bundle(strategy_id)
        return bundle.product.model_dump(mode="json")

    return [get_org, get_product]



def contact_finder_tools(
    session: AsyncSession, strategy_id: str, company_id: str, thread_id: str
) -> list[BaseTool]:
    service = LoopService(session)

    @tool
    async def get_sales_strategy_bundle() -> dict[str, Any]:
        """Read immutable sales context and targeting rules."""
        return (await service.bundle(strategy_id)).model_dump(mode="json")

    @tool
    async def get_company() -> dict[str, Any]:
        """Read the assigned company and its current contact queue."""
        return (await service.company_detail(strategy_id, company_id)).model_dump(
            mode="json"
        )

    @tool
    async def is_profile_present(linkedin_url: str) -> dict[str, Any]:
        """Check canonical profile presence before visiting or registering."""
        return await service.profile_presence(strategy_id, linkedin_url)

    @tool
    async def register_contact(
        full_name: str,
        job_title: str,
        linkedin_url: str,
        selection_reason: str,
        fit_rationale: str,
        confidence_score: float,
        department: str | None = None,
        seniority: str | None = None,
        public_email: str | None = None,
        public_phone: str | None = None,
        location: str | None = None,
        evidence_urls: list[str] | None = None,
    ) -> dict[str, Any]:
        """Register one verified decision maker; Contact Finder is sole authority."""
        from urllib.parse import urlparse

        urls = evidence_urls or []
        for url in [linkedin_url, *urls]:
            host = urlparse(url if "://" in url else f"https://{url}").hostname
            if not host:
                raise ValueError("Invented or invalid URLs are rejected; use observed evidence only.")
        result = await service.register_contact(
            strategy_id,
            company_id,
            RegisterContactRequest(
                full_name=full_name,
                job_title=job_title,
                linkedin_url=linkedin_url,
                selection_reason=selection_reason,
                fit_rationale=fit_rationale,
                confidence_score=confidence_score,
                department=department,
                seniority=seniority,
                public_email=public_email,
                public_phone=public_phone,
                location=location,
                evidence_urls=evidence_urls or [],
            ),
            thread_id=thread_id,
        )
        return result.model_dump(mode="json")

    @tool
    async def blacklist_prospect(
        linkedin_url: str,
        blacklist_reason: str,
        full_name: str | None = None,
        job_title: str | None = None,
    ) -> dict[str, Any]:
        """Persist a wrong-fit observed profile so future efforts skip it."""
        result = await service.blacklist_prospect(
            strategy_id,
            company_id,
            BlacklistProspectRequest(
                linkedin_url=linkedin_url,
                blacklist_reason=blacklist_reason,
                full_name=full_name,
                job_title=job_title,
            ),
        )
        return result.model_dump(mode="json")

    return [
        get_sales_strategy_bundle,
        get_company,
        is_profile_present,
        register_contact,
        blacklist_prospect,
    ]


def brain_tools(
    session: AsyncSession, strategy_id: str, agent_type: str
) -> list[BaseTool]:
    memory = BrainMemoryService(session)

    @tool
    async def recall_memory(query: str, limit: int = 8) -> list[dict[str, Any]]:
        """Retrieve strategy-and-role-isolated long-term memories."""
        rows = await memory.recall(
            strategy_id=strategy_id,
            agent_type=agent_type,
            query=query,
            limit=limit,
        )
        return [
            {
                "id": row.id,
                "category": row.category,
                "content": row.content,
                "evidence_urls": row.evidence_urls,
            }
            for row in rows
        ]

    @tool
    async def manage_memory(
        action: Literal["create", "update", "delete", "compact"],
        category: Literal["actions", "failures", "decisions", "insights"],
        content: str = "",
        evidence_urls: list[str] | None = None,
        memory_id: str | None = None,
    ) -> dict[str, Any]:
        """Create, update, delete, or compact isolated evidence-backed memory."""
        if action == "compact":
            removed = await memory.compact(
                strategy_id=strategy_id, agent_type=agent_type
            )
            return {"action": "compact", "removed": removed}
        if action == "delete":
            if not memory_id:
                raise ValueError("memory_id is required to delete memory.")
            await memory.delete(memory_id)
            return {"action": "delete", "memory_id": memory_id}
        if action == "update":
            if not memory_id:
                raise ValueError("memory_id is required to update memory.")
            row = await memory.update(
                memory_id, content=content, evidence_urls=evidence_urls
            )
            return {"action": "update", "memory_id": row.id}
        row = await memory.remember(
            strategy_id=strategy_id,
            agent_type=agent_type,
            category=category,
            content=content,
            evidence_urls=evidence_urls,
        )
        return {"action": "create", "memory_id": row.id}

    return [recall_memory, manage_memory]
