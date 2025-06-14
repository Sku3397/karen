@echo off
echo 🚀 Starting Karen AI Handyman Business System with MCP Monitoring
echo ================================================================

REM Activate virtual environment
echo 📦 Activating virtual environment...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo ❌ Failed to activate virtual environment
    echo Make sure .venv exists and run: python -m venv .venv
    pause
    exit /b 1
)

REM Check if Redis is running
echo 🔗 Checking Redis connection...
python -c "import redis; r=redis.Redis(); r.ping(); print('✅ Redis connected')" 2>nul
if errorlevel 1 (
    echo ⚠️  Redis not running - some features may not work
    echo 💡 To start Redis: docker run -d --name karen-redis -p 6379:6379 redis
    echo    Or install Redis locally and start the service
    echo.
)

REM Create logs directory
if not exist logs mkdir logs

REM Start Celery Beat (scheduler)
echo 📅 Starting Celery Beat scheduler...
start "Karen Celery Beat" /MIN python -m celery -A src.celery_app:celery_app beat -l INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler

REM Wait a moment for Beat to start
timeout /t 2 /nobreak >nul

REM Start Celery Worker
echo ⚙️  Starting Celery Worker...
start "Karen Celery Worker" /MIN python -m celery -A src.celery_app:celery_app worker -l DEBUG --pool=solo --without-heartbeat --without-gossip --without-mingle

REM Wait a moment for Worker to start  
timeout /t 3 /nobreak >nul

REM Start Main Application
echo 🏠 Starting Main Karen Application...
start "Karen Main App" /MIN python -m src.main

REM Wait a moment for main app to start
timeout /t 2 /nobreak >nul

REM Start MCP Server for monitoring
echo 📊 Starting MCP Monitoring Server...
start "Karen MCP Monitor" /MIN python karen_mcp_server.py

echo.
echo ✅ Karen AI System Started with MCP Monitoring!
echo ================================================================
echo 🎛️  Services Running:
echo    • Celery Beat Scheduler (background)
echo    • Celery Worker (background)  
echo    • Main Karen Application (background)
echo    • MCP Monitoring Server (background)
echo.
echo 📊 Check system status: python test_karen_mcp_real.py
echo 🛑 To stop services: Use Task Manager or run stop_karen.bat
echo ================================================================

pause 