import asyncio
import datetime

from loguru import logger

from beaverhabits import views
from beaverhabits.configs import settings


async def daily_backup_task():
    while True:
        now = datetime.datetime.now()

        # Default to run at midnight
        next_run = (now + datetime.timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        wait_time = (next_run - now).total_seconds()

        if settings.DAILY_BACKUP_INTERVAL:
            # If the backup interval is set, adjust the next run time
            wait_time = settings.DAILY_BACKUP_INTERVAL

        await asyncio.sleep(wait_time)

        # Call the function to backup all users' data
        try:
            await views.backup_all_users()
        except Exception:
            logger.exception("Error during daily backup task")
