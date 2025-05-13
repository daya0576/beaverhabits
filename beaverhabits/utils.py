import datetime
import gc
import hashlib
import os
import smtplib
import time
import tracemalloc
from collections import Counter
from email.mime.text import MIMEText
from functools import wraps
from typing import Literal, TypeAlias

import psutil
import pytz
from cachetools import TTLCache
from dateutil.relativedelta import relativedelta
from fastapi import HTTPException
from nicegui import app, ui
from psutil._common import bytes2human
from starlette import status

from beaverhabits.configs import settings
from beaverhabits.logger import logger

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


def timeit(threshold: float):
    """
    Decorator to measure the execution time of a function and log it if it exceeds a threshold.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            result = func(*args, **kwargs)
            end_time = time.perf_counter()
            total_time = (end_time - start_time) * 1000  # Convert to milliseconds
            if total_time > threshold:
                logger.warning(
                    f"Function {func.__name__} took {total_time:.4f} milliseconds"
                )
            return result

        return wrapper

    return decorator


def send_email(subject: str, body: str, recipients: list[str]):
    sender = settings.SMTP_EMAIL_USERNAME
    password = settings.SMTP_EMAIL_PASSWORD

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp_server:
        smtp_server.login(sender, password)
        smtp_server.sendmail(sender, recipients, msg.as_string())


class MemoryMonitor:

    def __init__(self, source: str, diff_threshold: int = 0, total_threshold: int = 0):
        self.source = source
        self.last_mem: int = 0
        self.obj_count: dict[str, int] = {}

        self.diff_threshold: int = diff_threshold
        self.total_threshold: int = total_threshold

    def _key(self, obj: object) -> str:
        try:
            return f"{type(obj).__name__},{obj.__class__.__module__}"
        except Exception as e:
            logger.warning(f"Error getting key for object: {e}")
            return f"{type(obj).__name__},<unknown>"

    def print_stats(self) -> None:
        gc.collect()

        # print memory usage
        memory = psutil.Process(os.getpid()).memory_info().rss
        growth = memory - self.last_mem
        print(f"{self.source} total memory: {bytes2human(memory)}", end=" ")
        print(bytes2human(growth, r"%(value)+.1f%(symbol)s"), end=" ")

        # print objects by types
        counter: Counter = Counter()
        for obj in gc.get_objects():
            counter[self._key(obj)] += 1
        for cls, count in counter.most_common():
            prev_count = self.obj_count.get(cls, 0)
            if (
                abs(count - prev_count) > self.diff_threshold
                and count > self.total_threshold
            ):
                print(f"{cls}={count} ({count - prev_count:+})", end=" ")
        print()

        self.obj_count = {cls: count for cls, count in counter.items() if count > 0}
        self.last_mem = memory


_SNAPSHOT = _RSS = None


def print_memory_snapshot():
    global _SNAPSHOT, _RSS

    memory = psutil.Process(os.getpid()).memory_info().rss
    if _RSS is not None:
        growth = memory - _RSS
        print(f"[DEBUG]Total memory: {bytes2human(memory)}", end=" ")
        print(bytes2human(growth, r"%(value)+.1f%(symbol)s"), end=" ")
        print()
    else:
        _RSS = memory

    new_snapshot = tracemalloc.take_snapshot()
    new_snapshot = new_snapshot.filter_traces(
        (
            tracemalloc.Filter(False, "<unknown>"),
            tracemalloc.Filter(False, "<frozen importlib._bootstrap_external>"),
            tracemalloc.Filter(False, "<frozen importlib._bootstrap>"),
            tracemalloc.Filter(False, tracemalloc.__file__),
        )
    )

    # print top 10 memory usage with traceback
    top_stats = new_snapshot.statistics("traceback")
    for stat in top_stats[:10]:
        print(f"[DEBUG Traceback]Top memory usage:", end=" ")
        print("%s memory blocks: %.1f KiB" % (stat.count, stat.size / 1024))
        for line in stat.traceback.format():
            print("[DEBUG Traceback]", line)
        print("[DEBUG Traceback]", "=" * 30)

    # print top 10 diff memory usage
    if _SNAPSHOT is not None:
        diff = new_snapshot.compare_to(_SNAPSHOT, "lineno")
        if diff:
            print("[DEBUG Diff]Snapshot diff:", end=":")
            for stat in diff[:10]:
                if stat.size_diff < 0:
                    continue
                print(stat, end=";")
            print()
        else:
            print("No memory usage difference")
    else:
        _SNAPSHOT = new_snapshot
