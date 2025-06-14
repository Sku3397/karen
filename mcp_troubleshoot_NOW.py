#!/usr/bin/env python3
"""
MCP Troubleshooter - Identifies and fixes common MCP issues
Run this to get specific fixes for your MCP problems
"""

import os
import sys
import json
import subprocess
from pathlib import Path
import platform

def print_section(title):
    print(f"\n{'='*50}")
    print(f"  {title}")
    print('='*50)

def check_python_mcp():
    """Check if MCP SDK is available"""
    print_section("CHECKING PYTHON & MCP SDK")
    
    # Test Python versions
    python_commands = ['python', 'py', 'python3']
    working_python = None
    
    for cmd in python_commands:
        try:
            result = subprocess.run([cmd, '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                version = result.stdout.strip()
                print(f"✅ {cmd}: {version}")
                
                # Test MCP with this Python
                mcp_test = subprocess.run([cmd, '-c', 
                    'from mcp.server import Server; print("MCP OK")'], 
                    capture_output=True, text=True, timeout=5)
                
                if mcp_test.returncode == 0:
                    print(f"✅ {cmd}: MCP SDK working")
                    working_python = cmd
                    break
                else:
                    print(f"❌ {cmd}: MCP SDK missing")
            
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print(f"❌ {cmd}: Not found")
    
    return working_python

def find_claude_configs():
    """Find Claude Desktop configuration locations"""
    print_section("FINDING CLAUDE DESKTOP CONFIGS")
    
    if platform.system() == "Windows":
        possible_locations = [
            os.path.expandvars(r"%APPDATA%\Claude\claude_desktop_config.json"),
            os.path.expandvars(r"%LOCALAPPDATA%\Claude\claude_desktop_config.json"),
            os.path.expandvars(r"%USERPROFILE%\.claude\claude_desktop_config.json"),
        ]
    else:
        possible_locations = [
            "/mnt/c/Users/Man/AppData/Roaming/Claude/claude_desktop_config.json",
            "/mnt/c/Users/Man/AppData/Local/Claude/claude_desktop_config.json",
        ]
    
    found_configs = []
    for location in possible_locations:
        if os.path.exists(location):
            print(f"✅ Found: {location}")
            found_configs.append(location)
            
            # Check config content
            try:
                with open(location, 'r') as f:
                    config = json.load(f)
                
                if 'mcpServers' in config:
                    server_count = len(config['mcpServers'])
                    print(f"   📊 {server_count} MCP servers configured")
                    
                    for name, server in config['mcpServers'].items():
                        print(f"   🔸 {name}: {server.get('command', 'no command')}")
                else:
                    print(f"   ❌ No mcpServers section")
                    
            except Exception as e:
                print(f"   ❌ Invalid config: {e}")
        else:
            print(f"❌ Not found: {location}")
    
    return found_configs

def test_mcp_servers():
    """Test our MCP server files"""
    print_section("TESTING MCP SERVER FILES")
    
    project_root = Path.cwd()
    print(f"📁 Project root: {project_root}")
    
    # Check server files exist
    server_files = [
        'ultra_minimal_mcp.py',
        'simple_mcp_test_robust.py', 
        'mcp_karen_monitor.py'
    ]
    
    for server_file in server_files:
        if (project_root / server_file).exists():
            print(f"✅ {server_file} exists")
            
            # Test import (without MCP SDK)
            try:
                with open(server_file, 'r') as f:
                    content = f.read()
                
                if 'from mcp.server import Server' in content:
                    print(f"   📝 Uses MCP SDK imports")
                else:
                    print(f"   ⚠️  No MCP imports found")
                    
            except Exception as e:
                print(f"   ❌ Error reading {server_file}: {e}")
        else:
            print(f"❌ {server_file} missing")

def create_fixes():
    """Create targeted fixes based on findings"""
    print_section("CREATING TARGETED FIXES")
    
    project_root = Path.cwd().resolve()
    
    # Fix 1: MCP SDK Installation script
    install_script = f'''
@echo off
echo Installing MCP SDK...
pip install "mcp[cli]"
if %errorlevel% neq 0 (
    pip install mcp
    if %errorlevel% neq 0 (
        pip install python-mcp
    )
)
echo MCP SDK installation complete
'''
    
    with open('install_mcp_sdk.bat', 'w') as f:
        f.write(install_script)
    print("✅ Created: install_mcp_sdk.bat")
    
    # Fix 2: Ultra minimal config
    minimal_config = {
        "mcpServers": {
            "ultra-minimal": {
                "command": "python",
                "args": [str(project_root / "ultra_minimal_mcp.py")],
                "env": {
                    "PYTHONUNBUFFERED": "1"
                }
            }
        }
    }
    
    with open('claude_config_minimal.json', 'w') as f:
        json.dump(minimal_config, f, indent=2)
    print("✅ Created: claude_config_minimal.json")
    
    # Fix 3: Robust config with multiple servers
    robust_config = {
        "mcpServers": {
            "karen-minimal": {
                "command": "python",
                "args": [str(project_root / "ultra_minimal_mcp.py")],
                "env": {
                    "KAREN_PROJECT_ROOT": str(project_root),
                    "PYTHONUNBUFFERED": "1"
                }
            },
            "karen-test": {
                "command": "python", 
                "args": [str(project_root / "simple_mcp_test_robust.py")],
                "env": {
                    "KAREN_PROJECT_ROOT": str(project_root),
                    "PYTHONPATH": str(project_root),
                    "PYTHONUNBUFFERED": "1"
                }
            },
            "karen-monitor": {
                "command": "python",
                "args": [str(project_root / "mcp_karen_monitor.py")],
                "env": {
                    "KAREN_PROJECT_ROOT": str(project_root),
                    "PYTHONPATH": str(project_root),
                    "PYTHONUNBUFFERED": "1"
                }
            }
        }
    }
    
    with open('claude_config_robust.json', 'w') as f:
        json.dump(robust_config, f, indent=2)
    print("✅ Created: claude_config_robust.json")
    
    # Fix 4: Deployment script
    deploy_script = f'''
@echo off
echo Deploying MCP configuration...

REM Create Claude config directory
if not exist "%APPDATA%\\Claude" mkdir "%APPDATA%\\Claude"

REM Copy minimal config first
copy claude_config_minimal.json "%APPDATA%\\Claude\\claude_desktop_config.json"
echo ✅ Minimal config deployed

echo.
echo 🔄 Please restart Claude Desktop
echo 🧪 Test: "Can you access the ultra-minimal server?"
echo.
echo If minimal works, then copy claude_config_robust.json to test more servers
pause
'''
    
    with open('deploy_mcp_config.bat', 'w') as f:
        f.write(deploy_script)
    print("✅ Created: deploy_mcp_config.bat")

def main():
    """Main troubleshooting routine"""
    print("🔧 MCP TROUBLESHOOTER - Finding Your Specific Issues")
    print("="*60)
    
    # Step 1: Check Python/MCP
    working_python = check_python_mcp()
    if not working_python:
        print("\n🚨 CRITICAL: No Python with MCP SDK found!")
        print("   Run: install_mcp_sdk.bat")
        return
    
    # Step 2: Find Claude configs
    configs = find_claude_configs()
    if not configs:
        print("\n🚨 CRITICAL: No Claude Desktop config locations found!")
        print("   Claude Desktop may not be installed properly")
        return
    
    # Step 3: Test our servers
    test_mcp_servers()
    
    # Step 4: Create fixes
    create_fixes()
    
    # Summary and next steps
    print_section("NEXT STEPS")
    print("1. 🔧 Run: install_mcp_sdk.bat")
    print("2. 🚀 Run: deploy_mcp_config.bat") 
    print("3. 🔄 Restart Claude Desktop completely")
    print("4. 🧪 Test: 'Can you access the ultra-minimal server?'")
    print("\n🎯 If ultra-minimal works, upgrade to robust config")
    print("📊 If issues persist, check Claude Desktop error messages")

if __name__ == "__main__":
    main()