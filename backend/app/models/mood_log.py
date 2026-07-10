import uuid
from datetime import date as date_type, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class MoodLog(Base):
    __tablename__ = "mood_logs"
    __table_args__ = (
        UniqueConstraint("user_id", "logged_date", name="uq_mood_logs_user_date"),
        CheckConstraint("mood_score BETWEEN 1 AND 10", name="ck_mood_logs_score_range"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    mood_label: Mapped[str] = mapped_column(String(30), nullable=False)
    mood_score: Mapped[int] = mapped_column(Integer, nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    logged_date: Mapped[date_type] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
