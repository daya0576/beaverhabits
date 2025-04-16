import asyncio
from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI, status
from nicegui import ui
from pydantic import BaseModel

from beaverhabits import views
from beaverhabits.api import init_api_routes
from beaverhabits.plan.paddle import init_paddle_routes

from .app.app import init_auth_routes
from .app.db import create_db_and_tables
from .configs import settings
from .logging import logger
from .routes import init_gui_routes

logger.info("Starting BeaverHabits...")


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("Creating database and tables")
    await create_db_and_tables()
    logger.info("Database and tables created")
    yield


app = FastAPI(lifespan=lifespan)

if settings.is_dev():

    @app.on_event("startup")
    def startup():
        loop = asyncio.get_running_loop()
        loop.set_debug(True)
        loop.slow_callback_duration = 0.01


class HealthCheck(BaseModel):
    """Response model to validate and return when performing a health check."""

    status: str = "OK"


@app.get(
    "/health",
    tags=["healthcheck"],
    summary="Perform a Health Check",
    response_description="Return HTTP Status Code 200 (OK)",
    status_code=status.HTTP_200_OK,
    response_model=HealthCheck,
)
def read_root():
    return HealthCheck(status="OK")


# auth
init_auth_routes(app)
init_api_routes(app)
init_paddle_routes(app)
init_gui_routes(app)


# sentry
if settings.SENTRY_DSN:
    logger.info("Setting up Sentry...")
    sentry_sdk.init(
        settings.SENTRY_DSN,
        traces_sample_rate=1.0,
        profile_session_sample_rate=1.0,
        profile_lifecycle="trace",
    )


if settings.DEBUG:
    import gc
    import os
    from collections import Counter

    import psutil
    from psutil._common import bytes2human

    class MemoryMonitor:

        def __init__(self) -> None:
            self.last_mem: int = 0
            self.obj_count: dict[str, int] = {}

        def print_stats(self) -> None:
            gc.collect()
            memory = psutil.Process(os.getpid()).memory_info().rss
            growth = memory - self.last_mem
            print(bytes2human(memory), end=" ")
            print(
                bytes2human(growth, r"%(value)+.1f%(symbol)s") if growth else "",
                end=" ",
            )
            counter: Counter = Counter()
            for obj in gc.get_objects():
                counter[type(obj).__name__] += 1
            for cls, count in counter.items():
                prev_count = self.obj_count.get(cls, 0)
                if count != prev_count:
                    print(f"{cls}={count} ({count - prev_count:+})", end=" ")
                    self.obj_count[cls] = count
            self.obj_count = {
                cls: count for cls, count in self.obj_count.items() if count > 0
            }
            print()
            self.last_mem = memory

    monitor = MemoryMonitor()
    ui.timer(5.0, monitor.print_stats)


if settings.ENABLE_DAILY_BACKUP:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from pytz import utc

    scheduler = AsyncIOScheduler(timezone=utc)
    scheduler.start()

    @scheduler.scheduled_job("cron", hour=0, minute=0)
    async def backup():
        logger.info("Starting daily backup...")
        await views.backup_all_users()
        logger.info("Daily backup completed")


if __name__ == "__main__":
    print(
        'Please start the app with the "uvicorn"'
        "command as shown in the start.sh script",
    )
