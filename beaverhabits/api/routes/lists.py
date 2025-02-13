from fastapi import APIRouter, HTTPException
from beaverhabits import views
from beaverhabits.app.auth import user_authenticate
from beaverhabits.api.models import ExportCredentials
from beaverhabits.logging import logger

router = APIRouter(tags=["lists"])


@router.post("/lists", response_model=dict[str, list[dict[str, str]]])
async def get_lists(credentials: ExportCredentials):
    """Get all lists for the authenticated user."""
    # Handle authentication first
    try:
        user = await user_authenticate(credentials.email, credentials.password)
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )
    except Exception as auth_error:
        logger.error(f"Authentication error: {str(auth_error)}")
        raise HTTPException(
            status_code=401,
            detail="Authentication failed"
        ) from auth_error

    # Get lists
    try:
        lists = await views.get_user_lists(user)
        return {
            "lists": [
                {
                    "id": list_obj.id,
                    "name": list_obj.name
                }
                for list_obj in lists
            ]
        }
    except Exception as e:
        logger.exception("Error getting user lists")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve lists"
        ) from e
