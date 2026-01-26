import os

from fastapi import Depends, FastAPI
from fastapi.responses import FileResponse
from nicegui import app, ui

from beaverhabits import views
from beaverhabits.app.db import User
from beaverhabits.app.dependencies import current_admin_user
from beaverhabits.configs import settings
from beaverhabits.frontend import paddle_page
from beaverhabits.frontend.admin import admin_page
from beaverhabits.frontend.paddle_page import PRIVACY, TERMS
from beaverhabits.logger import logger


# Add NiceGUI pages for terms, privacy, and admin
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


def init_astro_routes(fastapi_app: FastAPI) -> None:
    """Mount Astro static files using NiceGUI"""
    ASTRO_DIST_PATH = "statics/astro/dist"

    @fastapi_app.get("/robots.txt")
    async def robots():
        return FileResponse("statics/robots.txt", media_type="text/plain")

    @fastapi_app.get("/sitemap.xml")
    async def sitemap():
        return FileResponse("statics/sitemap.xml", media_type="application/xml")

    if os.path.exists(ASTRO_DIST_PATH):
        logger.info(f"Mounting Astro static files from {ASTRO_DIST_PATH}")
        # Use NiceGUI's add_static_files to serve Astro static files
        app.add_static_files(
            "/_astro", "statics/astro/dist/_astro", max_cache_age=7 * 24 * 60 * 60
        )
        app.add_static_files(
            "/landing", "statics/astro/dist/landing", max_cache_age=7 * 24 * 60 * 60
        )

        # Add explicit routes for landing page
        @fastapi_app.get("/")
        @fastapi_app.get("/pricing")
        @fastapi_app.get("/pricing/")
        async def landing_index():
            return FileResponse("statics/astro/dist/index.html", media_type="text/html")

    else:
        logger.warning(
            f"Astro dist path not found: {ASTRO_DIST_PATH}, skipping static file mount"
        )
