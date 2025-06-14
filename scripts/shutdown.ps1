#!/usr/bin/env pwsh
# Karen AI System Shutdown Script

param(
    [switch]$Force,
    [switch]$BackupFirst,
    [int]$TimeoutSeconds = 30
)

$ErrorActionPreference = "Stop"

function Write-Success { param($Message) Write-Host "✅ $Message" -ForegroundColor Green }
function Write-Warning { param($Message) Write-Host "⚠️  $Message" -ForegroundColor Yellow }
function Write-Info { param($Message) Write-Host "ℹ️  $Message" -ForegroundColor Cyan }
function Write-Header { param($Message) Write-Host "`n🛑 $Message" -ForegroundColor Red }

Write-Header "KAREN AI SYSTEM SHUTDOWN"
Write-Info "Shutdown initiated at $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"

try {
    # Backup before shutdown if requested
    if ($BackupFirst) {
        Write-Info "Creating backup before shutdown..."
        & "scripts\backup.ps1" -BackupType "incremental"
        Write-Success "Backup completed"
    }
    
    # Stop main application processes
    Write-Info "Stopping Karen AI application processes..."
    
    # Stop Python processes (main app and Celery workers)
    $pythonProcesses = Get-Process -Name python -ErrorAction SilentlyContinue
    if ($pythonProcesses) {
        Write-Info "Found $($pythonProcesses.Count) Python processes"
        foreach ($proc in $pythonProcesses) {
            Write-Info "Stopping process: $($proc.ProcessName) (PID: $($proc.Id))"
            if ($Force) {
                $proc | Stop-Process -Force -ErrorAction SilentlyContinue
            } else {
                $proc | Stop-Process -ErrorAction SilentlyContinue
            }
        }
        Write-Success "Python processes stopped"
    }
    
    # Stop Celery processes specifically
    $celeryProcesses = Get-Process -Name celery -ErrorAction SilentlyContinue
    if ($celeryProcesses) {
        Write-Info "Stopping Celery processes..."
        $celeryProcesses | Stop-Process -Force -ErrorAction SilentlyContinue
        Write-Success "Celery processes stopped"
    }
    
    # Clean up PID files
    Write-Info "Cleaning up process files..."
    $pidFiles = @("celerybeat.pid", "karen.pid", "worker.pid")
    foreach ($pidFile in $pidFiles) {
        if (Test-Path $pidFile) {
            Remove-Item -Path $pidFile -Force -ErrorAction SilentlyContinue
            Write-Info "Removed: $pidFile"
        }
    }
    
    # Clean up temporary files
    Write-Info "Cleaning up temporary files..."
    if (Test-Path "temp") {
        Get-ChildItem "temp" -File | Remove-Item -Force -ErrorAction SilentlyContinue
        Write-Info "Temporary files cleaned"
    }
    
    # Wait for processes to fully terminate
    Write-Info "Waiting for processes to terminate gracefully..."
    Start-Sleep 3
    
    # Force kill any remaining Karen AI processes
    if (-not $Force) {
        $remainingProcesses = Get-Process -Name python, celery -ErrorAction SilentlyContinue
        if ($remainingProcesses) {
            Write-Warning "Some processes still running. Use -Force to terminate immediately."
        }
    } else {
        # Force terminate any remaining processes
        Get-Process -Name python, celery -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
        Write-Info "Force terminated remaining processes"
    }
    
    # Log shutdown
    $shutdownLog = @{
        Timestamp = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
        Type = "Normal Shutdown"
        BackupPerformed = $BackupFirst.IsPresent
        ForcedShutdown = $Force.IsPresent
        Success = $true
    }
    
    if (-not (Test-Path "logs")) {
        New-Item -Path "logs" -ItemType Directory -Force | Out-Null
    }
    
    $shutdownLog | ConvertTo-Json | Out-File -FilePath "logs/shutdown_log.json" -Append -Encoding UTF8
    
    Write-Header "SHUTDOWN COMPLETED"
    Write-Success "Karen AI system has been stopped successfully"
    Write-Info "All processes terminated and cleanup completed"
    
    if ($BackupFirst) {
        Write-Info "Backup was created before shutdown"
    }
    
    Write-Info "To restart the system, run: scripts\startup.ps1"
    
} catch {
    Write-Warning "Error during shutdown: $($_.Exception.Message)"
    
    # Log shutdown failure
    $failureLog = @{
        Timestamp = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
        Type = "Failed Shutdown"
        Error = $_.Exception.Message
        Success = $false
    }
    
    if (-not (Test-Path "logs")) {
        New-Item -Path "logs" -ItemType Directory -Force | Out-Null
    }
    
    $failureLog | ConvertTo-Json | Out-File -FilePath "logs/shutdown_failures.json" -Append -Encoding UTF8
    
    # Force cleanup on error
    Write-Info "Performing force cleanup due to error..."
    Get-Process -Name python, celery -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Remove-Item -Path "*.pid" -Force -ErrorAction SilentlyContinue
    
    Write-Warning "Shutdown completed with errors. Check logs for details."
} 