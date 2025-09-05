@echo off
echo ================================================
echo Maritime Speech Processing API - Docker Setup
echo ================================================
echo.

REM Check if Docker is running
docker info > nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker is not running or not installed!
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)

echo Docker is running...
echo.

REM Navigate to the script directory
cd /d "%~dp0"

REM Display menu
:menu
echo ================================================
echo Select an option:
echo ================================================
echo 1. Build Docker image
echo 2. Run API (detached mode)
echo 3. Run API (with logs)
echo 4. Stop API
echo 5. View logs
echo 6. Remove containers and images
echo 7. Check API status
echo 8. Open API documentation
echo 9. Exit
echo ================================================
set /p choice="Enter your choice (1-9): "

if "%choice%"=="1" goto build
if "%choice%"=="2" goto run_detached
if "%choice%"=="3" goto run_logs
if "%choice%"=="4" goto stop
if "%choice%"=="5" goto logs
if "%choice%"=="6" goto cleanup
if "%choice%"=="7" goto status
if "%choice%"=="8" goto docs
if "%choice%"=="9" goto exit
echo Invalid choice. Please try again.
goto menu

:build
echo ================================================
echo Building Docker image...
echo ================================================
docker-compose build
if %errorlevel% neq 0 (
    echo Build failed!
    pause
    goto menu
)
echo Build completed successfully!
echo.
pause
goto menu

:run_detached
echo ================================================
echo Starting API in detached mode...
echo ================================================
docker-compose up -d
if %errorlevel% neq 0 (
    echo Failed to start API!
    pause
    goto menu
)
echo API started successfully!
echo API is running at: http://localhost:8000
echo API Documentation: http://localhost:8000/docs
echo.
pause
goto menu

:run_logs
echo ================================================
echo Starting API with logs...
echo ================================================
echo Press Ctrl+C to stop
echo.
docker-compose up
goto menu

:stop
echo ================================================
echo Stopping API...
echo ================================================
docker-compose down
echo API stopped.
echo.
pause
goto menu

:logs
echo ================================================
echo Viewing API logs...
echo ================================================
echo Press Ctrl+C to exit logs
echo.
docker-compose logs -f maritime-api
goto menu

:cleanup
echo ================================================
echo Cleaning up containers and images...
echo ================================================
set /p confirm="Are you sure? This will remove all containers and images (y/N): "
if /i not "%confirm%"=="y" (
    echo Cleanup cancelled.
    pause
    goto menu
)
docker-compose down --rmi all --volumes
docker system prune -f
echo Cleanup completed.
echo.
pause
goto menu

:status
echo ================================================
echo Checking API status...
echo ================================================
docker-compose ps
echo.
echo Checking API health...
curl -s http://localhost:8000/health
echo.
echo.
pause
goto menu

:docs
echo ================================================
echo Opening API documentation...
echo ================================================
start http://localhost:8000/docs
echo API documentation opened in browser.
echo.
pause
goto menu

:exit
echo ================================================
echo Goodbye!
echo ================================================
exit /b 0
