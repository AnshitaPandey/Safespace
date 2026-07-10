"""
Vector DB wrapper around Qdrant. Every user's memories live in the same collection but are
filtered by a `user_id` payload field on every query — a per-user *namespace* rather than a
per-user collection, which keeps collection count manageable at scale while still guaranteeing
one user's memories never leak into another's retrieval results.
"""
import uuid

from qdrant_client import AsyncQdrantClient, QdrantClient
from qdrant_client.models import Distance, FieldCondition, Filter, MatchValue, PointStruct, VectorParams

from app.ai.embeddings import EMBEDDING_DIM
from app.core.config import settings

COLLECTION_NAME = "safespace_memories"

_client = AsyncQdrantClient(url=settings.QDRANT_URL)
_sync_client = QdrantClient(url=settings.QDRANT_URL)


def ensure_collection_sync() -> None:
    """Used by Celery workers, which run outside the asyncio event loop."""
    existing_names = {c.name for c in _sync_client.get_collections().collections}
    if COLLECTION_NAME not in existing_names:
        _sync_client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
        )


def upsert_memory_vector_sync(
    memory_id: uuid.UUID, user_id: uuid.UUID, vector: list[float], content: str, memory_type: str
) -> str:
    point_id = str(memory_id)
    ensure_collection_sync()
    _sync_client.upsert(
        collection_name=COLLECTION_NAME,
        points=[
            PointStruct(
                id=point_id,
                vector=vector,
                payload={"user_id": str(user_id), "content": content, "memory_type": memory_type},
            )
        ],
    )
    return point_id


async def ensure_collection() -> None:
    collections = await _client.get_collections()
    existing_names = {c.name for c in collections.collections}
    if COLLECTION_NAME not in existing_names:
        await _client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
        )


async def upsert_memory_vector(
    memory_id: uuid.UUID, user_id: uuid.UUID, vector: list[float], content: str, memory_type: str
) -> str:
    point_id = str(memory_id)
    await _client.upsert(
        collection_name=COLLECTION_NAME,
        points=[
            PointStruct(
                id=point_id,
                vector=vector,
                payload={"user_id": str(user_id), "content": content, "memory_type": memory_type},
            )
        ],
    )
    return point_id


async def search_similar_memories(user_id: uuid.UUID, query_vector: list[float], top_k: int = 20) -> list[dict]:
    results = await _client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        query_filter=Filter(must=[FieldCondition(key="user_id", match=MatchValue(value=str(user_id)))]),
        limit=top_k,
    )
    return [
        {"memory_id": point.id, "score": point.score, "content": point.payload.get("content")}
        for point in results.points
    ]


async def delete_memory_vector(memory_id: uuid.UUID) -> None:
    await _client.delete(collection_name=COLLECTION_NAME, points_selector=[str(memory_id)])
