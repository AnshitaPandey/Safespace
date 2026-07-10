import asyncio
from collections import Counter
from datetime import date, timedelta

import httpx
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.analytics_snapshot import AnalyticsSnapshot
from app.models.mood_log import MoodLog
from app.models.user import User
from app.schemas.analytics import AnalyticsSnapshotResponse
from app.workers.analytics_rollup import generate_monthly_report_for_user, generate_weekly_report_for_user

router = APIRouter(prefix="/analytics", tags=["analytics"])


async def _get_or_generate_report(
    db: AsyncSession, user: User, period_type: str, max_age_days: int
) -> AnalyticsSnapshotResponse:
    since = date.today() - timedelta(days=max_age_days)
    result = await db.execute(
        select(AnalyticsSnapshot)
        .where(
            AnalyticsSnapshot.user_id == user.id,
            AnalyticsSnapshot.period_type == period_type,
            AnalyticsSnapshot.period_end >= since,
        )
        .order_by(AnalyticsSnapshot.created_at.desc())
    )
    snapshot = result.scalars().first()

    if not snapshot:
        # No recent snapshot — generate one on-demand (blocking call moved off the event loop,
        # since it makes a synchronous LLM call). In steady state, Celery Beat keeps these
        # fresh so this on-demand path is mostly hit for brand-new users.
        task_fn = generate_weekly_report_for_user if period_type == "weekly" else generate_monthly_report_for_user
        await asyncio.to_thread(task_fn, str(user.id))

        result = await db.execute(
            select(AnalyticsSnapshot)
            .where(AnalyticsSnapshot.user_id == user.id, AnalyticsSnapshot.period_type == period_type)
            .order_by(AnalyticsSnapshot.created_at.desc())
        )
        snapshot = result.scalars().first()

    return AnalyticsSnapshotResponse.model_validate(snapshot)


@router.get("/weekly-report", response_model=AnalyticsSnapshotResponse)
async def weekly_report(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await _get_or_generate_report(db, current_user, "weekly", max_age_days=7)


@router.get("/monthly-report", response_model=AnalyticsSnapshotResponse)
async def monthly_report(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await _get_or_generate_report(db, current_user, "monthly", max_age_days=30)


@router.get("/emotional-patterns")
async def emotional_patterns(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    since = date.today() - timedelta(days=days)
    result = await db.execute(
        select(MoodLog).where(MoodLog.user_id == current_user.id, MoodLog.logged_date >= since)
    )
    logs = result.scalars().all()
    label_counts = Counter(m.mood_label for m in logs)
    return {
        "period_days": days,
        "mood_label_distribution": dict(label_counts),
        "total_logs": len(logs),
        # Topic distribution will populate once message-level topic tagging (Week 5-6) lands.
        "top_topics": [],
    }


@router.get("/mood-forecast")
async def mood_forecast(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    since = date.today() - timedelta(days=60)
    result = await db.execute(
        select(MoodLog)
        .where(MoodLog.user_id == current_user.id, MoodLog.logged_date >= since)
        .order_by(MoodLog.logged_date.asc())
    )
    logs = result.scalars().all()

    if len(logs) < 5:
        return {
            "forecast": [],
            "message": "Not enough mood history yet — log your mood for a few more days to unlock a forecast.",
        }

    history = [{"date": m.logged_date.isoformat(), "score": m.mood_score} for m in logs]

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(f"{settings.ML_SERVICE_URL}/predict/mood-forecast", json={"history": history})
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError:
        # ml-service unavailable or model not yet trained — fall back to a naive moving-average
        # trend rather than failing the whole dashboard. See ml-service/training/train_mood_forecaster.py
        # for the real GRU/LSTM model this is meant to be replaced by once trained.
        recent_scores = [m.mood_score for m in logs[-7:]]
        avg = sum(recent_scores) / len(recent_scores)
        return {
            "forecast": [{"day_offset": i, "predicted_score": round(avg, 1)} for i in range(1, 4)],
            "model": "naive_moving_average_fallback",
        }
