#!/usr/bin/env pwsh
# Simple Karen AI System Backup

param(
    [string]$BackupType = "config",
    [string]$Destination = "backups"
)

function Write-Success { param($Message) Write-Host "[OK] $Message" -ForegroundColor Green }
function Write-Info { param($Message) Write-Host "[INFO] $Message" -ForegroundColor Cyan }
function Write-Header { param($Message) Write-Host "`n=== $Message ===" -ForegroundColor Magenta }

Write-Header "KAREN AI SYSTEM BACKUP"
Write-Info "Backup Type: $BackupType"
Write-Info "Destination: $Destination"

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupName = "backup_${BackupType}_${timestamp}"
$backupPath = Join-Path $Destination $backupName

# Create backup directory
if (-not (Test-Path $Destination)) {
    New-Item -Path $Destination -ItemType Directory -Force | Out-Null
    Write-Info "Created destination directory: $Destination"
}

New-Item -Path $backupPath -ItemType Directory -Force | Out-Null
Write-Info "Created backup directory: $backupPath"

# Backup configuration files
Write-Info "Backing up configuration files..."
$configPath = Join-Path $backupPath "config"
New-Item -Path $configPath -ItemType Directory -Force | Out-Null

$configFiles = @(".env", "autonomous_state.json")
$backupCount = 0

foreach ($file in $configFiles) {
    if (Test-Path $file) {
        Copy-Item -Path $file -Destination $configPath -Force
        Write-Success "Backed up: $file"
        $backupCount++
    } else {
        Write-Info "File not found: $file"
    }
}

# Backup Python requirements
if (Test-Path "src/requirements.txt") {
    Copy-Item -Path "src/requirements.txt" -Destination $configPath -Force
    Write-Success "Backed up: src/requirements.txt"
    $backupCount++
}

# Backup credentials if they exist
$credFiles = @("credentials.json", "gmail_token.json", "monitored_email_token.json")
$credPath = Join-Path $configPath "credentials"

$credCount = 0
foreach ($file in $credFiles) {
    if (Test-Path $file) {
        if ($credCount -eq 0) {
            New-Item -Path $credPath -ItemType Directory -Force | Out-Null
        }
        Copy-Item -Path $file -Destination $credPath -Force
        Write-Success "Backed up credential: $file"
        $credCount++
        $backupCount++
    }
}

# For full backup, include logs and source
if ($BackupType -eq "full") {
    # Backup logs
    if (Test-Path "logs") {
        Write-Info "Backing up logs..."
        Copy-Item -Path "logs" -Destination $backupPath -Recurse -Force
        Write-Success "Logs backed up"
        $backupCount++
    }
    
    # Backup source code
    if (Test-Path "src") {
        Write-Info "Backing up source code..."
        Copy-Item -Path "src" -Destination $backupPath -Recurse -Force
        Write-Success "Source code backed up"
        $backupCount++
    }
    
    # Backup scripts
    if (Test-Path "scripts") {
        Write-Info "Backing up scripts..."
        Copy-Item -Path "scripts" -Destination $backupPath -Recurse -Force
        Write-Success "Scripts backed up"
        $backupCount++
    }
}

# Create backup manifest
$manifest = @{
    BackupType = $BackupType
    Timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    BackupPath = $backupPath
    FilesBackedUp = $backupCount
    Computer = $env:COMPUTERNAME
    User = $env:USERNAME
}

$manifestPath = Join-Path $backupPath "backup_manifest.json"
$manifest | ConvertTo-Json | Out-File -FilePath $manifestPath -Encoding UTF8
Write-Success "Created backup manifest: backup_manifest.json"

# Calculate backup size
$backupSize = 0
Get-ChildItem $backupPath -Recurse -File | ForEach-Object { $backupSize += $_.Length }
$backupSizeMB = [math]::Round($backupSize / 1MB, 2)

Write-Header "BACKUP COMPLETED"
Write-Success "Backup location: $backupPath"
Write-Info "Files backed up: $backupCount"
Write-Info "Backup size: $backupSizeMB MB"
Write-Info "Manifest: $manifestPath"

# Log the backup
if (-not (Test-Path "logs")) {
    New-Item -Path "logs" -ItemType Directory -Force | Out-Null
}

$logEntry = @{
    Timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    Type = $BackupType
    Path = $backupPath
    Files = $backupCount
    SizeMB = $backupSizeMB
    Success = $true
}

$logEntry | ConvertTo-Json | Out-File -FilePath "logs/backup_log.json" -Append -Encoding UTF8
Write-Info "Backup logged to: logs/backup_log.json" 