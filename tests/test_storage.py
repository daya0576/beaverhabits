import pytest
from nicegui import ui
from nicegui.testing import Screen

from beaverhabits import views
from beaverhabits.app.auth import user_authenticate, user_create
from beaverhabits.app.db import create_db_and_tables
from beaverhabits.configs import StorageType, settings
from beaverhabits.utils import dummy_days

EMAIL = "test@test.com"
PASSWORD = "test"


async def get_or_create_user():
    await create_db_and_tables()
    user = await user_authenticate(email=EMAIL, password=PASSWORD)
    if not user:
        user = await user_create(email="test@test.com", password="test")
    return user


@pytest.mark.asyncio
async def test_user_session(screen: Screen):
    @ui.page("/")
    async def page():
        days = await dummy_days(5)
        habit_list = views.get_or_create_session_habit_list(days)
        assert habit_list is not None

    screen.open("/", timeout=60)


@pytest.mark.asyncio
async def test_user_db(screen: Screen):
    settings.HABITS_STORAGE = StorageType.USER_DATABASE
    user = await get_or_create_user()

    @ui.page("/")
    async def page():
        days = await dummy_days(5)
        habit_list = await views.get_or_create_user_habit_list(user, days)
        assert habit_list is not None

    screen.open("/", timeout=60)


@pytest.mark.asyncio
async def test_user_disk(screen: Screen):
    settings.HABITS_STORAGE = StorageType.USER_DISK
    user = await get_or_create_user()

    @ui.page("/")
    async def page():
        days = await dummy_days(5)
        habit_list = await views.get_or_create_user_habit_list(user, days)
        assert habit_list is not None

    screen.open("/", timeout=60)
