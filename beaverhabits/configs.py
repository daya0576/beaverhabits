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
    APP_URL: str = ""
    SENTRY_DSN: str = ""
    HIGHLIGHT_KEY: str = ""
    ADMIN_EMAIL: str = ""
    UMAMI_ANALYTICS_ID: str = ""
    UMAMI_SCRIPT_URL: str = "https://cloud.umami.is/script.js"
    ENABLE_PLAN: bool = False
    MAX_HABIT_COUNT: int = 5
    PADDLE_SANDBOX: bool = True
    PADDLE_CLIENT_SIDE_TOKEN: str = ""
    PADDLE_API_TOKEN: str = ""
    PADDLE_PRODUCT_ID: str = ""
    PADDLE_PRICE_ID: str = ""
    PADDLE_CALLBACK_KEY: str = ""
    HIGHLIGHT_IO_PROJECT_ID: str = ""

    # Email
    SMTP_EMAIL_USERNAME: str = ""
    SMTP_EMAIL_PASSWORD: str = ""

    # NiceGUI
    NICEGUI_STORAGE_SECRET: str = "dev"
    GUI_MOUNT_PATH: str = "/gui"
    DEMO_MOUNT_PATH: str = "/demo"
    DARK_MODE: bool | None = None

    # Storage
    HABITS_STORAGE: StorageType = StorageType.USER_DATABASE
    DATABASE_URL: str = f"sqlite+aiosqlite:///./{USER_DATA_FOLDER}/habits.db"
    MAX_USER_COUNT: int = -1
    JWT_SECRET: str = "SECRET"
    JWT_LIFETIME_SECONDS: int = 0

    # Auth
    TRUSTED_EMAIL_HEADER: str = ""
    TRUSTED_LOCAL_EMAIL: str = ""
    RESET_PASSWORD_TOKEN_SECRET: str = ""
    RESET_PASSWORD_TOKEN_LIFETIME_SECONDS: int = 60 * 60  # 1 hour

    # Customization
    FIRST_DAY_OF_WEEK: int = calendar.MONDAY
    # Set to 0-6 to align today to specific day of week, e.g., 0 for Monday
    ALIGN_TODAY_TO_DAY_OF_WEEK: int | None = None
    ENABLE_IOS_STANDALONE: bool = True
    TAG_SELECTION_MODE: TagSelectionMode = TagSelectionMode.MULTI
    ENABLE_TAG_FILTERS: bool = True

    INDEX_SHOW_HABIT_COUNT: bool = False
    INDEX_SHOW_HABIT_STREAK: bool = False
    INDEX_HABIT_NAME_COLUMNS: int = 5
    INDEX_HABIT_DATE_COLUMNS: int = 5
    INDEX_HABIT_DATE_REVERSE: bool = False

    HABIT_SHOW_EVERY_DAY_STREAKS: bool = False

    DAILY_NOTE_MAX_LENGTH: int = 1024

    # Backup inverval(in seconds), default is oneday
    ENABLE_DAILY_BACKUP: bool = False
    DAILY_BACKUP_INTERVAL: int = 60 * 60 * 24

    # Get your Google Client ID from the Google Cloud Console.
    # See https://developers.google.com/identity/gsi/web/guides/get-google-api-clientid#get_your_google_api_client_id.
    # For local development, you should add http://localhost:8080 to the authorized JavaScript origins.
    # In production, you should add the domain of your website to the authorized JavaScript origins.
    # Make sure you include <origin>/google/auth in "Authorized redirect URIs".
    GOOGLE_ONE_TAP_CLIENT_ID: str = ""
    GOOGLE_ONE_TAP_ENABLED: bool = False
    GOOGLE_ONE_TAP_CALLBACK_URL: str = ""

    def is_dev(self):
        return self.ENV == "dev"

    def is_trusted_env(self):
        return self.TRUSTED_LOCAL_EMAIL


settings = Settings()
