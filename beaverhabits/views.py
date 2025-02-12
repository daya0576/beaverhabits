import datetime
from typing import List as TypeList, Optional

import json
from nicegui import app, ui

from beaverhabits.logging import logger

from beaverhabits.app.auth import user_authenticate, user_create_token, user_create
from beaverhabits.app.crud import get_user_count
from beaverhabits.app.db import User
from beaverhabits.configs import settings
from beaverhabits.storage.dict import DictList, DictHabit, DictHabitList
from beaverhabits.storage.storage import List, Habit
from beaverhabits.storage.user_file import get_user_storage
from beaverhabits.storage.session_file import SessionDictStorage
from beaverhabits.utils import generate_short_hash

user_storage = get_user_storage()
session_storage = SessionDictStorage()


def get_session_habit_list() -> Optional[DictHabitList]:
    """Get session habit list."""
    return session_storage.get_user_habit_list()


def get_or_create_session_habit_list(days: list[datetime.date]) -> DictHabitList:
    """Get or create session habit list."""
    habit_list = get_session_habit_list()
    if not habit_list:
        habit_list = DictHabitList({"habits": []})
        session_storage.save_user_habit_list(habit_list)
    return habit_list


async def get_session_habit(habit_id: str) -> Optional[DictHabit]:
    """Get a specific habit from session."""
    habit_list = get_session_habit_list()
    if not habit_list:
        return None
    return await habit_list.get_habit_by(habit_id)


async def get_user_habit_list(user: User) -> DictHabitList:
    """Get or create user's habit list."""
    habit_list = await user_storage.get_user_habit_list(user)
    if not habit_list:
        habit_list = DictHabitList({"habits": []})
        await user_storage.save_user_habit_list(user, habit_list)
    return habit_list


async def get_user_habit(user: User, habit_id: str) -> Optional[DictHabit]:
    """Get a specific habit for a user."""
    habit_list = await user_storage.get_user_habit_list(user)
    if not habit_list:
        return None
    return await habit_list.get_habit_by(habit_id)


async def get_user_lists(user: User) -> TypeList[List[Habit]]:
    """Get all lists for a user."""
    data = await user_storage.get_user_habit_list(user)
    if not data:
        data = DictHabitList({"habits": [], "lists": []})
    
    # Get lists from storage
    lists = data.data.get("lists", [])
    return [DictList(d) for d in lists]


async def add_list(user: User, name: str) -> List[Habit]:
    """Add a new list for a user."""
    data = await user_storage.get_user_habit_list(user)
    if not data:
        data = DictHabitList({"habits": [], "lists": []})
    
    # Create new list
    list_id = generate_short_hash(name)
    list_data = {"id": list_id, "name": name}
    
    # Add to storage
    if "lists" not in data.data:
        data.data["lists"] = []
    data.data["lists"].append(list_data)
    
    await user_storage.save_user_habit_list(user, data)
    return DictList(list_data)


async def update_list(user: User, list_id: str, name: str) -> None:
    """Update a list's name."""
    data = await user_storage.get_user_habit_list(user)
    if not data:
        return
    
    # Find and update list
    for list_data in data.data.get("lists", []):
        if list_data["id"] == list_id:
            list_data["name"] = name
            await user_storage.save_user_habit_list(user, data)
            break


async def delete_list(user: User, list_id: str) -> None:
    """Delete a list and unassign its habits."""
    data = await user_storage.get_user_habit_list(user)
    if not data:
        return
    
    # Remove list
    data.data["lists"] = [
        l for l in data.data.get("lists", []) 
        if l["id"] != list_id
    ]
    
    # Unassign habits
    for habit in data.data.get("habits", []):
        if habit.get("list_id") == list_id:
            habit["list_id"] = None
    
    await user_storage.save_user_habit_list(user, data)


async def is_gui_authenticated() -> bool:
    """Check if user is authenticated."""
    token = app.storage.user.get("auth_token")
    return bool(token)


async def validate_max_user_count() -> None:
    """Validate max user count."""
    if await get_user_count() >= settings.MAX_USER_COUNT > 0:
        raise ValueError("Maximum number of users reached")


async def register_user(email: str, password: str) -> User:
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


async def export_user_habit_list(habit_list: DictHabitList, filename: str) -> None:
    """Export user habit list."""
    ui.download(json.dumps(habit_list.data, indent=2), filename=f"{filename}.json")
