# Minimal RTH Test Automation Script
# Usage: Run in PowerShell to start frontend with RTH, check readiness, run smoke test, and stop frontend.

# --- CONFIGURATION ---
$RTH = "python C:\Users\Man\CursorAgentUtils\robust_terminal_handler.py"
$STATUS_DIR = "C:\Users\Man\rth_status_files"
$FRONTEND_STATUS = "$STATUS_DIR\frontend_status.json"
$FRONTEND_PORT = 8080
$FRONTEND_URL = "http://localhost:$FRONTEND_PORT"
$FRONTEND_SMOKE_TEST = "node tests/frontend_smoke_test.js"
$WAIT_TIMEOUT_SEC = 60

# --- START FRONTEND WITH RTH ---
Write-Host "[RTH] Starting frontend..."
Start-Process -NoNewWindow -PassThru -FilePath "python" -ArgumentList "C:\Users\Man\CursorAgentUtils\robust_terminal_handler.py --status-file-path $FRONTEND_STATUS --command 'npm start'" | Out-Null

# --- WAIT FOR FRONTEND TO BE READY ---
Write-Host "[RTH] Waiting for frontend at $FRONTEND_URL..."
$ready = $false
$elapsed = 0
while (-not $ready -and $elapsed -lt $WAIT_TIMEOUT_SEC) {
    try {
        $resp = Invoke-WebRequest -Uri $FRONTEND_URL -UseBasicParsing -TimeoutSec 3
        if ($resp.StatusCode -eq 200) { $ready = $true }
    } catch { }
    if (-not $ready) { Start-Sleep -Seconds 2; $elapsed += 2 }
}
if (-not $ready) {
    Write-Host "[RTH] ERROR: Frontend did not become ready in $WAIT_TIMEOUT_SEC seconds." -ForegroundColor Red
    exit 1
}
Write-Host "[RTH] Frontend is up. Running smoke test..."

# --- RUN FRONTEND SMOKE TEST ---
Invoke-Expression $FRONTEND_SMOKE_TEST
if ($LASTEXITCODE -ne 0) {
    Write-Host "[RTH] Frontend smoke test failed!" -ForegroundColor Red
    exit 2
}
Write-Host "[RTH] Frontend smoke test passed."

# --- STOP FRONTEND (by port) ---
Write-Host "[RTH] Stopping frontend (port $FRONTEND_PORT)..."
$frontendPid = (Get-NetTCPConnection -LocalPort $FRONTEND_PORT -State Listen | Select-Object -First 1).OwningProcess
if ($frontendPid) {
    Stop-Process -Id $frontendPid -Force
    Write-Host "[RTH] Stopped process $frontendPid."
} else {
    Write-Host "[RTH] No process found on port $FRONTEND_PORT."
}

Write-Host "[RTH] Done. See $STATUS_DIR for logs and status files." 