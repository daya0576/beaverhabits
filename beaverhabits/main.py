from contextlib import asynccontextmanager
from fastapi import FastAPI

from .app.app import init_auth_routes
from .app.db import create_db_and_tables
from .gui import init_gui_routes


@asynccontextmanager
async def lifespan(_: FastAPI):
    await create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/")
def read_root():
    return {"Hello": "World"}


# auth
init_auth_routes(app)
init_gui_routes(app)


if __name__ == "__main__":
    print(
        'Please start the app with the "uvicorn" command as shown in the start.sh script'
    )
