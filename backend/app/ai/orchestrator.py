"""
AI orchestration layer — chains the pipeline stages described in the architecture doc:
Safety -> Memory (RAG) -> Prompt -> LLM -> Persistence -> async extraction/tagging.

Long-term memory retrieval now runs on every non-gated turn (Week 3). Sentiment/emotion/topic
tagging (Week 5-6) and long-term memory extraction (this file, via Celery) run asynchronously
and don't block the chat response.
"""
import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import short_term_memory
from app.ai.llm_adapter import get_llm_provider
from app.ai.memory_retrieval import format_memories_for_prompt, retrieve_relevant_memories
from app.ai.prompt_builder import build_system_prompt
from app.ai.safety_layer import (
    CRISIS_RESPONSE,
    MEDIUM_RISK_PROMPT_ADDENDUM,
    RiskLevel,
    check_message_safety_combined,
)
from app.models.message import Message
from app.models.safety_event import SafetyEvent
from app.workers.memory_extraction import extract_memory_from_message
from app.workers.message_tagging import tag_message
from app.workers.quality_scoring import score_assistant_message


@dataclass
class ChatTurnResult:
    assistant_message: Message
    was_safety_gated: bool


async def handle_user_message(
    db: AsyncSession,
    chat_id: uuid.UUID,
    user_id: uuid.UUID,
    personality_type: str,
    content: str,
) -> ChatTurnResult:
    # 1. Persist the user's message first, always — even a safety-gated message is real
    #    conversation history and should not be silently dropped.
    user_message = Message(chat_id=chat_id, user_id=user_id, role="user", content=content)
    db.add(user_message)
    await db.flush()  # get user_message.id without committing yet

    # 2. Safety gate — runs before anything else touches the LLM. Combines the deterministic
    #    keyword matcher with the learned risk classifier served by ml-service (Week 7-8).
    safety_result = await check_message_safety_combined(content)

    if safety_result.risk_level == RiskLevel.high:
        user_message.safety_flag = True
        user_message.safety_risk_level = safety_result.risk_level.value

        assistant_message = Message(
            chat_id=chat_id, user_id=user_id, role="assistant", content=CRISIS_RESPONSE
        )
        db.add(assistant_message)
        await db.flush()

        db.add(
            SafetyEvent(
                user_id=user_id,
                message_id=user_message.id,
                risk_level=safety_result.risk_level.value,
                trigger_type=safety_result.trigger_type,
                action_taken="showed_crisis_resources",
            )
        )
        await db.commit()

        # Short-term memory still records this turn, so the AI has continuity if the
        # conversation continues after the resource card is shown. No long-term memory
        # extraction is triggered for safety-gated turns, but tagging still runs — knowing
        # the emotional tenor of a flagged message is useful for the safety audit trail.
        await short_term_memory.append_turn(str(chat_id), "user", content)
        await short_term_memory.append_turn(str(chat_id), "assistant", CRISIS_RESPONSE)
        tag_message.delay(str(user_message.id))

        return ChatTurnResult(assistant_message=assistant_message, was_safety_gated=True)

    # 3. Medium risk: LLM still responds, but with an added instruction to acknowledge
    #    distress and surface resources gently.
    prompt_addendum = MEDIUM_RISK_PROMPT_ADDENDUM if safety_result.risk_level == RiskLevel.medium else ""
    if safety_result.risk_level == RiskLevel.medium:
        user_message.safety_flag = True
        user_message.safety_risk_level = safety_result.risk_level.value
        db.add(
            SafetyEvent(
                user_id=user_id,
                message_id=user_message.id,
                risk_level=safety_result.risk_level.value,
                trigger_type=safety_result.trigger_type,
                action_taken="augmented_prompt_with_resources",
            )
        )

    # 4. Long-term memory retrieval (RAG) — hybrid ranked, scoped to this user.
    relevant_memories = await retrieve_relevant_memories(db, user_id, content)
    memories_block = format_memories_for_prompt(relevant_memories)

    # 5. Build prompt from personality + memories + short-term history.
    system_prompt = build_system_prompt(personality_type, memories_block, prompt_addendum)
    recent_turns = await short_term_memory.get_recent_turns(str(chat_id))
    llm_messages = recent_turns + [{"role": "user", "content": content}]

    # 6. Call the LLM.
    llm = get_llm_provider()
    response_text = await llm.generate(system_prompt=system_prompt, messages=llm_messages)

    # 7. Persist assistant response and update short-term memory.
    assistant_message = Message(chat_id=chat_id, user_id=user_id, role="assistant", content=response_text)
    db.add(assistant_message)
    await db.commit()

    await short_term_memory.append_turn(str(chat_id), "user", content)
    await short_term_memory.append_turn(str(chat_id), "assistant", response_text)

    # 8. Fire off async work — none of this blocks the response:
    #    long-term memory extraction, emotion/sentiment/topic tagging, and quality scoring.
    extract_memory_from_message.delay(str(user_message.id))
    tag_message.delay(str(user_message.id))
    score_assistant_message.delay(str(assistant_message.id), content)

    return ChatTurnResult(assistant_message=assistant_message, was_safety_gated=False)
