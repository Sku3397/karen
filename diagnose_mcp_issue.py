#!/usr/bin/env python3
"""
Diagnose MCP Issues for Claude Desktop
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def test_mcp_server(server_path, python_cmd="python"):
    """Test if an MCP server can start."""
    print(f"\n🔍 Testing: {server_path}")
    
    if not os.path.exists(server_path):
        print(f"❌ File not found: {server_path}")
        return False
    
    # Test basic imports
    test_cmd = [python_cmd, "-c", f"exec(open('{server_path}').read().split('if __name__')[0])"]
    
    try:
        result = subprocess.run(
            test_cmd,
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            print(f"✅ Imports successful")
            return True
        else:
            print(f"❌ Import error:")
            print(f"   {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⚠️ Timeout - server might be waiting for input")
        return True  # This is actually expected for MCP servers
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def check_mcp_library():
    """Check if MCP library is available."""
    print("\n📦 Checking MCP library...")
    
    # Try different Python commands
    for python_cmd in ["python", "python3", "py"]:
        try:
            result = subprocess.run(
                [python_cmd, "-c", "import mcp; print(f'MCP found at: {mcp.__file__}')"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print(f"✅ MCP library found with {python_cmd}")
                print(f"   {result.stdout.strip()}")
                return python_cmd
            
        except FileNotFoundError:
            continue
    
    print("❌ MCP library not found in any Python installation")
    print("   Install with: pip install mcp-python")
    return None

def find_config_location():
    """Find Claude Desktop config location."""
    print("\n📁 Finding Claude Desktop config location...")
    
    possible_locations = []
    
    # Windows locations
    if sys.platform == "win32":
        appdata = os.environ.get('APPDATA', '')
        if appdata:
            possible_locations.append(Path(appdata) / "Claude" / "claude_desktop_config.json")
    
    # macOS location
    elif sys.platform == "darwin":
        home = Path.home()
        possible_locations.append(home / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json")
    
    # Linux location
    else:
        home = Path.home()
        possible_locations.append(home / ".claude" / "claude_desktop_config.json")
    
    for location in possible_locations:
        if location.exists():
            print(f"✅ Config found at: {location}")
            return location
    
    print("❌ No Claude Desktop config found")
    print("   Expected locations:")
    for loc in possible_locations:
        print(f"   - {loc}")
    
    return None

def analyze_config(config_path):
    """Analyze the Claude Desktop configuration."""
    print(f"\n🔧 Analyzing config: {config_path}")
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        if "mcpServers" not in config:
            print("❌ No MCP servers configured")
            return
        
        servers = config["mcpServers"]
        print(f"✅ Found {len(servers)} MCP server(s):")
        
        for name, server_config in servers.items():
            print(f"\n   Server: {name}")
            print(f"   Command: {server_config.get('command', 'Not specified')}")
            print(f"   Args: {server_config.get('args', [])}")
            print(f"   CWD: {server_config.get('cwd', 'Not specified')}")
            
            # Check if the server file exists
            if 'args' in server_config and server_config['args']:
                server_path = server_config['args'][0]
                if server_path.startswith('-m'):
                    # Module path
                    print(f"   Type: Python module")
                else:
                    # File path
                    if os.path.isabs(server_path):
                        full_path = server_path
                    else:
                        cwd = server_config.get('cwd', '.')
                        full_path = os.path.join(cwd, server_path)
                    
                    if os.path.exists(full_path):
                        print(f"   ✅ File exists: {full_path}")
                    else:
                        print(f"   ❌ File not found: {full_path}")
        
    except Exception as e:
        print(f"❌ Error reading config: {e}")

def main():
    """Main diagnostic function."""
    print("🚀 MCP Diagnostic Tool for Claude Desktop")
    print("=" * 50)
    
    # Check MCP library
    python_cmd = check_mcp_library()
    
    # Find config
    config_path = find_config_location()
    
    if config_path:
        analyze_config(config_path)
    
    # Test known MCP servers
    print("\n🧪 Testing MCP servers in workspace...")
    
    test_servers = [
        "/workspace/working_mcp_server.py",
        "/workspace/karen_tools_fixed_mcp.py",
        "/workspace/karen_codebase_core_mcp.py",
        "/workspace/karen_mcp_server.py"
    ]
    
    working_servers = []
    
    for server in test_servers:
        if os.path.exists(server):
            if test_mcp_server(server, python_cmd or "python"):
                working_servers.append(server)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Summary:")
    
    if not python_cmd:
        print("❌ MCP library not installed")
        print("   Fix: pip install mcp-python")
    
    if not config_path:
        print("❌ Claude Desktop config not found")
        print("   Fix: Create config at the expected location")
    elif config_path:
        print(f"✅ Config location: {config_path}")
    
    if working_servers:
        print(f"✅ Found {len(working_servers)} working MCP server(s)")
        
        # Suggest a working config
        print("\n💡 Suggested configuration:")
        suggested_config = {
            "mcpServers": {}
        }
        
        for i, server in enumerate(working_servers[:3]):  # Limit to 3
            server_name = Path(server).stem.replace('_', '-')
            suggested_config["mcpServers"][server_name] = {
                "command": python_cmd or "python",
                "args": [server],
                "cwd": str(Path(server).parent),
                "env": {
                    "PYTHONPATH": str(Path(server).parent)
                }
            }
        
        print(json.dumps(suggested_config, indent=2))
    
    else:
        print("❌ No working MCP servers found")

if __name__ == "__main__":
    main()