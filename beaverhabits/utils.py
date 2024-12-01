import datetime
import hashlib

import pytz
from nicegui import app, ui

from beaverhabits.logging import logger

WEEK_DAYS = 7
TIME_ZONE_KEY = "timezone"


async def fetch_user_timezone() -> None:
    timezone = await ui.run_javascript(
        "Intl.DateTimeFormat().resolvedOptions().timeZone"
    )
    app.storage.user[TIME_ZONE_KEY] = timezone
    logger.info(f"User timezone from browser: {timezone}")


async def get_or_create_user_timezone() -> str:
    logger.info("Getting user timezone...")
    if timezone := app.storage.user.get(TIME_ZONE_KEY):
        logger.info(f"User timezone from storage: {timezone}")
        return timezone

    ui.context.client.on_connect(fetch_user_timezone)

    return "UTC"


async def get_user_today_date() -> datetime.date:
    timezone = await get_or_create_user_timezone()
    return datetime.datetime.now(pytz.timezone(timezone)).date()


async def dummy_days(days: int) -> list[datetime.date]:
    today = await get_user_today_date()
    return [today - datetime.timedelta(days=i) for i in reversed(range(days))]


def generate_short_hash(name: str) -> str:
    h = hashlib.new("sha1")
    h.update(name.encode())
    h.update(str(datetime.datetime.now()).encode())
    return h.hexdigest()[:6]
