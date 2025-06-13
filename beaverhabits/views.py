import asyncio
import datetime
import json
import random
from dataclasses import dataclass
from typing import Sequence

from fastapi import HTTPException
from nicegui import app, run, ui

from beaverhabits import const
from beaverhabits.app import crud
from beaverhabits.app.auth import (
    user_check_token,
    user_create,
    user_create_reset_token,
    user_create_token,
    user_get_by_email,
    user_reset_password,
)
from beaverhabits.app.crud import get_customer_list, get_user_count, get_user_list
from beaverhabits.app.db import User
from beaverhabits.configs import settings
from beaverhabits.core.backup import backup_to_telegram
from beaverhabits.frontend.components import redirect
from beaverhabits.logger import logger
from beaverhabits.storage import get_user_dict_storage, session_storage
from beaverhabits.storage.dict import DAY_MASK, DictHabitList
from beaverhabits.storage.meta import GUI_ROOT_PATH
from beaverhabits.storage.storage import Habit, HabitList, HabitListBuilder, HabitStatus
from beaverhabits.utils import generate_short_hash, ratelimiter, send_email

user_storage = get_user_dict_storage()


def dummy_habit_list(days: list[datetime.date]):
    pick = lambda: random.randint(0, 4) == 0
    items = [
        {
            "id": generate_short_hash(name),
            "name": name,
            "records": [
                {"day": day.strftime(DAY_MASK), "done": True} for day in days if pick()
            ],
        }
        for name in ("Order pizz", "Running", "Table Tennis", "Clean", "Call mom")
    ]
    return DictHabitList({"habits": items})


def get_session_habit_list() -> HabitList | None:
    return session_storage.get_user_habit_list()


async def get_session_habit(habit_id: str) -> Habit | None:
    habit_list = get_session_habit_list()
    if habit_list is None:
        return None

    habit = await habit_list.get_habit_by(habit_id)
    if habit is None:
        return None

    return habit


def get_or_create_session_habit_list(days: list[datetime.date]) -> HabitList:
    if (habit_list := get_session_habit_list()) is not None:
        return habit_list

    session_storage.save_user_habit_list(dummy_habit_list(days))

    habit_list = get_session_habit_list()
    if habit_list is None:
        raise Exception("Panic! Failed to load habit list")
    return habit_list


async def get_user_habit_list(user: User) -> HabitList:
    try:
        return await user_storage.get_user_habit_list(user)
    except Exception:
        raise HTTPException(
            status_code=404,
            detail="The habit list data may be broken or missing, please contact the administrator. /logout",
        )


async def get_user_habit(user: User, habit_id: str) -> Habit:
    habit_list = await get_user_habit_list(user)

    habit = await habit_list.get_habit_by(habit_id)
    if habit is None:
        raise HTTPException(status_code=404, detail="Habit not found")

    return habit


async def create_user_habit(user: User, name: str) -> str:
    habit_list = await get_user_habit_list(user)
    return await habit_list.add(name)


async def remove_user_habit(user: User, habit: Habit) -> None:
    habit_list = await get_user_habit_list(user)
    await habit_list.remove(habit)


async def get_or_create_user_habit_list(
    user: User, days: list[datetime.date]
) -> HabitList:
    try:
        return await get_user_habit_list(user)
    except HTTPException:
        logger.warning(f"Failed to load habit list for user {user.email}")

    logger.info(f"Creating dummy habit list for user {user.email}")
    await user_storage.init_user_habit_list(user, dummy_habit_list(days))

    habit_list = await get_user_habit_list(user)
    if habit_list is None:
        raise Exception("Panic! Failed to load habit list")
    return habit_list


async def export_user_habit_list(habit_list: HabitList, user_identify: str) -> None:
    habits = HabitListBuilder(habit_list).status(HabitStatus.ACTIVE).build()

    # json to binary
    now = datetime.datetime.now()
    if isinstance(habit_list, DictHabitList):
        export_d = {
            "user_email": user_identify,
            "exported_at": now.strftime("%Y-%m-%d %H:%M:%S"),
            "habits": [habit.to_dict() for habit in habits],
        }
        binary_data = json.dumps(export_d).encode()
        file_name = f"beaverhabits_{now.strftime('%Y_%m_%d')}.json"
        ui.download(binary_data, file_name)
    else:
        ui.notification("Export failed, please try again later.")


async def validate_max_user_count():
    if await get_user_count() >= settings.MAX_USER_COUNT > 0:
        raise HTTPException(status_code=404, detail="User limit reached")


async def login_user(user: User) -> None:
    token = await user_create_token(user)
    if token is not None:
        app.storage.user.update({"auth_token": token})


async def register_user(email: str, password: str = "") -> User:
    logger.info(f"Registering user {email}...")
    user = await user_create(email=email, password=password)
    # Create a dummy habit list for the new users
    days = [datetime.date.today() - datetime.timedelta(days=i) for i in range(30)]
    await get_or_create_user_habit_list(user, days)
    logger.info(f"User {email} registered successfully")
    return user


async def is_gui_authenticated() -> bool:
    if settings.is_trusted_env():
        return True

    if await user_check_token(app.storage.user.get("auth_token", None)):
        return True

    return False


async def get_activated_users() -> Sequence[User]:
    users = await get_user_list()
    if not settings.ENABLE_PLAN:
        return users

    customers = await get_customer_list()
    emails = [customer.email for customer in customers if customer.activated]
    logger.debug(f"Activated users: {emails}")

    return [user for user in users if user.email in emails]


async def backup_all_users():
    for user in await get_activated_users():
        logger.info(f"Backing up habit list for user {user.email}...")
        habit_list = await get_user_habit_list(user)
        if habit_list is None:
            logger.warning(f"Failed to load habit list for user {user.email}")
            continue

        backup = habit_list.backup
        if not backup.telegram_bot_token or not backup.telegram_chat_id:
            logger.warning(f"User {user.email} has no backup settings")
            continue

        try:
            backup_to_telegram(
                backup.telegram_bot_token, backup.telegram_chat_id, habit_list
            )
        except Exception as e:
            logger.error(f"Failed to backup habit list for user {user.email}: {e}")
        else:
            logger.info(f"Successfully backed up habit list for user {user.email}")


@ratelimiter(limit=3, window=1)
async def forgot_password(email: str) -> None:
    user = await user_get_by_email(email)
    if user is None:
        ui.notify(
            "Email address not found, please check your email address and try again.",
            color="negative",
        )
        return

    token = user_create_reset_token(user)
    if token is None:
        ui.notify(
            "Failed to create reset password token, please try again later.",
            color="negative",
        )
        return

    logger.debug(f"Reset password token for {user.email}: {token}")
    async with asyncio.timeout(1):
        await run.io_bound(
            send_email,
            "Reset your password",
            f"Click the link to reset your password: {settings.APP_URL}/reset-password?token={token}",
            [user.email],
        )
        ui.notify(f"Reset password email sent to {user.email}", color="positive")
        logger.debug(f"Reset password email sent to {user.email}")


async def reset_password(user: User, password: str) -> None:
    new_user = await user_reset_password(user, password)

    ui.notify("Password reset successfully", color="positive")

    await login_user(new_user)
    redirect(GUI_ROOT_PATH)


@dataclass
class UserConfigs:
    custom_css: str | None = None


async def get_user_configs(user: User) -> UserConfigs:
    configs = await crud.get_user_configs(user) or {}
    return UserConfigs(
        custom_css=configs.get("css", None),
    )


async def cache_user_configs(user: User) -> None:
    configs = await get_user_configs(user)
    app.storage.user.update(
        {
            "custom_css": configs.custom_css or "",
        }
    )


async def update_custom_css(user: User, css: str) -> None:
    app.storage.user["custom_css"] = css

    await crud.update_user_configs(
        user,
        {
            "css": css,
        },
    )


async def apply_theme_style() -> None:
    try:
        custom_css = app.storage.user.get("custom_css", "")
    except Exception as e:
        logger.error(f"Failed to get custom CSS: {e}")
        return None

    if custom_css:
        ui.add_head_html(f"<style>{custom_css}</style>")
        logger.info(f"Applied custom CSS: {custom_css[:30]}...")
    else:
        ui.add_head_html(f"<style>{const.CSS_EDIT_ME}</style>")
