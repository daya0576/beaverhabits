from dataclasses import dataclass, field
from functools import wraps
from typing import Callable, Optional

from fastapi import APIRouter, FastAPI
from fastapi import Request as FastAPIRequest
from paddle_billing.Notifications import Secret, Verifier
from paddle_billing.Notifications.Requests import Request
from paddle_billing.Notifications.Requests.Headers import Headers

from beaverhabits.app import crud
from beaverhabits.configs import settings
from beaverhabits.logger import logger

router = APIRouter()


@dataclass
class PaddleHeaders(Headers, dict):
    data: dict = field(default_factory=dict)

    def get(self, key: str, default=None) -> str | None:
        return self.data.get(key.lower(), default)


@dataclass
class PaddleRequest(Request):
    body: Optional[bytes]
    content: Optional[bytes]
    data: Optional[bytes]
    headers: Headers


CALLBACKS: dict[str, Callable] = {}


def callback(event: str):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        # register the callback function
        CALLBACKS[event] = func

        return wrapper

    return decorator


@callback("customer.created")
@callback("customer.updated")
async def customer_created(data: dict) -> None:
    email, customer_id = data["email"], data["id"]
    await crud.get_or_create_user_identity(
        email, customer_id, provider="paddle", data=data
    )


@callback("transaction.completed")
async def transaction(data: dict) -> None:
    customer_id = data.get("customer_id") or data.get("customer", {}).get("id")
    if not customer_id:
        logger.warning("Transaction completed missing customer_id in payload")
        return
    await crud.update_user_identity(customer_id, data=data, activate=True)
    logger.info(f"Transaction completed for customer_id: {customer_id}")


@callback("adjustment.updated")
async def refund(data: dict) -> None:
    if action := data.get("action") != "refund":
        logger.warning(f"Unknown adjustment action: {action}")
        return

    if status := data.get("status") != "approved":
        logger.warning(f"Unknown adjustment status: {status}")
        return

    customer_id = data["customer_id"]
    await crud.update_user_identity(customer_id, data=data, activate=False)
    logger.info(f"Refund for customer_id: {customer_id}")


@router.post("/callback", include_in_schema=False)
async def webhook(data: dict, request: FastAPIRequest) -> dict:
    paddle_request = PaddleRequest(
        body=await request.body(),
        content=await request.body(),
        data=await request.body(),
        headers=PaddleHeaders(data=dict(request.headers)),
    )
    integrity_check = Verifier().verify(
        paddle_request, Secret(settings.PADDLE_CALLBACK_KEY)
    )
    if not integrity_check:
        raise ValueError("Integrity check failed")

    event_id, event_name = data["notification_id"], data["event_type"]
    if event_name not in CALLBACKS:
        logger.warning(f"Unknown event: {event_name}, event_id: {event_id}")
        return {"status": "unknown event"}

    logger.info(f"Received event: {event_name}, event_id: {event_id}")
    await CALLBACKS[event_name](data["data"])
    return {"status": "success"}


def init_paddle_routes(app: FastAPI) -> None:
    app.include_router(router, prefix="/paddle")
