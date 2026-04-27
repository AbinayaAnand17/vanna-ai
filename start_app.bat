@echo off
setlocal

echo --- Starting MySQL Task Manager Setup ---

:: 1. Check if .env exists
if not exist .env (
    echo [!] Warning: .env file not found.
    echo [!] Copying .env.example to .env ...
    copy .env.example .env
    echo [!] Please update your MySQL credentials in the .env file and then run this script again.
    pause
    exit /b
)

:: 1.5 Activate Virtual Environment
if exist .venv-1\Scripts\activate (
    echo --- Activating .venv-1 ---
    call .venv-1\Scripts\activate
) else if exist .venv\Scripts\activate (
    echo --- Activating .venv ---
    call .venv\Scripts\activate
) else if exist venv\Scripts\activate (
    echo --- Activating venv ---
    call venv\Scripts\activate
)

:: 2. Run Database Connection Check
echo --- Checking Database Connection ---
python check_db_connection.py
if %ERRORLEVEL% neq 0 (
    echo [!] Database connection failed. Please ensure MySQL is running and credentials are correct.
    pause
    exit /b
)

:: 3. Start the vanna AI Agent
echo --- Starting vanna AI Agent ---
python mysql_task_agent.py

endlocal

