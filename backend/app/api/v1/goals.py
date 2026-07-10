import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import get_current_user
from app.db.session import get_db
from app.models.goal import Goal
from app.models.streak import Streak
from app.models.user import User
from app.schemas.goal import CreateGoalRequest, GoalResponse, StreakResponse, UpdateGoalRequest

router = APIRouter(tags=["goals"])


@router.post("/goals", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
async def create_goal(
    payload: CreateGoalRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    goal = Goal(user_id=current_user.id, title=payload.title, description=payload.description, target_date=payload.target_date)
    db.add(goal)
    await db.commit()
    await db.refresh(goal)
    return GoalResponse.model_validate(goal)


@router.get("/goals", response_model=list[GoalResponse])
async def list_goals(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Goal).where(Goal.user_id == current_user.id).order_by(Goal.created_at.desc()))
    return [GoalResponse.model_validate(g) for g in result.scalars().all()]


@router.patch("/goals/{goal_id}", response_model=GoalResponse)
async def update_goal(
    goal_id: uuid.UUID,
    payload: UpdateGoalRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Goal).where(Goal.id == goal_id, Goal.user_id == current_user.id))
    goal = result.scalar_one_or_none()
    if not goal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")

    for field in ("title", "description", "target_date"):
        value = getattr(payload, field)
        if value is not None:
            setattr(goal, field, value)

    if payload.is_completed is not None:
        goal.is_completed = payload.is_completed
        goal.completed_at = datetime.now(timezone.utc) if payload.is_completed else None

    await db.commit()
    await db.refresh(goal)
    return GoalResponse.model_validate(goal)


@router.delete("/goals/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_goal(
    goal_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Goal).where(Goal.id == goal_id, Goal.user_id == current_user.id))
    goal = result.scalar_one_or_none()
    if not goal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
    await db.delete(goal)
    await db.commit()
    return None


@router.get("/streaks", response_model=list[StreakResponse])
async def list_streaks(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Streak).where(Streak.user_id == current_user.id))
    return [StreakResponse.model_validate(s) for s in result.scalars().all()]
