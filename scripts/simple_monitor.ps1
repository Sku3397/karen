#!/usr/bin/env pwsh
# Simple Karen AI System Monitor

param(
    [string]$Mode = "check"
)

function Write-Success { param($Message) Write-Host "[OK] $Message" -ForegroundColor Green }
function Write-Warning { param($Message) Write-Host "[WARN] $Message" -ForegroundColor Yellow }
function Write-Info { param($Message) Write-Host "[INFO] $Message" -ForegroundColor Cyan }
function Write-Header { param($Message) Write-Host "`n=== $Message ===" -ForegroundColor Magenta }

Write-Header "KAREN AI SYSTEM MONITOR"

# Check Redis
Write-Info "Checking Redis connection..."
$redisRunning = Test-NetConnection -ComputerName localhost -Port 6379 -InformationLevel Quiet
if ($redisRunning) {
    Write-Success "Redis is running on port 6379"
} else {
    Write-Warning "Redis is not accessible on port 6379"
}

# Check Python processes
Write-Info "Checking Python processes..."
$pythonProcesses = Get-Process -Name python -ErrorAction SilentlyContinue
if ($pythonProcesses) {
    Write-Success "Found $($pythonProcesses.Count) Python processes running"
} else {
    Write-Warning "No Python processes found"
}

# Check Celery Beat
Write-Info "Checking Celery Beat..."
if (Test-Path "celerybeat.pid") {
    Write-Success "Celery Beat PID file exists"
} else {
    Write-Warning "Celery Beat PID file not found"
}

# Check logs directory
Write-Info "Checking logs..."
if (Test-Path "logs") {
    $logFiles = Get-ChildItem "logs" -File
    Write-Success "Found $($logFiles.Count) log files"
} else {
    Write-Warning "Logs directory not found"
}

# Check configuration
Write-Info "Checking configuration..."
if (Test-Path ".env") {
    Write-Success ".env file exists"
} else {
    Write-Warning ".env file not found"
}

# Memory check
Write-Info "Checking system memory..."
try {
    $memory = Get-WmiObject -Class Win32_OperatingSystem
    $totalMemoryGB = [math]::Round($memory.TotalVisibleMemorySize/1MB, 2)
    $freeMemoryGB = [math]::Round($memory.FreePhysicalMemory/1MB, 2)
    $usedPercent = [math]::Round((($totalMemoryGB - $freeMemoryGB) / $totalMemoryGB) * 100, 1)
    
    if ($usedPercent -lt 80) {
        Write-Success "Memory usage: $usedPercent% ($freeMemoryGB GB free of $totalMemoryGB GB)"
    } else {
        Write-Warning "High memory usage: $usedPercent% ($freeMemoryGB GB free of $totalMemoryGB GB)"
    }
} catch {
    Write-Warning "Could not check memory usage"
}

Write-Header "SYSTEM STATUS SUMMARY"

# Calculate health score
$healthScore = 0
$totalChecks = 5

if ($redisRunning) { $healthScore++ }
if ($pythonProcesses) { $healthScore++ }
if (Test-Path "celerybeat.pid") { $healthScore++ }
if (Test-Path "logs") { $healthScore++ }
if (Test-Path ".env") { $healthScore++ }

$healthPercent = [math]::Round(($healthScore / $totalChecks) * 100, 1)

if ($healthPercent -ge 80) {
    Write-Success "Overall Health: $healthPercent% ($healthScore/$totalChecks checks passed)"
    Write-Info "System is running well!"
} elseif ($healthPercent -ge 60) {
    Write-Warning "Overall Health: $healthPercent% ($healthScore/$totalChecks checks passed)"
    Write-Info "System has some issues that need attention"
} else {
    Write-Warning "Overall Health: $healthPercent% ($healthScore/$totalChecks checks passed)"
    Write-Warning "System has critical issues!"
}

Write-Info "Monitor completed at $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" 