"""
Conversation quality scoring — LLM-as-judge, per the blueprint's recommendation over training
a bespoke model from scratch: a smaller/cheaper LLM call with a structured rubric prompt,
scoring Helpfulness, Empathy, Relevance, and Consistency (each 0-1), run asynchronously so it
never adds latency to the chat response. Once a few thousand labeled examples accumulate this
way, they can be distilled into a small supervised regression head for cheaper scoring at
scale (mirrors RLAIF-style reward modeling) — noted here, not built yet, since it needs the
LLM-judge labels to exist first.
"""
import json
import uuid

from app.ai.llm_adapter import generate_sync
from app.db.sync_session import get_sync_db
from app.models.message import Message
from app.workers.celery_app import celery_app

_JUDGE_SYSTEM_PROMPT = """
You are scoring a single AI assistant response in a supportive-companion chat app, given the
user's message it was replying to. Respond with ONLY a JSON object, no other text:

{"helpfulness": float 0-1, "empathy": float 0-1, "relevance": float 0-1, "consistency": float 0-1}

- helpfulness: did it move the conversation forward or just restate feelings with no substance?
- empathy: did it validate the person's experience without toxic positivity or dismissiveness?
- relevance: did it actually address what the user said, or drift off-topic?
- consistency: is the tone/persona coherent with a supportive-companion (not clinical, not cold)?
""".strip()


@celery_app.task(name="app.workers.quality_scoring.score_assistant_message")
def score_assistant_message(assistant_message_id: str, user_message_content: str) -> None:
    db = get_sync_db()
    try:
        message = db.get(Message, uuid.UUID(assistant_message_id))
        if not message or message.role != "assistant":
            return

        judge_input = f"User said: {user_message_content}\n\nAssistant replied: {message.content}"
        raw_response = generate_sync(
            system_prompt=_JUDGE_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": judge_input}],
            max_tokens=128,
        )

        try:
            scores = json.loads(raw_response)
        except json.JSONDecodeError:
            return

        # Store the average of the four dimensions as the single `quality_score` column;
        # the per-dimension breakdown could go in a JSONB column if per-dimension analytics
        # become useful later.
        values = [scores.get(k, 0.5) for k in ("helpfulness", "empathy", "relevance", "consistency")]
        message.quality_score = sum(values) / len(values)
        db.commit()
    finally:
        db.close()
