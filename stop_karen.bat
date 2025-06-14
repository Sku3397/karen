@echo off
echo 🛑 Stopping Karen AI Handyman Business System
echo ===============================================

echo 🔍 Finding and stopping Karen processes...

REM Stop Python processes related to Karen
echo ⚙️  Stopping Celery Worker processes...
for /f "tokens=2" %%i in ('tasklist /fi "imagename eq python.exe" /fo table /nh ^| findstr "celery.*worker"') do (
    taskkill /PID %%i /F 2>nul
    if not errorlevel 1 echo   ✅ Stopped Celery Worker (PID %%i)
)

echo 📅 Stopping Celery Beat processes...
for /f "tokens=2" %%i in ('tasklist /fi "imagename eq python.exe" /fo table /nh ^| findstr "celery.*beat"') do (
    taskkill /PID %%i /F 2>nul
    if not errorlevel 1 echo   ✅ Stopped Celery Beat (PID %%i)
)

echo 🏠 Stopping Main Application processes...
for /f "tokens=2" %%i in ('tasklist /fi "imagename eq python.exe" /fo table /nh ^| findstr "src.main"') do (
    taskkill /PID %%i /F 2>nul
    if not errorlevel 1 echo   ✅ Stopped Main App (PID %%i)
)

echo 📊 Stopping MCP Server processes...
for /f "tokens=2" %%i in ('tasklist /fi "imagename eq python.exe" /fo table /nh ^| findstr "karen_mcp_server"') do (
    taskkill /PID %%i /F 2>nul
    if not errorlevel 1 echo   ✅ Stopped MCP Server (PID %%i)
)

REM Alternative approach - kill all python processes on common ports
echo 🔌 Checking for processes on Karen ports...
for /f "tokens=5" %%i in ('netstat -ano ^| findstr ":8002"') do (
    taskkill /PID %%i /F 2>nul
    if not errorlevel 1 echo   ✅ Stopped process on port 8002 (PID %%i)
)

REM Clean up temporary files
echo 🧹 Cleaning up temporary files...
if exist celerybeat.pid (
    del celerybeat.pid 2>nul
    echo   ✅ Removed celerybeat.pid
)

if exist celerybeat-schedule.sqlite3 (
    echo   📋 Keeping celerybeat-schedule.sqlite3 (contains scheduled tasks)
)

echo.
echo ✅ Karen AI System Stopped
echo ===============================================
echo 💡 To restart: run start_karen_with_mcp.bat
echo 📊 Check status: python test_karen_mcp_real.py
echo ===============================================

pause 