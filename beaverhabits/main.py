import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
import sentry_sdk

from .app.app import init_auth_routes
from .app.db import create_db_and_tables
from .configs import settings
from .logging import logger
from .routes import init_gui_routes

logger.info("Starting BeaverHabits...")


@asynccontextmanager
async def lifespan(_: FastAPI):
    logging.info("Creating database and tables")
    await create_db_and_tables()
    logging.info("Database and tables created")
    yield


app = FastAPI(lifespan=lifespan)
if settings.is_dev():

    @app.on_event("startup")
    def startup():
        loop = asyncio.get_running_loop()
        loop.set_debug(True)
        loop.slow_callback_duration = 0.05


@app.get("/health")
def read_root():
    return {"Hello": "World"}


# auth
init_auth_routes(app)
init_gui_routes(app)

# sentry
if settings.SENTRY_DSN:
    sentry_sdk.init(settings.SENTRY_DSN)


if __name__ == "__main__":
    print(
        'Please start the app with the "uvicorn"'
        "command as shown in the start.sh script",
    )
