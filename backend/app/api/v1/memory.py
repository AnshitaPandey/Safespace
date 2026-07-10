import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.vector_store import delete_memory_vector
from app.api.v1.auth import get_current_user
from app.db.session import get_db
from app.models.memory import Memory
from app.models.user import User
from app.schemas.memory import MemoryResponse

router = APIRouter(prefix="/memories", tags=["memory"])


@router.get("", response_model=list[MemoryResponse])
async def list_memories(
    memory_type: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Memory).where(Memory.user_id == current_user.id)
    if memory_type:
        query = query.where(Memory.memory_type == memory_type)
    query = query.order_by(Memory.importance_score.desc())
    result = await db.execute(query)
    return [MemoryResponse.model_validate(m) for m in result.scalars().all()]


@router.delete("/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memory(
    memory_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lets a user remove something the AI remembered about them — a privacy control called
    out explicitly in the PRD, not an afterthought."""
    result = await db.execute(select(Memory).where(Memory.id == memory_id, Memory.user_id == current_user.id))
    memory = result.scalar_one_or_none()
    if not memory:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Memory not found")

    await delete_memory_vector(memory.id)
    await db.delete(memory)
    await db.commit()
    return None
