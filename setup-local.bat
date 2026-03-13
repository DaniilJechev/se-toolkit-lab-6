@echo off
echo ========================================
echo Lab 6 Local Setup Script
echo ========================================
echo.

cd /d %~dp0

echo Step 1: Starting Docker containers...
docker compose --env-file .env.docker.secret up --build -d
if %errorlevel% neq 0 (
    echo ERROR: Failed to start Docker containers.
    echo Please check if Docker Desktop is running.
    exit /b 1
)

echo.
echo Step 2: Waiting for containers to be ready (30 seconds)...
timeout /t 30 /nobreak

echo.
echo Step 3: Checking container status...
docker compose --env-file .env.docker.secret ps

echo.
echo ========================================
echo Setup complete!
echo ========================================
echo.
echo Next steps:
echo 1. Open http://localhost:42002/docs in your browser
echo 2. Authorize with API key: Abcd1234
echo 3. Call POST /pipeline/sync to populate the database
echo 4. Call GET /items/ to verify data
echo.
echo Frontend: http://localhost:42002/
echo ========================================
