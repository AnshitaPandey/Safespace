"""
Celery tasks: precompute weekly/monthly analytics rollups (avg mood, dominant emotion, top
topics, message volume) and generate an AI-written narrative summary. Precomputing these
rather than calculating on every dashboard load is what makes the analytics page fast.
"""
import statistics
from collections import Counter
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select

from app.ai.llm_adapter import generate_sync
from app.db.sync_session import get_sync_db
from app.models.analytics_snapshot import AnalyticsSnapshot
from app.models.message import Message
from app.models.mood_log import MoodLog
from app.models.user import User
from app.workers.celery_app import celery_app

_REPORT_SYSTEM_PROMPT = """
You write a brief, warm, second-person weekly reflection summary for someone using a journaling
and mood-tracking app. You are given aggregated stats, not raw messages. Write 3-4 sentences.
Do not diagnose. Do not moralize. Notice patterns gently, the way a thoughtful friend would,
not a clinician. If the data is sparse, it's fine to say something short and encouraging about
building the habit rather than inventing patterns that aren't there.
""".strip()


def _build_report(db, user_id, period_type: str, period_start: date, period_end: date) -> AnalyticsSnapshot:
    mood_rows = db.execute(
        select(MoodLog.mood_score, MoodLog.mood_label).where(
            MoodLog.user_id == user_id,
            MoodLog.logged_date >= period_start,
            MoodLog.logged_date <= period_end,
        )
    ).all()

    message_count = db.execute(
        select(func.count(Message.id)).where(
            Message.user_id == user_id,
            Message.created_at >= period_start,
            Message.created_at <= period_end,
            Message.role == "user",
        )
    ).scalar_one()

    avg_mood = statistics.mean([r.mood_score for r in mood_rows]) if mood_rows else None
    dominant_emotion = Counter([r.mood_label for r in mood_rows]).most_common(1)[0][0] if mood_rows else None

    stats_summary = (
        f"Period: {period_start} to {period_end}. "
        f"Mood logs: {len(mood_rows)}, avg score: {avg_mood or 'n/a'}, "
        f"most common mood label: {dominant_emotion or 'n/a'}. "
        f"Chat messages sent: {message_count}."
    )
    narrative = generate_sync(
        system_prompt=_REPORT_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": stats_summary}],
        max_tokens=256,
    )

    snapshot = AnalyticsSnapshot(
        user_id=user_id,
        period_type=period_type,
        period_start=period_start,
        period_end=period_end,
        avg_mood_score=avg_mood,
        dominant_emotion=dominant_emotion,
        top_topics=[],  # populated once topic detection (Week 5-6) is wired into message tagging
        message_count=message_count,
        generated_report=narrative,
    )
    db.add(snapshot)
    db.commit()
    return snapshot


@celery_app.task(name="app.workers.analytics_rollup.generate_weekly_report_for_user")
def generate_weekly_report_for_user(user_id: str) -> None:
    db = get_sync_db()
    try:
        today = datetime.now(timezone.utc).date()
        period_start = today - timedelta(days=7)
        _build_report(db, user_id, "weekly", period_start, today)
    finally:
        db.close()


@celery_app.task(name="app.workers.analytics_rollup.generate_monthly_report_for_user")
def generate_monthly_report_for_user(user_id: str) -> None:
    db = get_sync_db()
    try:
        today = datetime.now(timezone.utc).date()
        period_start = today - timedelta(days=30)
        _build_report(db, user_id, "monthly", period_start, today)
    finally:
        db.close()


@celery_app.task(name="app.workers.analytics_rollup.generate_all_weekly_reports")
def generate_all_weekly_reports() -> None:
    """Celery Beat entry point — runs daily, only generates reports on the weekly cadence."""
    if datetime.now(timezone.utc).weekday() != 0:  # Monday
        return
    db = get_sync_db()
    try:
        user_ids = db.execute(select(User.id).where(User.is_active.is_(True))).scalars().all()
    finally:
        db.close()
    for user_id in user_ids:
        generate_weekly_report_for_user.delay(str(user_id))
