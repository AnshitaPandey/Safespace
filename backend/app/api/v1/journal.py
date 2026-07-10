import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import get_current_user
from app.ai.streaks import record_activity
from app.db.session import get_db
from app.models.journal_entry import JournalEntry
from app.models.user import User
from app.schemas.journal import CreateJournalEntryRequest, JournalEntryResponse, UpdateJournalEntryRequest
from app.workers.journal_summarization import summarize_journal_entry

router = APIRouter(prefix="/journal", tags=["journal"])


async def _get_owned_entry(db: AsyncSession, entry_id: uuid.UUID, user: User) -> JournalEntry:
    result = await db.execute(select(JournalEntry).where(JournalEntry.id == entry_id, JournalEntry.user_id == user.id))
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Journal entry not found")
    return entry


@router.post("", response_model=JournalEntryResponse, status_code=status.HTTP_201_CREATED)
async def create_journal_entry(
    payload: CreateJournalEntryRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    entry = JournalEntry(user_id=current_user.id, raw_content=payload.raw_content)
    db.add(entry)
    await record_activity(db, current_user.id, "journal")
    await db.commit()
    await db.refresh(entry)

    # Summary/themes/reflection questions are filled in asynchronously — the entry saves
    # instantly, and the frontend can poll or refetch to pick up the enriched fields.
    summarize_journal_entry.delay(str(entry.id))

    return JournalEntryResponse.model_validate(entry)


@router.get("", response_model=list[JournalEntryResponse])
async def list_journal_entries(
    limit: int = Query(default=20, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(JournalEntry)
        .where(JournalEntry.user_id == current_user.id)
        .order_by(JournalEntry.created_at.desc())
        .limit(limit)
    )
    return [JournalEntryResponse.model_validate(e) for e in result.scalars().all()]


@router.get("/{entry_id}", response_model=JournalEntryResponse)
async def get_journal_entry(
    entry_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    entry = await _get_owned_entry(db, entry_id, current_user)
    return JournalEntryResponse.model_validate(entry)


@router.patch("/{entry_id}", response_model=JournalEntryResponse)
async def update_journal_entry(
    entry_id: uuid.UUID,
    payload: UpdateJournalEntryRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    entry = await _get_owned_entry(db, entry_id, current_user)
    entry.raw_content = payload.raw_content
    # Re-summarize on edit, since the content changed.
    await db.commit()
    await db.refresh(entry)
    summarize_journal_entry.delay(str(entry.id))
    return JournalEntryResponse.model_validate(entry)


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_journal_entry(
    entry_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    entry = await _get_owned_entry(db, entry_id, current_user)
    await db.delete(entry)
    await db.commit()
    return None
