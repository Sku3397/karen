@echo off
REM Karen AI Environment Setup Script for Windows
REM Configures memory allocation and environment variables for optimal performance

echo 🚀 Setting up Karen AI environment with optimized memory allocation...

REM Memory Configuration for Node.js processes
echo 📊 Configuring Node.js memory allocation (4GB)...
set NODE_OPTIONS=--max-old-space-size=4096

REM Memory Configuration for Java-based tools (if using any)
echo ☕ Configuring Java memory allocation (4GB heap, 2GB initial)...
set JAVA_OPTS=-Xmx4g -Xms2g

REM Python memory optimizations for NLP processing
echo 🐍 Configuring Python memory optimizations...
set PYTHONHASHSEED=0
set PYTHONUNBUFFERED=1

REM NLP-specific environment variables
echo 🧠 Configuring NLP engine settings...
set NLP_CONFIDENCE_THRESHOLD=0.6
set NLP_BATCH_SIZE=10
set NLP_MAX_CONTEXT_MESSAGES=5

REM Celery optimizations for background task processing
echo 🔄 Configuring Celery worker optimizations...
set CELERY_WORKER_POOL=solo
set CELERY_WORKER_CONCURRENCY=2
set CELERY_TASK_SOFT_TIME_LIMIT=300
set CELERY_TASK_TIME_LIMIT=600

REM SMS/Communication optimizations
echo 📱 Configuring SMS processing optimizations...
set SMS_BATCH_PROCESSING=true
set SMS_RESPONSE_TIMEOUT=30
set SMS_RETRY_ATTEMPTS=3

REM Logging configuration
echo 📝 Configuring logging levels...
set LOG_LEVEL=INFO
set LOG_FORMAT=structured
set LOG_MAX_FILES=10
set LOG_MAX_SIZE=100MB

REM Performance monitoring
echo 📈 Enabling performance monitoring...
set ENABLE_PERFORMANCE_MONITORING=true
set METRICS_COLLECTION_INTERVAL=60

REM Load existing .env file if it exists
if exist .env (
    echo 📋 Loading existing .env configuration...
    for /f "delims=" %%i in (.env) do (
        set %%i 2>nul
    )
) else (
    echo ⚠️  No .env file found. Please ensure environment variables are configured.
)

REM Validate critical environment variables
echo ✅ Validating critical environment variables...

if not defined GEMINI_API_KEY (
    echo ❌ Missing required environment variable: GEMINI_API_KEY
) else (
    echo ✅ GEMINI_API_KEY is configured
)

if not defined TWILIO_ACCOUNT_SID (
    echo ❌ Missing required environment variable: TWILIO_ACCOUNT_SID
) else (
    echo ✅ TWILIO_ACCOUNT_SID is configured
)

if not defined TWILIO_AUTH_TOKEN (
    echo ❌ Missing required environment variable: TWILIO_AUTH_TOKEN
) else (
    echo ✅ TWILIO_AUTH_TOKEN is configured
)

if not defined CELERY_BROKER_URL (
    echo ❌ Missing required environment variable: CELERY_BROKER_URL
) else (
    echo ✅ CELERY_BROKER_URL is configured
)

if not defined TWILIO_PHONE_NUMBER (
    echo ⚠️  TWILIO_PHONE_NUMBER not set - SMS integration may not work
)

REM Check if Redis is accessible (if redis-cli is available)
where redis-cli >nul 2>&1
if %errorlevel% equ 0 (
    redis-cli ping >nul 2>&1
    if %errorlevel% equ 0 (
        echo ✅ Redis is running and accessible
    ) else (
        echo ❌ Redis is not running. Start it with: docker-compose up -d redis
    )
) else (
    echo ⚠️  Redis CLI not found. Install redis-tools or use Docker
)

REM Create startup script for Windows
echo 📝 Creating optimized startup script for Windows...
(
echo @echo off
echo REM Karen AI Optimized Startup Script for Windows
echo echo 🚀 Starting Karen AI with optimized settings...
echo.
echo REM Load environment
echo call setup_environment.bat
echo.
echo REM Start Redis if not running ^(using Docker^)
echo redis-cli ping ^>nul 2^>^&1
echo if %%errorlevel%% neq 0 ^(
echo     echo 🔧 Starting Redis...
echo     docker-compose up -d redis
echo     timeout /t 5 /nobreak ^>nul
echo ^)
echo.
echo REM Start Celery Beat ^(scheduler^) with optimizations
echo echo ⏰ Starting Celery Beat scheduler...
echo start "Celery Beat" /min .venv\Scripts\python.exe -m celery -A src.celery_app:celery_app beat -l INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler
echo.
echo REM Start Celery Worker with optimizations
echo echo 👷 Starting Celery Worker...
echo start "Celery Worker" /min .venv\Scripts\python.exe -m celery -A src.celery_app:celery_app worker -l INFO --pool=solo --concurrency=2
echo.
echo REM Start FastAPI server ^(optional^)
echo if "%%START_API_SERVER%%"=="true" ^(
echo     echo 🌐 Starting FastAPI server...
echo     start "FastAPI" /min python -m src.main
echo ^)
echo.
echo REM Start Frontend ^(if needed^)
echo if "%%START_FRONTEND%%"=="true" ^(
echo     echo 🎨 Starting frontend server...
echo     start "Frontend" /min npm start
echo ^)
echo.
echo echo ✅ Karen AI started successfully!
echo echo 📊 Monitor processes in Task Manager or check individual windows
) > start_karen_optimized.bat

REM Create monitoring script for Windows
echo 📊 Creating monitoring script for Windows...
(
echo @echo off
echo REM Karen AI Monitoring Script for Windows
echo echo 📊 Karen AI System Monitor
echo echo ==========================
echo.
echo REM Check memory usage
echo echo Memory Usage:
echo wmic OS get TotalVisibleMemorySize,FreePhysicalMemory /format:table
echo.
echo echo Node.js Processes:
echo tasklist /fi "imagename eq node.exe" 2^>nul ^|^| echo No Node.js processes found
echo.
echo echo Python Processes:
echo tasklist /fi "imagename eq python.exe" 2^>nul ^|^| echo No Python processes found
echo.
echo echo Redis Status:
echo redis-cli ping 2^>nul ^|^| echo Redis not accessible
echo.
echo echo Recent Log Entries:
echo if exist celery_worker_logs.txt ^(
echo     echo Celery Worker ^(last 5 lines^):
echo     powershell "Get-Content celery_worker_logs.txt -Tail 5"
echo ^) else ^(
echo     echo No worker logs found
echo ^)
echo.
echo if exist celery_beat_logs.txt ^(
echo     echo Celery Beat ^(last 5 lines^):
echo     powershell "Get-Content celery_beat_logs.txt -Tail 5"
echo ^) else ^(
echo     echo No beat logs found
echo ^)
) > monitor_karen.bat

REM Create cleanup script for Windows
echo 🧹 Creating cleanup script for Windows...
(
echo @echo off
echo REM Karen AI Cleanup Script for Windows
echo echo 🧹 Cleaning up Karen AI processes...
echo.
echo REM Stop Python processes ^(Celery workers^)
echo echo 🛑 Stopping Celery processes...
echo taskkill /f /im python.exe 2^>nul ^|^| echo No Python processes to stop
echo.
echo REM Stop Node.js processes ^(if any^)
echo taskkill /f /im node.exe 2^>nul ^|^| echo No Node.js processes to stop
echo.
echo REM Clean up log files ^(optional^)
echo if "%%1"=="--clean-logs" ^(
echo     echo 🗑️  Cleaning log files...
echo     del /q *.log *.txt celerybeat-schedule.sqlite3 2^>nul
echo ^)
echo.
echo echo ✅ Cleanup complete!
) > cleanup_karen.bat

REM Final configuration summary
echo.
echo 🎉 Environment setup complete!
echo ================================
echo.
echo Memory Configuration:
echo   • Node.js heap: 4GB (NODE_OPTIONS=%NODE_OPTIONS%)
echo   • Java heap: 4GB max, 2GB initial (JAVA_OPTS=%JAVA_OPTS%)
echo   • Python optimizations enabled
echo.
echo Scripts Created:
echo   • start_karen_optimized.bat - Start all services with optimizations
echo   • monitor_karen.bat - Monitor system status and performance
echo   • cleanup_karen.bat - Clean shutdown and cleanup
echo.
echo Next Steps:
echo 1. Run: start_karen_optimized.bat
echo 2. Monitor: monitor_karen.bat
echo 3. Test NLP: python test_nlp_integration.py
echo 4. Test SMS: python test_sms_nlp_integration.py
echo.
echo 💡 Pro Tips:
echo   • Monitor memory usage in Task Manager
echo   • Check individual service windows for real-time logs
echo   • Use cleanup_karen.bat --clean-logs to reset everything
echo.
echo ✅ Setup complete! Environment variables are now configured for this session.

pause