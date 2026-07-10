from fastapi import APIRouter

from app.api.v1 import analytics, auth, chat, goals, journal, memory, mood, notifications, personality, voice

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(chat.router)
api_router.include_router(memory.router)
api_router.include_router(mood.router)
api_router.include_router(journal.router)
api_router.include_router(analytics.router)
api_router.include_router(personality.router)
api_router.include_router(goals.router)
api_router.include_router(notifications.router)
api_router.include_router(voice.router)
