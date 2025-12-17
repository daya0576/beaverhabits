import uuid

import pytest
from nicegui import ui
from nicegui.testing import Screen, User

from beaverhabits import views
from beaverhabits.app.auth import user_authenticate, user_create
from beaverhabits.app.db import create_db_and_tables, engine
from beaverhabits.configs import StorageType, settings
from beaverhabits.utils import dummy_days

EMAIL = f"{uuid.uuid1()}@test.com"
PASSWORD = "test"


async def get_or_create_user():
    await create_db_and_tables()

    user = await user_authenticate(email=EMAIL, password=PASSWORD)
    if not user:
        user = await user_create(email=EMAIL, password=PASSWORD)
    return user


async def test_user_session(user: User):
    @ui.page("/")
    async def page():
        days = await dummy_days(5)
        habit_list = views.get_or_create_session_habit_list(days)
        assert habit_list is not None

    await user.open("/")


async def test_user_db(user: User):
    settings.HABITS_STORAGE = StorageType.USER_DATABASE
    _user = await get_or_create_user()

    @ui.page("/")
    async def page():
        days = await dummy_days(5)
        habit_list = await views.get_or_create_user_habit_list(_user, days)
        assert habit_list is not None

        habit_list = await views.get_user_habit_list(_user)
        assert habit_list is not None

    await user.open("/")

    # close db connection after test

    await engine.dispose()


async def test_user_disk(user: User):
    settings.HABITS_STORAGE = StorageType.USER_DISK
    _user = await get_or_create_user()

    @ui.page("/")
    async def page():
        days = await dummy_days(5)
        habit_list = await views.get_or_create_user_habit_list(_user, days)
        assert habit_list is not None

        habit_list = await views.get_user_habit_list(_user)
        assert habit_list is not None

    await user.open("/")
    # close db connection after test
    await engine.dispose()
