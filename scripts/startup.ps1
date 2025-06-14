#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Karen AI System Startup Script
    
.DESCRIPTION
    Comprehensive startup script that initializes all Karen AI services
    - Checks system requirements
    - Starts Redis server
    - Initializes Python environment
    - Starts Celery workers and beat scheduler
    - Launches main application
    - Performs health checks
    
.PARAMETER Environment
    Target environment (development, staging, production)
    
.PARAMETER SkipHealthCheck
    Skip initial health checks
    
.EXAMPLE
    .\startup.ps1 -Environment development
    .\startup.ps1 -Environment production -SkipHealthCheck
#>

param(
    [Parameter()]
    [ValidateSet("development", "staging", "production")]
    [string]$Environment = "development",
    
    [Parameter()]
    [switch]$SkipHealthCheck
)

# Script configuration
$ErrorActionPreference = "Stop"
$StartTime = Get-Date

# Color functions for output
function Write-Success { param($Message) Write-Host "✅ $Message" -ForegroundColor Green }
function Write-Warning { param($Message) Write-Host "⚠️  $Message" -ForegroundColor Yellow }
function Write-Error { param($Message) Write-Host "❌ $Message" -ForegroundColor Red }
function Write-Info { param($Message) Write-Host "ℹ️  $Message" -ForegroundColor Cyan }
function Write-Header { param($Message) Write-Host "`n🚀 $Message" -ForegroundColor Magenta }

Write-Header "KAREN AI SYSTEM STARTUP"
Write-Info "Environment: $Environment"
Write-Info "Start Time: $($StartTime.ToString('yyyy-MM-dd HH:mm:ss'))"
Write-Info "Working Directory: $(Get-Location)"

# Function to check if a process is running
function Test-ProcessRunning {
    param([string]$ProcessName)
    return (Get-Process -Name $ProcessName -ErrorAction SilentlyContinue) -ne $null
}

# Function to wait for service to be ready
function Wait-ForService {
    param(
        [string]$ServiceName,
        [scriptblock]$TestScript,
        [int]$TimeoutSeconds = 30,
        [int]$RetryIntervalSeconds = 2
    )
    
    Write-Info "Waiting for $ServiceName to be ready..."
    $elapsed = 0
    
    while ($elapsed -lt $TimeoutSeconds) {
        if (& $TestScript) {
            Write-Success "$ServiceName is ready"
            return $true
        }
        
        Start-Sleep -Seconds $RetryIntervalSeconds
        $elapsed += $RetryIntervalSeconds
        Write-Host "." -NoNewline
    }
    
    Write-Error "$ServiceName failed to start within $TimeoutSeconds seconds"
    return $false
}

# Function to start service safely
function Start-ServiceSafely {
    param(
        [string]$ServiceName,
        [scriptblock]$StartScript,
        [scriptblock]$TestScript
    )
    
    Write-Info "Starting $ServiceName..."
    
    try {
        & $StartScript
        
        if (Wait-ForService -ServiceName $ServiceName -TestScript $TestScript) {
            Write-Success "$ServiceName started successfully"
            return $true
        } else {
            Write-Error "Failed to start $ServiceName"
            return $false
        }
    } catch {
        Write-Error "Error starting $ServiceName: $($_.Exception.Message)"
        return $false
    }
}

# Clean up function
function Stop-AllServices {
    Write-Header "Stopping all services..."
    
    # Stop Python processes
            Get-Process -Name python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
        Get-Process -Name celery -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    
    # Clean up PID files
    Remove-Item -Path "celerybeat.pid" -Force -ErrorAction SilentlyContinue
    Remove-Item -Path "*.pid" -Force -ErrorAction SilentlyContinue
    
    Write-Info "Services stopped and cleaned up"
}

# Trap for cleanup on exit
trap { Stop-AllServices; exit 1 }

try {
    # Step 1: Environment Validation
    Write-Header "ENVIRONMENT VALIDATION"
    
    # Check Python
    try {
        $pythonVersion = python --version 2>&1
        Write-Success "Python found: $pythonVersion"
    } catch {
        Write-Error "Python not found. Please install Python 3.8+ and add to PATH"
        exit 1
    }
    
    # Check virtual environment
    if (Test-Path ".venv") {
        Write-Success "Virtual environment found"
        
        # Activate virtual environment
        if ($IsWindows -or $env:OS -eq "Windows_NT") {
            & ".\.venv\Scripts\Activate.ps1"
        } else {
            . .venv/bin/activate
        }
        Write-Success "Virtual environment activated"
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
    
    # Check Redis availability
    $redisRunning = Test-NetConnection -ComputerName localhost -Port 6379 -InformationLevel Quiet -ErrorAction SilentlyContinue
    if (-not $redisRunning) {
        Write-Warning "Redis not running on port 6379"
        Write-Info "Please ensure Redis is installed and running"
        Write-Info "Windows: Download from https://github.com/microsoftarchive/redis/releases"
        Write-Info "Or use Docker: docker run -d -p 6379:6379 redis:alpine"
    } else {
        Write-Success "Redis is accessible on port 6379"
    }
    
    # Step 2: Configuration Setup
    Write-Header "CONFIGURATION SETUP"
    
    # Check environment file
    if (Test-Path ".env") {
        Write-Success ".env file found"
    } else {
        Write-Warning ".env file not found. Creating template..."
        @"
# Karen AI Configuration
ENVIRONMENT=$Environment
REDIS_URL=redis://localhost:6379/0
LOG_LEVEL=INFO
ADMIN_EMAIL=admin@example.com
MONITORED_EMAIL_ACCOUNT=hello@757handy.com
USE_MOCK_EMAIL_CLIENT=False
"@ | Out-File -FilePath ".env" -Encoding UTF8
        Write-Info "Please configure .env file with your settings"
    }
    
    # Set environment variables
    $env:KAREN_ENVIRONMENT = $Environment
    $env:PYTHONPATH = "$(Get-Location);$(Get-Location)\src"
    
    # Step 3: System Health Check (unless skipped)
    if (-not $SkipHealthCheck) {
        Write-Header "SYSTEM HEALTH CHECK"
        
        Write-Info "Running system status check..."
        $healthResult = python system_status_check.py
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "System health check passed"
        } else {
            Write-Warning "System health check reported issues. Continuing with startup..."
        }
    }
    
    # Step 4: Service Startup
    Write-Header "SERVICE STARTUP"
    
    # Clean up any existing processes
    Write-Info "Cleaning up existing processes..."
    Stop-AllServices
    
    # Start Redis (if not running)
    if (-not $redisRunning) {
        Write-Info "Attempting to start Redis..."
        if (Get-Command redis-server -ErrorAction SilentlyContinue) {
            Start-Process -FilePath "redis-server" -WindowStyle Hidden
            Start-Sleep 3
        } else {
            Write-Warning "Redis server command not found. Please start Redis manually."
        }
    }
    
    # Start Celery Worker
    $celeryWorkerStarted = Start-ServiceSafely -ServiceName "Celery Worker" -StartScript {
        $celeryCmd = "celery -A src.celery_app worker --loglevel=info --pool=solo"
        Start-Process -FilePath "powershell" -ArgumentList "-Command", $celeryCmd -WindowStyle Minimized
    } -TestScript {
        # Check if celery worker is running by checking Redis for worker registration
        try {
            $result = python -c "import redis; r = redis.Redis(); print(len(r.smembers('celery.workers')))" 2>$null
            return [int]$result -gt 0
        } catch {
            return $false
        }
    }
    
    if (-not $celeryWorkerStarted) {
        Write-Error "Failed to start Celery Worker"
        exit 1
    }
    
    # Start Celery Beat
    $celeryBeatStarted = Start-ServiceSafely -ServiceName "Celery Beat" -StartScript {
        $celeryBeatCmd = "celery -A src.celery_app beat --loglevel=info"
        Start-Process -FilePath "powershell" -ArgumentList "-Command", $celeryBeatCmd -WindowStyle Minimized
    } -TestScript {
        # Check if beat scheduler is running by checking for PID file
        return Test-Path "celerybeat.pid"
    }
    
    if (-not $celeryBeatStarted) {
        Write-Error "Failed to start Celery Beat"
        exit 1
    }
    
    # Start Main Application
    Write-Info "Starting main Karen AI application..."
    $mainAppProcess = Start-Process -FilePath "python" -ArgumentList "-m", "src.main" -WindowStyle Minimized -PassThru
    
    # Wait for main app to initialize
    Start-Sleep 5
    
    if ($mainAppProcess.HasExited) {
        Write-Error "Main application failed to start"
        exit 1
    } else {
        Write-Success "Main application started (PID: $($mainAppProcess.Id))"
    }
    
    # Step 5: Final Health Check
    Write-Header "FINAL SYSTEM VERIFICATION"
    
    # Test system components
    $systemChecks = @(
        @{ Name = "Redis Connection"; Test = { 
            try { 
                python -c "import redis; redis.Redis().ping()" 2>$null
                return $LASTEXITCODE -eq 0
            } catch { return $false }
        }},
        @{ Name = "Celery Worker"; Test = { 
            try {
                $result = python -c "import redis; r = redis.Redis(); print(len(r.smembers('celery.workers')))" 2>$null
                return [int]$result -gt 0
            } catch { return $false }
        }},
        @{ Name = "Celery Beat"; Test = { Test-Path "celerybeat.pid" }},
        @{ Name = "Main Application"; Test = { -not $mainAppProcess.HasExited }}
    )
    
    $allChecksPass = $true
    foreach ($check in $systemChecks) {
        if (& $check.Test) {
            Write-Success "$($check.Name): OK"
        } else {
            Write-Error "$($check.Name): FAILED"
            $allChecksPass = $false
        }
    }
    
    # Step 6: Startup Complete
    Write-Header "STARTUP COMPLETE"
    
    $endTime = Get-Date
    $duration = $endTime - $StartTime
    
    if ($allChecksPass) {
        Write-Success "Karen AI system startup completed successfully!"
        Write-Info "Total startup time: $($duration.TotalSeconds.ToString('F1')) seconds"
        Write-Info "Environment: $Environment"
        Write-Info "Main Application PID: $($mainAppProcess.Id)"
        
        Write-Host "`n📊 Service Status:" -ForegroundColor Cyan
        Write-Host "  • Redis: Running on port 6379"
        Write-Host "  • Celery Worker: Running"
        Write-Host "  • Celery Beat: Running"
        Write-Host "  • Main Application: Running (PID $($mainAppProcess.Id))"
        
        Write-Host "`n🔗 Access Information:" -ForegroundColor Cyan
        Write-Host "  • System Status: Run 'python system_status_check.py'"
        Write-Host "  • Logs: Check 'logs/' directory"
        Write-Host "  • Stop System: Run 'scripts\shutdown.ps1'"
        
        Write-Host "`n✨ Karen AI is ready to process customer requests!" -ForegroundColor Green
        
        # Save startup info
        $startupInfo = @{
            StartTime = $StartTime.ToString('yyyy-MM-dd HH:mm:ss')
            Environment = $Environment
            Duration = $duration.TotalSeconds
            MainAppPID = $mainAppProcess.Id
            Status = "Success"
        }
        $startupInfo | ConvertTo-Json | Out-File -FilePath "logs/last_startup.json" -Encoding UTF8
        
    } else {
        Write-Error "System startup completed with errors. Please check the failed components."
        exit 1
    }
    
} catch {
    Write-Error "Startup failed: $($_.Exception.Message)"
    Write-Error $_.ScriptStackTrace
    Stop-AllServices
    exit 1
} 