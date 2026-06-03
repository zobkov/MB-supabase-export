import calendar
from collections import defaultdict
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import Button, Row, ScrollingGroup, Select
from aiogram_dialog.widgets.text import Format

from ...services.db import fetch_all_created_at_dates

_MOSCOW = ZoneInfo("Europe/Moscow")

_MONTHS_RU = {
    1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель",
    5: "Май", 6: "Июнь", 7: "Июль", 8: "Август",
    9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь",
}


class StatSG(StatesGroup):
    main = State()
    day_list = State()
    day_detail = State()
    week_list = State()
    week_detail = State()
    month_list = State()
    month_detail = State()


def _week_start(d: date) -> date:
    return d - timedelta(days=d.weekday())


def _format_table(rows: list[tuple[str, int]], col_header: str = "Дата") -> str:
    pad = " " * (6 - len(col_header))
    header = f"{col_header}{pad}| Новых"
    lines = [header] + [f"{ds} | {n:>5}" for ds, n in rows]
    return "\n".join(lines)


def _load_datetimes(manager: DialogManager) -> list[datetime]:
    return [datetime.fromisoformat(s) for s in manager.dialog_data["datetimes"]]


def _load_dates(manager: DialogManager) -> list[date]:
    return [datetime.fromisoformat(s).date() for s in manager.dialog_data["datetimes"]]


# ── data bootstrap ────────────────────────────────────────────────────────────

async def _on_dialog_start(start_data, manager: DialogManager) -> None:
    total, datetimes = await fetch_all_created_at_dates()
    manager.dialog_data["total"] = total
    manager.dialog_data["datetimes"] = [dt.isoformat() for dt in datetimes]


# ── getters ───────────────────────────────────────────────────────────────────

async def _main_getter(dialog_manager: DialogManager, **kwargs) -> dict:
    total = dialog_manager.dialog_data["total"]
    dates = _load_dates(dialog_manager)

    counts: dict[date, int] = defaultdict(int)
    for d in dates:
        counts[d] += 1

    today = date.today()
    rows = [(( today - timedelta(days=i)).strftime("%d.%m"), counts.get(today - timedelta(days=i), 0))
            for i in range(6, -1, -1)]

    return {"total": total, "seven_day_table": _format_table(rows)}


async def _day_list_getter(dialog_manager: DialogManager, **kwargs) -> dict:
    dates = _load_dates(dialog_manager)
    counts: dict[date, int] = defaultdict(int)
    for d in dates:
        counts[d] += 1
    items = [
        {"key": d.isoformat(), "label": f"{d.strftime('%d.%m.%Y')} ({counts[d]})"}
        for d in sorted(counts.keys(), reverse=True)
    ]
    return {"days": items}


async def _day_detail_getter(dialog_manager: DialogManager, **kwargs) -> dict:
    sel = date.fromisoformat(dialog_manager.dialog_data["selected_day"])
    datetimes = _load_datetimes(dialog_manager)
    day_dts = [dt for dt in datetimes if dt.date() == sel]
    count = len(day_dts)
    hour_counts: dict[int, int] = defaultdict(int)
    for dt in day_dts:
        hour_counts[dt.hour] += 1
    hourly_rows = [(f"{h:02d}:00", hour_counts[h]) for h in sorted(hour_counts)]
    return {
        "date_str": sel.strftime("%d.%m.%Y"),
        "count": count,
        "hourly_table": _format_table(hourly_rows, col_header="Час"),
    }


async def _week_list_getter(dialog_manager: DialogManager, **kwargs) -> dict:
    dates = _load_dates(dialog_manager)
    week_counts: dict[date, int] = defaultdict(int)
    for d in dates:
        week_counts[_week_start(d)] += 1
    items = []
    for ws in sorted(week_counts.keys(), reverse=True):
        we = ws + timedelta(days=6)
        items.append({
            "key": ws.isoformat(),
            "label": f"{ws.strftime('%d.%m')} – {we.strftime('%d.%m')} ({week_counts[ws]})",
        })
    return {"weeks": items}


async def _week_detail_getter(dialog_manager: DialogManager, **kwargs) -> dict:
    ws = date.fromisoformat(dialog_manager.dialog_data["selected_week"])
    we = ws + timedelta(days=6)
    dates = _load_dates(dialog_manager)
    day_counts: dict[date, int] = defaultdict(int)
    for d in dates:
        if ws <= d <= we:
            day_counts[d] += 1
    rows = [((ws + timedelta(days=i)).strftime("%d.%m"), day_counts.get(ws + timedelta(days=i), 0))
            for i in range(7)]
    return {
        "week_label": f"{ws.strftime('%d.%m')} – {we.strftime('%d.%m')}",
        "table": _format_table(rows),
    }


async def _month_list_getter(dialog_manager: DialogManager, **kwargs) -> dict:
    dates = _load_dates(dialog_manager)
    month_counts: dict[tuple, int] = defaultdict(int)
    for d in dates:
        month_counts[(d.year, d.month)] += 1
    items = []
    for (y, m) in sorted(month_counts.keys(), reverse=True):
        items.append({
            "key": f"{y}-{m:02d}",
            "label": f"{_MONTHS_RU[m]} {y} ({month_counts[(y, m)]})",
        })
    return {"months": items}


async def _month_detail_getter(dialog_manager: DialogManager, **kwargs) -> dict:
    sel = dialog_manager.dialog_data["selected_month"]
    y, m = int(sel[:4]), int(sel[5:7])
    days_in_month = calendar.monthrange(y, m)[1]
    dates = _load_dates(dialog_manager)
    day_counts: dict[date, int] = defaultdict(int)
    for d in dates:
        if d.year == y and d.month == m:
            day_counts[d] += 1
    rows = [(date(y, m, n).strftime("%d.%m"), day_counts.get(date(y, m, n), 0))
            for n in range(1, days_in_month + 1)]
    return {
        "month_label": f"{_MONTHS_RU[m]} {y}",
        "table": _format_table(rows),
    }


# ── click handlers ────────────────────────────────────────────────────────────

async def _go_main(c: CallbackQuery, b: Button, m: DialogManager) -> None:
    await m.switch_to(StatSG.main)

async def _go_day_list(c: CallbackQuery, b: Button, m: DialogManager) -> None:
    await m.switch_to(StatSG.day_list)

async def _go_week_list(c: CallbackQuery, b: Button, m: DialogManager) -> None:
    await m.switch_to(StatSG.week_list)

async def _go_month_list(c: CallbackQuery, b: Button, m: DialogManager) -> None:
    await m.switch_to(StatSG.month_list)

async def _on_day_selected(c: CallbackQuery, w: Select, m: DialogManager, item_id: str) -> None:
    m.dialog_data["selected_day"] = item_id
    await m.switch_to(StatSG.day_detail)

async def _on_week_selected(c: CallbackQuery, w: Select, m: DialogManager, item_id: str) -> None:
    m.dialog_data["selected_week"] = item_id
    await m.switch_to(StatSG.week_detail)

async def _on_month_selected(c: CallbackQuery, w: Select, m: DialogManager, item_id: str) -> None:
    m.dialog_data["selected_month"] = item_id
    await m.switch_to(StatSG.month_detail)


# ── windows ───────────────────────────────────────────────────────────────────

_main_window = Window(
    Format(
        "<b>Статистика участников</b>\n"
        "Всего: {total}\n\n"
        "<b>Регистрации за последние 7 дней:</b>\n"
        "<code>{seven_day_table}</code>"
    ),
    Row(
        Button(Format("День"), id="go_day", on_click=_go_day_list),
        Button(Format("Неделя"), id="go_week", on_click=_go_week_list),
        Button(Format("Месяц"), id="go_month", on_click=_go_month_list),
    ),
    state=StatSG.main,
    getter=_main_getter,
    parse_mode="HTML",
)

_day_list_window = Window(
    Format("<b>Выберите день:</b>"),
    ScrollingGroup(
        Select(
            Format("{item[label]}"),
            id="day_sel",
            item_id_getter=lambda i: i["key"],
            items="days",
            on_click=_on_day_selected,
        ),
        id="day_sg",
        width=1,
        height=7,
    ),
    Button(Format("◀ Назад"), id="day_back", on_click=_go_main),
    state=StatSG.day_list,
    getter=_day_list_getter,
    parse_mode="HTML",
)

_day_detail_window = Window(
    Format(
        "<b>{date_str}</b>\n"
        "Регистраций: {count}\n\n"
        "<b>По часам:</b>\n"
        "<code>{hourly_table}</code>"
    ),
    Button(Format("◀ Назад"), id="dd_back", on_click=_go_day_list),
    state=StatSG.day_detail,
    getter=_day_detail_getter,
    parse_mode="HTML",
)

_week_list_window = Window(
    Format("<b>Выберите неделю:</b>"),
    ScrollingGroup(
        Select(
            Format("{item[label]}"),
            id="week_sel",
            item_id_getter=lambda i: i["key"],
            items="weeks",
            on_click=_on_week_selected,
        ),
        id="week_sg",
        width=1,
        height=7,
    ),
    Button(Format("◀ Назад"), id="wl_back", on_click=_go_main),
    state=StatSG.week_list,
    getter=_week_list_getter,
    parse_mode="HTML",
)

_week_detail_window = Window(
    Format(
        "<b>Неделя {week_label}</b>\n\n"
        "<code>{table}</code>"
    ),
    Button(Format("◀ Назад"), id="wd_back", on_click=_go_week_list),
    state=StatSG.week_detail,
    getter=_week_detail_getter,
    parse_mode="HTML",
)

_month_list_window = Window(
    Format("<b>Выберите месяц:</b>"),
    ScrollingGroup(
        Select(
            Format("{item[label]}"),
            id="month_sel",
            item_id_getter=lambda i: i["key"],
            items="months",
            on_click=_on_month_selected,
        ),
        id="month_sg",
        width=1,
        height=7,
    ),
    Button(Format("◀ Назад"), id="ml_back", on_click=_go_main),
    state=StatSG.month_list,
    getter=_month_list_getter,
    parse_mode="HTML",
)

_month_detail_window = Window(
    Format(
        "<b>{month_label}</b>\n\n"
        "<code>{table}</code>"
    ),
    Button(Format("◀ Назад"), id="md_back", on_click=_go_month_list),
    state=StatSG.month_detail,
    getter=_month_detail_getter,
    parse_mode="HTML",
)


stat_dialog = Dialog(
    _main_window,
    _day_list_window,
    _day_detail_window,
    _week_list_window,
    _week_detail_window,
    _month_list_window,
    _month_detail_window,
    on_start=_on_dialog_start,
)
