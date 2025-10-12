import datetime
from datetime import timedelta

from nicegui import ui


def build_weeks_text_alternative(
    today: datetime.date, ticked_days: list[datetime.date]
) -> str:
    text = "last 3 weeks progress: "
    for i in range(3):
        end = today - timedelta(days=today.weekday() + 7 * i)
        start = end - timedelta(days=7 * (i + 1))
        count = sum(1 for day in ticked_days if start <= day < end)
        text += f"{count} "

    return text


def build_months_text_alternative(
    today: datetime.date, ticked_days: list[datetime.date]
) -> str:
    text = "last 3 months progress: "

    end = today
    for _ in range(3):
        end = end.replace(day=1) - timedelta(days=1)
        start = end.replace(day=1) - timedelta(days=1)
        count = sum(1 for day in ticked_days if start <= day <= end)
        text += f"{count} "

    return text


def description(text: str):
    # l = ui.label(text).classes("hidden")
    # return l.props('aria-hidden="false" tabindex="0" aria-label="{text}"')
    with ui.element("p").classes("hidden"):
        ui.html(text, sanitize=False)


def index_total_badge_alternative_text(today: datetime.date, habit):
    return f"{build_weeks_text_alternative(today, habit.ticked_days)}; {build_months_text_alternative(today, habit.ticked_days)}"
