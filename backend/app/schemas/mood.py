from datetime import date

from pydantic import BaseModel, Field


class CreateMoodLogRequest(BaseModel):
    mood_label: str
    mood_score: int = Field(ge=1, le=10)
    note: str | None = None
    logged_date: date


class MoodLogResponse(BaseModel):
    id: str
    mood_label: str
    mood_score: int
    note: str | None
    logged_date: date

    class Config:
        from_attributes = True


class MoodTrendPoint(BaseModel):
    logged_date: date
    mood_score: int
    mood_label: str
