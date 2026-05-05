# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Supabase → Excel → Telegram pipeline for the `participants` table. Two entry points:
- `supabase_manual_export.py` — standalone script, writes `.xlsx` to disk
- `bot/` — aiogram 3 Telegram bot with scheduled + on-demand exports and a stats dialog

## Setup

```bash
poetry install          # install all dependencies
redis-server            # required for the bot (FSM storage + incremental state)
```

`.env` (project root) must contain:
```
SUPABASE_URL=
SUPABASE_KEY=
BOT_TOKEN=
ADMIN_CHAT_ID=          # numeric Telegram user ID
REDIS_URL=redis://localhost:6379
SCHEDULE_CRON=0 9 * * *
SCHEDULE_TZ=Europe/Moscow
```

## Running

```bash
# Standalone export script (no Redis/bot needed)
poetry run python supabase_manual_export.py

# Telegram bot
poetry run python -m bot.main
```

## Bot commands

| Command | Behaviour |
|---|---|
| `/export_full` | Sends Excel with all participants |
| `/export_inc` | Sends Excel with rows added since last scheduled export (does **not** update state) |
| `/stat` | Opens aiogram-dialog window: total count + 7-day daily breakdown. Refresh button reloads. |

The bot silently ignores all messages from non-admin chat IDs (`AdminOnlyMiddleware`).

## Architecture

```
bot/
  main.py               # startup: Bot → Dispatcher → RedisStorage → APScheduler
  config.py             # frozen Settings dataclass from .env
  middleware.py         # AdminOnlyMiddleware (outer, on dp.update)
  services/
    db.py               # async Supabase queries (acreate_client)
    excel.py            # build_xlsx_bytes(rows) → bytes via BytesIO (no temp files)
    redis_state.py      # get/set export:last_exported_id (direct redis.asyncio, not FSM)
  features/
    export/
      handlers.py       # /export_full, /export_inc, /stat command Router
      scheduler.py      # scheduled_export_job() — ONLY place that updates last_exported_id
    stat/
      dialog.py         # StatSG states + aiogram-dialog Window + getter
```

**Adding a new feature**: create `bot/features/<name>/`, add a router or dialog, include it in `bot/main.py` with `dp.include_router(...)`.

### Incremental export state

`export:last_exported_id` in Redis tracks the max `id` sent by the scheduled job. On first run (key absent) it is treated as 0, so all rows are "new". Only `scheduler.py` writes this key; `/export_inc` reads it but never writes it.

### Key dependencies

| Package | Purpose |
|---|---|
| `aiogram ^3.27` | Bot framework, FSM, routing |
| `aiogram-dialog ^2.6` | Dialog/window UI (used for /stat) |
| `redis[hiredis] ^7.4` | RedisStorage for FSM + direct state key |
| `apscheduler ^3.11` | AsyncIOScheduler for cron-based scheduled export |
| `supabase ^2.10` | Async Supabase client (`acreate_client`) |
| `openpyxl ^3.1` | Excel generation |
