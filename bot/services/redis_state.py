import redis.asyncio as aioredis

from ..config import settings

_LAST_EXPORTED_KEY = "export:last_exported_id"


def _redis() -> aioredis.Redis:
    return aioredis.from_url(settings.redis_url, decode_responses=True)


async def get_last_exported_id() -> int:
    r = _redis()
    try:
        val = await r.get(_LAST_EXPORTED_KEY)
        return int(val) if val is not None else 0
    finally:
        await r.aclose()


async def set_last_exported_id(new_id: int) -> None:
    r = _redis()
    try:
        await r.set(_LAST_EXPORTED_KEY, new_id)
    finally:
        await r.aclose()
