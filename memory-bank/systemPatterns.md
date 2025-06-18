# System Patterns: BeaverHabits

## System Architecture

BeaverHabits is a web application built with a Python backend using FastAPI and a frontend powered by NiceGUI. It follows a client-server architecture where the NiceGUI application serves the UI and interacts with the FastAPI backend for data operations and authentication.

## Key Technical Decisions

-   **FastAPI for Backend:** Chosen for its high performance, automatic interactive API documentation (Swagger UI), and ease of use for building robust APIs.
-   **NiceGUI for Frontend:** Selected for its ability to build web UIs directly in Python, simplifying development by avoiding JavaScript frameworks for the main UI.
-   **SQLite for Database:** Used for local development and potentially for lightweight deployments due to its file-based nature and ease of setup.
-   **OAuth2PasswordBearer for Authentication:** Standard and secure way to handle user authentication and token management.

## Design Patterns in Use

-   **MVC-like separation:** While not strictly MVC, there's a clear separation between:
    -   **Models:** Defined in `beaverhabits/api/models.py` and `beaverhabits/app/db.py` (SQLAlchemy models).
    -   **Views (UI):** Handled by NiceGUI pages in `beaverhabits/frontend/` and its components.
    -   **Controllers/Logic:** Handled by FastAPI routes in `beaverhabits/api/routes/` and NiceGUI page functions in `beaverhabits/routes.py`, along with `beaverhabits/app/crud.py` for database operations.
-   **Dependency Injection:** FastAPI's dependency injection system is heavily used for managing database sessions and current user authentication.

## Component Relationships

-   `beaverhabits/routes.py`: Defines the main UI pages and their routing, integrating backend logic (authentication, data retrieval) with frontend components.
-   `beaverhabits/app/auth.py`: Manages user authentication, including login, token creation, and user registration.
-   `beaverhabits/app/crud.py`: Contains functions for Create, Read, Update, Delete (CRUD) operations on habits and lists.
-   `beaverhabits/app/db.py`: Defines database models and session management.
-   `beaverhabits/frontend/`: Contains the NiceGUI UI pages and reusable components.

## Critical Implementation Paths

-   **User Authentication Flow:** `login_page` in `beaverhabits/routes.py` -> `user_authenticate` in `beaverhabits/app/auth.py` -> `user_create_token` in `beaverhabits/app/auth.py` -> `app.storage.user` for token storage.
-   **Habit Management:** UI pages (`index_page`, `add_page`, `habit_page`) interact with `beaverhabits/app/crud.py` for data persistence.
