# Tech Context: BeaverHabits

## Technologies Used

-   **Backend Framework:** FastAPI (Python)
-   **Frontend Framework:** NiceGUI (Python)
-   **Database:** SQLAlchemy (ORM) with SQLite (for development/local)
-   **Authentication:** FastAPI-Users with JWT strategy
-   **Logging:** Standard Python `logging` module
-   **Dependency Management:** Poetry (based on `pyproject.toml` and `poetry.lock`)

## Development Setup

-   **Python Version:** Specified in `.python-version` (e.g., 3.10 or higher).
-   **Virtual Environment:** Managed by Poetry.
-   **Dependencies:** Listed in `pyproject.toml` and `requirements.txt` (generated from Poetry).
-   **Running the application:** `start.bat` (Windows) or `start.sh` (Linux/macOS) scripts are provided.

## Technical Constraints

-   **NiceGUI limitations:** UI elements and interactions are limited to what NiceGUI provides. Complex frontend features might require custom JavaScript.
-   **Database choice:** SQLite is suitable for small-scale applications but might need to be replaced with a more robust database (e.g., PostgreSQL) for larger deployments.
-   **Authentication:** Current setup uses JWT, which is stateless. Session management is handled by NiceGUI's `app.storage.user`.

## Dependencies

Key dependencies include:

-   `fastapi`
-   `nicegui`
-   `fastapi-users`
-   `sqlalchemy`
-   `uvicorn` (for serving the application)

## Tool Usage Patterns

-   **File Editing:** `replace_in_file` for targeted changes, `write_to_file` for new files or complete rewrites.
-   **Code Exploration:** `read_file` for understanding file contents, `list_files` for directory structure.
-   **Command Execution:** `execute_command` for running scripts, installing dependencies, etc.
-   **Browser Interaction:** `browser_action` for testing and verifying UI changes.
