import datetime
import hashlib
import pytz

from nicegui import app, ui

from beaverhabits.logging import logger

WEEK_DAYS = 7


def get_user_timezone() -> str:
    return app.storage.user.get("timezone", "UTC")


async def get_or_create_user_timezone() -> str:
    timezone = app.storage.user.get("timezone")
    if not timezone:
        timezone = await ui.run_javascript(
            "Intl.DateTimeFormat().resolvedOptions().timeZone"
        )
        logger.info(f"User timezone: {timezone}")
        app.storage.user["timezone"] = timezone

    return timezone


def dummy_days(days: int) -> list[datetime.date]:
    today = datetime.date.today()
    return [today - datetime.timedelta(days=i) for i in reversed(range(days))]


def generate_short_hash(name: str) -> str:
    h = hashlib.new("sha1")
    h.update(name.encode())
    h.update(str(datetime.datetime.now()).encode())
    return h.hexdigest()[:6]
