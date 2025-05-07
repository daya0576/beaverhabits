import random

from nicegui import app, context, ui

from beaverhabits.app import crud
from beaverhabits.app.auth import user_from_token
from beaverhabits.configs import settings
from beaverhabits.logger import logger
from beaverhabits.storage.storage import HabitList, HabitListBuilder, HabitStatus


async def checkout():
    token = app.storage.user.get("auth_token")
    logger.debug(f"Checkout token: {token}")
    user = await user_from_token(token)
    email = user.email if user else ""
    logger.info(f"Checkout email: {email}")

    if not email:
        ui.notify("Please sign to continue checkout", position="top", color="negative")
        app.storage.user["referrer_path"] = "/pricing"
        ui.timer(2, lambda: ui.navigate.to("/register", new_tab=True), once=True)
        return

    ui.run_javascript(f"openCheckout('{email}')")


def redirect_pricing(msg: str):
    ui.notify(msg, color="negative")
    ui.timer(1.5, lambda: ui.navigate.to("/pricing"), once=True)


async def check_pro() -> bool:
    if "demo" in context.client.page.path:
        return True

    token = app.storage.user.get("auth_token")
    user = await user_from_token(token)
    if user:
        customer = await crud.get_user_identity(user.email)
        if customer and customer.activated:
            logger.info(f"User is Pro: {user.email}, {customer.id}")
            return True

    return False


# decorator to check if user is pro, e.g. @pro_required("Max user reached")
def pro_required(msg: str, rate: float = 1.0):
    if not (0 < rate <= 1):
        raise ValueError("Rate must be between 0 and 1")

    def decorator(func):
        async def wrapper(*args, **kwargs):
            if await check_pro() and random.random() <= rate:
                return func(*args, **kwargs)
            else:
                redirect_pricing(msg)

        return wrapper

    return decorator


async def habit_limit_reached(habit_list: HabitList) -> bool:
    if await check_pro():
        return False

    habits = HabitListBuilder(habit_list).status(HabitStatus.ACTIVE).build()
    if len(habits) >= settings.MAX_HABIT_COUNT:
        redirect_pricing("Max habit count reached!")
        return True

    return False
