from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import get_current_user
from app.ai.streaks import record_activity
from app.db.session import get_db
from app.models.mood_log import MoodLog
from app.models.user import User
from app.schemas.mood import CreateMoodLogRequest, MoodLogResponse

router = APIRouter(prefix="/mood", tags=["mood"])


@router.post("", response_model=MoodLogResponse, status_code=status.HTTP_201_CREATED)
async def log_mood(
    payload: CreateMoodLogRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # One log per day, enforced at the DB level too (uq_mood_logs_user_date) — upsert semantics
    # so re-logging the same day updates rather than errors.
    result = await db.execute(
        select(MoodLog).where(MoodLog.user_id == current_user.id, MoodLog.logged_date == payload.logged_date)
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.mood_label = payload.mood_label
        existing.mood_score = payload.mood_score
        existing.note = payload.note
        mood_log = existing
    else:
        mood_log = MoodLog(
            user_id=current_user.id,
            mood_label=payload.mood_label,
            mood_score=payload.mood_score,
            note=payload.note,
            logged_date=payload.logged_date,
        )
        db.add(mood_log)

    await record_activity(db, current_user.id, "mood_log")
    await db.commit()
    await db.refresh(mood_log)
    return MoodLogResponse.model_validate(mood_log)


@router.get("", response_model=list[MoodLogResponse])
async def list_mood_logs(
    range_days: int = Query(default=30, alias="range", le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    since = date.today() - timedelta(days=range_days)
    result = await db.execute(
        select(MoodLog)
        .where(MoodLog.user_id == current_user.id, MoodLog.logged_date >= since)
        .order_by(MoodLog.logged_date.asc())
    )
    return [MoodLogResponse.model_validate(m) for m in result.scalars().all()]


@router.get("/trends")
async def mood_trends(
    period: str = Query(default="weekly", pattern="^(weekly|monthly)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    days = 90 if period == "monthly" else 30
    since = date.today() - timedelta(days=days)
    result = await db.execute(
        select(MoodLog)
        .where(MoodLog.user_id == current_user.id, MoodLog.logged_date >= since)
        .order_by(MoodLog.logged_date.asc())
    )
    logs = result.scalars().all()

    if not logs:
        return {"period": period, "points": [], "average_score": None}

    average_score = sum(m.mood_score for m in logs) / len(logs)
    return {
        "period": period,
        "points": [
            {"logged_date": m.logged_date.isoformat(), "mood_score": m.mood_score, "mood_label": m.mood_label}
            for m in logs
        ],
        "average_score": round(average_score, 2),
    }
