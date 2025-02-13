from fastapi import Depends, HTTPException
from beaverhabits import views
from beaverhabits.app.db import User
from beaverhabits.app.dependencies import current_active_user
from beaverhabits.storage.storage import HabitList


async def current_habit_list(user: User = Depends(current_active_user)) -> HabitList:
    """Get the current user's habit list."""
    habit_list = await views.get_user_habit_list(user)
    if not habit_list:
        raise HTTPException(status_code=404, detail="No habits found")
    return habit_list
