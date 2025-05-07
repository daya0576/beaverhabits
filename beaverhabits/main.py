import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, status
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


# auth
init_auth_routes(app)
init_api_routes(app)
init_gui_routes(app)


if __name__ == "__main__":
    import uvicorn

    if settings.DEBUG:
        # start fastapi app
        logger.info("Starting in debug mode")
        uvicorn.run(app=app, host="0.0.0.0", port=9001, workers=1)
    else:
        raise RuntimeError("This script should not be run directly in production.")
