# Simple Working Docker Claude Code Agent System
# Direct command approach to avoid PowerShell multiline issues

param(
    [string]$Action = "help",
    [string]$AgentName = "",
    [switch]$AutoName
)

# Track terminal windows
$script:TerminalWindows = @{}

function Get-NextAgentName {
    param([string]$BaseName)
    
    # Get existing agents with this base name
    $existingAgents = docker ps -a --filter "name=claude-agent-$BaseName" --format "{{.Names}}" 2>$null
    
    if (-not $existingAgents) {
        return "$BaseName-1"
    }
    
    # Find the highest number
    $maxNum = 0
    $existingAgents | ForEach-Object {
        if ($_ -match "claude-agent-$BaseName-(\d+)$") {
            $num = [int]$matches[1]
            if ($num -gt $maxNum) {
                $maxNum = $num
            }
        }
    }
    
    return "$BaseName-$($maxNum + 1)"
}

function Start-OpusAgent {
    $name = if ($AgentName) { $AgentName } elseif ($AutoName) { Get-NextAgentName "opus" } else { "opus-1" }
    
    Write-Host "Starting Claude Opus Agent '$name' (16GB memory, 12GB heap)..." -ForegroundColor Magenta
    Start-SimpleAgent -Name $name -Memory "16g" -CPUs 4 -HeapSize "12288"
}

function Start-SonnetAgent {
    $name = if ($AgentName) { $AgentName } elseif ($AutoName) { Get-NextAgentName "sonnet" } else { "sonnet-1" }
    
    Write-Host "Starting Claude Sonnet Agent '$name' (8GB memory, 6GB heap)..." -ForegroundColor Cyan
    Start-SimpleAgent -Name $name -Memory "8g" -CPUs 2 -HeapSize "6144"
}

function Start-SimpleAgent {
    param([string]$Name, [string]$Memory, [int]$CPUs, [string]$HeapSize)
    
    # Check if container already exists
    $existing = docker ps -a --filter "name=claude-agent-$Name" --format "{{.Names}}" 2>$null
    if ($existing) {
        Write-Host "[X] Agent $Name already exists!" -ForegroundColor Red
        Write-Host "Options:" -ForegroundColor Yellow
        Write-Host "  1. Use -AutoName flag to auto-generate a unique name" -ForegroundColor Yellow
        Write-Host "  2. Use -AgentName to specify a custom name" -ForegroundColor Yellow
        Write-Host "  3. Stop the existing agent: .\docker-claude-simple.ps1 -Action stop" -ForegroundColor Yellow
        return
    }
    
    $port = 8000 + ($Name.GetHashCode() % 1000)
    Write-Host "Starting agent $Name on port $port..." -ForegroundColor Yellow
    
    # Single command approach
    $cmd = "apt-get update; apt-get install -y curl; curl -fsSL https://deb.nodesource.com/setup_18.x | bash -; apt-get install -y nodejs; npm install -g @anthropic-ai/claude-code; echo '=== Claude Code Ready ==='; claude --version; echo 'Agent ready on port $port'; tail -f /dev/null"
    
    $containerId = docker run -d `
        --name "claude-agent-$Name" `
        --memory="$Memory" `
        --cpus="$CPUs" `
        -v "C:\Users\Man\ultra\projects\karen:/workspace" `
        -w /workspace `
        -p "${port}:3000" `
        -e "NODE_OPTIONS=--max-old-space-size=$HeapSize" `
        -e "SHELL=/bin/bash" `
        -e "TERM=xterm-256color" `
        -e "DEBIAN_FRONTEND=noninteractive" `
        ubuntu:22.04 `
        bash -c $cmd
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Agent $Name started! Container: $containerId" -ForegroundColor Green
        Write-Host "[OK] Port: $port" -ForegroundColor Green
        Write-Host "[OK] Connect: docker exec -it claude-agent-$Name bash" -ForegroundColor Green
        Write-Host "[OK] Logs: docker logs -f claude-agent-$Name" -ForegroundColor Green
        
        # Wait for Claude Code to be installed
        Write-Host "`nWaiting for Claude Code installation..." -ForegroundColor Yellow
        $maxWait = 120  # Increased to 2 minutes
        $waited = 0
        $dotCount = 0
        
        while ($waited -lt $maxWait) {
            # Check if claude is installed
            $checkCmd = docker exec "claude-agent-$Name" bash -c "which claude 2>/dev/null || echo 'not-found'" 2>$null
            
            if ($checkCmd -and $checkCmd.Trim() -ne "" -and $checkCmd.Trim() -ne "not-found") {
                Write-Host "`n[OK] Claude Code is ready!" -ForegroundColor Green
                
                # Open new terminal window with Claude Code
                Write-Host "Opening Claude Code terminal..." -ForegroundColor Cyan
                Start-Process powershell -ArgumentList "-NoExit", "-Command", "docker exec -it claude-agent-$Name claude"
                
                Write-Host "[OK] Claude Code terminal opened in new window!" -ForegroundColor Green
                Write-Host "[OK] You can also connect manually: docker exec -it claude-agent-$Name bash" -ForegroundColor Green
                break
            }
            
            Start-Sleep -Seconds 3
            $waited += 3
            $dotCount++
            
            # Show progress
            Write-Host "." -NoNewline
            
            # Every 15 seconds, show more info
            if ($dotCount % 5 -eq 0) {
                Write-Host " ($waited seconds)" -NoNewline -ForegroundColor DarkGray
                
                # Check if container is still running
                $running = docker ps --filter "name=claude-agent-$Name" --format "{{.Names}}" 2>$null
                if (-not $running) {
                    Write-Host "`n[X] Container stopped unexpectedly!" -ForegroundColor Red
                    Write-Host "Check logs: docker logs claude-agent-$Name" -ForegroundColor Yellow
                    return
                }
            }
        }
        
        if ($waited -ge $maxWait) {
            Write-Host "`n[WARNING] Claude Code installation is taking longer than expected." -ForegroundColor Yellow
            Write-Host "Options:" -ForegroundColor Yellow
            Write-Host "  1. Check logs: docker logs -f claude-agent-$Name" -ForegroundColor Cyan
            Write-Host "  2. Connect to container: docker exec -it claude-agent-$Name bash" -ForegroundColor Cyan
            Write-Host "  3. Manually run: claude" -ForegroundColor Cyan
        }
    } else {
        Write-Host "[X] Failed to start agent $Name" -ForegroundColor Red
    }
}

function Get-AgentStatus {
    Write-Host "Claude Agent Status:" -ForegroundColor Cyan
    docker ps --filter "name=claude-agent-*" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
}

function Stop-AllAgents {
    Write-Host "Stopping all agents..." -ForegroundColor Red
    $containers = docker ps -q --filter "name=claude-agent-*"
    if ($containers) {
        docker stop $containers
        docker rm $containers
        Write-Host "All agents stopped." -ForegroundColor Green
    } else {
        Write-Host "No agents running." -ForegroundColor Yellow
    }
}

function Test-Agent {
    param([string]$Name)
    Write-Host "Testing Claude Code in agent $Name..." -ForegroundColor Yellow
    
    # Check if container exists
    $exists = docker ps -a --filter "name=claude-agent-$Name" --format "{{.Names}}" 2>$null
    if (-not $exists) {
        Write-Host "[X] Agent $Name not found!" -ForegroundColor Red
        return
    }
    
    # Check if running
    $running = docker ps --filter "name=claude-agent-$Name" --format "{{.Names}}" 2>$null
    if (-not $running) {
        Write-Host "[X] Agent $Name is not running!" -ForegroundColor Red
        return
    }
    
    Write-Host "`nChecking installations..." -ForegroundColor Cyan
    Write-Host "Node.js:" -ForegroundColor Yellow
    docker exec "claude-agent-$Name" node --version 2>&1
    
    Write-Host "`nNPM:" -ForegroundColor Yellow
    docker exec "claude-agent-$Name" npm --version 2>&1
    
    Write-Host "`nClaude Code:" -ForegroundColor Yellow
    $claudePath = docker exec "claude-agent-$Name" which claude 2>&1
    if ($claudePath -match "claude") {
        Write-Host "  Path: $claudePath" -ForegroundColor Green
        docker exec "claude-agent-$Name" claude --version 2>&1
    } else {
        Write-Host "  [X] Not installed yet" -ForegroundColor Red
        Write-Host "`nChecking npm global packages:" -ForegroundColor Yellow
        docker exec "claude-agent-$Name" npm list -g --depth=0 2>&1
    }
    
    Write-Host "`nContainer Status:" -ForegroundColor Yellow
    docker ps --filter "name=claude-agent-$Name" --no-trunc
}

function Connect-ToAgent {
    # Get running agents
    $runningAgents = docker ps --filter "name=claude-agent-*" --format "{{.Names}}" | Where-Object { $_ -match "claude-agent-" }
    
    if (-not $runningAgents) {
        Write-Host "No Claude agents are currently running." -ForegroundColor Yellow
        Write-Host "Start an agent first with:" -ForegroundColor Yellow
        Write-Host "  .\docker-claude-simple.ps1 -Action sonnet" -ForegroundColor Cyan
        Write-Host "  .\docker-claude-simple.ps1 -Action opus" -ForegroundColor Cyan
        return
    }
    
    # Convert to array if single result
    if ($runningAgents -is [string]) {
        $runningAgents = @($runningAgents)
    }
    
    Write-Host "`nRunning Claude Agents:" -ForegroundColor Cyan
    Write-Host "======================" -ForegroundColor Cyan
    
    for ($i = 0; $i -lt $runningAgents.Count; $i++) {
        $agentName = $runningAgents[$i]
        $shortName = $agentName -replace "claude-agent-", ""
        
        # Check if Claude is installed
        $claudeInstalled = docker exec $agentName which claude 2>$null
        $status = if ($claudeInstalled) { "Ready" } else { "Installing..." }
        
        Write-Host "[$($i+1)] $shortName ($status)" -ForegroundColor Green
    }
    
    Write-Host "`nSelect an agent to connect to (1-$($runningAgents.Count)) or 'q' to quit: " -NoNewline -ForegroundColor Yellow
    $selection = Read-Host
    
    if ($selection -eq 'q') {
        return
    }
    
    try {
        $index = [int]$selection - 1
        if ($index -lt 0 -or $index -ge $runningAgents.Count) {
            Write-Host "Invalid selection." -ForegroundColor Red
            return
        }
    } catch {
        Write-Host "Invalid selection." -ForegroundColor Red
        return
    }
    
    $selectedAgent = $runningAgents[$index]
    $shortName = $selectedAgent -replace "claude-agent-", ""
    
    # Check if Claude is ready
    $claudeReady = docker exec $selectedAgent which claude 2>$null
    if (-not $claudeReady) {
        Write-Host "`nClaude Code is still installing in $shortName. Please wait..." -ForegroundColor Yellow
        Write-Host "Check installation progress with: docker logs -f $selectedAgent" -ForegroundColor Yellow
        return
    }
    
    # Try to find existing window
    $existingWindow = Get-Process powershell -ErrorAction SilentlyContinue | 
        Where-Object { $_.MainWindowTitle -match "Claude Code - $shortName" }
    
    if ($existingWindow) {
        Write-Host "`nFocusing existing Claude Code window for $shortName..." -ForegroundColor Green
        
        # Simple method to activate window
        try {
            Add-Type -AssemblyName Microsoft.VisualBasic
            [Microsoft.VisualBasic.Interaction]::AppActivate($existingWindow.Id)
        } catch {
            # Fallback: just notify user
            Write-Host "Window found but couldn't auto-focus. Please switch to it manually." -ForegroundColor Yellow
        }
    } else {
        Write-Host "`nOpening new Claude Code terminal for $shortName..." -ForegroundColor Green
        
        # Create custom title for the window
        $windowTitle = "Claude Code - $shortName"
        
        # Start new PowerShell window with Claude
        Start-Process powershell -ArgumentList `
            "-NoExit", `
            "-Command", `
            "`$host.ui.RawUI.WindowTitle = '$windowTitle'; docker exec -it $selectedAgent claude"
    }
    
    Write-Host "[OK] Connected to $shortName!" -ForegroundColor Green
}

# Main logic
switch ($Action.ToLower()) {
    "opus" { Start-OpusAgent }
    "sonnet" { Start-SonnetAgent }
    "connect" { Connect-ToAgent }
    "status" { Get-AgentStatus }
    "stop" { Stop-AllAgents }
    "test" { Test-Agent -Name $AgentName }
    default {
        Write-Host @"
Simple Docker Claude Code Agent System

USAGE:
  .\docker-claude-simple.ps1 -Action <action> [-AutoName] [-AgentName <name>]

COMMANDS:
  -Action opus      # Start Opus agent (16GB memory, 12GB heap)
  -Action sonnet    # Start Sonnet agent (8GB memory, 6GB heap)
  -Action connect   # Connect to running agent (interactive selection)
  -Action status    # Show running agents
  -Action stop      # Stop all agents
  -Action test      # Test agent (use -AgentName)

FLAGS:
  -AutoName         # Auto-generate unique name (opus-2, opus-3, etc.)
  -AgentName <name> # Specify custom agent name

EXAMPLES:
  # Start multiple agents
  .\docker-claude-simple.ps1 -Action sonnet
  .\docker-claude-simple.ps1 -Action sonnet -AutoName
  .\docker-claude-simple.ps1 -Action opus -AgentName "opus-research"
  .\docker-claude-simple.ps1 -Action opus -AgentName "opus-coding"
  
  # Connect and manage
  .\docker-claude-simple.ps1 -Action connect
  .\docker-claude-simple.ps1 -Action status

NOTES:
  - Uses Ubuntu 22.04 (fixes Alpine env -S issues)
  - Large heap sizes prevent memory exhaustion
  - Automatically opens Claude terminal on start
  - 'connect' command reuses existing terminals or opens new ones
  - Each agent gets unique port based on name hash
  - Run multiple concurrent agents with -AutoName or custom names
"@ -ForegroundColor Cyan
    }
}