from fastapi import APIRouter, Depends, FastAPI

from beaverhabits import views
from beaverhabits.app.db import User
from beaverhabits.app.users import current_active_user
from beaverhabits.storage.storage import HabitListBuilder, HabitStatus

api_router = APIRouter()


@api_router.get("/habits", tags=["habits"])
async def get_habits(
    status: HabitStatus = HabitStatus.ACTIVE,
    user: User = Depends(current_active_user),
):
    habit_list = await views.get_user_habit_list(user)
    if not habit_list:
        return []

    habits = HabitListBuilder(habit_list).status(status).build()
    return [{"id": x.id, "name": x.name} for x in habits]


def init_api_routes(app: FastAPI) -> None:
    app.include_router(api_router, prefix="/api")
