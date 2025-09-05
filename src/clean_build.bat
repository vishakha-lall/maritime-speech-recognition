@echo off
echo ============================================
echo Maritime API - Clean Build Script
echo ============================================

echo Stopping and removing existing containers...
docker stop maritime-speech-api 2>nul
docker rm maritime-speech-api 2>nul

echo Removing existing images...
docker rmi maritime-speech-api 2>nul

echo Cleaning Docker cache...
docker system prune -f

echo Starting fresh build (this will take a while)...
echo Installing system dependencies and Python packages...
docker build --no-cache --pull -t maritime-speech-api .

if %errorlevel%==0 (
    echo.
    echo ============================================
    echo Build completed successfully!
    echo ============================================
    echo You can now run: quick_docker.bat
    echo Or manually: docker run -d --name maritime-speech-api -p 8000:8000 --network host maritime-speech-api
) else (
    echo.
    echo ============================================
    echo Build failed! Check the output above.
    echo ============================================
)

pause
