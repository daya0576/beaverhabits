import asyncio
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request

from beaverhabits.app.app import init_auth_routes
from beaverhabits.app.db import create_db_and_tables
from beaverhabits.configs import settings
from beaverhabits.logger import logger
from beaverhabits.routes.api import init_api_routes
from beaverhabits.routes.metrics import init_metrics_routes
from beaverhabits.routes.routes import init_gui_routes
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


# auth
init_metrics_routes(app)
init_auth_routes(app)
init_api_routes(app)
if settings.ENABLE_PLAN:
    from beaverhabits.plan.paddle import init_paddle_routes

    init_paddle_routes(app)
init_gui_routes(app)


if settings.SENTRY_DSN:
    logger.info("Setting up Sentry...")
    import sentry_sdk

    sentry_sdk.init(settings.SENTRY_DSN, send_default_pii=True)


@app.middleware("http")
async def Digest(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = (time.perf_counter() - start_time) * 1000
    response.headers["X-Process-Time"] = str(process_time)
    logger.info(
        f"DIGEST {request.method} {request.url.path} {response.status_code} {process_time:.0f}ms"
    )
    return response


if __name__ == "__main__":
    import uvicorn

    if settings.DEBUG:
        # start fastapi app
        logger.info("Starting in debug mode")
        uvicorn.run(app=app, host="0.0.0.0", port=9001, workers=1)
    else:
        raise RuntimeError("This script should not be run directly in production.")
