#!/usr/bin/env pwsh
# Simple Karen AI System Shutdown

param(
    [switch]$Force,
    [switch]$BackupFirst
)

function Write-Success { param($Message) Write-Host "[OK] $Message" -ForegroundColor Green }
function Write-Warning { param($Message) Write-Host "[WARN] $Message" -ForegroundColor Yellow }
function Write-Info { param($Message) Write-Host "[INFO] $Message" -ForegroundColor Cyan }
function Write-Header { param($Message) Write-Host "`n=== $Message ===" -ForegroundColor Magenta }

Write-Header "KAREN AI SYSTEM SHUTDOWN"
Write-Info "Shutdown initiated at $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"

# Backup before shutdown if requested
if ($BackupFirst) {
    Write-Info "Creating backup before shutdown..."
    try {
        & "scripts\simple_backup.ps1" -BackupType "config"
        Write-Success "Backup completed"
    } catch {
        Write-Warning "Backup failed: $_"
    }
}

# Stop main application processes
Write-Info "Stopping Karen AI processes..."

# Get current processes
$pythonProcesses = Get-Process -Name python -ErrorAction SilentlyContinue
$celeryProcesses = Get-Process -Name celery -ErrorAction SilentlyContinue

if ($pythonProcesses) {
    Write-Info "Found $($pythonProcesses.Count) Python processes"
    foreach ($proc in $pythonProcesses) {
        Write-Info "Stopping Python process (PID: $($proc.Id))"
        if ($Force) {
            $proc | Stop-Process -Force -ErrorAction SilentlyContinue
        } else {
            $proc | Stop-Process -ErrorAction SilentlyContinue
        }
    }
    Write-Success "Python processes stopped"
} else {
    Write-Info "No Python processes found"
}

if ($celeryProcesses) {
    Write-Info "Stopping Celery processes..."
    $celeryProcesses | Stop-Process -Force -ErrorAction SilentlyContinue
    Write-Success "Celery processes stopped"
} else {
    Write-Info "No Celery processes found"
}

# Clean up PID files
Write-Info "Cleaning up process files..."
$pidFiles = @("celerybeat.pid", "karen.pid", "worker.pid")
$cleanedFiles = 0

foreach ($pidFile in $pidFiles) {
    if (Test-Path $pidFile) {
        Remove-Item -Path $pidFile -Force -ErrorAction SilentlyContinue
        Write-Info "Removed: $pidFile"
        $cleanedFiles++
    }
}

if ($cleanedFiles -eq 0) {
    Write-Info "No PID files to clean"
} else {
    Write-Success "Cleaned $cleanedFiles PID files"
}

# Clean up temporary files
Write-Info "Cleaning up temporary files..."
if (Test-Path "temp") {
    $tempFiles = Get-ChildItem "temp" -File -ErrorAction SilentlyContinue
    if ($tempFiles) {
        $tempFiles | Remove-Item -Force -ErrorAction SilentlyContinue
        Write-Success "Cleaned $($tempFiles.Count) temporary files"
    } else {
        Write-Info "No temporary files to clean"
    }
} else {
    Write-Info "Temp directory not found"
}

# Wait for processes to terminate
Write-Info "Waiting for processes to terminate..."
Start-Sleep 3

# Check for remaining processes
$remainingProcesses = Get-Process -Name python, celery -ErrorAction SilentlyContinue
if ($remainingProcesses) {
    if ($Force) {
        Write-Info "Force terminating remaining processes..."
        $remainingProcesses | Stop-Process -Force -ErrorAction SilentlyContinue
        Write-Warning "Force terminated $($remainingProcesses.Count) processes"
    } else {
        Write-Warning "Some processes still running. Use -Force to terminate immediately"
        Write-Info "Remaining processes:"
        $remainingProcesses | ForEach-Object {
            Write-Info "  - $($_.ProcessName) (PID: $($_.Id))"
        }
    }
} else {
    Write-Success "All processes terminated successfully"
}

# Log shutdown
$shutdownLog = @{
    Timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    BackupPerformed = $BackupFirst.IsPresent
    ForcedShutdown = $Force.IsPresent
    ProcessesStopped = if ($pythonProcesses) { $pythonProcesses.Count } else { 0 }
    CleanedFiles = $cleanedFiles
    Success = (-not $remainingProcesses)
}

if (-not (Test-Path "logs")) {
    New-Item -Path "logs" -ItemType Directory -Force | Out-Null
}

$shutdownLog | ConvertTo-Json | Out-File -FilePath "logs/shutdown_log.json" -Append -Encoding UTF8

Write-Header "SHUTDOWN COMPLETED"
if ($shutdownLog.Success) {
    Write-Success "Karen AI system has been stopped successfully"
    Write-Info "All processes terminated and cleanup completed"
} else {
    Write-Warning "Shutdown completed with some processes still running"
    Write-Info "Use -Force parameter to terminate remaining processes"
}

if ($BackupFirst) {
    Write-Info "Backup was created before shutdown"
}

Write-Info "To restart the system, run: scripts\simple_startup.ps1"
Write-Info "Shutdown logged to: logs/shutdown_log.json" 