import datetime
import hashlib
import time
from functools import wraps
from typing import Literal, TypeAlias

import pytz
from cachetools import TTLCache
from dateutil.relativedelta import relativedelta
from fastapi import HTTPException
from nicegui import app, ui
from starlette import status

from beaverhabits.logging import logger

WEEK_DAYS = 7
TIME_ZONE_KEY = "timezone"

PERIOD_TYPES = D, W, M, Y = "D", "W", "M", "Y"
PERIOD_TYPES_FOR_HUMAN = {D: "Day(s)", W: "Week(s)", M: "Month(s)", Y: "Year(s)"}
PERIOD_TYPE: TypeAlias = Literal["D", "W", "M", "Y"]


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


def get_period_fist_day(date: datetime.date, period_type: str) -> datetime.date:
    if period_type == W:
        date = date - datetime.timedelta(days=date.weekday())
    elif period_type == M:
        date = date.replace(day=1)
    elif period_type == Y:
        date = date.replace(month=1, day=1)
    return date


def date_move(
    date: datetime.date, step: int, period_type: PERIOD_TYPE
) -> datetime.date:
    if date in (datetime.date.min, datetime.date.max):
        return date

    if period_type == D:
        date = date + datetime.timedelta(days=step)
    elif period_type == W:
        date = date + datetime.timedelta(weeks=step)
    elif period_type == M:
        date = date + relativedelta(months=step)
    elif period_type == Y:
        date = date.replace(year=date.year + step)
    return date


def timeit(func):
    @wraps(func)
    def timeit_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        total_time = end_time - start_time
        logger.info(f"Function {func.__name__} Took {total_time:.4f} seconds")
        return result

    return timeit_wrapper
