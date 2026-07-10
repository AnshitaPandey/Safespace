import uuid
from datetime import date as date_type, datetime

from sqlalchemy import ARRAY, Date, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class AnalyticsSnapshot(Base):
    __tablename__ = "analytics_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    period_type: Mapped[str] = mapped_column(String(20), nullable=False)  # weekly/monthly
    period_start: Mapped[date_type] = mapped_column(Date, nullable=False)
    period_end: Mapped[date_type] = mapped_column(Date, nullable=False)
    avg_mood_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    dominant_emotion: Mapped[str | None] = mapped_column(String(30), nullable=True)
    top_topics: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    message_count: Mapped[int] = mapped_column(Integer, default=0)
    generated_report: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
