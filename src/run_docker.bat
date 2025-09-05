@echo off
title Maritime Speech Processing API - Docker Runner

:main_menu
cls
echo ============================================
echo    Maritime Speech Processing API
echo ============================================
echo.
echo 1. Build Docker Image
echo 2. Run API (default database)
echo 3. Run API (custom database)
echo 4. Stop API
echo 5. View Logs
echo 6. Remove Container
echo 7. Check Status
echo 8. Open API Docs
echo 9. Exit
echo.
set /p choice="Enter your choice (1-9): "

if %choice%==1 goto build
if %choice%==2 goto run_default
if %choice%==3 goto run_custom
if %choice%==4 goto stop
if %choice%==5 goto logs
if %choice%==6 goto remove
if %choice%==7 goto status
if %choice%==8 goto docs
if %choice%==9 goto exit
echo Invalid choice. Try again.
pause
goto main_menu

:build
echo ============================================
echo Building Docker Image (Fresh Build)...
echo ============================================
echo This may take a while as we're downloading all dependencies...
docker build --no-cache --pull -t maritime-speech-api .
if %errorlevel%==0 (
    echo Build successful!
) else (
    echo Build failed!
)
pause
goto main_menu

:run_default
echo ============================================
echo Starting API with default database...
echo ============================================
echo Database: aicatsan@localhost:3306/aicatsan
echo.

docker run -d ^
  --name maritime-speech-api ^
  -p 8000:8000 ^
  --network host ^
  -v "%cd%\models:/app/models" ^
  -v "%cd%\data:/app/data" ^
  -v "%cd%\videos:/app/videos" ^
  -v "%cd%\results:/app/results" ^
  -v "%cd%\temp:/app/temp" ^
  maritime-speech-api

if %errorlevel%==0 (
    echo.
    echo ============================================
    echo API Started Successfully!
    echo ============================================
    echo API URL: http://localhost:8000
    echo API Docs: http://localhost:8000/docs
    echo Health: http://localhost:8000/health
    echo ============================================
) else (
    echo Failed to start API!
)
pause
goto main_menu

:run_custom
echo ============================================
echo Custom Database Configuration
echo ============================================
echo Enter database details (press Enter for defaults):
echo.
set /p db_user="Username [aicatsan]: "
set /p db_password="Password [aicatsan2024]: "
set /p db_host="Host [localhost]: "
set /p db_port="Port [3306]: "
set /p db_name="Database [aicatsan]: "

if "%db_user%"=="" set db_user=aicatsan
if "%db_password%"=="" set db_password=aicatsan2024
if "%db_host%"=="" set db_host=localhost
if "%db_port%"=="" set db_port=3306
if "%db_name%"=="" set db_name=aicatsan

echo.
echo Starting API with: %db_user%@%db_host%:%db_port%/%db_name%

docker run -d ^
  --name maritime-speech-api ^
  -p 8000:8000 ^
  --network host ^
  -e DB_USER=%db_user% ^
  -e DB_PASSWORD=%db_password% ^
  -e DB_HOST=%db_host% ^
  -e DB_PORT=%db_port% ^
  -e DB_NAME=%db_name% ^
  -v "%cd%\models:/app/models" ^
  -v "%cd%\data:/app/data" ^
  -v "%cd%\videos:/app/videos" ^
  -v "%cd%\results:/app/results" ^
  -v "%cd%\temp:/app/temp" ^
  maritime-speech-api

if %errorlevel%==0 (
    echo.
    echo ============================================
    echo API Started Successfully!
    echo ============================================
    echo API URL: http://localhost:8000
    echo API Docs: http://localhost:8000/docs
    echo Database: %db_user%@%db_host%:%db_port%/%db_name%
    echo ============================================
) else (
    echo Failed to start API!
)
pause
goto main_menu

:stop
echo ============================================
echo Stopping API...
echo ============================================
docker stop maritime-speech-api
if %errorlevel%==0 (
    echo API stopped successfully!
) else (
    echo No running container found or stop failed.
)
pause
goto main_menu

:logs
echo ============================================
echo API Logs (Press Ctrl+C to exit)
echo ============================================
docker logs -f maritime-speech-api
pause
goto main_menu

:remove
echo ============================================
echo Removing Container...
echo ============================================
docker stop maritime-speech-api 2>nul
docker rm maritime-speech-api
if %errorlevel%==0 (
    echo Container removed successfully!
) else (
    echo No container found or removal failed.
)
pause
goto main_menu

:status
echo ============================================
echo API Status
echo ============================================
docker ps --filter "name=maritime-speech-api" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo.

REM Check if container exists and is running
docker ps -q --filter "name=maritime-speech-api" >nul 2>&1
if %errorlevel%==0 (
    echo Testing API health...
    timeout /t 2 >nul
    curl -s http://localhost:8000/health 2>nul
    if %errorlevel%==0 (
        echo.
        echo ✓ API is healthy and responding
    ) else (
        echo.
        echo ✗ API container running but not responding
    )
) else (
    echo ✗ API container is not running
)
pause
goto main_menu

:docs
echo Opening API documentation...
start http://localhost:8000/docs
goto main_menu

:exit
echo ============================================
echo Goodbye!
echo ============================================
exit
