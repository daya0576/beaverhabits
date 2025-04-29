import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, status
from fastapi.responses import Response
from nicegui import ui
from pydantic import BaseModel

from beaverhabits.api import init_api_routes
from beaverhabits.app.app import init_auth_routes
from beaverhabits.app.db import create_db_and_tables
from beaverhabits.configs import settings
from beaverhabits.logger import logger
from beaverhabits.routes import init_gui_routes
from beaverhabits.scheduler import daily_backup_task

logger.info("Starting BeaverHabits...")


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Enable warning msg
    if settings.DEBUG:
        logger.info("Debug mode enabled")
        loop = asyncio.get_running_loop()
        loop.set_debug(True)
        loop.slow_callback_duration = 0.01

    # Create new database and tables if they don't exist
    await create_db_and_tables()

    # Start scheduler
    if settings.ENABLE_DAILY_BACKUP:
        loop = asyncio.get_event_loop()
        loop.create_task(daily_backup_task())

    yield


app = FastAPI(lifespan=lifespan)


class HealthCheck(BaseModel):
    """Response model to validate and return when performing a health check."""

    status: str = "OK"
    stats: dict = {}


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


METRICS_TEMPLATE = """\
# HELP rss Resident Set Size in bytes.
# TYPE rss gauge
rss {rss}
# TYPE mem_total gauge
mem_total {mem_total}
# TYPE mem_available gauge
mem_available {mem_available}
"""


@app.get("/metrics", tags=["metrics"])
def exporter():
    # Memory heap and stats
    process = psutil.Process()
    memory_info = process.memory_info()
    ram = psutil.virtual_memory()
    text = METRICS_TEMPLATE.format(
        rss=memory_info.rss,  # non-swapped physical memory a process has used
        mem_total=ram.total,  # total physical memory
        mem_available=ram.available,  # available memory
    )
    return Response(content=text, media_type="text/plain")


# auth
init_auth_routes(app)
init_api_routes(app)
if settings.ENABLE_PLAN:
    from beaverhabits.plan.paddle import init_paddle_routes

    init_paddle_routes(app)
init_gui_routes(app)


# sentry
if settings.SENTRY_DSN:
    import sentry_sdk

    logger.info("Setting up Sentry...")
    sentry_sdk.init(
        settings.SENTRY_DSN,
        traces_sample_rate=1.0,
        profile_session_sample_rate=1.0,
        profile_lifecycle="trace",
    )


if settings.DEBUG:
    import os
    import tracemalloc
    from tracemalloc import Snapshot

    import psutil
    from psutil._common import bytes2human

    class MemoryMonitor:

        def __init__(self, snapshot: Snapshot) -> None:
            self.last_mem: int = 0
            self.last_snapshot = snapshot

        def print_stats(self) -> None:
            # print memory diff
            memory = psutil.Process(os.getpid()).memory_info().rss
            growth = memory - self.last_mem
            if growth < 1024:
                return

            print(f"Memory: {bytes2human(memory)} ({bytes2human(growth)})")

            # print heap
            snapshot = tracemalloc.take_snapshot()
            top_stats = snapshot.compare_to(self.last_snapshot, "lineno")
            print("[ Top 10 differences ]")
            for stat in top_stats[:10]:
                print(stat)

            self.last_mem = memory
            self.last_snapshot = snapshot

    tracemalloc.start()
    monitor = MemoryMonitor(tracemalloc.take_snapshot())
    ui.timer(5.0, monitor.print_stats)


if __name__ == "__main__":
    import os

    import uvicorn

    if settings.DEBUG:
        # start fastapi app
        logger.info("Starting in debug mode")
        uvicorn.run(app=app, host="0.0.0.0", port=9001, workers=1)
    else:
        raise RuntimeError("This script should not be run directly in production.")
