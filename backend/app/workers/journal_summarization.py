"""
Celery task: given a raw journal entry, generate a summary, extract recurring themes, and
produce reflection questions — the "AI Journal" feature from the PRD. Runs async so journal
saving feels instant even though it triggers an LLM call.
"""
import json
import uuid

from app.ai.llm_adapter import generate_sync
from app.db.sync_session import get_sync_db
from app.models.journal_entry import JournalEntry
from app.workers.celery_app import celery_app

_SUMMARIZATION_SYSTEM_PROMPT = """
You analyze a personal journal entry. Respond with ONLY a JSON object, no other text, no
markdown fences. Schema:

{"summary": string (2-3 sentences, second person, e.g. "You wrote about..."),
 "themes": [string, ...] (2-5 short theme tags, e.g. "career anxiety", "family conflict"),
 "reflection_questions": [string, ...] (2-3 open-ended questions to help the writer go deeper),
 "sentiment_score": float between -1 and 1}

Do not diagnose or moralize. Reflection questions should be curious and specific to what was
actually written, not generic ("What made you feel that way about the meeting?" not "How do
you feel?").
""".strip()


@celery_app.task(name="app.workers.journal_summarization.summarize_journal_entry")
def summarize_journal_entry(entry_id: str) -> None:
    db = get_sync_db()
    try:
        entry = db.get(JournalEntry, uuid.UUID(entry_id))
        if not entry:
            return

        raw_response = generate_sync(
            system_prompt=_SUMMARIZATION_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": entry.raw_content}],
            max_tokens=512,
        )

        try:
            parsed = json.loads(raw_response)
        except json.JSONDecodeError:
            return

        entry.summary = parsed.get("summary")
        entry.themes = parsed.get("themes", [])
        entry.reflection_questions = parsed.get("reflection_questions", [])
        entry.sentiment_score = parsed.get("sentiment_score")
        db.commit()
    finally:
        db.close()
