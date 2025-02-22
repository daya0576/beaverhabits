import datetime
import json
from typing import List as TypeList, Optional

from nicegui import app, ui

from beaverhabits.logging import logger
from beaverhabits.app.auth import user_authenticate, user_create_token, user_create, user_check_token
from beaverhabits.app.crud import (
    get_user_count, get_user_habits, get_user_lists,
    create_list, update_list as update_list_db,
    update_habit, get_habit_checks
)
from beaverhabits.app.db import User
from beaverhabits.configs import settings
from beaverhabits.sql.models import Habit, HabitList, CheckedRecord
from beaverhabits.utils import generate_short_hash


async def get_user_habit(user: User, habit_id: str) -> Optional[Habit]:
    """Get a specific habit for a user."""
    habits = await get_user_habits(user)
    for habit in habits:
        if str(habit.id) == habit_id:
            return habit
    return None


async def add_list(user: User, name: str) -> HabitList:
    """Add a new list for a user."""
    return await create_list(user, name)


async def update_list(user: User, list_id: int, name: str) -> None:
    """Update a list's name."""
    await update_list_db(list_id, user.id, name=name)


async def delete_list(user: User, list_id: int) -> None:
    """Delete a list and unassign its habits."""
    await update_list_db(list_id, user.id, deleted=True)


async def is_gui_authenticated() -> bool:
    """Check if user is authenticated with a valid token."""
    token = app.storage.user.get("auth_token")
    if not token:
        return False
    return await user_check_token(token)


async def validate_max_user_count() -> None:
    """Validate max user count."""
    if await get_user_count() >= settings.MAX_USER_COUNT > 0:
        raise ValueError("Maximum number of users reached")


async def register_user(email: str, password: str = "") -> User:
    """Register a new user."""
    try:
        logger.info(f"Attempting to register user with email: {email}")
        user = await user_create(email=email, password=password)
        if not user:
            logger.error(f"Registration failed for email: {email} - User creation returned None")
            raise ValueError("Failed to register user - Creation failed")
        logger.info(f"Successfully registered user with email: {email}")
        return user
    except Exception as e:
        logger.exception(f"Registration failed for email: {email}")
        raise ValueError(f"Failed to register user: {str(e)}")


async def login_user(user: User) -> None:
    """Login a user."""
    token = await user_create_token(user)
    if not token:
        raise ValueError("Failed to login user")
    app.storage.user.update({"auth_token": token})


async def export_user_habits(habits: TypeList[Habit], filename: str) -> None:
    """Export user habits."""
    # Convert habits to JSON-friendly format
    data = {
        "habits": [],
        "lists": []
    }
    
    # Add habits with their records
    for habit in habits:
        records = await get_habit_checks(habit.id, habit.user_id)
        habit_data = {
            "id": habit.id,
            "name": habit.name,
            "order": habit.order,
            "weekly_goal": habit.weekly_goal,
            "list_id": habit.list_id,
            "records": [
                {
                    "day": record.day.isoformat(),
                    "done": record.done,
                    "text": record.text
                }
                for record in records
            ]
        }
        data["habits"].append(habit_data)
    
    # Add lists
    lists = await get_user_lists(habits[0].user if habits else None)
    data["lists"] = [
        {
            "id": list.id,
            "name": list.name,
            "order": list.order
        }
        for list in lists
    ]
    
    ui.download(json.dumps(data, indent=2), filename=f"{filename}.json")
