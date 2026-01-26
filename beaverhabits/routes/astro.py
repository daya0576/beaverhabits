import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse

from beaverhabits.logger import logger


class SPAStaticFiles(StaticFiles):
    """Custom StaticFiles that falls back to index.html for SPA routing"""

    async def get_response(self, path: str, scope):
        try:
            return await super().get_response(path, scope)
        except Exception:
            # If file not found, return index.html for SPA routing
            return FileResponse(os.path.join(self.directory, "index.html"))


def init_astro_routes(app: FastAPI) -> None:
    """Mount Astro static files at root path"""
    # Get the project root directory (where start.sh and statics/ are located)
    project_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    default_path = os.path.join(project_root, "statics", "astro", "dist")
    ASTRO_DIST_PATH = os.getenv("ASTRO_DIST_PATH", default_path)

    if os.path.exists(ASTRO_DIST_PATH):
        logger.info(f"Mounting Astro static files from {ASTRO_DIST_PATH} at /")
        app.mount(
            "/",
            SPAStaticFiles(directory=ASTRO_DIST_PATH, html=True),
            name="astro",
        )
    else:
        logger.warning(
            f"Astro dist path not found: {ASTRO_DIST_PATH}, skipping static file mount"
        )
