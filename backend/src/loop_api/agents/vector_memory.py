"""Strategy-scoped Brain vector retrieval ports.

RecreationDocs §9.7 stores long-term memory in pgvector / dedicated vector DB
inside the agent checkpoint instance. OLTP remains SQLite; embeddings live with
BrainMemory rows or an optional PostgreSQL agent_brain vectors table.
"""

from __future__ import annotations

import hashlib
import math
from typing import Protocol, cast

from psycopg import AsyncConnection
from psycopg.rows import dict_row


def local_hash_embedding(text: str, *, dimensions: int = 64) -> list[float]:
    """Deterministic local embedding substitute that needs no provider credentials."""
    vector = [0.0] * dimensions
    tokens = [part for part in text.lower().split() if part]
    if not tokens:
        return vector
    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        for index in range(dimensions):
            vector[index] += (digest[index % len(digest)] / 255.0) - 0.5
    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [value / norm for value in vector]


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    numerator = sum(a * b for a, b in zip(left, right, strict=True))
    denominator = math.sqrt(sum(a * a for a in left)) * math.sqrt(sum(b * b for b in right))
    return numerator / denominator if denominator else 0.0


class VectorMemoryPort(Protocol):
    async def ensure_schema(self) -> None: ...

    async def upsert(
        self,
        *,
        memory_id: str,
        strategy_id: str,
        agent_type: str,
        category: str,
        content: str,
        embedding: list[float],
    ) -> None: ...

    async def search(
        self,
        *,
        strategy_id: str,
        agent_type: str,
        embedding: list[float],
        limit: int = 8,
    ) -> list[dict[str, object]]: ...


class InMemoryVectorStore:
    """Process-local store used by unit tests and deterministic local runs."""

    def __init__(self) -> None:
        self._rows: dict[str, dict[str, object]] = {}

    async def ensure_schema(self) -> None:
        return None

    async def upsert(
        self,
        *,
        memory_id: str,
        strategy_id: str,
        agent_type: str,
        category: str,
        content: str,
        embedding: list[float],
    ) -> None:
        self._rows[memory_id] = {
            "memory_id": memory_id,
            "strategy_id": strategy_id,
            "agent_type": agent_type,
            "category": category,
            "content": content,
            "embedding": embedding,
        }

    async def search(
        self,
        *,
        strategy_id: str,
        agent_type: str,
        embedding: list[float],
        limit: int = 8,
    ) -> list[dict[str, object]]:
        scored = [
            (
                cosine_similarity(embedding, cast(list[float], row["embedding"])),
                row,
            )
            for row in self._rows.values()
            if row["strategy_id"] == strategy_id and row["agent_type"] == agent_type
        ]
        scored.sort(key=lambda item: item[0], reverse=True)
        return [row for score, row in scored[:limit] if score > 0]


class PostgresVectorStore:
    """Optional PostgreSQL agent_brain vectors adapter (same instance as checkpoints)."""

    def __init__(self, database_url: str) -> None:
        self.database_url = database_url

    async def ensure_schema(self) -> None:
        async with await AsyncConnection.connect(
            self.database_url, row_factory=dict_row, autocommit=True
        ) as connection:
            await connection.execute("CREATE SCHEMA IF NOT EXISTS agent_brain")
            await connection.execute(
                """
                CREATE TABLE IF NOT EXISTS agent_brain.brain_vectors (
                    memory_id TEXT PRIMARY KEY,
                    sales_strategy_id TEXT NOT NULL,
                    agent_type TEXT NOT NULL,
                    category TEXT NOT NULL,
                    content TEXT NOT NULL,
                    embedding DOUBLE PRECISION[] NOT NULL
                )
                """
            )
            await connection.execute(
                """
                CREATE INDEX IF NOT EXISTS brain_vectors_strategy_agent_idx
                ON agent_brain.brain_vectors (sales_strategy_id, agent_type)
                """
            )

    async def upsert(
        self,
        *,
        memory_id: str,
        strategy_id: str,
        agent_type: str,
        category: str,
        content: str,
        embedding: list[float],
    ) -> None:
        async with await AsyncConnection.connect(
            self.database_url, row_factory=dict_row, autocommit=True
        ) as connection:
            await connection.execute(
                """
                INSERT INTO agent_brain.brain_vectors
                    (memory_id, sales_strategy_id, agent_type, category, content, embedding)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (memory_id) DO UPDATE SET
                    content = EXCLUDED.content,
                    category = EXCLUDED.category,
                    embedding = EXCLUDED.embedding
                """,
                (memory_id, strategy_id, agent_type, category, content, embedding),
            )

    async def search(
        self,
        *,
        strategy_id: str,
        agent_type: str,
        embedding: list[float],
        limit: int = 8,
    ) -> list[dict[str, object]]:
        async with await AsyncConnection.connect(
            self.database_url, row_factory=dict_row, autocommit=True
        ) as connection:
            cursor = await connection.execute(
                """
                SELECT memory_id, sales_strategy_id AS strategy_id, agent_type, category,
                       content, embedding
                FROM agent_brain.brain_vectors
                WHERE sales_strategy_id = %s AND agent_type = %s
                """,
                (strategy_id, agent_type),
            )
            rows = await cursor.fetchall()
        scored = [
            (cosine_similarity(embedding, list(row["embedding"])), dict(row))
            for row in rows
        ]
        scored.sort(key=lambda item: item[0], reverse=True)
        return [row for score, row in scored[:limit] if score > 0]


def resolve_vector_store(database_url: str | None) -> VectorMemoryPort:
    if database_url:
        return PostgresVectorStore(database_url)
    return InMemoryVectorStore()
