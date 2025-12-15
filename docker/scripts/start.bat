@echo off
REM Quick start script for Windows
REM Run from project root

echo ================================
echo AI Inkubator - Docker Setup
echo ================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not running!
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)

REM Check if firebase-credentials.json exists
if not exist firebase-credentials.json (
    echo [WARNING] firebase-credentials.json not found!
    echo Please copy your Firebase credentials file to:
    echo   %cd%\firebase-credentials.json
    echo.
    choice /C YN /M "Continue anyway?"
    if errorlevel 2 exit /b 1
)

echo [INFO] Starting services with docker-compose...
docker-compose up -d --build

if errorlevel 1 (
    echo [ERROR] Failed to start services
    pause
    exit /b 1
)

echo.
echo ================================
echo Services Started Successfully!
echo ================================
echo.
echo Backend API:  http://localhost:8000
echo API Docs:     http://localhost:8000/docs
echo Health:       http://localhost:8000/health
echo phpMyAdmin:   http://localhost:8081
echo.
echo Useful commands:
echo   docker-compose logs -f backend  # View backend logs
echo   docker-compose ps               # Check status
echo   docker-compose down             # Stop all services
echo.
pause
