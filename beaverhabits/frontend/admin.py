from nicegui import background_tasks, ui

from beaverhabits import views
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

        ui.separator()

        user_email = ui.input(label="User email")
        ui.button(
            "Promote to Pro",
            on_click=lambda: background_tasks.create_lazy(
                views.promote_user_to_pro(user_email.value), name="promote_user"
            ),
        )
        ui.button(
            "Demote from Pro",
            on_click=lambda: background_tasks.create_lazy(
                views.promote_user_to_pro(user_email.value, False), name="demote_user"
            ),
        )
