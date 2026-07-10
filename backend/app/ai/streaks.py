"""
Streak bookkeeping — shared logic called whenever a user logs a mood, writes a journal entry,
or sends a chat message. Kept as a plain function (not a Celery task) since it's a fast,
single-row update that should reflect immediately in the UI.
"""
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.streak import Streak


async def record_activity(db: AsyncSession, user_id, activity_type: str) -> Streak:
    today = date.today()
    result = await db.execute(
        select(Streak).where(Streak.user_id == user_id, Streak.activity_type == activity_type)
    )
    streak = result.scalar_one_or_none()

    if not streak:
        streak = Streak(user_id=user_id, activity_type=activity_type, current_streak=1, longest_streak=1, last_activity_date=today)
        db.add(streak)
        return streak

    if streak.last_activity_date == today:
        return streak  # already logged today, no change
    elif streak.last_activity_date == today - timedelta(days=1):
        streak.current_streak += 1
    else:
        streak.current_streak = 1  # streak broken, restart

    streak.longest_streak = max(streak.longest_streak, streak.current_streak)
    streak.last_activity_date = today
    return streak
