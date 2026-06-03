from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from supabase import acreate_client, AsyncClient

from ..config import settings

_MOSCOW = ZoneInfo("Europe/Moscow")


async def _client() -> AsyncClient:
    return await acreate_client(settings.supabase_url, settings.supabase_key)


async def fetch_all_participants() -> list[dict]:
    c = await _client()
    res = await c.table("participants").select("*").order("id").execute()
    return res.data


async def fetch_participants_after(last_id: int) -> list[dict]:
    c = await _client()
    res = (
        await c.table("participants")
        .select("*")
        .gt("id", last_id)
        .order("id")
        .execute()
    )
    return res.data


async def fetch_all_created_at_dates() -> tuple[int, list[date]]:
    c = await _client()
    res = await c.table("participants").select("created_at", count="exact").execute()
    total: int = res.count or 0
    dates: list[date] = []
    for row in res.data:
        raw = row.get("created_at")
        if raw:
            dt = datetime.fromisoformat(raw)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            dates.append(dt.astimezone(_MOSCOW).date())
    return total, dates


async def fetch_stats() -> dict:
    c = await _client()

    total_res = await c.table("participants").select("id", count="exact").execute()
    total: int = total_res.count or 0

    today = date.today()
    daily: list[tuple[str, int]] = []
    for delta in range(6, -1, -1):
        day = today - timedelta(days=delta)
        day_start = day.isoformat() + "T00:00:00+00:00"
        day_end   = day.isoformat() + "T23:59:59+00:00"
        res = (
            await c.table("participants")
            .select("id", count="exact")
            .gte("created_at", day_start)
            .lte("created_at", day_end)
            .execute()
        )
        daily.append((day.strftime("%d.%m"), res.count or 0))

    return {"total": total, "daily": daily}
