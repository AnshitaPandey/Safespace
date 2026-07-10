from fastapi import APIRouter

router = APIRouter(prefix="/personalities", tags=["personality"])

# Static for now — personalities are prompt templates (app/ai/prompt_builder.py), not DB rows.
# A `personality_profiles` table would only earn its keep once personalities gain per-user
# customization (e.g. a saved custom tone); until then this avoids a needless join on every chat.
_PERSONALITIES = [
    {"type": "supportive_friend", "label": "Supportive Friend", "description": "Warm, casual, validating"},
    {"type": "mentor", "label": "Mentor", "description": "Reflective, growth-oriented"},
    {"type": "career_coach", "label": "Career Coach", "description": "Structured, action-oriented"},
    {"type": "study_buddy", "label": "Study Buddy", "description": "Encouraging, accountability-focused"},
    {"type": "reflective_listener", "label": "Reflective Listener", "description": "Mostly listens, asks questions"},
]


@router.get("")
async def list_personalities():
    return _PERSONALITIES
