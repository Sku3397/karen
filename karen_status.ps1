# Safe Karen AI Monitor
Clear-Host
Write-Host " KAREN AI STATUS REPORT" -ForegroundColor Cyan
Write-Host "=========================" -ForegroundColor Cyan
Write-Host ""

# Completed tasks
$completed = (Get-ChildItem agent_progress/completed_* -ErrorAction SilentlyContinue | Measure-Object).Count
Write-Host " Completed Tasks: $completed" -ForegroundColor Green

# Recent completions
$recent = Get-ChildItem agent_progress/completed_* -ErrorAction SilentlyContinue | 
           Sort-Object LastWriteTime -Descending | 
           Select-Object -First 5
Write-Host "
 Recent Completions:" -ForegroundColor Yellow
$recent | ForEach-Object { Write-Host "   $($_.Name)" -ForegroundColor Gray }

# Check for pending work
$pending = Get-ChildItem agent_instructions/*.md -ErrorAction SilentlyContinue | 
            Where-Object { $_.Name -notlike '*.processing' }
Write-Host "
 Pending in agent_instructions: $($pending.Count)" -ForegroundColor Yellow

# WSL process check
Write-Host "
 WSL Process Check:" -ForegroundColor Yellow
wsl ps aux | grep wrapper | head -5

# Last activity
Write-Host "
 Last 3 Activities:" -ForegroundColor Yellow
Get-Content agent_activities.jsonl -Tail 3 | ForEach-Object {
    $activity = $_ | ConvertFrom-Json
    Write-Host "   $($activity.timestamp) - $($activity.agent): $($activity.activity_type)" -ForegroundColor Gray
}
