# Beaver Habit Tracker - Main Repository

## Project Overview
A self-hosted habit tracking app built with FastAPI, NiceGUI, and SQLAlchemy. This is the main backend application.

## Tech Stack
- **FastAPI** - Modern Python web framework
- **NiceGUI** - Python-based web UI framework
- **SQLAlchemy** - ORM for database operations
- **Python 3.9+** - Main programming language

## Repository Structure
This repository contains a **submodule**:
- `statics/astro/` → Points to `daya0576/beaverhabits-landing` (landing page)

## Git Workflow with Submodule

### When modifying landing page (`statics/astro/`):
1. Make changes in `statics/astro/` directory
2. **First commit and push the submodule:**
   ```bash
   cd statics/astro
   git add -A
   git commit -m "your message"
   git push origin main
   cd ../..
   ```
3. **Then update parent repository:**
   ```bash
   git add statics/astro
   git commit -m "chore: update landing page submodule"
   git push origin main
   ```

### Quick command (one-liner):
```bash
cd statics/astro && git add -A && git commit -m "Update landing" && git push && cd ../.. && git add statics/astro && git commit -m "chore: update landing page" && git push
```

### Important Notes
- Always commit submodule **before** parent repository
- Parent repo only tracks the submodule commit hash, not file changes
- When AI suggests changes to `statics/astro/`, remind user about the two-step commit process

## Code Standards

### Python Style
- Follow PEP 8 conventions
- Use type hints for function parameters and returns
- Prefer `pathlib` over `os.path` for file operations
- Use f-strings for string formatting

### Commit Messages
- Format: `type: description`
- Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`
- Examples:
  - `feat: add backup export feature`
  - `fix: resolve timezone issue in scheduler`
  - `chore: update landing page submodule`

### File Organization
- Keep routes in `beaverhabits/routes/`
- Storage logic in `beaverhabits/storage/`
- Frontend components in `beaverhabits/frontend/`
- Core business logic in `beaverhabits/core/`

## Development Workflow
- Test locally before committing
- Update `pyproject.toml` when adding dependencies
- Run tests with `pytest` before pushing
- Check Docker build if modifying dependencies

## Project Goals
- Simple, goal-free habit tracking
- Self-hostable with minimal configuration
- Clean, intuitive UI
- Reliable data backup and export
