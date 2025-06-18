# Progress: BeaverHabits

## What works

-   Initial setup of FastAPI and NiceGUI.
-   Basic routing for various pages (e.g., `/`, `/gui`, `/login`, `/register`).
-   User authentication and registration flow.
-   Habit and list management (CRUD operations).
-   Display of habits on the index page.
-   Export functionality for habits.
-   Import functionality for habits.
-   "Remember me" functionality on the login page:
    -   Checkbox added to the login form.
    -   Email address is pre-filled if "Remember me" was checked during the last successful login.
    -   Stored email and "remember me" flag are cleared if the checkbox is unchecked.

## What's left to build

-   Further UI/UX improvements.
-   More advanced habit tracking features (e.g., recurring habits, custom reminders).
-   Comprehensive testing suite.
-   Deployment automation.

## Current status

The core habit tracking and user management features are implemented. The "remember me" functionality has been added to the login screen.

## Known issues

-   Pylance error: `Line 43: Cannot access attribute "query" for class "page" Attribute "query" is unknown` in `get_current_list_id`. This was addressed by simplifying the function to rely solely on `app.storage.user` for current list ID, as the query parameter handling is done in page functions.

## Evolution of project decisions

-   Initial decision to use NiceGUI for frontend to simplify development.
-   Decision to use `app.storage.user` for storing user preferences like "remembered email" and "remember me" flag, as it's suitable for client-side persistence in NiceGUI.
-   Decision not to store passwords directly due to security best practices, instead relying on browser's built-in password management.
