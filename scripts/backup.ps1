#!/usr/bin/env pwsh
# Karen AI System Backup Script

param(
    [string]$BackupType = "incremental",
    [string]$Destination = "backups",
    [int]$RetentionDays = 30,
    [switch]$Compress
)

$ErrorActionPreference = "Stop"
$StartTime = Get-Date

function Write-Success { param($Message) Write-Host "✅ $Message" -ForegroundColor Green }
function Write-Info { param($Message) Write-Host "ℹ️  $Message" -ForegroundColor Cyan }
function Write-Header { param($Message) Write-Host "`n💾 $Message" -ForegroundColor Magenta }

Write-Header "KAREN AI SYSTEM BACKUP"
Write-Info "Starting $BackupType backup at $($StartTime.ToString('yyyy-MM-dd HH:mm:ss'))"

# Create backup directory
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupName = "backup_${BackupType}_${timestamp}"
$backupPath = Join-Path $Destination $backupName

if (-not (Test-Path $Destination)) {
    New-Item -Path $Destination -ItemType Directory -Force | Out-Null
}
New-Item -Path $backupPath -ItemType Directory -Force | Out-Null

# Backup configuration files
Write-Info "Backing up configuration..."
$configPath = Join-Path $backupPath "config"
New-Item -Path $configPath -ItemType Directory -Force | Out-Null

$configFiles = @(".env", "src/requirements.txt", "src/config.py", "autonomous_state.json")
foreach ($file in $configFiles) {
    if (Test-Path $file) {
        Copy-Item -Path $file -Destination $configPath -Force
        Write-Success "Backed up: $file"
    }
}

# Backup credentials (if they exist)
$credFiles = @("credentials.json", "gmail_token.json", "monitored_email_token.json")
$credPath = Join-Path $configPath "credentials"
New-Item -Path $credPath -ItemType Directory -Force | Out-Null

foreach ($file in $credFiles) {
    if (Test-Path $file) {
        Copy-Item -Path $file -Destination $credPath -Force
        Write-Success "Credential backed up: $file"
    }
}

# Backup logs
if (Test-Path "logs") {
    Write-Info "Backing up logs..."
    Copy-Item -Path "logs" -Destination $backupPath -Recurse -Force
    Write-Success "Logs backed up"
}

# For full backup, include additional items
if ($BackupType -eq "full") {
    # Backup source code
    if (Test-Path "src") {
        Write-Info "Backing up source code..."
        Copy-Item -Path "src" -Destination $backupPath -Recurse -Force
        Write-Success "Source code backed up"
    }
    
    # Backup scripts
    if (Test-Path "scripts") {
        Copy-Item -Path "scripts" -Destination $backupPath -Recurse -Force
        Write-Success "Scripts backed up"
    }
    
    # Backup data directories
    $dataLocations = @("data", "temp", "cache")
    foreach ($location in $dataLocations) {
        if (Test-Path $location) {
            Copy-Item -Path $location -Destination $backupPath -Recurse -Force
            Write-Success "Backed up: $location"
        }
    }
}

# Create backup manifest
$manifest = @{
    BackupType = $BackupType
    Timestamp = $StartTime.ToString('yyyy-MM-dd HH:mm:ss')
    BackupPath = $backupPath
    Computer = $env:COMPUTERNAME
}
$manifest | ConvertTo-Json | Out-File -FilePath (Join-Path $backupPath "backup_manifest.json")

# Compress if requested
if ($Compress) {
    Write-Info "Creating compressed archive..."
    $archivePath = "$backupPath.zip"
    Compress-Archive -Path "$backupPath\*" -DestinationPath $archivePath -Force
    Remove-Item -Path $backupPath -Recurse -Force
    $backupPath = $archivePath
    Write-Success "Archive created: $archivePath"
}

# Clean old backups
$cutoffDate = (Get-Date).AddDays(-$RetentionDays)
Get-ChildItem $Destination | Where-Object { $_.CreationTime -lt $cutoffDate } | ForEach-Object {
    Write-Info "Removing old backup: $($_.Name)"
    Remove-Item -Path $_.FullName -Recurse -Force
}

# Summary
$duration = (Get-Date) - $StartTime
Write-Header "BACKUP COMPLETED"
Write-Success "Location: $backupPath"
Write-Info "Duration: $([math]::Round($duration.TotalMinutes, 2)) minutes"

# Log the backup
if (-not (Test-Path "logs")) { New-Item -Path "logs" -ItemType Directory -Force | Out-Null }
@{
    Timestamp = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
    Type = $BackupType
    Path = $backupPath
    Success = $true
} | ConvertTo-Json | Out-File -FilePath "logs/backup_log.json" -Append 