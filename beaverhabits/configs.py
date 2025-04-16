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


class TagSelectionMode(Enum):
    SINGLE = "SINGLE"
    MULTI = "MULTI"


class Settings(BaseSettings):
    ENV: str = "dev"
    DEBUG: bool = False

    # SaaS
    SENTRY_DSN: str = ""
    ADMIN_EMAIL: str = ""
    UMAMI_ANALYTICS_ID: str = ""
    ENABLE_PLAN: bool = False
    MAX_HABIT_COUNT: int = 5
    PADDLE_SANDBOX: bool = True
    PADDLE_CLIENT_SIDE_TOKEN: str = ""
    PADDLE_API_TOKEN: str = ""
    PADDLE_PRODUCT_ID: str = ""
    PADDLE_PRICE_ID: str = ""
    PADDLE_CALLBACK_KEY: str = ""

    # NiceGUI
    NICEGUI_STORAGE_SECRET: str = "dev"
    GUI_MOUNT_PATH: str = "/gui"
    DEMO_MOUNT_PATH: str = "/demo"

    # Storage
    HABITS_STORAGE: StorageType = StorageType.USER_DATABASE
    DATABASE_URL: str = f"sqlite+aiosqlite:///./{USER_DATA_FOLDER}/habits.db"
    MAX_USER_COUNT: int = -1
    JWT_SECRET: str = "SECRET"
    JWT_LIFETIME_SECONDS: int = 60 * 60 * 24 * 30

    # Auth
    TRUSTED_EMAIL_HEADER: str = ""
    TRUSTED_LOCAL_EMAIL: str = ""

    # Customization
    FIRST_DAY_OF_WEEK: int = calendar.MONDAY
    ENABLE_IOS_STANDALONE: bool = True
    ENABLE_DESKTOP_ALGIN_CENTER: bool = True
    TAG_SELECTION_MODE: TagSelectionMode = TagSelectionMode.MULTI

    INDEX_SHOW_HABIT_COUNT: bool = False
    INDEX_HABIT_NAME_COLUMNS: int = 5
    INDEX_HABIT_DATE_COLUMNS: int = 5
    INDEX_HABIT_DATE_REVERSE: bool = False

    # Daily backup cron job
    ENABLE_DAILY_BACKUP: bool = False

    def is_dev(self):
        return self.ENV == "dev"

    def is_trusted_env(self):
        return self.TRUSTED_LOCAL_EMAIL


settings = Settings()
