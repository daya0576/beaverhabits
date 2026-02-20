# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
uv sync --group dev

# Run development server (port 9001, auto-reload)
./start.sh dev

# Run production server (Gunicorn, single worker, port 9001)
./start.sh prd

# Run all tests
uv run pytest

# Run a single test file
uv run pytest tests/test_apis.py

# Run a specific test
uv run pytest tests/test_apis.py::test_function_name

# Tests require environment variables
DATABASE_URL="sqlite+aiosqlite:///:memory:" HABITS_STORAGE="USER_DISK" uv run pytest
```

## Architecture

**Tech stack**: FastAPI + NiceGUI (frontend), SQLAlchemy (ORM), fastapi-users (auth), Paddle (payments). Python 3.12+.

**Entry point**: `beaverhabits/main.py` — FastAPI app with lifespan, initializes DB, registers routers, starts backup scheduler.

**Key directories**:
- `beaverhabits/app/` — Auth, DB models, user management (fastapi-users), CRUD, dependencies
- `beaverhabits/routes/` — HTTP route handlers: `api.py` (REST), `routes.py` (GUI pages), `metrics.py` (health)
- `beaverhabits/frontend/` — NiceGUI UI components; `components.py` is the largest file (~43KB)
- `beaverhabits/storage/` — Storage abstraction layer with multiple backends (see below)
- `beaverhabits/core/` — Business logic: completions/streaks, backup, notes
- `beaverhabits/plan/` — Paddle payment integration (optional, gated by `ENABLE_PLAN`)
- `beaverhabits/configs.py` — All configuration via environment variables

**Storage backends** (selected via `HABITS_STORAGE` env var):
- `DATABASE` — SQLAlchemy (SQLite or PostgreSQL)
- `USER_DISK` — JSON files per user
- `SESSION` — In-memory session storage (demo/test)
- File-based session storage

**REST API**: All endpoints under `/api/v1`. Habits CRUD at `/habits`, completions at `/habits/{id}/completions`.

**Authentication**: Email/password JWT, Google One-Tap, and trusted-email-header modes. All controlled via `configs.py`.

**Production constraint**: Must run single Gunicorn worker to maintain Socket.IO connections (NiceGUI requirement).

**Submodule**: `statics/astro/` is the landing page (`daya0576/beaverhabits-landing`). Update with `git submodule update --remote`.

## Commit Style

Format: `type: description` where type is one of: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`.

## Code Conventions

- Type hints required throughout
- Use f-strings for string formatting
- Prefer `pathlib` over `os.path`
- PEP 8 naming conventions
