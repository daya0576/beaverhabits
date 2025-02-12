import datetime
import hashlib
import time

import pytz
from cachetools import TTLCache
from fastapi import HTTPException
from nicegui import app, ui
from starlette import status

from beaverhabits.logging import logger

WEEK_DAYS = 7
TIME_ZONE_KEY = "timezone"
WEEK_OFFSET_KEY = "week_offset"
NAVIGATING_KEY = "is_navigating"


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


def get_week_offset() -> int:
    """Get the current week offset from storage, default to 0 (current week)"""
    return app.storage.user.get(WEEK_OFFSET_KEY, 0)

def set_week_offset(offset: int) -> None:
    """Set the week offset in storage"""
    # Don't allow future weeks
    app.storage.user[WEEK_OFFSET_KEY] = min(0, offset)

def reset_week_offset() -> None:
    """Reset week offset to 0 (current week)"""
    app.storage.user[WEEK_OFFSET_KEY] = 0

def set_navigating(value: bool) -> None:
    """Set whether we're currently navigating between weeks"""
    app.storage.user[NAVIGATING_KEY] = value

def is_navigating() -> bool:
    """Check if we're currently navigating between weeks"""
    return app.storage.user.get(NAVIGATING_KEY, False)

async def get_display_days() -> list[datetime.date]:
    from beaverhabits.configs import settings
    
    today = await get_user_today_date()
    offset = get_week_offset()
    
    if settings.INDEX_HABIT_DATE_COLUMNS == -1:
        # Week view: Monday-Sunday
        days_since_monday = today.weekday()
        current_monday = today - datetime.timedelta(days=days_since_monday)
        # Apply week offset
        start_monday = current_monday + datetime.timedelta(weeks=offset)
        return [start_monday + datetime.timedelta(days=i) for i in range(WEEK_DAYS)]
    else:
        # Past N days view
        days = max(1, settings.INDEX_HABIT_DATE_COLUMNS)
        # Apply offset to the end date
        end_date = today + datetime.timedelta(weeks=offset)
        return [end_date - datetime.timedelta(days=i) for i in reversed(range(days))]

# Keep for backward compatibility
async def dummy_days(days: int) -> list[datetime.date]:
    today = await get_user_today_date()
    return [today - datetime.timedelta(days=i) for i in reversed(range(days))]


def generate_short_hash(name: str) -> str:
    h = hashlib.new("sha1")
    h.update(name.encode())
    h.update(str(datetime.datetime.now()).encode())
    return h.hexdigest()[:6]


def ratelimiter(limit: int, window: int):
    if window <= 0 or window > 60 * 60:
        raise ValueError("Window must be between 1 and 3600 seconds.")
    cache = TTLCache(maxsize=128, ttl=60 * 60)

    def decorator(func):
        async def wrapper(*args, **kwargs):
            current_time = time.time()
            key = f"{args}_{kwargs}"

            # Update timestamps
            if key not in cache:
                cache[key] = [current_time]
            else:
                cache[key].append(current_time)
            cache[key] = [i for i in cache[key] if i >= current_time - window]

            # Check with threshold
            if len(cache[key]) > limit:
                logger.warning(
                    f"Rate limit exceeded for {func.__name__} with key {key}"
                )
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Try again later.",
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator
