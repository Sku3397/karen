#!/usr/bin/env python3
"""
Quick MCP Status Checker
Run this to see exactly why MCP is disconnected
"""

import os
import sys
import json
import subprocess
from pathlib import Path

def check_python_mcp():
    """Check if Python can import MCP"""
    print("🔍 Checking Python MCP availability...")
    
    commands = ['python', 'py', 'python3']
    for cmd in commands:
        try:
            result = subprocess.run([cmd, '-c', '''
try:
    from mcp.server import Server
    from mcp.types import Resource, TextContent
    from mcp.server.stdio import stdio_server
    print("MCP_OK")
except ImportError as e:
    print(f"MCP_MISSING: {e}")
except Exception as e:
    print(f"MCP_ERROR: {e}")
'''], capture_output=True, text=True, timeout=10)
            
            output = result.stdout.strip()
            print(f"  {cmd:10}: {output}")
            
            if "MCP_OK" in output:
                return cmd
                
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print(f"  {cmd:10}: Not found")
    
    return None

def check_config():
    """Check Claude Desktop configuration"""
    print("\n📝 Checking Claude Desktop config...")
    
    config_locations = [
        os.path.expandvars(r"%APPDATA%\Claude\claude_desktop_config.json"),
        "/mnt/c/Users/Man/AppData/Roaming/Claude/claude_desktop_config.json"
    ]
    
    for location in config_locations:
        if os.path.exists(location):
            print(f"✅ Config found: {location}")
            
            try:
                with open(location, 'r') as f:
                    config = json.load(f)
                
                if 'mcpServers' in config:
                    for name, server in config['mcpServers'].items():
                        print(f"  🔸 {name}")
                        print(f"     Command: {server.get('command', 'MISSING')}")
                        print(f"     Args: {server.get('args', 'MISSING')}")
                        
                        # Check if server file exists
                        if 'args' in server and server['args']:
                            server_file = server['args'][0]
                            if os.path.exists(server_file):
                                print(f"     ✅ Server file exists")
                            else:
                                print(f"     ❌ Server file missing: {server_file}")
                else:
                    print("  ❌ No mcpServers section")
                    
                return True
                
            except Exception as e:
                print(f"  ❌ Config error: {e}")
        else:
            print(f"❌ Config not found: {location}")
    
    return False

def test_server_startup():
    """Test if our server can start"""
    print("\n🧪 Testing server startup...")
    
    # Check if server files exist
    servers = ['ultra_minimal_mcp.py', 'minimal_test_server.py']
    for server in servers:
        if os.path.exists(server):
            print(f"✅ {server} exists")
            
            # Try to read it
            try:
                with open(server, 'r') as f:
                    content = f.read()
                
                if 'from mcp.server import Server' in content:
                    print(f"  📝 Uses MCP imports")
                else:
                    print(f"  ⚠️  No MCP imports")
                    
            except Exception as e:
                print(f"  ❌ Error reading {server}: {e}")
        else:
            print(f"❌ {server} missing")

def main():
    """Run all checks"""
    print("🩺 MCP DISCONNECT DIAGNOSIS")
    print("=" * 30)
    
    # Check 1: Python MCP
    working_python = check_python_mcp()
    
    # Check 2: Configuration
    config_ok = check_config()
    
    # Check 3: Server files
    test_server_startup()
    
    # Summary
    print("\n📊 DIAGNOSIS SUMMARY")
    print("=" * 20)
    
    if not working_python:
        print("❌ CRITICAL: No Python with MCP SDK")
        print("   Fix: pip install 'mcp[cli]'")
        
    if not config_ok:
        print("❌ CRITICAL: No valid config found")
        print("   Fix: Run FIX_MCP_DISCONNECT.bat")
        
    if working_python and config_ok:
        print("🤔 Python and config OK, but still disconnected?")
        print("   Likely issues:")
        print("   1. Server crashes on startup")
        print("   2. Path issues in config")  
        print("   3. Environment variables missing")
        print("   4. Claude Desktop permissions")
        
    print(f"\n🔧 Recommended actions:")
    print(f"1. Run: FIX_MCP_DISCONNECT.bat")
    print(f"2. Run: FIND_MCP_LOGS.ps1")
    print(f"3. Check Claude Desktop logs for exact errors")

if __name__ == "__main__":
    main()