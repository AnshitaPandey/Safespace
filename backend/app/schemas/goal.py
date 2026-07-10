from datetime import date as date_type, datetime

from pydantic import BaseModel


class CreateGoalRequest(BaseModel):
    title: str
    description: str | None = None
    target_date: date_type | None = None


class UpdateGoalRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    target_date: date_type | None = None
    is_completed: bool | None = None


class GoalResponse(BaseModel):
    id: str
    title: str
    description: str | None
    target_date: date_type | None
    is_completed: bool
    completed_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class StreakResponse(BaseModel):
    activity_type: str
    current_streak: int
    longest_streak: int
    last_activity_date: date_type | None

    class Config:
        from_attributes = True


class NotificationResponse(BaseModel):
    id: str
    notification_type: str
    title: str
    body: str | None
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True
