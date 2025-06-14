# Karen MCP Setup Script for Windows
# Run this in PowerShell as Administrator if needed

Write-Host "🚀 Karen MCP Setup for Claude Desktop (Windows)" -ForegroundColor Cyan
Write-Host "=" * 50

# Get project path from user
$defaultPath = "C:\path\to\your\karen\project"
Write-Host "📁 Enter your Karen project path (where this script is located):" -ForegroundColor Yellow
Write-Host "   Press Enter to use: $defaultPath" -ForegroundColor Gray
$projectPath = Read-Host "Project path"

if ([string]::IsNullOrWhiteSpace($projectPath)) {
    $projectPath = $defaultPath
}

# Verify project path exists
if (-not (Test-Path $projectPath)) {
    Write-Host "❌ Error: Project path not found: $projectPath" -ForegroundColor Red
    Write-Host "Please run this script from your Karen project directory or provide the correct path."
    exit 1
}

Write-Host "✅ Using project path: $projectPath" -ForegroundColor Green

# Create Claude config directory
$claudeConfigDir = "$env:APPDATA\Claude"
if (-not (Test-Path $claudeConfigDir)) {
    Write-Host "📁 Creating Claude config directory..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $claudeConfigDir -Force | Out-Null
}

# Backup existing config
$configFile = "$claudeConfigDir\claude_desktop_config.json"
if (Test-Path $configFile) {
    $backupFile = "$configFile.backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    Write-Host "📋 Backing up existing config to: $backupFile" -ForegroundColor Yellow
    Copy-Item $configFile $backupFile
}

# Create configuration
$config = @{
    mcpServers = @{
        "karen-codebase-core" = @{
            command = "python"
            args = @("-m", "src.mcp_servers.karen_codebase_core_mcp")
            cwd = $projectPath
            env = @{
                PYTHONPATH = $projectPath
            }
        }
        "karen-codebase-search-basic" = @{
            command = "python"
            args = @("-m", "src.mcp_servers.karen_codebase_search_basic_mcp")
            cwd = $projectPath
            env = @{
                PYTHONPATH = $projectPath
            }
        }
        "karen-codebase-analysis" = @{
            command = "python"
            args = @("-m", "src.mcp_servers.karen_codebase_analysis_mcp")
            cwd = $projectPath
            env = @{
                PYTHONPATH = $projectPath
            }
        }
        "karen-codebase-git" = @{
            command = "python"
            args = @("-m", "src.mcp_servers.karen_codebase_git_mcp")
            cwd = $projectPath
            env = @{
                PYTHONPATH = $projectPath
            }
        }
        "karen-codebase-architecture" = @{
            command = "python"
            args = @("-m", "src.mcp_servers.karen_codebase_architecture_mcp")
            cwd = $projectPath
            env = @{
                PYTHONPATH = $projectPath
            }
        }
        "karen-tools" = @{
            command = "python"
            args = @("-m", "src.mcp_servers.karen_tools_mcp")
            cwd = $projectPath
            env = @{
                PYTHONPATH = $projectPath
            }
        }
    }
}

# Write configuration
Write-Host "💾 Writing configuration to: $configFile" -ForegroundColor Yellow
$config | ConvertTo-Json -Depth 10 | Set-Content -Path $configFile -Encoding UTF8
Write-Host "✅ Configuration written successfully!" -ForegroundColor Green

# Verify setup
Write-Host "`n🔍 Verifying setup..." -ForegroundColor Cyan

# Check Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python available: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Python not found - please install Python and ensure it's in PATH" -ForegroundColor Yellow
}

# Check MCP package
Write-Host "`n📦 Checking MCP package..." -ForegroundColor Yellow
$pipList = pip list 2>&1 | Select-String "mcp"
if ($pipList) {
    Write-Host "✅ MCP package is installed" -ForegroundColor Green
} else {
    Write-Host "⚠️ MCP package not found - installing..." -ForegroundColor Yellow
    pip install mcp
}

# Check if Claude Desktop is running
$claudeProcess = Get-Process "Claude*" -ErrorAction SilentlyContinue
if ($claudeProcess) {
    Write-Host "`n⚠️ Claude Desktop is running - please restart it to load the new configuration" -ForegroundColor Yellow
}

Write-Host "`n" + ("=" * 50)
Write-Host "✅ Setup completed!" -ForegroundColor Green
Write-Host "`n📋 Next steps:" -ForegroundColor Cyan
Write-Host "1. Close Claude Desktop completely (check system tray)"
Write-Host "2. Start Claude Desktop again"
Write-Host "3. Test by asking: 'What MCP servers are connected?'"
Write-Host "4. Try a tool: 'Use karen_system_health to check the system'"

Write-Host "`n🎯 You now have 35 tools across 6 MCP servers:" -ForegroundColor Green
Write-Host "   - karen-codebase-core (5 tools)"
Write-Host "   - karen-codebase-search-basic (5 tools)"
Write-Host "   - karen-codebase-analysis (5 tools)"
Write-Host "   - karen-codebase-git (7 tools)"
Write-Host "   - karen-codebase-architecture (7 tools)"
Write-Host "   - karen-tools (6 tools)"

Write-Host "`nPress any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")