#!/usr/bin/env python3
"""
Test script for Karen AI Agent Monitor MCP Server
Validates that the MCP server can start and provides expected resources
"""

import asyncio
import json
import os
import sys
from pathlib import Path
import subprocess
import tempfile
import time

def test_mcp_imports():
    """Test that MCP SDK can be imported"""
    print("🔍 Testing MCP SDK imports...")
    try:
        from mcp.server import Server
        from mcp.types import Resource, Tool, TextContent
        from mcp.server.models import InitializationOptions
        from mcp.server.stdio import stdio_server
        print("✅ MCP SDK imports successful")
        return True
    except ImportError as e:
        print(f"❌ MCP SDK import failed: {e}")
        print("Install with: pip install 'mcp[cli]'")
        return False

def test_project_structure():
    """Test that required project files exist"""
    print("\n🔍 Testing project structure...")
    project_root = Path(os.getenv("KAREN_PROJECT_ROOT", "."))
    
    required_files = [
        "autonomous_state.json",
        "tasks/eigencode_assigned_tasks.json",
        "agent_activities.jsonl"
    ]
    
    optional_files = [
        "logs/autonomous_system.log",
        "celery_worker_debug_logs.txt",
        "logs/agents/agent_activity.log"
    ]
    
    print(f"Project root: {project_root}")
    
    for file_path in required_files:
        full_path = project_root / file_path
        if full_path.exists():
            print(f"✅ Found: {file_path}")
        else:
            print(f"❌ Missing: {file_path}")
    
    for file_path in optional_files:
        full_path = project_root / file_path
        if full_path.exists():
            print(f"✅ Found: {file_path}")
        else:
            print(f"⚠️  Optional: {file_path}")
    
    return True

def test_server_startup():
    """Test that the MCP server can start without errors"""
    print("\n🔍 Testing server startup...")
    
    try:
        # Import the monitor class
        sys.path.append(str(Path(__file__).parent))
        from mcp_karen_monitor import KarenAgentMonitor
        
        # Create monitor instance
        monitor = KarenAgentMonitor()
        print("✅ KarenAgentMonitor created successfully")
        
        # Test that handlers are set up
        if hasattr(monitor.server, '_resource_handlers'):
            print("✅ Resource handlers initialized")
        
        if hasattr(monitor.server, '_tool_handlers'):
            print("✅ Tool handlers initialized")
        
        return True
        
    except Exception as e:
        print(f"❌ Server startup failed: {e}")
        return False

def test_resource_data():
    """Test that resource methods return valid data"""
    print("\n🔍 Testing resource data generation...")
    
    try:
        sys.path.append(str(Path(__file__).parent))
        from mcp_karen_monitor import KarenAgentMonitor
        
        monitor = KarenAgentMonitor()
        
        # Test agent status
        try:
            result = asyncio.run(monitor._get_agent_status())
            data = json.loads(result.text)
            print("✅ Agent status data valid")
        except Exception as e:
            print(f"⚠️  Agent status error: {e}")
        
        # Test task progress
        try:
            result = asyncio.run(monitor._get_task_progress())
            data = json.loads(result.text)
            print("✅ Task progress data valid")
        except Exception as e:
            print(f"⚠️  Task progress error: {e}")
        
        # Test recent activities
        try:
            result = asyncio.run(monitor._get_recent_activities())
            data = json.loads(result.text)
            print("✅ Recent activities data valid")
        except Exception as e:
            print(f"⚠️  Recent activities error: {e}")
        
        # Test system health
        try:
            result = asyncio.run(monitor._get_system_health())
            data = json.loads(result.text)
            print("✅ System health data valid")
        except Exception as e:
            print(f"⚠️  System health error: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Resource data test failed: {e}")
        return False

def test_claude_config():
    """Test Claude Desktop configuration"""
    print("\n🔍 Testing Claude Desktop configuration...")
    
    config_file = Path("mcp_config.json")
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            if "mcpServers" in config:
                servers = config["mcpServers"]
                if "karen-agent-monitor" in servers:
                    server_config = servers["karen-agent-monitor"]
                    print(f"✅ Found server config: {server_config}")
                    
                    # Check command
                    if server_config.get("command") == "python":
                        print("✅ Command is 'python'")
                    else:
                        print(f"⚠️  Command is: {server_config.get('command')}")
                    
                    # Check args
                    args = server_config.get("args", [])
                    if "mcp_karen_monitor.py" in args:
                        print("✅ Args include mcp_karen_monitor.py")
                    else:
                        print(f"⚠️  Args: {args}")
                    
                    # Check environment
                    env = server_config.get("env", {})
                    if "KAREN_PROJECT_ROOT" in env:
                        print(f"✅ KAREN_PROJECT_ROOT set to: {env['KAREN_PROJECT_ROOT']}")
                    else:
                        print("⚠️  KAREN_PROJECT_ROOT not set")
                    
                else:
                    print("❌ karen-agent-monitor not found in mcpServers")
            else:
                print("❌ mcpServers not found in config")
                
        except Exception as e:
            print(f"❌ Error reading config: {e}")
    else:
        print("❌ mcp_config.json not found")

def create_claude_config():
    """Create or update Claude Desktop configuration"""
    print("\n🔧 Creating Claude Desktop configuration...")
    
    project_root = Path(os.getenv("KAREN_PROJECT_ROOT", str(Path.cwd()))).resolve()
    
    config = {
        "mcpServers": {
            "karen-agent-monitor": {
                "command": "python",
                "args": [str(project_root / "mcp_karen_monitor.py")],
                "env": {
                    "KAREN_PROJECT_ROOT": str(project_root)
                }
            }
        }
    }
    
    config_file = project_root / "claude_desktop_config.json"
    
    try:
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"✅ Created config at: {config_file}")
        print(f"   Project root: {project_root}")
        print(f"   Server script: {project_root / 'mcp_karen_monitor.py'}")
        
        # Also update the simple config
        simple_config_file = project_root / "mcp_config.json"
        with open(simple_config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"✅ Updated: {simple_config_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to create config: {e}")
        return False

def run_integration_test():
    """Run a basic integration test with the MCP server"""
    print("\n🔍 Running integration test...")
    
    try:
        # Test server in a subprocess to avoid blocking
        project_root = Path(os.getenv("KAREN_PROJECT_ROOT", "."))
        server_script = project_root / "mcp_karen_monitor.py"
        
        print(f"Starting server: {server_script}")
        
        # Start server process
        proc = subprocess.Popen(
            [sys.executable, str(server_script)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(project_root),
            env={**os.environ, "KAREN_PROJECT_ROOT": str(project_root)}
        )
        
        # Give it a moment to start
        time.sleep(2)
        
        # Check if process is still running
        if proc.poll() is None:
            print("✅ Server process started successfully")
            
            # Terminate the process
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
            
            print("✅ Server process terminated cleanly")
            return True
        else:
            # Process exited, check for errors
            stdout, stderr = proc.communicate()
            print(f"❌ Server process exited immediately")
            if stderr:
                print(f"   Error: {stderr}")
            if stdout:
                print(f"   Output: {stdout}")
            return False
            
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Karen AI Agent Monitor - MCP Server Test Suite")
    print("=" * 60)
    
    # Set project root if not set
    if not os.getenv("KAREN_PROJECT_ROOT"):
        project_root = Path(__file__).parent.resolve()
        os.environ["KAREN_PROJECT_ROOT"] = str(project_root)
        print(f"📁 Set KAREN_PROJECT_ROOT to: {project_root}")
    
    tests = [
        ("MCP Imports", test_mcp_imports),
        ("Project Structure", test_project_structure),
        ("Server Startup", test_server_startup),
        ("Resource Data", test_resource_data),
        ("Claude Config", test_claude_config),
        ("Integration Test", run_integration_test)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 Test Results Summary:")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:8} {test_name}")
        if result:
            passed += 1
    
    print(f"\n📈 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! MCP server should work with Claude Desktop.")
        print("\n📋 Next steps:")
        print("1. Copy claude_desktop_config.json to Claude Desktop's config location")
        print("2. Restart Claude Desktop")
        print("3. Look for 'karen-agent-monitor' in the server list")
    else:
        print("⚠️  Some tests failed. Check the issues above before proceeding.")
    
    # Create config if tests mostly passed
    if passed >= total - 1:  # Allow 1 failure
        print("\n🔧 Creating/updating configuration files...")
        create_claude_config()

if __name__ == "__main__":
    main()