from loguru import logger
import os

# Create logs directory if it doesn't exist
log_dir = os.path.join(".user", "logs")
os.makedirs(log_dir, exist_ok=True)

# Add file logger with daily rotation at midnight
log_file = os.path.join(log_dir, "beaver.log")
logger.add(log_file, rotation="00:00", retention="7 days", level="DEBUG", format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}")
