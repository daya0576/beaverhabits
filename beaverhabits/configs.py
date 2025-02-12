import calendar
import logging
from enum import Enum

import dotenv
from pydantic_settings import BaseSettings

logging.getLogger("niceGUI").setLevel(logging.INFO)
dotenv.load_dotenv()

USER_DATA_FOLDER = ".user"


class StorageType(Enum):
    SESSION = "SESSION"
    USER_DATABASE = "DATABASE"
    USER_DISK = "USER_DISK"


class Settings(BaseSettings):
    ENV: str = "dev"
    DEBUG: bool = False
    SENTRY_DSN: str = ""

    # NiceGUI
    NICEGUI_STORAGE_SECRET: str = "dev"
    GUI_MOUNT_PATH: str = "/gui"
    DEMO_MOUNT_PATH: str = "/demo"

    # Storage
    HABITS_STORAGE: StorageType = StorageType.USER_DATABASE
    DATABASE_URL: str = f"sqlite+aiosqlite:///./{USER_DATA_FOLDER}/habits.db"
    MAX_USER_COUNT: int = -1
    JWT_SECRET: str = "54o53o847gdlfjfdljgd"
    JWT_LIFETIME_SECONDS: int = 60 * 60 * 24 * 30

    # Auth
    TRUSTED_EMAIL_HEADER: str = ""
    TRUSTED_LOCAL_EMAIL: str = ""

    # Customization
    FIRST_DAY_OF_WEEK: int = calendar.MONDAY
    ENABLE_IOS_STANDALONE: bool = False
    ENABLE_DESKTOP_ALGIN_CENTER: bool = True

    INDEX_SHOW_HABIT_COUNT: bool = False
    INDEX_HABIT_NAME_COLUMNS: int = 8
    INDEX_HABIT_DATE_COLUMNS: int = -1  # -1 for week view (Mon-Sun), positive number for past N days

    # Colors
    HABIT_COLOR_COMPLETED: str = "lightgreen"
    HABIT_COLOR_INCOMPLETE: str = "yellow"
    HABIT_COLOR_SKIPPED: str = "grey"

    # Features
    ENABLE_HABIT_NOTES: bool = False  # Set to False to disable notes

    # Logging
    LOG_LEVEL: str = "WARNING"  # Can be DEBUG, INFO, WARNING, ERROR, CRITICAL

    def is_dev(self):
        return self.ENV == "dev"

    def is_trusted_env(self):
        return self.TRUSTED_LOCAL_EMAIL


settings = Settings()
