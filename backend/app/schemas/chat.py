from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class PersonalityType(str, Enum):
    supportive_friend = "supportive_friend"
    mentor = "mentor"
    career_coach = "career_coach"
    study_buddy = "study_buddy"
    reflective_listener = "reflective_listener"


class CreateChatRequest(BaseModel):
    personality_type: PersonalityType = PersonalityType.supportive_friend
    title: str | None = None


class UpdateChatRequest(BaseModel):
    title: str | None = None
    is_archived: bool | None = None


class ChatResponse(BaseModel):
    id: str
    title: str | None
    personality_type: str
    created_at: datetime
    last_message_at: datetime | None
    is_archived: bool

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    id: str
    chat_id: str
    role: str
    content: str
    safety_flag: bool
    safety_risk_level: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class SendMessageRequest(BaseModel):
    content: str
