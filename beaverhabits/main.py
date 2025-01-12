import asyncio
import logging
from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI
from nicegui import ui

from beaverhabits.api import init_api_routes
from beaverhabits.app import crud

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


@app.get("/health")
def read_root():
    return {"Hello": "World"}


@app.get("/users/count", include_in_schema=False)
async def user_count():
    return {"count": await crud.get_user_count()}


# auth
init_auth_routes(app)
init_api_routes(app)
init_gui_routes(app)


# sentry
if settings.SENTRY_DSN:
    logger.info("Setting up Sentry...")
    sentry_sdk.init(settings.SENTRY_DSN)


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

if __name__ == "__main__":
    print(
        'Please start the app with the "uvicorn"'
        "command as shown in the start.sh script",
    )
