#!/usr/bin/env bash

# use path of this example as working directory; enables starting this script from anywhere
cd "$(dirname "$0")"

# create directory for user data
mkdir -p .user

if [ "$1" = "prd" ]; then
    echo "Starting Uvicorn server in production mode..."
    export ENV=production
    # Set nicegui storage path to avoid permission issues
    if [ -z "$NICEGUI_STORAGE_PATH" ]; then
        export NICEGUI_STORAGE_PATH=".user/.nicegui"
    fi
    # we also use a single worker in production mode so socket.io connections are always handled by the same worker
    uvicorn beaverhabits.main:app --workers 1 --log-level info --port 8080 --host 0.0.0.0
elif [ "$1" = "dev" ]; then
    echo "Starting Uvicorn server in development mode..."
    # reload implies workers = 1
    uvicorn beaverhabits.main:app --workers 1 --reload --port 9001 --host 0.0.0.0
else
    echo "Invalid parameter. Use 'prod' or 'dev'."
    exit 1
fi
