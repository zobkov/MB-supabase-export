from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router(name="common")

_HELP_TEXT = (
    "<b>Доступные команды:</b>\n\n"
    "/export_full — полная выгрузка всех участников\n"
    "/export_inc — новые участники с последнего планового экспорта\n"
    "/stat — статистика за последние 7 дней\n"
    "/help — эта справка"
)


@router.message(Command("start", "help"))
async def cmd_help(message: Message) -> None:
    await message.answer(_HELP_TEXT)
