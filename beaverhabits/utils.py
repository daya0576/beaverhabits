import datetime
import hashlib

import pytz
from nicegui import app, ui

from beaverhabits.logging import logger

WEEK_DAYS = 7
TIME_ZONE_KEY = "timezone"


async def get_or_create_user_timezone() -> str:
    if timezone := app.storage.user.get(TIME_ZONE_KEY):
        logger.info(f"User timezone from storage: {timezone}")
        return timezone

    try:
        await ui.context.client.connected(timeout=0.5)
        timezone = await ui.run_javascript(
            "Intl.DateTimeFormat().resolvedOptions().timeZone"
        )
        app.storage.user[TIME_ZONE_KEY] = timezone or "UTC"
        logger.warning(f"User timezone from browser: {timezone}")
    except Exception as e:
        logger.error("Get browser timezone failed", e)
        return "UTC"

    return timezone


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
