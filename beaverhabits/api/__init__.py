from fastapi import FastAPI
from fastapi.routing import APIRouter

from beaverhabits.api.routes import habits, export

# Create the main API router
api_router = APIRouter()

# Include all route modules
api_router.include_router(habits.router)
api_router.include_router(export.router)

def init_api_routes(app: FastAPI) -> None:
    """Initialize all API routes with the FastAPI application."""
    app.include_router(api_router, prefix="/api/v1")
