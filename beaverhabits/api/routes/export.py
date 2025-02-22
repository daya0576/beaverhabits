from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends

from beaverhabits.app.crud import get_user_habits, get_habit_checks
from beaverhabits.app.db import User
from beaverhabits.app.dependencies import current_active_user

router = APIRouter(tags=["export"])

@router.get("/export")
async def export_data(
    user: User = Depends(current_active_user),
):
    """Export all user data in a format suitable for backup/restore."""
    habits = await get_user_habits(user)
    
    export_data = []
    for habit in habits:
        checks = await get_habit_checks(habit.id, user.id)
        export_data.append({
            "id": habit.id,
            "name": habit.name,
            "list_id": habit.list_id,
            "order": habit.order,
            "completions": [
                {
                    "date": check.day.strftime("%Y-%m-%d"),
                    "done": check.done
                }
                for check in checks
            ]
        })
    
    return {
        "version": "2.0",
        "exported_at": datetime.utcnow().isoformat(),
        "habits": export_data
    }
