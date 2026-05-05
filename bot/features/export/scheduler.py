from datetime import datetime

from aiogram import Bot
from aiogram.types import BufferedInputFile

from ...config import settings
from ...services.db import fetch_participants_after
from ...services.excel import build_xlsx_bytes
from ...services.redis_state import get_last_exported_id, set_last_exported_id


async def scheduled_export_job(bot: Bot) -> None:
    last_id = await get_last_exported_id()
    rows = await fetch_participants_after(last_id)

    if not rows:
        for chat_id in settings.admin_chat_ids:
            await bot.send_message(chat_id, "Нет новых участников с последней выгрузки.")
        return

    data = build_xlsx_bytes(rows)
    filename = f"participants_new_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.xlsx"
    for chat_id in settings.admin_chat_ids:
        await bot.send_document(
            chat_id,
            document=BufferedInputFile(data, filename=filename),
            caption=f"Новые участники: {len(rows)} записей",
        )

    await set_last_exported_id(max(r["id"] for r in rows))
