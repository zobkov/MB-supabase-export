from datetime import datetime

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, Message
from aiogram_dialog import DialogManager, StartMode

from ...services.db import fetch_all_participants, fetch_participants_after
from ...services.excel import build_xlsx_bytes
from ...services.redis_state import get_last_exported_id
from ..stat.dialog import StatSG

router = Router(name="export")


@router.message(Command("export_full"))
async def cmd_export_full(message: Message) -> None:
    await message.answer("Получаю все данные...")
    rows = await fetch_all_participants()
    if not rows:
        await message.answer("Таблица пуста.")
        return
    data = build_xlsx_bytes(rows)
    filename = f"participants_full_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.xlsx"
    await message.answer_document(
        BufferedInputFile(data, filename=filename),
        caption=f"Все участники: {len(rows)} записей",
    )


@router.message(Command("export_inc"))
async def cmd_export_inc(message: Message) -> None:
    last_id = await get_last_exported_id()
    rows = await fetch_participants_after(last_id)
    if not rows:
        await message.answer("Нет новых участников.")
        return
    data = build_xlsx_bytes(rows)
    filename = f"participants_inc_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.xlsx"
    await message.answer_document(
        BufferedInputFile(data, filename=filename),
        caption=f"Новые участники: {len(rows)} записей (last_id={last_id})",
    )


@router.message(Command("stat"))
async def cmd_stat(message: Message, dialog_manager: DialogManager) -> None:
    await dialog_manager.start(StatSG.main, mode=StartMode.RESET_STACK)
