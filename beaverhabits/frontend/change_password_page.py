from nicegui import ui, app
# Ensure this import path is correct and the function is available
from beaverhabits.app.users import change_user_password, UserManager # Import UserManager
# Assuming get_current_user_id is not used directly here anymore, as user_id is passed to change_password_ui
# from beaverhabits.app.auth import get_current_user_id
from fastapi_users.exceptions import InvalidPasswordException # To catch specific exception
import uuid # For user_id type hint
from beaverhabits.frontend.layout import layout # Import the main layout
from beaverhabits.app.db import User # Import User for type hinting if needed by layout

async def change_password_ui(user_manager: UserManager, user_id: uuid.UUID | None = None): # Add user_manager, change user_id type
    if user_id is None:
        ui.notify("User session not found. Cannot display page.", color="negative")
        # Optionally redirect or show a more prominent error
        return

    # Fetch the user object to pass to the layout
    # This assumes user_manager.get() is an async method that returns a User object or None
    # and that it doesn't raise an exception if user_id is None (already checked)
    # or if user is not found (though a valid user_id should exist if this page is reached via protected route)
    current_user: User | None = await user_manager.get(user_id)
    if current_user is None:
        ui.notify("User not found. Cannot display page.", color="negative")
        return

    async with layout(user=current_user): # Apply the layout, removed title="Change Password"
        # Define handle_submit first, it will close over the input variables defined later
        async def handle_submit():
            # Access to old_password_input etc. will be resolved when handle_submit is called
            old_pw = old_password_input.value
            new_pw = new_password_input.value
            confirm_pw = confirm_password_input.value

            if not old_pw or not new_pw or not confirm_pw:
                ui.notify("All fields are required.", color="negative")
                return

            if new_pw != confirm_pw:
                ui.notify("New passwords do not match.", color="negative")
                return

            if user_id is None: # This check is technically redundant due to earlier check, but harmless
                ui.notify("User session not found. Cannot change password.", color="negative")
                return

            try:
                # Call the actual backend function, passing the received user_manager
                success = await change_user_password(user_manager=user_manager, user_id=user_id, old_password=old_pw, new_password=new_pw)

                if success:
                    ui.notify("Password changed successfully!", color="positive")
                    old_password_input.set_value("")
                    new_password_input.set_value("")
                    confirm_password_input.set_value("")
                else:
                    ui.notify("Failed to change password. An unexpected error occurred.", color="negative")

            except InvalidPasswordException:
                ui.notify("Incorrect old password. Please try again.", color="negative")
            except Exception as e:
                detail = getattr(e, 'detail', str(e))
                ui.notify(f"An error occurred: {detail}", color="negative")

        # Wrap card in a column for centering
        with ui.column().classes("w-full items-center pt-6"): # Added some padding-top for spacing
            with ui.card().classes("w-full max-w-md p-6"):
                ui.label("Change Password").classes("text-2xl font-semibold mb-4 text-center")
                with ui.element('form').classes("space-y-4"):
                    # Define inputs here so they are rendered inside the card and form
                    old_password_input = ui.input(label="Old Password", password=True, password_toggle_button=True).props("w-full")
                    new_password_input = ui.input(label="New Password", password=True, password_toggle_button=True).props("w-full")
                    confirm_password_input = ui.input(label="Confirm New Password", password=True, password_toggle_button=True).props("w-full")
                    ui.button("Change Password", on_click=handle_submit).props("w-full")
