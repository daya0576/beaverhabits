import datetime
import functools
import gc
import hashlib
import os
import re
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
from beaverhabits.frontend.icons import PRIMARY_COLOR
from beaverhabits.logger import logger

WEEK_DAYS = 7
TIME_ZONE_KEY = "timezone"
DARK_MODE_KEY = "dark_mode"

PERIOD_TYPES = D, W, M, Y = "D", "W", "M", "Y"
PERIOD_TYPES_FOR_HUMAN = {D: "Day(s)", W: "Week(s)", M: "Month(s)", Y: "Year(s)"}
PERIOD_TYPE: TypeAlias = Literal["D", "W", "M", "Y"]


def on_connect_task(fn):
    @functools.wraps(fn)
    async def wrapper(*args, **kwargs):
        logger.info(f"On connect: {fn.__name__}")
        return await fn(*args, **kwargs)

    return wrapper


@on_connect_task
async def fetch_user_timezone() -> None:
    timezone = await ui.run_javascript(
        "Intl.DateTimeFormat().resolvedOptions().timeZone"
    )
    app.storage.user[TIME_ZONE_KEY] = timezone
    logger.info(f"User timezone from browser: {timezone}")


async def get_or_create_user_timezone() -> str:
    if timezone := app.storage.user.get(TIME_ZONE_KEY):
        return timezone

    ui.context.client.on_connect(fetch_user_timezone)

    return "UTC"


@on_connect_task
async def fetch_user_dark_mode() -> None:
    if app.storage.user.get(DARK_MODE_KEY) is not None:
        return

    try:
        dark = await ui.run_javascript("Quasar.Dark.isActive")
        app.storage.user[DARK_MODE_KEY] = dark
        logger.info(f"User dark mode from browser: {dark}")
    except Exception as e:
        logger.error(f"Error fetching user dark mode: {e}")


def set_user_dark_mode(dark: bool) -> None:
    if settings.DARK_MODE != None:
        raise ValueError("Dark mode is set in settings, cannot change it manually.")

    try:
        app.storage.user[DARK_MODE_KEY] = dark
        logger.info(f"User dark mode set to: {dark}")
    except Exception as e:
        logger.error(f"Error setting user dark mode: {e}")


def get_user_dark_mode() -> bool | None:
    if settings.DARK_MODE != None:
        return settings.DARK_MODE

    try:
        dark = app.storage.user.get(DARK_MODE_KEY)
    except Exception as e:
        logger.error(f"Error get user dark mode: {e}")
        dark = None

    return dark


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

    msg = MIMEText(body or subject)
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
    current, peak = tracemalloc.get_traced_memory()
    growth = 0
    if _RSS is not None:
        growth = memory - _RSS
    else:
        _RSS = memory

    print(f"[DEBUG]Total memory: {bytes2human(memory)}", end=" ")
    print(bytes2human(growth, r"%(value)+.1f%(symbol)s"), end=" ")
    print(f"Current memory usage: {current / 1024**2:.4f} MB", end=" ")
    print(f"Peak memory usage: {peak / 1024**2:.4f} MB", end=" ")
    print()

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


def format_date_difference(start: datetime.date, today: datetime.date) -> str:
    if today < start:
        return ""

    start = start - datetime.timedelta(days=1)
    diff = relativedelta(today, start)

    parts = []
    if diff.years >= 1:
        parts.append(f"{diff.years} years")

    if diff.months >= 1:
        parts.append(f"{diff.months} months")

    if diff.days >= 1:
        parts.append(f"{diff.days} days")

    return " ".join(parts)


RGB_PATTERN = r"rgb\((\d+),\s*(\d+),\s*(\d+)\)"


def hex2rgb(color: str) -> tuple[int, int, int] | None:
    color = color.lstrip("#")

    # rgb color
    if m := re.match(RGB_PATTERN, color):
        return int(m.group(1)), int(m.group(2)), int(m.group(3))

    # hex color
    if len(color) != 6:
        return None

    try:
        int(color, 16)
    except ValueError:
        return None

    return (
        int(color[0:2], 16),
        int(color[2:4], 16),
        int(color[4:6], 16),
    )


COLORS = {
    # Brand colors
    "primary": PRIMARY_COLOR,
    "secondary": "rgb(38, 166, 154)",
    "accent": "rgb(156, 39, 176)",
    "positive": "rgb(33, 186, 69)",
    "negative": "rgb(193, 0, 21)",
    "info": "rgb(49, 204, 236)",
    "warning": "rgb(242, 192, 55)",
    # Colors provided out of the box
    "red": "#f44336",
    "red-1": "#ffebee",
    "red-2": "#ffcdd2",
    "red-3": "#ef9a9a",
    "red-4": "#e57373",
    "red-5": "#ef5350",
    "red-6": "#f44336",
    "red-7": "#e53935",
    "red-8": "#d32f2f",
    "red-9": "#c62828",
    "red-10": "#b71c1c",
    "red-11": "#ff8a80",
    "red-12": "#ff5252",
    "red-13": "#ff1744",
    "red-14": "#d50000",
    "pink": "#e91e63",
    "pink-1": "#fce4ec",
    "pink-2": "#f8bbd0",
    "pink-3": "#f48fb1",
    "pink-4": "#f06292",
    "pink-5": "#ec407a",
    "pink-6": "#e91e63",
    "pink-7": "#d81b60",
    "pink-8": "#c2185b",
    "pink-9": "#ad1457",
    "pink-10": "#880e4f",
    "pink-11": "#ff80ab",
    "pink-12": "#ff4081",
    "pink-13": "#f50057",
    "pink-14": "#c51162",
    "purple": "#9c27b0",
    "purple-1": "#f3e5f5",
    "purple-2": "#e1bee7",
    "purple-3": "#ce93d8",
    "purple-4": "#ba68c8",
    "purple-5": "#ab47bc",
    "purple-6": "#9c27b0",
    "purple-7": "#8e24aa",
    "purple-8": "#7b1fa2",
    "purple-9": "#6a1b9a",
    "purple-10": "#4a148c",
    "purple-11": "#ea80fc",
    "purple-12": "#e040fb",
    "purple-13": "#d500f9",
    "purple-14": "#aa00ff",
    "deep-purple": "#673ab7",
    "deep-purple-1": "#ede7f6",
    "deep-purple-2": "#d1c4e9",
    "deep-purple-3": "#b39ddb",
    "deep-purple-4": "#9575cd",
    "deep-purple-5": "#7e57c2",
    "deep-purple-6": "#673ab7",
    "deep-purple-7": "#5e35b1",
    "deep-purple-8": "#512da8",
    "deep-purple-9": "#4527a0",
    "deep-purple-10": "#311b92",
    "deep-purple-11": "#b388ff",
    "deep-purple-12": "#7c4dff",
    "deep-purple-13": "#651fff",
    "deep-purple-14": "#6200ea",
    "indigo": "#3f51b5",
    "indigo-1": "#e8eaf6",
    "indigo-2": "#c5cae9",
    "indigo-3": "#9fa8da",
    "indigo-4": "#7986cb",
    "indigo-5": "#5c6bc0",
    "indigo-6": "#3f51b5",
    "indigo-7": "#3949ab",
    "indigo-8": "#303f9f",
    "indigo-9": "#283593",
    "indigo-10": "#1a237e",
    "indigo-11": "#8c9eff",
    "indigo-12": "#536dfe",
    "indigo-13": "#3d5afe",
    "indigo-14": "#304ffe",
    "blue": "#2196f3",
    "blue-1": "#e3f2fd",
    "blue-2": "#bbdefb",
    "blue-3": "#90caf9",
    "blue-4": "#64b5f6",
    "blue-5": "#42a5f5",
    "blue-6": "#2196f3",
    "blue-7": "#1e88e5",
    "blue-8": "#1976d2",
    "blue-9": "#1565c0",
    "blue-10": "#0d47a1",
    "blue-11": "#82b1ff",
    "blue-12": "#448aff",
    "blue-13": "#2979ff",
    "blue-14": "#2962ff",
    "light-blue": "#03a9f4",
    "light-blue-1": "#e1f5fe",
    "light-blue-2": "#b3e5fc",
    "light-blue-3": "#81d4fa",
    "light-blue-4": "#4fc3f7",
    "light-blue-5": "#29b6f6",
    "light-blue-6": "#03a9f4",
    "light-blue-7": "#039be5",
    "light-blue-8": "#0288d1",
    "light-blue-9": "#0277bd",
    "light-blue-10": "#01579b",
    "light-blue-11": "#80d8ff",
    "light-blue-12": "#40c4ff",
    "light-blue-13": "#00b0ff",
    "light-blue-14": "#0091ea",
    "cyan": "#00bcd4",
    "cyan-1": "#e0f7fa",
    "cyan-2": "#b2ebf2",
    "cyan-3": "#80deea",
    "cyan-4": "#4dd0e1",
    "cyan-5": "#26c6da",
    "cyan-6": "#00bcd4",
    "cyan-7": "#00acc1",
    "cyan-8": "#0097a7",
    "cyan-9": "#00838f",
    "cyan-10": "#006064",
    "cyan-11": "#84ffff",
    "cyan-12": "#18ffff",
    "cyan-13": "#00e5ff",
    "cyan-14": "#00b8d4",
    "teal": "#009688",
    "teal-1": "#e0f2f1",
    "teal-2": "#b2dfdb",
    "teal-3": "#80cbc4",
    "teal-4": "#4db6ac",
    "teal-5": "#26a69a",
    "teal-6": "#009688",
    "teal-7": "#00897b",
    "teal-8": "#00796b",
    "teal-9": "#00695c",
    "teal-10": "#004d40",
    "teal-11": "#a7ffeb",
    "teal-12": "#64ffda",
    "teal-13": "#1de9b6",
    "teal-14": "#00bfa5",
    "green": "#4caf50",
    "green-1": "#e8f5e9",
    "green-2": "#c8e6c9",
    "green-3": "#a5d6a7",
    "green-4": "#81c784",
    "green-5": "#66bb6a",
    "green-6": "#4caf50",
    "green-7": "#43a047",
    "green-8": "#388e3c",
    "green-9": "#2e7d32",
    "green-10": "#1b5e20",
    "green-11": "#b9f6ca",
    "green-12": "#69f0ae",
    "green-13": "#00e676",
    "green-14": "#00c853",
    "light-green": "#8bc34a",
    "light-green-1": "#f1f8e9",
    "light-green-2": "#dcedc8",
    "light-green-3": "#c5e1a5",
    "light-green-4": "#aed581",
    "light-green-5": "#9ccc65",
    "light-green-6": "#8bc34a",
    "light-green-7": "#7cb342",
    "light-green-8": "#689f38",
    "light-green-9": "#558b2f",
    "light-green-10": "#33691e",
    "light-green-11": "#ccff90",
    "light-green-12": "#b2ff59",
    "light-green-13": "#76ff03",
    "light-green-14": "#64dd17",
    "lime": "#cddc39",
    "lime-1": "#f9fbe7",
    "lime-2": "#f0f4c3",
    "lime-3": "#e6ee9c",
    "lime-4": "#dce775",
    "lime-5": "#d4e157",
    "lime-6": "#cddc39",
    "lime-7": "#c0ca33",
    "lime-8": "#afb42b",
    "lime-9": "#9e9d24",
    "lime-10": "#827717",
    "lime-11": "#f4ff81",
    "lime-12": "#eeff41",
    "lime-13": "#c6ff00",
    "lime-14": "#aeea00",
    "yellow": "#ffeb3b",
    "yellow-1": "#fffde7",
    "yellow-2": "#fff9c4",
    "yellow-3": "#fff59d",
    "yellow-4": "#fff176",
    "yellow-5": "#ffee58",
    "yellow-6": "#ffeb3b",
    "yellow-7": "#fdd835",
    "yellow-8": "#fbc02d",
    "yellow-9": "#f9a825",
    "yellow-10": "#f57f17",
    "yellow-11": "#ffff8d",
    "yellow-12": "#ffff00",
    "yellow-13": "#ffea00",
    "yellow-14": "#ffd600",
    "amber": "#ffc107",
    "amber-1": "#fff8e1",
    "amber-2": "#ffecb3",
    "amber-3": "#ffe082",
    "amber-4": "#ffd54f",
    "amber-5": "#ffca28",
    "amber-6": "#ffc107",
    "amber-7": "#ffb300",
    "amber-8": "#ffa000",
    "amber-9": "#ff8f00",
    "amber-10": "#ff6f00",
    "amber-11": "#ffe57f",
    "amber-12": "#ffd740",
    "amber-13": "#ffc400",
    "amber-14": "#ffab00",
    "orange": "#ff9800",
    "orange-1": "#fff3e0",
    "orange-2": "#ffe0b2",
    "orange-3": "#ffcc80",
    "orange-4": "#ffb74d",
    "orange-5": "#ffa726",
    "orange-6": "#ff9800",
    "orange-7": "#fb8c00",
    "orange-8": "#f57c00",
    "orange-9": "#ef6c00",
    "orange-10": "#e65100",
    "orange-11": "#ffd180",
    "orange-12": "#ffab40",
    "orange-13": "#ff9100",
    "orange-14": "#ff6d00",
    "deep-orange": "#ff5722",
    "deep-orange-1": "#fbe9e7",
    "deep-orange-2": "#ffccbc",
    "deep-orange-3": "#ffab91",
    "deep-orange-4": "#ff8a65",
    "deep-orange-5": "#ff7043",
    "deep-orange-6": "#ff5722",
    "deep-orange-7": "#f4511e",
    "deep-orange-8": "#e64a19",
    "deep-orange-9": "#d84315",
    "deep-orange-10": "#bf360c",
    "deep-orange-11": "#ff9e80",
    "deep-orange-12": "#ff6e40",
    "deep-orange-13": "#ff3d00",
    "deep-orange-14": "#dd2c00",
    "brown": "#795548",
    "brown-1": "#efebe9",
    "brown-2": "#d7ccc8",
    "brown-3": "#bcaaa4",
    "brown-4": "#a1887f",
    "brown-5": "#8d6e63",
    "brown-6": "#795548",
    "brown-7": "#6d4c41",
    "brown-8": "#5d4037",
    "brown-9": "#4e342e",
    "brown-10": "#3e2723",
    "brown-11": "#d7ccc8",
    "brown-12": "#bcaaa4",
    "brown-13": "#8d6e63",
    "brown-14": "#5d4037",
    "grey": "#9e9e9e",
    "grey-1": "#fafafa",
    "grey-2": "#f5f5f5",
    "grey-3": "#eeeeee",
    "grey-4": "#e0e0e0",
    "grey-5": "#bdbdbd",
    "grey-6": "#9e9e9e",
    "grey-7": "#757575",
    "grey-8": "#616161",
    "grey-9": "#424242",
    "grey-10": "#212121",
    "grey-11": "#f5f5f5",
    "grey-12": "#eeeeee",
    "grey-13": "#bdbdbd",
    "grey-14": "#616161",
    "blue-grey": "#607d8b",
    "blue-grey-1": "#eceff1",
    "blue-grey-2": "#cfd8dc",
    "blue-grey-3": "#b0bec5",
    "blue-grey-4": "#90a4ae",
    "blue-grey-5": "#78909c",
    "blue-grey-6": "#607d8b",
    "blue-grey-7": "#546e7a",
    "blue-grey-8": "#455a64",
    "blue-grey-9": "#37474f",
    "blue-grey-10": "#263238",
    "blue-grey-11": "#cfd8dc",
    "blue-grey-12": "#b0bec5",
    "blue-grey-13": "#78909c",
    "blue-grey-14": "#455a64",
}


def parse_percentage(rate: str) -> float | None:
    try:
        return float(rate)
    except ValueError:
        pass

    if "/" in rate:
        try:
            numerator, denominator = map(float, rate.split("/"))
            return numerator / denominator
        except ValueError:
            return None

    if rate.endswith("%"):
        try:
            percent_value = float(rate[:-1])
            return percent_value / 100.0
        except ValueError:
            return None

    return None


import colorsys


def adjust_color_brightness(r, g, b, rate, sat_strength=0.6):
    """
    Adjust brightness (HLS) with a GitHub-streak-inspired saturation curve.

    :param r, g, b: RGB 0–255.
    :param rate: Lightness multiplier. 0.5 -> 50%, 1.5 -> 150%.
    :param sat_strength: Blend strength toward the curved target saturation (0–1).
    :return: Adjusted (r, g, b) 0–255.
    """
    # Normalize
    r_f, g_f, b_f = r / 255.0, g / 255.0, b / 255.0

    # RGB -> HLS
    h, l, s = colorsys.rgb_to_hls(r_f, g_f, b_f)
    logger.debug(f"Before: RGB=({r},{g},{b}), HLS=({h:.4f}, {l:.4f}, {s:.4f})")

    # Adjust lightness (absolute multiplier)
    l_new = max(0.0, min(1.0, l * rate))

    # Saturation curve: further from mid-lightness -> stronger push toward vivid
    # t in [0,1]: 0 at l=0.5, 1 at l=0 or l=1
    t = abs(l_new - 0.5) * 2.0
    s_target = min(1.0, s + (1.0 - s) * t)  # aim closer to full saturation at extremes
    s_new = s + (s_target - s) * max(0.0, min(1.0, sat_strength))  # blend by strength
    s_new = max(0.0, min(1.0, s_new))

    # HLS -> RGB
    r_new, g_new, b_new = colorsys.hls_to_rgb(h, l_new, s_new)
    r_out, g_out, b_out = (int(round(x * 255)) for x in (r_new, g_new, b_new))

    logger.debug(
        f"After:  RGB=({r_out},{g_out},{b_out}), HLS=({h:.4f}, {l_new:.4f}, {s_new:.4f})"
    )

    return r_out, g_out, b_out
