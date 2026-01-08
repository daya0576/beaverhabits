# GEMINI.md

This file provides a high-level overview of the Beaver Habits project, its structure, and how to get started with development.

## Project Overview

Beaver Habits is a self-hosted habit tracking application. It is a web-based application built with a Python backend and a web-based frontend.

- **Backend:** The backend is built using the [FastAPI](https://fastapi.tiangolo.com/) framework. It provides a RESTful API for managing habits, users, and authentication.
- **Frontend:** The frontend is built using [NiceGUI](https://nicegui.io/), a Python-based UI framework. This allows for building a web interface with only Python.
- **Database:** The application uses [SQLAlchemy](https://www.sqlalchemy.org/) for database interaction. It supports both SQLite and PostgreSQL.
- **Authentication:** User authentication is handled by [FastAPI Users](https://fastapi-users.github.io/fastapi-users/).
- **Package Management:** The project uses [uv](https://docs.astral.sh/uv/getting-started/) for managing Python dependencies.

## Project Structure

The project is structured as follows:

- `beaverhabits/`: This directory contains the main source code for the application.
  - `main.py`: The main entry point of the application. It initializes the FastAPI application and the NiceGUI interface.
  - `app/`: This directory contains the core application logic, including database models, user authentication, and CRUD operations.
  - `routes/`: This directory contains the API and UI routes.
    - `routes.py`: Defines the web interface routes using NiceGUI.
    - `api.py`: Defines the RESTful API endpoints.
  - `frontend/`: This directory contains the reusable UI components and pages for the NiceGUI frontend.
  - `storage/`: This directory contains modules for handling data storage.
- `tests/`: This directory contains the tests for the application.
- `pyproject.toml`: This file defines the project's dependencies and other metadata.
- `start.sh`: This script is used to start the development and production servers.
- `README.md`: This file provides a general overview of the project.

## Building and Running

To get started with development, you will need to have Python and `uv` installed.

1.  **Install dependencies:**

    ```bash
    uv venv && uv sync
    ```

2.  **Start the development server:**

    ```bash
    ./start.sh dev
    ```

    This will start the application on `http://localhost:9001`.

## Development Conventions

- **Code Style:** The project uses `black` and `autopep8` for code formatting.
- **Testing:** The project uses `pytest` for testing. You can run the tests with the `pytest` command.
- **Linting:** The project uses `ruff` for linting.
