from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException
from beaverhabits import views
from beaverhabits.app.auth import user_authenticate
from beaverhabits.api.models import ExportCredentials
from beaverhabits.logging import logger

router = APIRouter(tags=["export"])


@router.post("/export/habits")
async def export_habits(credentials: ExportCredentials):
    """Export habit data for the last 30 days."""
    # Handle authentication first
    try:
        user = await user_authenticate(credentials.email, credentials.password)
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )
    except Exception as auth_error:
        logger.error(f"Authentication error: {str(auth_error)}")
        raise HTTPException(
            status_code=401,
            detail="Authentication failed"
        ) from auth_error

    # Handle data retrieval and processing
    try:
        # Get user's habit list
        habit_list = await views.get_user_habit_list(user)
        if not habit_list:
            raise HTTPException(
                status_code=404,
                detail="No habits found"
            )

        # Calculate date range for last 30 days
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)

        # Filter habits by list if specified
        habits = habit_list.habits
        if credentials.list_id is not None:
            habits = [
                habit for habit in habits
                if habit.list_id == credentials.list_id
            ]

        # Prepare response data
        habits_data = []
        for habit in habits:
            # Get ticked days within the date range
            ticked_days = [
                day for day in habit.ticked_days 
                if start_date <= day <= end_date
            ]
            
            # Get records for ticked days
            filtered_records = {}
            for day in ticked_days:
                record = habit.record_by(day)
                if record:
                    filtered_records[day.isoformat()] = {
                        "done": record.done,
                        "text": record.text if hasattr(record, "text") else ""
                    }

            habits_data.append({
                "id": habit.id,
                "name": habit.name,
                "star": habit.star,
                "status": habit.status.value,  # Convert enum to string
                "weekly_goal": habit.weekly_goal,
                "records": filtered_records
            })

        return {
            "habits": habits_data,
            "order": habit_list.order,
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error in export_habits endpoint")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while processing your request"
        ) from e
