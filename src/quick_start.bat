@echo off
echo ================================================
echo Maritime Speech Processing API - Quick Start
echo ================================================

REM Navigate to the script directory
cd /d "%~dp0"

REM Check if Docker is running
docker info > nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker is not running!
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)

echo Building and starting the API...
echo.

REM Build and run
docker-compose up --build -d

if %errorlevel% neq 0 (
    echo Failed to start API!
    pause
    exit /b 1
)

echo.
echo ================================================
echo API started successfully!
echo ================================================
echo API Base URL: http://localhost:8000
echo API Documentation: http://localhost:8000/docs
echo Health Check: http://localhost:8000/health
echo ================================================
echo.
echo To stop the API, run: docker-compose down
echo To view logs, run: docker-compose logs -f
echo.

REM Optional: Open API docs in browser
set /p open_docs="Open API documentation in browser? (y/N): "
if /i "%open_docs%"=="y" (
    start http://localhost:8000/docs
)

pause
