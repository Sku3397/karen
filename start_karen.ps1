# KAREN AI Startup Script
Write-Host " Starting KAREN AI System" -ForegroundColor Green
Write-Host "===========================" -ForegroundColor Green

# Option 1: Python-based runner (recommended)
Write-Host "`nStarting autonomous task runner..." -ForegroundColor Yellow
Start-Process python -ArgumentList "src/autonomous_agent_runner.py" -NoNewWindow

Write-Host "`n System started!" -ForegroundColor Green
Write-Host "`nTo monitor progress, run:" -ForegroundColor Cyan
Write-Host "  python monitor.py" -ForegroundColor White
