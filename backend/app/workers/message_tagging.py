"""
Celery task: tags a user message with emotion/sentiment/topic labels by calling ml-service.
Runs async so DL inference never blocks the chat response — results land on the message row
a moment after the reply, which is fine since nothing in the critical path reads them
synchronously (the mood dashboard and analytics rollups read them later, in batch).
"""
import uuid

import httpx

from app.core.config import settings
from app.db.sync_session import get_sync_db
from app.models.message import Message
from app.workers.celery_app import celery_app


@celery_app.task(name="app.workers.message_tagging.tag_message", bind=True, max_retries=2)
def tag_message(self, message_id: str) -> None:
    db = get_sync_db()
    try:
        message = db.get(Message, uuid.UUID(message_id))
        if not message:
            return

        try:
            with httpx.Client(timeout=10.0) as client:
                emotion_resp = client.post(f"{settings.ML_SERVICE_URL}/predict/emotion", json={"text": message.content})
                sentiment_resp = client.post(f"{settings.ML_SERVICE_URL}/predict/sentiment", json={"text": message.content})
                topic_resp = client.post(f"{settings.ML_SERVICE_URL}/predict/topic", json={"text": message.content})
                emotion_resp.raise_for_status()
                sentiment_resp.raise_for_status()
                topic_resp.raise_for_status()
        except httpx.HTTPError as exc:
            # ml-service may still be warming up its models on first boot — retry with backoff
            # rather than silently losing the tagging for this message.
            raise self.retry(exc=exc, countdown=10)

        message.emotion_label = emotion_resp.json()["emotion"]
        message.sentiment_score = sentiment_resp.json()["sentiment_score"]
        message.topic_labels = [t["topic"] for t in topic_resp.json()["topics"]]
        db.commit()
    finally:
        db.close()
