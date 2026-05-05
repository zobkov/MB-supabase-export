from datetime import date, timedelta

from supabase import acreate_client, AsyncClient

from ..config import settings


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
