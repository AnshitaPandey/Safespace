from datetime import date, datetime


from pydantic import BaseModel


class AnalyticsSnapshotResponse(BaseModel):
    id: str
    period_type: str
    period_start: date
    period_end: date
    avg_mood_score: float | None
    dominant_emotion: str | None
    top_topics: list[str] | None
    message_count: int
    generated_report: str | None
    created_at: datetime

    class Config:
        from_attributes = True
