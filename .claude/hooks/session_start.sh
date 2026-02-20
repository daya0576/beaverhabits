#!/bin/bash
# Claude Code SessionStart hook: sync uv venv and activate it

set -euo pipefail

uv sync --group dev --group fly

VENV_BIN="$(pwd)/.venv/bin"

if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
    echo "export VIRTUAL_ENV=\"$(pwd)/.venv\"" >> "$CLAUDE_ENV_FILE"
    echo "export PATH=\"$VENV_BIN:\$PATH\"" >> "$CLAUDE_ENV_FILE"
fi
