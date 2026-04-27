@echo off
title Sonline AI Launcher
echo.
echo  ================================================
echo   Sonline AI - Starting both servers
echo  ================================================
echo.

:: Check if uvicorn is installed
where uvicorn >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing backend dependencies...
    pip install fastapi uvicorn mysql-connector-python
)

:: Start FastAPI backend in a new window
echo  [1/2] Starting Backend on port 8001...
start "Sonline Backend :8001" cmd /k "cd /d %~dp0 && uvicorn main:app --reload --host 0.0.0.0 --port 8001"

:: Wait for backend to boot
timeout /t 4 /nobreak > nul

:: Start Vite frontend in a new window  
echo  [2/2] Starting Frontend on port 5173...
start "Sonline Frontend :5173" cmd /k "cd /d %~dp0frontends\sonline-ui && npm run dev"

echo.
echo  ================================================
echo   Backend  : http://127.0.0.1:8001
echo   Frontend : http://localhost:5173
echo   Health   : http://127.0.0.1:8001/health
echo  ================================================
echo.
echo  Both servers starting in separate windows...
pause
