"""
Memory retrieval layer — hybrid ranking combining vector similarity, importance, and recency,
as described in the architecture doc:

    final_score = 0.5 * cosine_similarity + 0.3 * importance_score + 0.2 * recency_decay
    recency_decay = exp(-days_since_last_accessed / half_life_days)

Retrieval flow: embed the query -> pull top-20 similarity candidates from Qdrant (already
scoped to this user) -> re-rank with the formula above using metadata from Postgres -> return
the top 5, formatted for prompt injection -> bump last_accessed_at/access_count on what was used
(this feeds back into future importance/recency scoring).
"""
import math
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.embeddings import embed_text
from app.ai.vector_store import search_similar_memories
from app.models.memory import Memory

_SIMILARITY_WEIGHT = 0.5
_IMPORTANCE_WEIGHT = 0.3
_RECENCY_WEIGHT = 0.2
_RECENCY_HALF_LIFE_DAYS = 14
_CANDIDATE_POOL_SIZE = 20
_TOP_K_RETURNED = 5


def _recency_decay(last_accessed_at: datetime | None) -> float:
    if last_accessed_at is None:
        return 0.5  # never-accessed memories get a neutral recency score, not zero
    days_since = (datetime.now(timezone.utc) - last_accessed_at).total_seconds() / 86400
    return math.exp(-days_since / _RECENCY_HALF_LIFE_DAYS)


async def retrieve_relevant_memories(db: AsyncSession, user_id: uuid.UUID, query_text: str) -> list[Memory]:
    query_vector = embed_text(query_text)
    candidates = await search_similar_memories(user_id, query_vector, top_k=_CANDIDATE_POOL_SIZE)
    if not candidates:
        return []

    candidate_ids = [uuid.UUID(c["memory_id"]) for c in candidates]
    similarity_by_id = {uuid.UUID(c["memory_id"]): c["score"] for c in candidates}

    result = await db.execute(select(Memory).where(Memory.id.in_(candidate_ids)))
    memories = {m.id: m for m in result.scalars().all()}

    scored: list[tuple[float, Memory]] = []
    for memory_id, memory in memories.items():
        similarity = similarity_by_id.get(memory_id, 0.0)
        recency = _recency_decay(memory.last_accessed_at)
        final_score = (
            _SIMILARITY_WEIGHT * similarity
            + _IMPORTANCE_WEIGHT * memory.importance_score
            + _RECENCY_WEIGHT * recency
        )
        scored.append((final_score, memory))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    top_memories = [memory for _, memory in scored[:_TOP_K_RETURNED]]

    now = datetime.now(timezone.utc)
    for memory in top_memories:
        memory.last_accessed_at = now
        memory.access_count += 1
    await db.commit()

    return top_memories


def format_memories_for_prompt(memories: list[Memory]) -> str:
    if not memories:
        return "(nothing remembered yet — this may be an early conversation)"
    return "\n".join(f"- {m.content}" for m in memories)
