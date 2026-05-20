import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    supabase_url: str
    supabase_key: str
    bot_token: str
    admin_chat_ids: frozenset[int]
    export_recipient_chat_ids: frozenset[int]
    redis_url: str
    schedule_cron: str
    schedule_tz: str


def _parse_ids(env_var: str, fallback_var: str = "") -> frozenset[int]:
    raw = os.environ.get(env_var, "")
    if not raw and fallback_var:
        raw = os.environ.get(fallback_var, "")
    return frozenset(int(x.strip()) for x in raw.split(",") if x.strip())


def _parse_admin_ids() -> frozenset[int]:
    return _parse_ids("ADMIN_CHAT_IDS", "ADMIN_CHAT_ID")


def _parse_recipient_ids(admin_ids: frozenset[int]) -> frozenset[int]:
    raw = os.environ.get("EXPORT_RECIPIENT_CHAT_IDS", "")
    if not raw:
        return admin_ids
    return frozenset(int(x.strip()) for x in raw.split(",") if x.strip())


_admin_ids = _parse_admin_ids()

settings = Settings(
    supabase_url=os.environ["SUPABASE_URL"],
    supabase_key=os.environ["SUPABASE_KEY"],
    bot_token=os.environ["BOT_TOKEN"],
    admin_chat_ids=_admin_ids,
    export_recipient_chat_ids=_parse_recipient_ids(_admin_ids),
    redis_url=os.environ.get("REDIS_URL", "redis://localhost:6379"),
    schedule_cron=os.environ.get("SCHEDULE_CRON", "0 9 * * *"),
    schedule_tz=os.environ.get("SCHEDULE_TZ", "Europe/Moscow"),
)
