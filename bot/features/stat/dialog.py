from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import Button, Cancel, Row
from aiogram_dialog.widgets.text import Const, Format, Multi

from ...services.db import fetch_stats


class StatSG(StatesGroup):
    main = State()


async def _stats_getter(dialog_manager: DialogManager, **kwargs) -> dict:
    stats = await fetch_stats()
    lines = ["<b>Дата</b>   | <b>Новых</b>", "───────────|───────"]
    for day_str, count in stats["daily"]:
        lines.append(f"{day_str}      |   {count}")
    return {
        "total": stats["total"],
        "daily_table": "\n".join(lines),
    }


async def _on_refresh(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    await dialog_manager.show()


stat_dialog = Dialog(
    Window(
        Multi(
            Const("<b>Статистика участников</b>"),
            Format("Всего: <b>{total}</b>"),
            Const(""),
            Const("Регистрации за последние 7 дней:"),
            Format("{daily_table}"),
            sep="\n",
        ),
        Row(
            Button(Const("🔄 Обновить"), id="refresh", on_click=_on_refresh),
            Cancel(Const("✖ Закрыть")),
        ),
        state=StatSG.main,
        getter=_stats_getter,
        parse_mode="HTML",
    ),
)
