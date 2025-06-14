# Start autonomous agent coordinator
Write-Host "🤖 Starting Autonomous Agent Coordinator" -ForegroundColor Green

# Start the Python autonomous runner
$env:PYTHONPATH = "."
Start-Process python -ArgumentList "src/autonomous_agent_runner.py" -NoNewWindow

Write-Host "✅ Autonomous coordinator started" -ForegroundColor Green
Write-Host "📋 Agents will now automatically pick up tasks from the queue" -ForegroundColor Yellow