import math
import re
from collections import Counter

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agents.vector_memory import (
    VectorMemoryPort,
    cosine_similarity,
    local_hash_embedding,
    resolve_vector_store,
)
from core.config import get_settings
from persistence import models

TOKEN_PATTERN = re.compile(r"[a-z0-9]{2,}")


def terms_for(text: str) -> list[str]:
    return TOKEN_PATTERN.findall(text.lower())


def similarity(left: list[str], right: list[str]) -> float:
    a, b = Counter(left), Counter(right)
    numerator = sum(value * b.get(key, 0) for key, value in a.items())
    denominator = math.sqrt(sum(value * value for value in a.values())) * math.sqrt(
        sum(value * value for value in b.values())
    )
    return numerator / denominator if denominator else 0.0


class BrainMemoryService:
    """SQLite-backed, strategy-isolated memory with local vector retrieval.

    Optional PostgreSQL agent_brain.brain_vectors mirrors embeddings when
    LOOP_THREADS_DATABASE_URL is configured (checkpoint instance only).
    """

    def __init__(
        self,
        session: AsyncSession,
        vector_store: VectorMemoryPort | None = None,
    ) -> None:
        self.session = session
        settings = get_settings()
        self.vector_store = vector_store or resolve_vector_store(
            settings.resolved_threads_database_url if settings.threads_enabled else None
        )

    async def remember(
        self,
        *,
        strategy_id: str,
        agent_type: str,
        category: str,
        content: str,
        evidence_urls: list[str] | None = None,
    ) -> models.BrainMemory:
        existing = await self.session.scalar(
            select(models.BrainMemory).where(
                models.BrainMemory.sales_strategy_id == strategy_id,
                models.BrainMemory.agent_type == agent_type,
                models.BrainMemory.category == category,
                models.BrainMemory.content == content,
            )
        )
        if existing:
            return existing
        candidates = (
            await self.session.scalars(
                select(models.BrainMemory).where(
                    models.BrainMemory.sales_strategy_id == strategy_id,
                    models.BrainMemory.agent_type == agent_type,
                    models.BrainMemory.category == category,
                )
            )
        ).all()
        content_terms = terms_for(content)
        embedding = local_hash_embedding(content)
        near = max(
            ((similarity(content_terms, row.terms), row) for row in candidates),
            default=(0.0, None),
            key=lambda item: item[0],
        )
        if near[1] is not None and near[0] >= 0.92:
            near[1].content = content
            near[1].terms = content_terms
            near[1].embedding = embedding
            if evidence_urls:
                near[1].evidence_urls = list(
                    dict.fromkeys([*near[1].evidence_urls, *evidence_urls])
                )
            await self.session.commit()
            await self._mirror_vector(near[1])
            return near[1]
        row = models.BrainMemory(
            sales_strategy_id=strategy_id,
            agent_type=agent_type,
            category=category,
            content=content,
            terms=content_terms,
            embedding=embedding,
            evidence_urls=evidence_urls or [],
        )
        self.session.add(row)
        await self.session.commit()
        await self._mirror_vector(row)
        return row

    async def _mirror_vector(self, row: models.BrainMemory) -> None:
        await self.vector_store.ensure_schema()
        await self.vector_store.upsert(
            memory_id=row.id,
            strategy_id=row.sales_strategy_id,
            agent_type=row.agent_type,
            category=row.category,
            content=row.content,
            embedding=row.embedding or local_hash_embedding(row.content),
        )

    async def update(
        self, memory_id: str, *, content: str, evidence_urls: list[str] | None = None
    ) -> models.BrainMemory:
        row = await self.session.get(models.BrainMemory, memory_id)
        if not row:
            raise ValueError("Memory was not found.")
        row.content = content
        row.terms = terms_for(content)
        row.embedding = local_hash_embedding(content)
        if evidence_urls is not None:
            row.evidence_urls = evidence_urls
        await self.session.commit()
        await self._mirror_vector(row)
        return row

    async def delete(self, memory_id: str) -> None:
        row = await self.session.get(models.BrainMemory, memory_id)
        if not row:
            raise ValueError("Memory was not found.")
        await self.session.delete(row)
        await self.session.commit()

    async def recall(
        self,
        *,
        strategy_id: str,
        agent_type: str,
        query: str,
        limit: int = 8,
    ) -> list[models.BrainMemory]:
        rows = (
            await self.session.scalars(
                select(models.BrainMemory).where(
                    models.BrainMemory.sales_strategy_id == strategy_id,
                    models.BrainMemory.agent_type == agent_type,
                )
            )
        ).all()
        query_embedding = local_hash_embedding(query)
        query_terms = terms_for(query)

        def score(row: models.BrainMemory) -> float:
            vector_score = cosine_similarity(
                query_embedding, row.embedding or local_hash_embedding(row.content)
            )
            lexical_score = similarity(query_terms, row.terms)
            return max(vector_score, lexical_score)

        ordered = sorted(rows, key=score, reverse=True)[:limit]
        # Keep strategy isolation even if remote vector hits arrive later.
        return [row for row in ordered if row.sales_strategy_id == strategy_id]

    async def compact(self, *, strategy_id: str, agent_type: str, max_entries: int = 100) -> int:
        rows = (
            await self.session.scalars(
                select(models.BrainMemory)
                .where(
                    models.BrainMemory.sales_strategy_id == strategy_id,
                    models.BrainMemory.agent_type == agent_type,
                )
                .order_by(models.BrainMemory.created_at.desc())
            )
        ).all()
        stale = rows[max_entries:]
        for row in stale:
            await self.session.delete(row)
        await self.session.commit()
        return len(stale)
