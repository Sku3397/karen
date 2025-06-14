#!/usr/bin/env python3
"""
Autonomous MCP Setup Script for Claude Desktop
Detects platform and configures everything automatically
"""

import os
import sys
import json
import platform
import subprocess
from pathlib import Path
import shutil

def detect_platform():
    """Detect the operating system and return config paths."""
    system = platform.system()
    home = Path.home()
    
    if system == "Windows":
        # Windows paths
        appdata = os.environ.get('APPDATA', '')
        if not appdata:
            appdata = home / "AppData" / "Roaming"
        
        config_dir = Path(appdata) / "Claude"
        python_cmd = "python"
    
    elif system == "Darwin":  # macOS
        config_dir = home / "Library" / "Application Support" / "Claude"
        python_cmd = "python3"
    
    else:  # Linux
        config_dir = home / ".claude"
        python_cmd = "python3"
    
    return {
        "system": system,
        "config_dir": config_dir,
        "config_file": config_dir / "claude_desktop_config.json",
        "python_cmd": python_cmd,
        "project_root": Path("/workspace").resolve()
    }

def install_mcp_package():
    """Install the MCP package."""
    print("📦 Installing MCP package...")
    try:
        # Try pip3 first, then pip
        for pip_cmd in ["pip3", "pip"]:
            try:
                result = subprocess.run(
                    [pip_cmd, "install", "mcp"],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    print("✅ MCP package installed successfully")
                    return True
            except FileNotFoundError:
                continue
        
        print("⚠️ Could not install MCP package - please install manually: pip install mcp")
        return False
    except Exception as e:
        print(f"⚠️ Error installing MCP: {e}")
        return False

def create_config(platform_info):
    """Create the MCP configuration for Claude Desktop."""
    print(f"\n🔧 Creating configuration for {platform_info['system']}...")
    
    # Determine path format based on OS
    if platform_info['system'] == "Windows":
        project_path = str(platform_info['project_root']).replace('/', '\\')
    else:
        project_path = str(platform_info['project_root'])
    
    config = {
        "mcpServers": {
            "karen-codebase-core": {
                "command": platform_info['python_cmd'],
                "args": ["-m", "src.mcp_servers.karen_codebase_core_mcp"],
                "cwd": project_path,
                "env": {
                    "PYTHONPATH": project_path
                }
            },
            "karen-codebase-search-basic": {
                "command": platform_info['python_cmd'],
                "args": ["-m", "src.mcp_servers.karen_codebase_search_basic_mcp"],
                "cwd": project_path,
                "env": {
                    "PYTHONPATH": project_path
                }
            },
            "karen-codebase-analysis": {
                "command": platform_info['python_cmd'],
                "args": ["-m", "src.mcp_servers.karen_codebase_analysis_mcp"],
                "cwd": project_path,
                "env": {
                    "PYTHONPATH": project_path
                }
            },
            "karen-codebase-git": {
                "command": platform_info['python_cmd'],
                "args": ["-m", "src.mcp_servers.karen_codebase_git_mcp"],
                "cwd": project_path,
                "env": {
                    "PYTHONPATH": project_path
                }
            },
            "karen-codebase-architecture": {
                "command": platform_info['python_cmd'],
                "args": ["-m", "src.mcp_servers.karen_codebase_architecture_mcp"],
                "cwd": project_path,
                "env": {
                    "PYTHONPATH": project_path
                }
            },
            "karen-tools": {
                "command": platform_info['python_cmd'],
                "args": ["-m", "src.mcp_servers.karen_tools_mcp"],
                "cwd": project_path,
                "env": {
                    "PYTHONPATH": project_path
                }
            }
        }
    }
    
    return config

def backup_existing_config(config_file):
    """Backup existing configuration if it exists."""
    if config_file.exists():
        backup_path = config_file.with_suffix('.json.backup')
        print(f"📋 Backing up existing config to {backup_path}")
        shutil.copy2(config_file, backup_path)
        return True
    return False

def write_config(platform_info, config):
    """Write the configuration to Claude Desktop's directory."""
    config_dir = platform_info['config_dir']
    config_file = platform_info['config_file']
    
    print(f"\n📁 Configuration directory: {config_dir}")
    
    # Create directory if it doesn't exist
    try:
        config_dir.mkdir(parents=True, exist_ok=True)
        print("✅ Configuration directory ready")
    except Exception as e:
        print(f"❌ Error creating directory: {e}")
        return False
    
    # Backup existing config
    backup_existing_config(config_file)
    
    # Write new config
    try:
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"✅ Configuration written to: {config_file}")
        return True
    except Exception as e:
        print(f"❌ Error writing configuration: {e}")
        return False

def verify_setup(platform_info):
    """Verify the setup is complete."""
    print("\n🔍 Verifying setup...")
    
    issues = []
    
    # Check config file exists
    if not platform_info['config_file'].exists():
        issues.append("Configuration file not found")
    else:
        print("✅ Configuration file exists")
    
    # Check Python command
    try:
        result = subprocess.run(
            [platform_info['python_cmd'], "--version"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"✅ Python available: {result.stdout.strip()}")
        else:
            issues.append(f"Python command '{platform_info['python_cmd']}' not working")
    except FileNotFoundError:
        issues.append(f"Python command '{platform_info['python_cmd']}' not found")
    
    # Check MCP servers exist
    mcp_servers_dir = platform_info['project_root'] / "src" / "mcp_servers"
    if mcp_servers_dir.exists():
        server_files = list(mcp_servers_dir.glob("karen_*.py"))
        print(f"✅ Found {len(server_files)} MCP server files")
    else:
        issues.append("MCP servers directory not found")
    
    # Check if we're in WSL
    if platform_info['system'] == "Linux" and 'microsoft' in platform.release().lower():
        print("\n⚠️ WSL Detected!")
        print("   You may need to configure Claude Desktop on the Windows side.")
        print("   The Windows config path would be: %APPDATA%\\Claude\\claude_desktop_config.json")
    
    return issues

def main():
    """Main setup function."""
    print("🚀 Karen MCP Autonomous Setup Script")
    print("=" * 50)
    
    # Detect platform
    platform_info = detect_platform()
    print(f"🖥️  Detected OS: {platform_info['system']}")
    print(f"📂 Project root: {platform_info['project_root']}")
    
    # Install MCP package
    install_mcp_package()
    
    # Create configuration
    config = create_config(platform_info)
    
    # Write configuration
    success = write_config(platform_info, config)
    
    if not success:
        print("\n❌ Setup failed - see errors above")
        return 1
    
    # Verify setup
    issues = verify_setup(platform_info)
    
    print("\n" + "=" * 50)
    
    if issues:
        print("⚠️ Setup completed with issues:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("✅ Setup completed successfully!")
    
    print("\n📋 Next steps:")
    print("1. Restart Claude Desktop completely")
    print("2. Test by asking: 'What MCP servers are connected?'")
    print("3. Try a tool: 'Use karen_system_health to check the system'")
    
    if platform_info['system'] == "Linux" and 'microsoft' in platform.release().lower():
        print("\n🪟 WSL Users:")
        print("   If Claude Desktop is running on Windows, copy this config:")
        print(f"   From: {platform_info['config_file']}")
        print("   To: %APPDATA%\\Claude\\claude_desktop_config.json")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())