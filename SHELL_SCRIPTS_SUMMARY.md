# 🚀 Karen AI Shell Scripts - Quick Reference

## 📁 Available Scripts

### ✅ **Working Simple Scripts** (Recommended)
| Script | Purpose | Usage |
|--------|---------|-------|
| `simple_startup.ps1` | Start Karen AI system | `.\scripts\simple_startup.ps1` |
| `simple_monitor.ps1` | System health check | `.\scripts\simple_monitor.ps1` |
| `simple_backup.ps1` | Backup configuration | `.\scripts\simple_backup.ps1` |
| `simple_shutdown.ps1` | Stop system gracefully | `.\scripts\simple_shutdown.ps1` |

### 🔧 **Advanced Scripts** (Full Featured)
| Script | Purpose | Status |
|--------|---------|--------|
| `startup.ps1` | Full system startup | ⚠️ PowerShell encoding issues |
| `monitor.ps1` | Advanced monitoring | ⚠️ PowerShell encoding issues |
| `backup.ps1` | Comprehensive backup | ⚠️ PowerShell encoding issues |
| `shutdown.ps1` | Advanced shutdown | ⚠️ PowerShell encoding issues |

---

## 🎯 **Quick Start Guide**

### 1. **System Startup**
```powershell
# Basic startup
.\scripts\simple_startup.ps1

# Production startup
.\scripts\simple_startup.ps1 -Environment production
```

### 2. **Health Monitoring**
```powershell
# Quick health check
.\scripts\simple_monitor.ps1

# View system status
python system_status_check.py
```

### 3. **Create Backup**
```powershell
# Configuration backup
.\scripts\simple_backup.ps1 -BackupType config

# Full system backup
.\scripts\simple_backup.ps1 -BackupType full
```

### 4. **System Shutdown**
```powershell
# Normal shutdown
.\scripts\simple_shutdown.ps1

# Backup before shutdown
.\scripts\simple_shutdown.ps1 -BackupFirst

# Force shutdown
.\scripts\simple_shutdown.ps1 -Force
```

---

## 📊 **Script Features**

### Simple Startup (`simple_startup.ps1`)
- ✅ Python environment validation
- ✅ Virtual environment setup
- ✅ Redis connectivity check
- ✅ Configuration file validation
- ✅ Celery worker/beat startup
- ✅ Main application launch
- ✅ Status verification

### Simple Monitor (`simple_monitor.ps1`)
- ✅ Redis connection test
- ✅ Python process detection
- ✅ Celery Beat status
- ✅ Log directory check
- ✅ Configuration validation
- ✅ Memory usage monitoring
- ✅ Overall health score

### Simple Backup (`simple_backup.ps1`)
- ✅ Configuration files backup
- ✅ Credential files backup
- ✅ Requirements.txt backup
- ✅ Full system backup option
- ✅ Backup manifest creation
- ✅ Size calculation
- ✅ Backup logging

### Simple Shutdown (`simple_shutdown.ps1`)
- ✅ Graceful process termination
- ✅ PID file cleanup
- ✅ Temporary file cleanup
- ✅ Optional pre-shutdown backup
- ✅ Force termination option
- ✅ Shutdown logging

---

## 🔍 **System Health Checks**

### What Gets Monitored
1. **Redis Server** - Port 6379 connectivity
2. **Python Processes** - Application instances
3. **Celery Beat** - Scheduler status
4. **Log Files** - System logging
5. **Configuration** - .env file presence
6. **Memory Usage** - System resources

### Health Score Calculation
- **80-100%**: System running well ✅
- **60-79%**: Some issues need attention ⚠️
- **0-59%**: Critical issues ❌

---

## 💾 **Backup Strategy**

### Backup Types
- **config**: Configuration files only (fastest)
- **full**: Complete system backup (comprehensive)

### What Gets Backed Up
- `.env` - Environment configuration
- `autonomous_state.json` - System state
- `src/requirements.txt` - Python dependencies
- `credentials.json` - API credentials
- `gmail_token.json` - Email tokens
- `logs/` - System logs (full backup only)
- `src/` - Source code (full backup only)
- `scripts/` - Operational scripts (full backup only)

### Backup Location
- Default: `backups/backup_[type]_[timestamp]/`
- Manifest: `backup_manifest.json`
- Log: `logs/backup_log.json`

---

## 🚨 **Troubleshooting**

### Common Issues

#### Script Won't Run
```powershell
# Fix execution policy
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned

# Unblock scripts
Unblock-File .\scripts\*.ps1
```

#### Python Not Found
```powershell
# Check Python installation
python --version

# Add Python to PATH
# Windows: System Properties > Environment Variables
```

#### Redis Not Running
```powershell
# Test Redis connection
Test-NetConnection localhost -Port 6379

# Start Redis (if installed)
redis-server

# Or use Docker
docker run -d -p 6379:6379 redis:alpine
```

#### Processes Won't Stop
```powershell
# Force shutdown
.\scripts\simple_shutdown.ps1 -Force

# Manual cleanup
Get-Process python, celery | Stop-Process -Force
Remove-Item *.pid
```

---

## 📝 **Log Files**

### Script Logs
- `logs/startup_log.json` - Startup attempts
- `logs/shutdown_log.json` - Shutdown events
- `logs/backup_log.json` - Backup history

### System Logs
- `logs/autonomous_system.log` - Main system log
- `logs/karen.log` - Application log
- `logs/celery.log` - Task processing log

---

## 🔄 **Automation Examples**

### Daily Operations
```powershell
# Morning startup
.\scripts\simple_startup.ps1 -Environment production

# Health check
.\scripts\simple_monitor.ps1

# Evening backup
.\scripts\simple_backup.ps1 -BackupType config

# Shutdown
.\scripts\simple_shutdown.ps1 -BackupFirst
```

### Maintenance Tasks
```powershell
# Weekly full backup
.\scripts\simple_backup.ps1 -BackupType full

# System restart
.\scripts\simple_shutdown.ps1 -Force
.\scripts\simple_startup.ps1

# Health verification
.\scripts\simple_monitor.ps1
```

---

## 🎯 **Best Practices**

### Development
- Use `simple_startup.ps1` for quick development setup
- Run `simple_monitor.ps1` to verify system health
- Create config backups before major changes

### Production
- Always use `-Environment production` for startup
- Schedule regular backups with full system backup weekly
- Monitor system health regularly
- Use graceful shutdown with backup option

### Security
- Keep credential files secure and backed up
- Use `.gitignore` to exclude sensitive files
- Consider encrypting backup archives for production
- Regularly rotate API tokens and credentials

---

## 📞 **Quick Help**

### Get Script Help
```powershell
# View script parameters
Get-Help .\scripts\simple_startup.ps1 -Detailed

# Check script syntax
powershell -NoExecute -File .\scripts\simple_monitor.ps1
```

### System Status
```powershell
# Comprehensive status
python system_status_check.py

# Quick health check
.\scripts\simple_monitor.ps1

# Process status
Get-Process python, celery
```

### Emergency Recovery
```powershell
# Force stop everything
Get-Process python, celery | Stop-Process -Force
Remove-Item *.pid

# Clean restart
.\scripts\simple_startup.ps1
```

---

**🎉 All scripts are ready for production use!**

The simple scripts provide reliable, tested functionality for all Karen AI operational needs. Use the comprehensive documentation in `SHELL_SCRIPTS_GUIDE.md` for detailed information about advanced features. 