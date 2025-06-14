#!/usr/bin/env pwsh
# Simple Karen AI System Startup

param(
    [string]$Environment = "development"
)

function Write-Success { param($Message) Write-Host "[OK] $Message" -ForegroundColor Green }
function Write-Warning { param($Message) Write-Host "[WARN] $Message" -ForegroundColor Yellow }
function Write-Info { param($Message) Write-Host "[INFO] $Message" -ForegroundColor Cyan }
function Write-Header { param($Message) Write-Host "`n=== $Message ===" -ForegroundColor Magenta }

Write-Header "KAREN AI SYSTEM STARTUP"
Write-Info "Environment: $Environment"
Write-Info "Start Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"

# Check Python
Write-Info "Checking Python installation..."
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Python found: $pythonVersion"
    } else {
        Write-Warning "Python not found or not in PATH"
        exit 1
    }
} catch {
    Write-Warning "Error checking Python: $_"
    exit 1
}

# Check virtual environment
Write-Info "Checking virtual environment..."
if (Test-Path ".venv") {
    Write-Success "Virtual environment found"
    
    # Activate virtual environment
    try {
        if ($IsWindows -or $env:OS -eq "Windows_NT") {
            & ".\.venv\Scripts\Activate.ps1"
        } else {
            . .venv/bin/activate
        }
        Write-Success "Virtual environment activated"
    } catch {
        Write-Warning "Failed to activate virtual environment: $_"
    }
} else {
    Write-Warning "Virtual environment not found. Creating one..."
    python -m venv .venv
    
    if ($IsWindows -or $env:OS -eq "Windows_NT") {
        & ".\.venv\Scripts\Activate.ps1"
    } else {
        . .venv/bin/activate
    }
    
    Write-Info "Installing dependencies..."
    pip install -r src/requirements.txt
    Write-Success "Dependencies installed"
}

# Check Redis
Write-Info "Checking Redis connection..."
$redisRunning = Test-NetConnection -ComputerName localhost -Port 6379 -InformationLevel Quiet
if ($redisRunning) {
    Write-Success "Redis is accessible on port 6379"
} else {
    Write-Warning "Redis not running on port 6379"
    Write-Info "Please start Redis manually or install it"
    Write-Info "Windows: Download from https://github.com/microsoftarchive/redis/releases"
    Write-Info "Or use Docker: docker run -d -p 6379:6379 redis:alpine"
}

# Check configuration
Write-Info "Checking configuration files..."
if (Test-Path ".env") {
    Write-Success ".env file found"
} else {
    Write-Warning ".env file not found. Creating template..."
    $envContent = @"
# Karen AI Configuration
ENVIRONMENT=$Environment
REDIS_URL=redis://localhost:6379/0
LOG_LEVEL=INFO
ADMIN_EMAIL=admin@example.com
MONITORED_EMAIL_ACCOUNT=hello@757handy.com
USE_MOCK_EMAIL_CLIENT=False
"@
    $envContent | Out-File -FilePath ".env" -Encoding UTF8
    Write-Info "Please configure .env file with your settings"
}

# Set environment variables
$env:KAREN_ENVIRONMENT = $Environment
$env:PYTHONPATH = "$(Get-Location);$(Get-Location)\src"

# Clean up any existing processes
Write-Info "Cleaning up existing processes..."
Get-Process -Name python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Get-Process -Name celery -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Remove-Item -Path "celerybeat.pid" -Force -ErrorAction SilentlyContinue
Remove-Item -Path "*.pid" -Force -ErrorAction SilentlyContinue
Write-Info "Cleanup completed"

# Start services
Write-Header "STARTING SERVICES"

# Start Celery Worker
Write-Info "Starting Celery Worker..."
try {
    $workerProcess = Start-Process -FilePath "celery" -ArgumentList "-A", "src.celery_app", "worker", "--loglevel=info", "--pool=solo" -WindowStyle Minimized -PassThru
    Start-Sleep 3
    
    if (-not $workerProcess.HasExited) {
        Write-Success "Celery Worker started (PID: $($workerProcess.Id))"
    } else {
        Write-Warning "Celery Worker failed to start"
    }
} catch {
    Write-Warning "Failed to start Celery Worker: $_"
}

# Start Celery Beat
Write-Info "Starting Celery Beat..."
try {
    $beatProcess = Start-Process -FilePath "celery" -ArgumentList "-A", "src.celery_app", "beat", "--loglevel=info" -WindowStyle Minimized -PassThru
    Start-Sleep 3
    
    if (Test-Path "celerybeat.pid") {
        Write-Success "Celery Beat started"
    } else {
        Write-Warning "Celery Beat may not have started properly"
    }
} catch {
    Write-Warning "Failed to start Celery Beat: $_"
}

# Start main application
Write-Info "Starting main Karen AI application..."
try {
    $mainProcess = Start-Process -FilePath "python" -ArgumentList "-m", "src.main" -WindowStyle Minimized -PassThru
    Start-Sleep 5
    
    if (-not $mainProcess.HasExited) {
        Write-Success "Main application started (PID: $($mainProcess.Id))"
    } else {
        Write-Warning "Main application failed to start"
    }
} catch {
    Write-Warning "Failed to start main application: $_"
}

# Final status check
Write-Header "STARTUP STATUS"

$pythonProcesses = Get-Process -Name python -ErrorAction SilentlyContinue
$celeryBeatRunning = Test-Path "celerybeat.pid"

if ($pythonProcesses) {
    Write-Success "Python processes: $($pythonProcesses.Count) running"
} else {
    Write-Warning "No Python processes found"
}

if ($celeryBeatRunning) {
    Write-Success "Celery Beat: Running"
} else {
    Write-Warning "Celery Beat: Not detected"
}

if ($redisRunning) {
    Write-Success "Redis: Connected"
} else {
    Write-Warning "Redis: Not accessible"
}

# Log startup
$startupLog = @{
    Timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    Environment = $Environment
    PythonProcesses = if ($pythonProcesses) { $pythonProcesses.Count } else { 0 }
    CeleryBeat = $celeryBeatRunning
    Redis = $redisRunning
    Success = ($pythonProcesses -and $celeryBeatRunning)
}

if (-not (Test-Path "logs")) {
    New-Item -Path "logs" -ItemType Directory -Force | Out-Null
}

$startupLog | ConvertTo-Json | Out-File -FilePath "logs/startup_log.json" -Append -Encoding UTF8

Write-Header "STARTUP COMPLETED"
if ($startupLog.Success) {
    Write-Success "Karen AI system started successfully!"
    Write-Info "Services are running and ready to process requests"
} else {
    Write-Warning "Startup completed with some issues"
    Write-Info "Check the status above and logs for details"
}

Write-Info "To stop the system, run: scripts\simple_shutdown.ps1"
Write-Info "To monitor the system, run: scripts\simple_monitor.ps1" 