import uuid
from datetime import datetime

from sqlalchemy import ARRAY, Boolean, DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chat_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("chats.id", ondelete="CASCADE"))
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # 'user' | 'assistant' | 'system'
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Populated in later weeks by the DL pipeline (emotion/sentiment/topic models); nullable for now.
    sentiment_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    emotion_label: Mapped[str | None] = mapped_column(String(30), nullable=True)
    topic_labels: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)

    safety_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    safety_risk_level: Mapped[str | None] = mapped_column(String(20), nullable=True)  # none/low/medium/high
    quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
