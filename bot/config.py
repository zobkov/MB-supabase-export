import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    supabase_url: str
    supabase_key: str
    bot_token: str
    admin_chat_id: int
    redis_url: str
    schedule_cron: str
    schedule_tz: str


settings = Settings(
    supabase_url=os.environ["SUPABASE_URL"],
    supabase_key=os.environ["SUPABASE_KEY"],
    bot_token=os.environ["BOT_TOKEN"],
    admin_chat_id=int(os.environ["ADMIN_CHAT_ID"]),
    redis_url=os.environ.get("REDIS_URL", "redis://localhost:6379"),
    schedule_cron=os.environ.get("SCHEDULE_CRON", "0 9 * * *"),
    schedule_tz=os.environ.get("SCHEDULE_TZ", "Europe/Moscow"),
)
