from loguru import logger
import os
import sys
from beaverhabits.configs import settings

# Remove default handler
logger.remove()

# Add console handler with configured level
logger.add(sys.stderr, level=settings.LOG_LEVEL)

# Add file handler with configured level
log_dir = os.path.join(".user", "logs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "beaver.log")
logger.add(log_file, rotation="00:00", retention="7 days", level=settings.LOG_LEVEL, format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}")
