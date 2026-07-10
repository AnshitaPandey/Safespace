"""chats, messages, safety_events tables

Revision ID: 0002_chat_message_safety
Revises: 0001_initial
Create Date: 2026-07-07

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0002_chat_message_safety"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "chats",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("personality_type", sa.String(50), nullable=False, server_default="supportive_friend"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_archived", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )
    op.create_index("ix_chats_user_id", "chats", ["user_id"])

    op.create_table(
        "messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("chat_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("chats.id", ondelete="CASCADE")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("sentiment_score", sa.Float(), nullable=True),
        sa.Column("emotion_label", sa.String(30), nullable=True),
        sa.Column("topic_labels", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("safety_flag", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("safety_risk_level", sa.String(20), nullable=True),
        sa.Column("quality_score", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_messages_chat_id", "messages", ["chat_id"])
    op.create_index("ix_messages_user_created", "messages", ["user_id", "created_at"])
    op.create_index(
        "ix_messages_safety_flagged",
        "messages",
        ["safety_flag"],
        postgresql_where=sa.text("safety_flag = true"),
    )

    op.create_table(
        "safety_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("message_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("messages.id")),
        sa.Column("risk_level", sa.String(20), nullable=False),
        sa.Column("trigger_type", sa.String(50), nullable=False),
        sa.Column("action_taken", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_safety_events_user_id", "safety_events", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_safety_events_user_id", table_name="safety_events")
    op.drop_table("safety_events")
    op.drop_index("ix_messages_safety_flagged", table_name="messages")
    op.drop_index("ix_messages_user_created", table_name="messages")
    op.drop_index("ix_messages_chat_id", table_name="messages")
    op.drop_table("messages")
    op.drop_index("ix_chats_user_id", table_name="chats")
    op.drop_table("chats")
