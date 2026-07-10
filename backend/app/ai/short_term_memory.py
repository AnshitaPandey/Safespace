"""
Short-term memory — Week 2 version. Just a rolling window of the last N turns for the
current chat, kept in Redis with a TTL. No retrieval/ranking involved (that's what makes
it "short-term" vs. the long-term RAG memory system landing in Week 3).
"""
import json

from app.core.redis_client import redis_client

_MAX_TURNS = 20
_TTL_SECONDS = 60 * 60 * 24  # 24 hours of inactivity before a chat's short-term window expires


def _key(chat_id: str) -> str:
    return f"short_term_memory:{chat_id}"


async def append_turn(chat_id: str, role: str, content: str) -> None:
    entry = json.dumps({"role": role, "content": content})
    key = _key(chat_id)
    await redis_client.rpush(key, entry)
    await redis_client.ltrim(key, -_MAX_TURNS, -1)
    await redis_client.expire(key, _TTL_SECONDS)


async def get_recent_turns(chat_id: str) -> list[dict[str, str]]:
    raw_entries = await redis_client.lrange(_key(chat_id), 0, -1)
    return [json.loads(entry) for entry in raw_entries]
