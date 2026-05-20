import asyncio
import logging

import redis.asyncio as aioredis
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import DefaultKeyBuilder, RedisStorage
from aiogram_dialog import setup_dialogs
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from .config import settings
from .features.common.handlers import router as common_router
from .features.export.handlers import router as export_router
from .features.export.scheduler import scheduled_export_job
from .features.stat.dialog import stat_dialog
from .middleware import AdminOnlyMiddleware

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


async def main() -> None:
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    redis_client = aioredis.from_url(settings.redis_url, decode_responses=False)
    storage = RedisStorage(redis=redis_client, key_builder=DefaultKeyBuilder(with_destiny=True))

    dp = Dispatcher(storage=storage)
    dp.update.outer_middleware(AdminOnlyMiddleware())

    dp.include_router(common_router)
    dp.include_router(export_router)
    dp.include_router(stat_dialog)
    setup_dialogs(dp)

    scheduler = AsyncIOScheduler(timezone=settings.schedule_tz)
    scheduler.add_job(
        scheduled_export_job,
        trigger=CronTrigger.from_crontab(settings.schedule_cron),
        kwargs={"bot": bot},
        id="scheduled_export",
        replace_existing=True,
        misfire_grace_time=300,
    )

    @dp.startup()
    async def on_startup(**_: object) -> None:
        scheduler.start()
        logger.info(
            "Bot started | admins=%s | export_recipients=%s | cron=%s %s",
            settings.admin_chat_ids,
            settings.export_recipient_chat_ids,
            settings.schedule_cron,
            settings.schedule_tz,
        )

    @dp.shutdown()
    async def on_shutdown(**_: object) -> None:
        scheduler.shutdown(wait=False)
        await redis_client.aclose()
        logger.info("Bot stopped")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
