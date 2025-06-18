from nicegui import ui, app
# Ensure this import path is correct and the function is available
from beaverhabits.app.users import change_user_password
# Assuming get_current_user_id is not used directly here anymore, as user_id is passed to change_password_ui
# from beaverhabits.app.auth import get_current_user_id
from fastapi_users.exceptions import InvalidPasswordException # To catch specific exception

async def change_password_ui(user_id: int | None = None): # user_id is passed from the route
    old_password_input = ui.input(label="Old Password", password=True, password_toggle_button=True).props("w-full")
    new_password_input = ui.input(label="New Password", password=True, password_toggle_button=True).props("w-full")
    confirm_password_input = ui.input(label="Confirm New Password", password=True, password_toggle_button=True).props("w-full")

    async def handle_submit():
        old_pw = old_password_input.value
        new_pw = new_password_input.value
        confirm_pw = confirm_password_input.value

        if not old_pw or not new_pw or not confirm_pw:
            ui.notify("All fields are required.", color="negative")
            return

        if new_pw != confirm_pw:
            ui.notify("New passwords do not match.", color="negative")
            return

        if user_id is None:
            ui.notify("User session not found. Cannot change password.", color="negative")
            # This should ideally be handled by auth protection on the route itself
            return

        try:
            # Call the actual backend function
            success = await change_user_password(user_id=user_id, old_password=old_pw, new_password=new_pw)

            if success:
                ui.notify("Password changed successfully!", color="positive")
                old_password_input.set_value("")
                new_password_input.set_value("")
                confirm_password_input.set_value("")
            else:
                # This else block might not be reached if change_user_password always raises exceptions on failure
                ui.notify("Failed to change password. An unexpected error occurred.", color="negative")

        except InvalidPasswordException:
            ui.notify("Incorrect old password. Please try again.", color="negative")
        except Exception as e:
            # Catch other exceptions that might be raised (e.g., HTTPException from backend)
            # Check if e has a 'detail' attribute, common for HTTPException
            detail = getattr(e, 'detail', str(e))
            ui.notify(f"An error occurred: {detail}", color="negative")

    with ui.card().classes("w-full max-w-md mx-auto p-6"):
        ui.label("Change Password").classes("text-2xl font-semibold mb-4 text-center")
        with ui.form().classes("space-y-4"): # Ensure this is ui.form, not just a div acting as one
            old_password_input
            new_password_input
            confirm_password_input
            ui.button("Change Password", on_click=handle_submit).props("w-full")
