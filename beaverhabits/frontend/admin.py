from nicegui import ui

from beaverhabits.app import crud
from beaverhabits.app.db import User
from beaverhabits.frontend.layout import layout


async def admin_page(user: User):
    with layout(title="Admin"):
        ui.label(f"Current user: {user.email}")
        ui.label(f"Total users: {await crud.get_user_count()}")

        ui.label("Customers:")
        customers = await crud.get_customer_list()
        rows = [
            {
                "email": customer.email,
                "is_pro": customer.activated,
                "created_at": customer.created_at,
                "updated_at": customer.updated_at,
                "customer_id": customer.customer_id,
            }
            for customer in customers
        ]
        ui.table(rows=rows)
