#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Karen AI System Monitoring Script
    
.DESCRIPTION
    Comprehensive monitoring script that checks system health and performance
    - Monitors all services and processes
    - Checks resource usage
    - Analyzes logs for errors
    - Generates alerts and reports
    - Provides real-time dashboard
    
.PARAMETER Mode
    Monitoring mode (dashboard, check, report, watch)
    
.PARAMETER Duration
    Duration for watch mode in seconds
    
.PARAMETER AlertThreshold
    Resource usage threshold for alerts (percentage)
    
.EXAMPLE
    .\monitor.ps1 -Mode dashboard
    .\monitor.ps1 -Mode watch -Duration 300
    .\monitor.ps1 -Mode check
#>

param(
    [Parameter()]
    [ValidateSet("dashboard", "check", "report", "watch", "alert")]
    [string]$Mode = "dashboard",
    
    [Parameter()]
    [int]$Duration = 60,
    
    [Parameter()]
    [ValidateRange(1, 100)]
    [int]$AlertThreshold = 80
)

# Script configuration
$ErrorActionPreference = "SilentlyContinue"

# Color functions for output
function Write-Success { param($Message) Write-Host "✅ $Message" -ForegroundColor Green }
function Write-Warning { param($Message) Write-Host "⚠️  $Message" -ForegroundColor Yellow }
function Write-Error { param($Message) Write-Host "❌ $Message" -ForegroundColor Red }
function Write-Info { param($Message) Write-Host "ℹ️  $Message" -ForegroundColor Cyan }
function Write-Header { param($Message) Write-Host "`n📊 $Message" -ForegroundColor Magenta }
function Write-Metric { param($Name, $Value, $Unit = "", $Good = $true) 
    $color = if ($Good) { "Green" } else { "Red" }
    $emoji = if ($Good) { "✅" } else { "❌" }
    Write-Host "$emoji $Name`: $Value$Unit" -ForegroundColor $color
}

# Function to get system metrics
function Get-SystemMetrics {
    $metrics = @{}
    
    # Memory usage
    if (Get-Command Get-ComputerInfo -ErrorAction SilentlyContinue) {
        $computerInfo = Get-ComputerInfo
        $totalMemoryGB = [math]::Round($computerInfo.TotalPhysicalMemory / 1GB, 2)
        $availableMemoryGB = [math]::Round($computerInfo.AvailablePhysicalMemory / 1GB, 2)
        $usedMemoryGB = [math]::Round($totalMemoryGB - $availableMemoryGB, 2)
        $memoryUsagePercent = [math]::Round(($usedMemoryGB / $totalMemoryGB) * 100, 1)
        
        $metrics["Memory"] = @{
            Total = $totalMemoryGB
            Used = $usedMemoryGB
            Available = $availableMemoryGB
            UsagePercent = $memoryUsagePercent
        }
    }
    
    # CPU usage
    $cpuUsage = Get-WmiObject Win32_Processor | Measure-Object -Property LoadPercentage -Average | Select-Object -ExpandProperty Average
    $metrics["CPU"] = @{
        UsagePercent = [math]::Round($cpuUsage, 1)
    }
    
    # Disk usage
    $diskInfo = Get-WmiObject -Class Win32_LogicalDisk -Filter "DriveType=3" | Where-Object { $_.DeviceID -eq "C:" }
    if ($diskInfo) {
        $totalDiskGB = [math]::Round($diskInfo.Size / 1GB, 2)
        $freeDiskGB = [math]::Round($diskInfo.FreeSpace / 1GB, 2)
        $usedDiskGB = [math]::Round($totalDiskGB - $freeDiskGB, 2)
        $diskUsagePercent = [math]::Round(($usedDiskGB / $totalDiskGB) * 100, 1)
        
        $metrics["Disk"] = @{
            Total = $totalDiskGB
            Used = $usedDiskGB
            Free = $freeDiskGB
            UsagePercent = $diskUsagePercent
        }
    }
    
    return $metrics
}

# Function to check service status
function Get-ServiceStatus {
    $services = @{}
    
    # Check Redis
    $redisStatus = Test-NetConnection -ComputerName localhost -Port 6379 -InformationLevel Quiet
    $services["Redis"] = @{
        Status = if ($redisStatus) { "Running" } else { "Stopped" }
        Port = 6379
        Healthy = $redisStatus
    }
    
    # Check Python processes
    $pythonProcesses = Get-Process -Name python -ErrorAction SilentlyContinue
    $celeryProcesses = Get-Process -Name celery -ErrorAction SilentlyContinue
    
    $services["Python"] = @{
        Status = if ($pythonProcesses) { "Running ($(@($pythonProcesses).Count) processes)" } else { "Stopped" }
        Processes = @($pythonProcesses).Count
        Healthy = $pythonProcesses -ne $null
    }
    
    # Check Celery Beat
    $celeryBeatRunning = Test-Path "celerybeat.pid"
    $services["Celery Beat"] = @{
        Status = if ($celeryBeatRunning) { "Running" } else { "Stopped" }
        PidFile = $celeryBeatRunning
        Healthy = $celeryBeatRunning
    }
    
    # Check Celery Workers via Redis
    try {
        $workerCount = python -c "import redis; r = redis.Redis(); print(len(r.smembers('celery.workers')))" 2>$null
        $workersHealthy = [int]$workerCount -gt 0
        $services["Celery Workers"] = @{
            Status = if ($workersHealthy) { "Running ($workerCount workers)" } else { "No workers detected" }
            Count = [int]$workerCount
            Healthy = $workersHealthy
        }
    } catch {
        $services["Celery Workers"] = @{
            Status = "Unknown (Redis connection failed)"
            Count = 0
            Healthy = $false
        }
    }
    
    return $services
}

# Function to analyze recent logs
function Get-LogAnalysis {
    $analysis = @{
        Errors = 0
        Warnings = 0
        Recent = @()
        ErrorMessages = @()
    }
    
    $logFiles = @(
        "logs/autonomous_system.log",
        "logs/karen.log",
        "logs/celery.log"
    )
    
    foreach ($logFile in $logFiles) {
        if (Test-Path $logFile) {
            $recentLines = Get-Content $logFile -Tail 100 | Where-Object { $_ -match (Get-Date).ToString("yyyy-MM-dd") }
            
            foreach ($line in $recentLines) {
                if ($line -match "ERROR|CRITICAL") {
                    $analysis.Errors++
                    $analysis.ErrorMessages += $line
                }
                elseif ($line -match "WARNING|WARN") {
                    $analysis.Warnings++
                }
            }
            
            $analysis.Recent += @{
                File = $logFile
                Lines = $recentLines.Count
                LastUpdate = (Get-Item $logFile).LastWriteTime
            }
        }
    }
    
    return $analysis
}

# Function to check email system
function Get-EmailSystemStatus {
    try {
        # Run a quick email system check
        $emailCheck = python -c @"
import sys
sys.path.append('src')
try:
    from config import ADMIN_EMAIL, MONITORED_EMAIL_ACCOUNT_CONFIG
    from email_client import EmailClient
    print(f'Admin: {ADMIN_EMAIL or "Not configured"}')
    print(f'Monitored: {MONITORED_EMAIL_ACCOUNT_CONFIG or "Not configured"}')
    print('Status: Configured')
except Exception as e:
    print(f'Status: Error - {str(e)}')
"@ 2>$null
        
        return @{
            Status = "Checked"
            Details = $emailCheck -split "`n"
            Healthy = $emailCheck -notmatch "Error"
        }
    } catch {
        return @{
            Status = "Error"
            Details = @("Failed to check email system")
            Healthy = $false
        }
    }
}

# Function to display dashboard
function Show-Dashboard {
    Clear-Host
    
    Write-Header "KAREN AI SYSTEM MONITORING DASHBOARD"
    Write-Host "🕒 Last Update: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
    Write-Host "🔄 Refresh: Every 5 seconds (Press Ctrl+C to exit)" -ForegroundColor Gray
    
    # System Metrics
    Write-Header "SYSTEM RESOURCES"
    $metrics = Get-SystemMetrics
    
    if ($metrics.Memory) {
        $memGood = $metrics.Memory.UsagePercent -lt $AlertThreshold
        Write-Metric "Memory Usage" "$($metrics.Memory.UsagePercent)%" "" $memGood
        Write-Host "   Total: $($metrics.Memory.Total) GB | Used: $($metrics.Memory.Used) GB | Available: $($metrics.Memory.Available) GB" -ForegroundColor Gray
    }
    
    if ($metrics.CPU) {
        $cpuGood = $metrics.CPU.UsagePercent -lt $AlertThreshold
        Write-Metric "CPU Usage" "$($metrics.CPU.UsagePercent)%" "" $cpuGood
    }
    
    if ($metrics.Disk) {
        $diskGood = $metrics.Disk.UsagePercent -lt $AlertThreshold
        Write-Metric "Disk Usage" "$($metrics.Disk.UsagePercent)%" "" $diskGood
        Write-Host "   Total: $($metrics.Disk.Total) GB | Used: $($metrics.Disk.Used) GB | Free: $($metrics.Disk.Free) GB" -ForegroundColor Gray
    }
    
    # Service Status
    Write-Header "SERVICE STATUS"
    $services = Get-ServiceStatus
    
    foreach ($service in $services.GetEnumerator()) {
        Write-Metric $service.Key $service.Value.Status "" $service.Value.Healthy
    }
    
    # Log Analysis
    Write-Header "LOG ANALYSIS (Last 24 hours)"
    $logAnalysis = Get-LogAnalysis
    Write-Metric "Errors" $logAnalysis.Errors "" ($logAnalysis.Errors -eq 0)
    Write-Metric "Warnings" $logAnalysis.Warnings "" ($logAnalysis.Warnings -lt 5)
    
    if ($logAnalysis.Recent.Count -gt 0) {
        Write-Host "`n📋 Recent Log Activity:" -ForegroundColor Cyan
        foreach ($log in $logAnalysis.Recent) {
            Write-Host "   • $($log.File): $($log.Lines) lines, updated $(($log.LastUpdate).ToString('HH:mm:ss'))" -ForegroundColor Gray
        }
    }
    
    # Email System
    Write-Header "EMAIL SYSTEM"
    $emailStatus = Get-EmailSystemStatus
    Write-Metric "Email System" $emailStatus.Status "" $emailStatus.Healthy
    
    # Overall Health Score
    Write-Header "OVERALL HEALTH"
    $healthScore = 0
    $totalChecks = 0
    
    # Count healthy services
    foreach ($service in $services.Values) {
        $totalChecks++
        if ($service.Healthy) { $healthScore++ }
    }
    
    # Add system metrics to health score
    if ($metrics.Memory -and $metrics.Memory.UsagePercent -lt $AlertThreshold) { $healthScore++; $totalChecks++ }
    if ($metrics.CPU -and $metrics.CPU.UsagePercent -lt $AlertThreshold) { $healthScore++; $totalChecks++ }
    if ($logAnalysis.Errors -eq 0) { $healthScore++; $totalChecks++ }
    
    $healthPercent = if ($totalChecks -gt 0) { [math]::Round(($healthScore / $totalChecks) * 100, 1) } else { 0 }
    $healthGood = $healthPercent -ge 80
    
    $healthText = "($healthScore/$totalChecks passed)"
    Write-Metric "System Health" "$healthPercent`%" $healthText $healthGood
    
    if ($healthPercent -ge 90) {
        Write-Host "`n🎉 System is running excellently!" -ForegroundColor Green
    } elseif ($healthPercent -ge 70) {
        Write-Host "`n⚠️  System has some issues that need attention." -ForegroundColor Yellow
    } else {
        Write-Host "`n🚨 System has critical issues that require immediate attention!" -ForegroundColor Red
    }
    
    # Show recent errors if any
    if ($logAnalysis.ErrorMessages.Count -gt 0) {
        Write-Header "RECENT ERRORS"
        $logAnalysis.ErrorMessages | Select-Object -First 5 | ForEach-Object {
            Write-Host "  • $_" -ForegroundColor Red
        }
    }
}

# Function to run quick health check
function Invoke-HealthCheck {
    Write-Header "KAREN AI SYSTEM HEALTH CHECK"
    
    $services = Get-ServiceStatus
    $metrics = Get-SystemMetrics
    $logAnalysis = Get-LogAnalysis
    
    Write-Host "`n🔍 Service Status:" -ForegroundColor Cyan
    foreach ($service in $services.GetEnumerator()) {
        $status = if ($service.Value.Healthy) { "✅ HEALTHY" } else { "❌ ISSUE" }
        Write-Host "  $($service.Key): $status - $($service.Value.Status)"
    }
    
    Write-Host "`n📊 Resource Usage:" -ForegroundColor Cyan
    if ($metrics.Memory) {
        $memStatus = if ($metrics.Memory.UsagePercent -lt $AlertThreshold) { "✅ OK" } else { "⚠️ HIGH" }
        Write-Host "  Memory: $memStatus - $($metrics.Memory.UsagePercent)% used"
    }
    if ($metrics.CPU) {
        $cpuStatus = if ($metrics.CPU.UsagePercent -lt $AlertThreshold) { "✅ OK" } else { "⚠️ HIGH" }
        Write-Host "  CPU: $cpuStatus - $($metrics.CPU.UsagePercent)% used"
    }
    
    Write-Host "`n📋 Log Summary:" -ForegroundColor Cyan
    Write-Host "  Errors: $($logAnalysis.Errors) | Warnings: $($logAnalysis.Warnings)"
    
    # Overall recommendation
    $issues = @()
    if (-not $services["Redis"].Healthy) { $issues += "Redis not running" }
    if (-not $services["Celery Workers"].Healthy) { $issues += "No Celery workers detected" }
    if ($metrics.Memory -and $metrics.Memory.UsagePercent -gt $AlertThreshold) { $issues += "High memory usage" }
    if ($logAnalysis.Errors -gt 0) { $issues += "$($logAnalysis.Errors) errors in logs" }
    
    Write-Host "`n🎯 Recommendation:" -ForegroundColor Cyan
    if ($issues.Count -eq 0) {
        Write-Host "  ✅ System is healthy and running well!" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️ Issues found that need attention:" -ForegroundColor Yellow
        foreach ($issue in $issues) {
            Write-Host "    • $issue" -ForegroundColor Red
        }
    }
}

# Function to generate detailed report
function New-MonitoringReport {
    $reportPath = "logs/monitoring_report_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
    
    $report = @{
        Timestamp = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
        SystemMetrics = Get-SystemMetrics
        ServiceStatus = Get-ServiceStatus
        LogAnalysis = Get-LogAnalysis
        EmailStatus = Get-EmailSystemStatus
    }
    
    $report | ConvertTo-Json -Depth 10 | Out-File -FilePath $reportPath -Encoding UTF8
    
    Write-Success "Monitoring report saved to: $reportPath"
    
    # Also create a summary
    Write-Header "MONITORING REPORT SUMMARY"
    Write-Info "Report generated at: $($report.Timestamp)"
    Write-Info "Services checked: $($report.ServiceStatus.Count)"
    Write-Info "Log errors found: $($report.LogAnalysis.Errors)"
    Write-Info "Full report saved to: $reportPath"
}

# Function for continuous monitoring
function Start-ContinuousMonitoring {
    param([int]$DurationSeconds)
    
    Write-Header "CONTINUOUS MONITORING MODE"
    Write-Info "Duration: $DurationSeconds seconds"
    Write-Info "Press Ctrl+C to stop early"
    
    $endTime = (Get-Date).AddSeconds($DurationSeconds)
    
    while ((Get-Date) -lt $endTime) {
        Show-Dashboard
        Start-Sleep 5
    }
    
    Write-Success "Monitoring completed"
}

# Function to check for alerts
function Test-SystemAlerts {
    $alerts = @()
    
    $services = Get-ServiceStatus
    $metrics = Get-SystemMetrics
    $logAnalysis = Get-LogAnalysis
    
    # Service alerts
    foreach ($service in $services.GetEnumerator()) {
        if (-not $service.Value.Healthy) {
            $alerts += @{
                Type = "Service"
                Severity = "Critical"
                Message = "$($service.Key) is not healthy: $($service.Value.Status)"
                Timestamp = Get-Date
            }
        }
    }
    
    # Resource alerts
    if ($metrics.Memory -and $metrics.Memory.UsagePercent -gt $AlertThreshold) {
        $alerts += @{
            Type = "Resource"
            Severity = "Warning"
            Message = "High memory usage: $($metrics.Memory.UsagePercent)%"
            Timestamp = Get-Date
        }
    }
    
    if ($metrics.CPU -and $metrics.CPU.UsagePercent -gt $AlertThreshold) {
        $alerts += @{
            Type = "Resource"
            Severity = "Warning"
            Message = "High CPU usage: $($metrics.CPU.UsagePercent)%"
            Timestamp = Get-Date
        }
    }
    
    # Log alerts
    if ($logAnalysis.Errors -gt 0) {
        $alerts += @{
            Type = "Logs"
            Severity = "Warning"
            Message = "$($logAnalysis.Errors) errors found in recent logs"
            Timestamp = Get-Date
        }
    }
    
    if ($alerts.Count -gt 0) {
        Write-Header "SYSTEM ALERTS"
        foreach ($alert in $alerts) {
            $color = switch ($alert.Severity) {
                "Critical" { "Red" }
                "Warning" { "Yellow" }
                default { "White" }
            }
            Write-Host "🚨 [$($alert.Severity)] $($alert.Message)" -ForegroundColor $color
        }
        
        # Save alerts to file
        $alertsPath = "logs/alerts_$(Get-Date -Format 'yyyyMMdd').json"
        $alerts | ConvertTo-Json -Depth 5 | Out-File -FilePath $alertsPath -Encoding UTF8 -Append
    } else {
        Write-Success "No alerts detected - system is healthy"
    }
    
    return $alerts
}

# Main execution
try {
    switch ($Mode) {
        "dashboard" {
            Show-Dashboard
        }
        "check" {
            Invoke-HealthCheck
        }
        "report" {
            New-MonitoringReport
        }
        "watch" {
            Start-ContinuousMonitoring -DurationSeconds $Duration
        }
        "alert" {
            Test-SystemAlerts
        }
        default {
            Write-Error "Unknown mode: $Mode"
            exit 1
        }
    }
} catch {
    Write-Error "Monitoring failed: $($_.Exception.Message)"
    exit 1
} 