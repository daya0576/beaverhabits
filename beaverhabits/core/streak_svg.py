"""Generate a standalone SVG image of a habit's streak heatmap."""

import calendar
import datetime
from dataclasses import dataclass

CELL_SIZE = 18
CELL_GAP = 2
CELL_STRIDE = CELL_SIZE + CELL_GAP
CELL_RADIUS = 2.5
WEEK_DAYS = 7
FONT_FAMILY = "Roboto, -apple-system, Helvetica Neue, Helvetica, Arial, sans-serif"


@dataclass(frozen=True)
class Theme:
    bg_color: str
    cell_unchecked: str
    cell_checked: str
    text_color: str
    cell_text_color: str
    header_color: str


DARK = Theme(
    bg_color="#1d1d1d",
    cell_unchecked="#363636",
    cell_checked="#6796cf",
    text_color="#ffffff",
    cell_text_color="#ffffff",
    header_color="#b8b9be",
)

LIGHT = Theme(
    bg_color="#ffffff",
    cell_unchecked="#dedede",
    cell_checked="#6796cf",
    text_color="#1d1d1d",
    cell_text_color="#646464",
    header_color="#4b5563",
)


def _generate_calendar_days(
    today: datetime.date, total_weeks: int, firstweekday: int = calendar.MONDAY
) -> list[list[datetime.date]]:
    lastweekday = (firstweekday - 1) % 7
    days_delta = (lastweekday - today.weekday()) % 7
    last_date = today + datetime.timedelta(days=days_delta)
    return [
        [
            last_date - datetime.timedelta(days=i, weeks=j)
            for j in reversed(range(total_weeks))
        ]
        for i in reversed(range(WEEK_DAYS))
    ]


def _generate_headers(days: list[datetime.date]) -> list[str]:
    result = []
    month = None
    for day in days:
        if day.month != month:
            result.append(calendar.month_abbr[day.month])
            month = day.month
        else:
            result.append("")
    return result


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def generate_streak_svg(
    habit_name: str,
    ticked_days: set[datetime.date],
    today: datetime.date,
    weeks: int = 15,
    firstweekday: int = calendar.MONDAY,
    habit_url: str | None = None,
    dark: bool = True,
) -> str:
    theme = DARK if dark else LIGHT
    data = _generate_calendar_days(today, weeks, firstweekday)
    headers = _generate_headers(data[0])
    week_day_abbr = [calendar.day_abbr[(firstweekday + i) % 7] for i in range(WEEK_DAYS)]

    # Layout
    left_pad = 14
    top_pad = 48
    header_height = 4
    weekday_label_width = 24

    grid_width = weeks * CELL_STRIDE
    total_width = left_pad + grid_width + weekday_label_width + 10
    total_height = top_pad + header_height + WEEK_DAYS * CELL_STRIDE + 12

    parts: list[str] = []

    # Title
    title_text = (
        f"<text x='{total_width // 2}' y='28' text-anchor='middle' "
        f"fill='{theme.text_color}' font-size='14' "
        f"style='font-family: {FONT_FAMILY};'>"
        f"{_escape(habit_name)}</text>"
    )
    if habit_url:
        parts.append(
            f"<a href='{_escape(habit_url)}' target='_blank'>{title_text}</a>"
        )
    else:
        parts.append(title_text)

    # Month headers
    for col_i, header in enumerate(headers):
        if header:
            x = left_pad + col_i * CELL_STRIDE + CELL_SIZE // 2
            parts.append(
                f"<text x='{x}' y='{top_pad}' text-anchor='middle' "
                f"fill='{theme.header_color}' font-size='9' "
                f"style='font-family: {FONT_FAMILY};'>{header}</text>"
            )

    # Day grid
    for row_i, weekday_days in enumerate(data):
        for col_i, day in enumerate(weekday_days):
            if day > today:
                continue
            x = left_pad + col_i * CELL_STRIDE
            y = top_pad + header_height + row_i * CELL_STRIDE
            checked = day in ticked_days
            cell_color = theme.cell_checked if checked else theme.cell_unchecked
            text_color = theme.text_color if checked else theme.cell_text_color
            parts.append(
                f"<rect x='{x}' y='{y}' width='{CELL_SIZE}' height='{CELL_SIZE}' "
                f"rx='{CELL_RADIUS}' fill='{cell_color}'/>"
                f"<text x='{x + CELL_SIZE // 2}' y='{y + CELL_SIZE // 2}' "
                f"text-anchor='middle' dominant-baseline='central' "
                f"fill='{text_color}' font-size='8' "
                f"style='font-family: {FONT_FAMILY};'>{day.day}</text>"
            )

        # Weekday label
        lx = left_pad + weeks * CELL_STRIDE + 4
        ly = top_pad + header_height + row_i * CELL_STRIDE + CELL_SIZE // 2
        parts.append(
            f"<text x='{lx}' y='{ly}' dominant-baseline='central' "
            f"fill='{theme.header_color}' font-size='9' "
            f"style='font-family: {FONT_FAMILY};'>{week_day_abbr[row_i]}</text>"
        )

    inner = "\n    ".join(parts)
    border = "" if dark else " stroke='#e0e0e0' stroke-width='1'"
    return (
        f"<svg xmlns='http://www.w3.org/2000/svg' xmlns:xlink='http://www.w3.org/1999/xlink' "
        f"width='{total_width}' height='{total_height}'>\n"
        f"  <rect width='100%' height='100%' fill='{theme.bg_color}' rx='8'{border}/>\n"
        f"    {inner}\n"
        f"</svg>"
    )
