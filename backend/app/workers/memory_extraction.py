"""
Celery task: after a user message is persisted, decide whether it contains a durable fact
worth remembering long-term (a goal, preference, life event, interest, or recurring concern),
and if so, normalize it, embed it, and store it in both Postgres (`memories`) and the vector
DB. Runs asynchronously so it never adds latency to the chat response itself.
"""
import json
import uuid

from app.ai.embeddings import embed_text
from app.ai.llm_adapter import generate_sync
from app.ai.vector_store import upsert_memory_vector_sync
from app.db.sync_session import get_sync_db
from app.models.embeddings_metadata import EmbeddingsMetadata
from app.models.memory import Memory
from app.models.message import Message
from app.workers.celery_app import celery_app

_EXTRACTION_SYSTEM_PROMPT = """
You extract durable, memory-worthy facts from a single chat message. Respond with ONLY a
JSON object, no other text, no markdown fences. Schema:

{"has_memory": bool, "memory_type": "preference"|"goal"|"life_event"|"interest"|"recurring_concern",
 "content": string, "importance_score": float between 0 and 1}

Only set has_memory to true for facts that would matter in a FUTURE conversation (e.g. "user is
preparing for a job interview next week", "user's mother has been ill", "user wants to run a
marathon", "user gets anxious before presentations"). Small talk, one-off venting with no
lasting fact, and generic statements should get has_memory: false. "content" should be a short,
third-person, normalized statement (not a quote), e.g. "User is preparing for a GATE exam in
December."
""".strip()


@celery_app.task(name="app.workers.memory_extraction.extract_memory_from_message")
def extract_memory_from_message(message_id: str) -> None:
    db = get_sync_db()
    try:
        message = db.get(Message, uuid.UUID(message_id))
        if not message or message.role != "user":
            return

        raw_response = generate_sync(
            system_prompt=_EXTRACTION_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": message.content}],
            max_tokens=256,
        )

        try:
            parsed = json.loads(raw_response)
        except json.JSONDecodeError:
            return  # fail closed — no memory extracted rather than a bad write

        if not parsed.get("has_memory"):
            return

        memory = Memory(
            user_id=message.user_id,
            source_message_id=message.id,
            memory_type=parsed.get("memory_type", "recurring_concern"),
            content=parsed["content"],
            importance_score=float(parsed.get("importance_score", 0.5)),
        )
        db.add(memory)
        db.flush()  # get memory.id

        vector = embed_text(memory.content)
        vector_db_id = upsert_memory_vector_sync(
            memory_id=memory.id, user_id=message.user_id, vector=vector,
            content=memory.content, memory_type=memory.memory_type,
        )
        memory.embedding_id = vector_db_id

        db.add(
            EmbeddingsMetadata(
                user_id=message.user_id,
                source_type="memory",
                source_id=memory.id,
                vector_db_id=vector_db_id,
                embedding_model="all-MiniLM-L6-v2",
            )
        )
        db.commit()
    finally:
        db.close()
