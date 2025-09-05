@echo off
echo ============================================
echo Maritime Speech Processing API - Quick Start
echo ============================================

REM Navigate to script directory
cd /d "%~dp0"

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker is not running!
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)

echo Building Docker image (fresh build)...
echo This may take a while as we're downloading all dependencies...
docker build --no-cache --pull -t maritime-speech-api .

if %errorlevel% neq 0 (
    echo Build failed!
    pause
    exit /b 1
)

echo.
echo Starting API container...

REM Stop and remove existing container if it exists
docker stop maritime-speech-api 2>nul
docker rm maritime-speech-api 2>nul

REM Run the container
docker run -d \
  --name maritime-speech-api \
  -p 8000:8000 \
  --network host \
  -e DB_USER=user \
  -e DB_PASSWORD=password \
  -e DB_HOST=localhost \
  -e DB_NAME=aicatsan \
  -v "./models:/app/models" \
  -v "./data:/app/data" \
  -v "./videos:/app/videos" \
  maritime-speech-api

if %errorlevel%==0 (
    echo.
    echo ============================================
    echo API Started Successfully!
    echo ============================================
    echo API URL: http://localhost:8000
    echo API Documentation: http://localhost:8000/docs
    echo Health Check: http://localhost:8000/health
    echo ============================================
    echo.
    echo Database: aicatsan@localhost:3306/aicatsan
    echo.
    echo To stop: docker stop maritime-speech-api
    echo To view logs: docker logs -f maritime-speech-api
    echo ============================================
    
    set /p open_docs="Open API documentation? (y/N): "
    if /i "%open_docs%"=="y" start http://localhost:8000/docs
) else (
    echo Failed to start API container!
)

pause
