# 🚀 Karen AI Shell Scripts Guide

This guide covers all operational shell scripts for the Karen AI system, providing comprehensive automation for startup, monitoring, backup, and shutdown operations.

## 📁 Scripts Overview

| Script | Purpose | Platform | Usage |
|--------|---------|----------|-------|
| `startup.ps1` | System startup and initialization | Windows/PowerShell | Production & Development |
| `monitor.ps1` | Real-time monitoring and health checks | Windows/PowerShell | Operations & Debugging |
| `backup.ps1` | Data backup and archival | Windows/PowerShell | Data Protection |
| `shutdown.ps1` | Graceful system shutdown | Windows/PowerShell | Operations |

---

## 🚀 Startup Script (`scripts/startup.ps1`)

### Purpose
Comprehensive system initialization that starts all Karen AI services with proper dependency checking and health verification.

### Features
- ✅ Environment validation (Python, virtual environment, Redis)
- ✅ Automatic dependency installation
- ✅ Service startup (Celery workers, beat scheduler, main app)
- ✅ Health checks and verification
- ✅ Configuration setup and validation
- ✅ Error handling and rollback

### Usage Examples

```powershell
# Basic development startup
.\scripts\startup.ps1

# Production startup with specific environment
.\scripts\startup.ps1 -Environment production

# Skip health checks for faster startup
.\scripts\startup.ps1 -SkipHealthCheck

# Startup with full logging
.\scripts\startup.ps1 -Environment staging -Verbose
```

### Parameters
- **Environment**: `development` | `staging` | `production` (default: `development`)
- **SkipHealthCheck**: Skip initial system health verification

### What It Does
1. **Environment Validation**
   - Checks Python installation and version
   - Validates virtual environment
   - Tests Redis connectivity
   - Verifies system requirements

2. **Configuration Setup**
   - Creates `.env` file if missing
   - Sets environment variables
   - Validates credentials

3. **Service Startup**
   - Starts Celery worker processes
   - Launches Celery beat scheduler
   - Starts main Karen AI application

4. **Health Verification**
   - Tests all service connections
   - Validates system components
   - Reports startup status

### Output Locations
- Startup logs: `logs/last_startup.json`
- Process information: Console output
- Service status: Real-time health checks

---

## 📊 Monitoring Script (`scripts/monitor.ps1`)

### Purpose
Real-time system monitoring with dashboard, alerts, and comprehensive health reporting.

### Features
- 📊 Real-time dashboard with live metrics
- 🔍 Health checks and service status
- 📋 Log analysis and error detection
- 🚨 Alert system with thresholds
- 📄 Detailed monitoring reports

### Usage Examples

```powershell
# Real-time dashboard (refreshes every 5 seconds)
.\scripts\monitor.ps1 -Mode dashboard

# Quick health check
.\scripts\monitor.ps1 -Mode check

# Generate detailed report
.\scripts\monitor.ps1 -Mode report

# Continuous monitoring for 5 minutes
.\scripts\monitor.ps1 -Mode watch -Duration 300

# Check for system alerts
.\scripts\monitor.ps1 -Mode alert -AlertThreshold 85
```

### Parameters
- **Mode**: `dashboard` | `check` | `report` | `watch` | `alert`
- **Duration**: Watch mode duration in seconds (default: 60)
- **AlertThreshold**: Resource usage threshold for alerts (default: 80%)

### Monitoring Modes

#### 1. Dashboard Mode
- Live system metrics (CPU, Memory, Disk)
- Service status (Redis, Celery, Python processes)
- Log analysis summary
- Overall health score
- Recent error display

#### 2. Check Mode
- Quick health verification
- Service status summary
- Resource usage overview
- Recommendations for issues

#### 3. Report Mode
- Comprehensive system report
- Detailed metrics collection
- Historical data analysis
- Saved to timestamped JSON file

#### 4. Watch Mode
- Continuous dashboard updates
- Specified duration monitoring
- Press Ctrl+C to stop early

#### 5. Alert Mode
- Check for system alerts
- Threshold-based warnings
- Save alerts to daily log file

### Metrics Tracked
- **System Resources**: Memory, CPU, Disk usage
- **Services**: Redis, Python processes, Celery workers/beat
- **Logs**: Error count, warning count, recent activity
- **Email System**: Configuration and connectivity

### Output Locations
- Monitoring reports: `logs/monitoring_report_YYYYMMDD_HHMMSS.json`
- Alert logs: `logs/alerts_YYYYMMDD.json`
- Real-time: Console dashboard

---

## 💾 Backup Script (`scripts/backup.ps1`)

### Purpose
Comprehensive data protection with multiple backup types, compression, and retention management.

### Features
- 🗂️ Multiple backup types (full, incremental, config, logs, data)
- 🗜️ Optional compression with size reporting
- 🔄 Automatic retention management
- 📋 Backup manifests and verification
- 📊 Size tracking and optimization

### Usage Examples

```powershell
# Quick incremental backup (default)
.\scripts\backup.ps1

# Full system backup
.\scripts\backup.ps1 -BackupType full

# Configuration-only backup
.\scripts\backup.ps1 -BackupType config

# Compressed backup to custom location
.\scripts\backup.ps1 -BackupType full -Destination "D:\Backups" -Compress

# Logs backup with extended retention
.\scripts\backup.ps1 -BackupType logs -RetentionDays 60
```

### Parameters
- **BackupType**: `full` | `incremental` | `config` | `logs` | `data`
- **Destination**: Backup directory path (default: `backups`)
- **RetentionDays**: Days to keep old backups (default: 30)
- **Compress**: Create compressed ZIP archive

### Backup Types

#### 1. Full Backup
**Includes**: Configuration, logs, data, source code, scripts
**Use Case**: Complete system snapshot, major version changes
**Size**: Largest, most comprehensive

#### 2. Incremental Backup (Default)
**Includes**: Configuration files, recent logs
**Use Case**: Daily/regular backups, quick protection
**Size**: Smallest, fastest

#### 3. Configuration Backup
**Includes**: .env, requirements.txt, config.py, credentials
**Use Case**: Before configuration changes
**Size**: Very small

#### 4. Logs Backup
**Includes**: All log files and monitoring data
**Use Case**: Log archival, troubleshooting
**Size**: Variable based on activity

#### 5. Data Backup
**Includes**: Application data, databases, cache
**Use Case**: Data protection, database snapshots
**Size**: Medium to large

### What Gets Backed Up

#### Configuration Files
- `.env` - Environment variables
- `src/requirements.txt` - Python dependencies
- `src/config.py` - Application configuration
- `autonomous_state.json` - System state
- Credential files (encrypted recommended)

#### Log Files
- `logs/` directory (all log files)
- Monitoring reports
- System status logs
- Error logs and alerts

#### Data Files
- `data/` - Application data
- `temp/` - Temporary files
- `cache/` - Cache files
- `*.db` - Database files

#### Source Code (Full backup only)
- `src/` - Source code
- `scripts/` - Operational scripts

### Output Structure
```
backup_[type]_[timestamp]/
├── config/
│   ├── credentials/
│   └── [config files]
├── logs/
├── data/
├── source/ (full backup only)
└── backup_manifest.json
```

### Output Locations
- Backup directory: `backups/backup_[type]_YYYYMMDD_HHMMSS/`
- Compressed: `backups/backup_[type]_YYYYMMDD_HHMMSS.zip`
- Backup log: `logs/backup_log.json`

---

## 🛑 Shutdown Script (`scripts/shutdown.ps1`)

### Purpose
Graceful system shutdown with optional backup and cleanup.

### Features
- 🔄 Graceful process termination
- 💾 Optional pre-shutdown backup
- 🧹 Cleanup of temporary files and PIDs
- ⚡ Force termination option
- 📝 Shutdown logging

### Usage Examples

```powershell
# Normal graceful shutdown
.\scripts\shutdown.ps1

# Backup before shutdown
.\scripts\shutdown.ps1 -BackupFirst

# Force immediate shutdown
.\scripts\shutdown.ps1 -Force

# Backup + force shutdown with custom timeout
.\scripts\shutdown.ps1 -BackupFirst -Force -TimeoutSeconds 60
```

### Parameters
- **Force**: Force terminate processes immediately
- **BackupFirst**: Create backup before shutdown
- **TimeoutSeconds**: Wait time for graceful termination (default: 30)

### Shutdown Process
1. **Optional Backup** (if -BackupFirst)
   - Creates incremental backup
   - Ensures data protection

2. **Process Termination**
   - Graceful shutdown of main application
   - Stop Celery workers and beat scheduler
   - Terminate Python processes

3. **Cleanup**
   - Remove PID files
   - Clean temporary files
   - Clear cache if needed

4. **Verification**
   - Confirm all processes stopped
   - Log shutdown completion

### Output Locations
- Shutdown log: `logs/shutdown_log.json`
- Failure log: `logs/shutdown_failures.json`

---

## 🔧 Advanced Usage

### Script Chaining
```powershell
# Complete restart with backup
.\scripts\shutdown.ps1 -BackupFirst -Force
.\scripts\startup.ps1 -Environment production

# Monitoring after startup
.\scripts\startup.ps1
Start-Sleep 10
.\scripts\monitor.ps1 -Mode check
```

### Automation Examples
```powershell
# Daily backup (scheduled task)
.\scripts\backup.ps1 -BackupType incremental -Compress

# Weekly full backup
.\scripts\backup.ps1 -BackupType full -Destination "\\server\backups" -Compress

# Health monitoring loop
while ($true) {
    .\scripts\monitor.ps1 -Mode alert -AlertThreshold 85
    Start-Sleep 300  # Check every 5 minutes
}
```

### Environment-Specific Configurations

#### Development
```powershell
.\scripts\startup.ps1 -Environment development -SkipHealthCheck
```

#### Staging
```powershell
.\scripts\startup.ps1 -Environment staging
.\scripts\monitor.ps1 -Mode watch -Duration 600
```

#### Production
```powershell
.\scripts\startup.ps1 -Environment production
.\scripts\backup.ps1 -BackupType full -Compress -Destination "\\backup-server\karen"
```

---

## 📋 Script Dependencies

### Required Software
- **PowerShell 5.1+** (Windows PowerShell or PowerShell Core)
- **Python 3.8+** with pip
- **Redis Server** (local or remote)
- **Git** (for source control)

### Python Packages
- All packages in `src/requirements.txt`
- Virtual environment recommended

### System Requirements
- **Memory**: Minimum 4GB RAM (8GB+ recommended)
- **Disk**: 10GB+ free space for backups
- **Network**: Internet access for dependencies

---

## 🚨 Troubleshooting

### Common Issues

#### Startup Failures
```powershell
# Check Python installation
python --version

# Verify virtual environment
ls .venv

# Test Redis connectivity
Test-NetConnection localhost -Port 6379
```

#### Permission Errors
```powershell
# Run as Administrator
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned

# Fix script permissions
Unblock-File .\scripts\*.ps1
```

#### Process Issues
```powershell
# Check running processes
Get-Process python, celery

# Force cleanup
.\scripts\shutdown.ps1 -Force

# Manual cleanup
Get-Process python | Stop-Process -Force
Remove-Item *.pid
```

### Log Locations
- **Startup**: `logs/last_startup.json`
- **Monitoring**: `logs/monitoring_report_*.json`
- **Backup**: `logs/backup_log.json`
- **Shutdown**: `logs/shutdown_log.json`
- **Errors**: `logs/*_failures.json`

### Health Check Commands
```powershell
# Quick system status
python system_status_check.py

# Script-based monitoring
.\scripts\monitor.ps1 -Mode check

# Manual service checks
Test-NetConnection localhost -Port 6379  # Redis
Get-Process python, celery               # Services
```

---

## 🔒 Security Considerations

### Credential Files
- Store credentials in `credentials/` directory
- Add to `.gitignore`
- Consider encryption for production
- Regular rotation of tokens

### Backup Security
- Encrypt backup archives for production
- Secure backup destination access
- Regular backup testing
- Offsite backup storage

### Script Execution
- Use signed scripts in production
- Validate script integrity
- Restrict execution permissions
- Audit script modifications

---

## 📈 Performance Optimization

### Startup Optimization
- Use `-SkipHealthCheck` for development
- Pre-warm virtual environment
- Optimize Redis configuration
- Parallel service startup

### Monitoring Optimization
- Adjust alert thresholds
- Use targeted monitoring modes
- Archive old monitoring reports
- Optimize log rotation

### Backup Optimization
- Use incremental backups daily
- Compress large backups
- Implement backup verification
- Regular cleanup of old backups

---

## 🔄 Maintenance

### Regular Tasks
- **Daily**: Run incremental backup
- **Weekly**: Full system backup, log cleanup
- **Monthly**: Update dependencies, security review
- **Quarterly**: Full system health audit

### Script Updates
- Keep scripts in version control
- Test script changes in staging
- Document script modifications
- Backup script configurations

### System Hygiene
```powershell
# Clean old logs (monthly)
Get-ChildItem logs -File | Where-Object { $_.CreationTime -lt (Get-Date).AddDays(-30) } | Remove-Item

# Clean old backups (automatic via retention)
.\scripts\backup.ps1 -BackupType config  # Triggers cleanup

# Update system status
python system_status_check.py > logs/monthly_status.txt
```

---

## 📞 Support

For script issues or improvements:
1. Check logs in `logs/` directory
2. Run monitoring check: `.\scripts\monitor.ps1 -Mode check`
3. Review this documentation
4. Create issue with full error output

**Happy Automation!** 🎉 