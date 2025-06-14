#!/usr/bin/env python3
"""
Autonomous MCP Fix for Claude Desktop
This script will fix all MCP issues and ensure Claude Desktop can see the tools
"""

import os
import sys
import json
import platform
from pathlib import Path
import shutil

def get_platform_config_path():
    """Get the correct config path for the current platform."""
    system = platform.system()
    home = Path.home()
    
    # Map of possible config locations
    locations = {
        "Windows": [
            Path(os.environ.get('APPDATA', '')) / "Claude" / "claude_desktop_config.json",
            Path(os.environ.get('LOCALAPPDATA', '')) / "Claude" / "claude_desktop_config.json",
            home / ".claude" / "claude_desktop_config.json"
        ],
        "Darwin": [  # macOS
            home / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json",
            home / ".claude" / "claude_desktop_config.json"
        ],
        "Linux": [
            home / ".claude" / "claude_desktop_config.json",
            home / ".config" / "claude" / "claude_desktop_config.json"
        ]
    }
    
    # Try each location
    for location in locations.get(system, locations["Linux"]):
        if location and location.parent.exists():
            return location
    
    # Default to first option
    return locations.get(system, locations["Linux"])[0]

def create_working_config():
    """Create a working MCP configuration."""
    # Use the standalone server that doesn't need MCP library
    config = {
        "mcpServers": {
            "karen-all-tools": {
                "command": "python3",
                "args": ["/workspace/karen_all_tools_mcp.py"],
                "cwd": "/workspace",
                "env": {
                    "PYTHONPATH": "/workspace"
                }
            },
            "karen-core": {
                "command": "python3",
                "args": ["/workspace/karen_codebase_core_mcp.py"],
                "cwd": "/workspace",
                "env": {
                    "PYTHONPATH": "/workspace"
                }
            },
            "karen-search": {
                "command": "python3",
                "args": ["/workspace/karen_codebase_search_basic_mcp.py"],
                "cwd": "/workspace",
                "env": {
                    "PYTHONPATH": "/workspace"
                }
            },
            "karen-analysis": {
                "command": "python3",
                "args": ["/workspace/karen_codebase_analysis_mcp.py"],
                "cwd": "/workspace",
                "env": {
                    "PYTHONPATH": "/workspace"
                }
            }
        }
    }
    
    # For Windows, use python instead of python3
    if platform.system() == "Windows":
        for server in config["mcpServers"].values():
            server["command"] = "python"
    
    return config

def fix_mcp_setup():
    """Main function to fix MCP setup."""
    print("🔧 Autonomous MCP Fix Starting...")
    print("=" * 50)
    
    # 1. Determine config location
    config_path = get_platform_config_path()
    print(f"📁 Config location: {config_path}")
    
    # 2. Create directory if needed
    config_dir = config_path.parent
    if not config_dir.exists():
        print(f"📂 Creating config directory: {config_dir}")
        config_dir.mkdir(parents=True, exist_ok=True)
    
    # 3. Backup existing config
    if config_path.exists():
        backup_path = config_path.with_suffix('.json.backup')
        print(f"💾 Backing up existing config to: {backup_path}")
        shutil.copy2(config_path, backup_path)
    
    # 4. Create and write new config
    config = create_working_config()
    
    print("✍️  Writing new configuration...")
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print("✅ Configuration written successfully!")
    
    # 5. Create summary file
    summary_path = Path("/workspace/MCP_FIX_SUMMARY.md")
    summary = f"""# ✅ MCP Fixed Successfully!

## What was done:

1. **Created standalone MCP server** at `/workspace/karen_all_tools_mcp.py`
   - No external dependencies needed
   - Implements MCP protocol manually
   - Includes 5 working tools

2. **Updated Claude Desktop config** at:
   `{config_path}`

3. **Configured 4 MCP servers**:
   - karen-all-tools (5 tools: system health, redis check, project structure, git status, file search)
   - karen-core (file operations)
   - karen-search (code search)
   - karen-analysis (code analysis)

## To activate:

1. **Restart Claude Desktop completely**
   - Close Claude Desktop
   - Make sure it's not in system tray
   - Start Claude Desktop again

2. **Test the connection**:
   ```
   What MCP servers are connected?
   ```

3. **Try a tool**:
   ```
   Use the karen_system_health tool to check the system
   ```

## Available tools:

- `karen_system_health` - Get system status
- `karen_check_redis` - Check Redis connection
- `karen_project_structure` - Show project structure
- `karen_git_status` - Show git status
- `karen_search_files` - Search for files

## Troubleshooting:

If tools still don't appear:
1. Check Claude Desktop logs
2. Ensure Python/Python3 is in PATH
3. Try the simpler config with just karen-all-tools

Config location: `{config_path}`
"""
    
    with open(summary_path, 'w') as f:
        f.write(summary)
    
    print(f"\n📄 Summary written to: {summary_path}")
    
    # 6. Platform-specific instructions
    print("\n" + "=" * 50)
    print("🎯 Next Steps:")
    print("1. Restart Claude Desktop completely")
    print("2. Test with: 'What MCP servers are connected?'")
    print("3. Try: 'Use karen_system_health to check the system'")
    
    if platform.system() == "Linux" and 'microsoft' in platform.release().lower():
        print("\n⚠️  WSL Detected!")
        print("If Claude Desktop runs on Windows, copy the config:")
        print(f"From: {config_path}")
        print("To: %APPDATA%\\Claude\\claude_desktop_config.json")

if __name__ == "__main__":
    try:
        fix_mcp_setup()
        print("\n✅ MCP fix completed successfully!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)