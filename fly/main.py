import sentry_sdk
from fastapi import Depends, FastAPI
from nicegui import ui

from beaverhabits import views
from beaverhabits.app.db import User
from beaverhabits.app.dependencies import current_admin_user
from beaverhabits.configs import settings
from beaverhabits.frontend import paddle_page
from beaverhabits.frontend.admin import admin_page
from beaverhabits.frontend.paddle_page import PRIVACY, TERMS
from beaverhabits.frontend.pricing_page import landing_page
from beaverhabits.logger import logger
from beaverhabits.main import app
from fly.plan.paddle import init_paddle_routes

if settings.SENTRY_DSN:
    logger.info("Setting up Sentry...")
    sentry_sdk.init(settings.SENTRY_DSN, send_default_pii=True)


@ui.page("/")
@ui.page("/pricing")
async def pricing_page():
    await landing_page()


@ui.page("/terms")
def terms_page():
    paddle_page.markdown(TERMS)


@ui.page("/privacy")
def privacy_page():
    paddle_page.markdown(PRIVACY)


@ui.page("/admin", include_in_schema=False)
async def admin(user: User = Depends(current_admin_user)):
    await admin_page(user)


@ui.page("/admin/backup", include_in_schema=False)
async def manual_backup(user: User = Depends(current_admin_user)):
    logger.info(f"Starting backup, triggered by {user.email}")
    await views.backup_all_users()


paddle_app = FastAPI()
init_paddle_routes(paddle_app)
paddle_app.mount("/", app)
