import uuid

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from sqlalchemy import select

from app.ai.orchestrator import handle_user_message
from app.core.security import decode_token
from app.db.session import AsyncSessionLocal
from app.models.chat import Chat
from app.models.user import User

router = APIRouter()


@router.websocket("/ws/chats/{chat_id}")
async def chat_websocket(websocket: WebSocket, chat_id: uuid.UUID, token: str = Query(...)):
    # Browsers can't set custom headers on a native WebSocket handshake, so the JWT is
    # passed as a query param here instead of an Authorization header.
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        await websocket.close(code=4401)
        return

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.id == uuid.UUID(payload["sub"])))
        user = result.scalar_one_or_none()
        if not user or not user.is_active:
            await websocket.close(code=4401)
            return

        result = await db.execute(select(Chat).where(Chat.id == chat_id, Chat.user_id == user.id))
        chat = result.scalar_one_or_none()
        if not chat:
            await websocket.close(code=4404)
            return

        await websocket.accept()

        try:
            while True:
                data = await websocket.receive_json()
                content = data.get("content", "").strip()
                if not content:
                    continue

                # Acknowledge receipt immediately so the frontend can show a "sent" state
                # and a typing indicator while the LLM call is in flight.
                await websocket.send_json({"type": "user_message_received"})

                turn_result = await handle_user_message(
                    db=db,
                    chat_id=chat.id,
                    user_id=user.id,
                    personality_type=chat.personality_type,
                    content=content,
                )

                chat.last_message_at = turn_result.assistant_message.created_at
                await db.commit()

                await websocket.send_json(
                    {
                        "type": "assistant_message",
                        "id": str(turn_result.assistant_message.id),
                        "content": turn_result.assistant_message.content,
                        "safety_gated": turn_result.was_safety_gated,
                        "created_at": turn_result.assistant_message.created_at.isoformat(),
                    }
                )
        except WebSocketDisconnect:
            pass
