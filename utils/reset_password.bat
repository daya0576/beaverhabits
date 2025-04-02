@echo off
echo Changing to project root directory...
cd /d "%~dp0.."

echo Activating virtual environment...
call .venv\Scripts\activate.bat

echo Running password reset script...
python -m utils.reset_password

echo.
pause
