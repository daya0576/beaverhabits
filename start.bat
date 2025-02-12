@echo off

rem use path of this batch file as working directory; enables starting this script from anywhere
cd /d "%~dp0"

call .venv\Scripts\activate 

rem create directory for user data
if not exist ".user" mkdir .user

if "%1"=="dev" (
	echo Starting Uvicorn server in development mode...
    rem Set debug logging
    set LOGURU_LEVEL=DEBUG
    set UVICORN_LOG_LEVEL=debug
    rem reload implies workers = 1
    uvicorn beaverhabits.main:app --reload --log-level debug --port 9001 --host 0.0.0.0
	
) else (
    echo Starting Uvicorn server in production mode...
    rem Set nicegui storage path to avoid permission issues if not already set
    if "%NICEGUI_STORAGE_PATH%"=="" set NICEGUI_STORAGE_PATH=.user\.nicegui
    rem we also use a single worker in production mode so socket.io connections are always handled by the same worker
    uvicorn beaverhabits.main:app --workers 2 --log-level info --port 9015 --host 0.0.0.0
)
