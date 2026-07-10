from datetime import datetime

from pydantic import BaseModel


class CreateJournalEntryRequest(BaseModel):
    raw_content: str


class UpdateJournalEntryRequest(BaseModel):
    raw_content: str


class JournalEntryResponse(BaseModel):
    id: str
    raw_content: str
    summary: str | None
    themes: list[str] | None
    reflection_questions: list[str] | None
    sentiment_score: float | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
