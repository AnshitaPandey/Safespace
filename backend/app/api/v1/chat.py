import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import get_current_user
from app.db.session import get_db
from app.models.chat import Chat
from app.models.message import Message
from app.models.user import User
from app.schemas.chat import ChatResponse, CreateChatRequest, MessageResponse, UpdateChatRequest

router = APIRouter(prefix="/chats", tags=["chat"])


def _chat_to_response(chat: Chat) -> ChatResponse:
    return ChatResponse(
        id=str(chat.id),
        title=chat.title,
        personality_type=chat.personality_type,
        created_at=chat.created_at,
        last_message_at=chat.last_message_at,
        is_archived=chat.is_archived,
    )


async def _get_owned_chat(db: AsyncSession, chat_id: uuid.UUID, user: User) -> Chat:
    result = await db.execute(select(Chat).where(Chat.id == chat_id, Chat.user_id == user.id))
    chat = result.scalar_one_or_none()
    if not chat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
    return chat


@router.get("", response_model=list[ChatResponse])
async def list_chats(
    include_archived: bool = Query(default=False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Chat).where(Chat.user_id == current_user.id)
    if not include_archived:
        query = query.where(Chat.is_archived.is_(False))
    query = query.order_by(Chat.last_message_at.desc().nullslast(), Chat.created_at.desc())

    result = await db.execute(query)
    chats = result.scalars().all()
    return [_chat_to_response(c) for c in chats]


@router.post("", response_model=ChatResponse, status_code=status.HTTP_201_CREATED)
async def create_chat(
    payload: CreateChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    chat = Chat(
        user_id=current_user.id,
        title=payload.title,
        personality_type=payload.personality_type.value,
    )
    db.add(chat)
    await db.commit()
    await db.refresh(chat)
    return _chat_to_response(chat)


@router.get("/{chat_id}/messages", response_model=list[MessageResponse])
async def get_chat_messages(
    chat_id: uuid.UUID,
    limit: int = Query(default=50, le=200),
    before: str | None = Query(default=None, description="ISO timestamp cursor for pagination"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_owned_chat(db, chat_id, current_user)

    query = select(Message).where(Message.chat_id == chat_id)
    if before:
        query = query.where(Message.created_at < before)
    query = query.order_by(Message.created_at.desc()).limit(limit)

    result = await db.execute(query)
    messages = result.scalars().all()
    messages.reverse()  # return oldest-first for easy rendering

    return [
        MessageResponse(
            id=str(m.id),
            chat_id=str(m.chat_id),
            role=m.role,
            content=m.content,
            safety_flag=m.safety_flag,
            safety_risk_level=m.safety_risk_level,
            created_at=m.created_at,
        )
        for m in messages
    ]


@router.patch("/{chat_id}", response_model=ChatResponse)
async def update_chat(
    chat_id: uuid.UUID,
    payload: UpdateChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    chat = await _get_owned_chat(db, chat_id, current_user)
    if payload.title is not None:
        chat.title = payload.title
    if payload.is_archived is not None:
        chat.is_archived = payload.is_archived
    await db.commit()
    await db.refresh(chat)
    return _chat_to_response(chat)


@router.delete("/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat(
    chat_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    chat = await _get_owned_chat(db, chat_id, current_user)
    await db.delete(chat)
    await db.commit()
    return None
