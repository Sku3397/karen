#!/usr/bin/env python3
"""
Direct MCP Server Tester
Tests the Karen MCP servers to identify specific errors
"""

import os
import sys
import json
import asyncio
import subprocess
import tempfile
from pathlib import Path

def test_mcp_imports():
    """Test MCP SDK imports"""
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
        print("   Install with: pip install 'mcp[cli]'")
        return False

def test_project_files():
    """Test that required project files exist"""
    print("\n🔍 Testing project files...")
    
    project_root = Path(os.getenv("KAREN_PROJECT_ROOT", "."))
    print(f"Project root: {project_root}")
    
    required_files = [
        "autonomous_state.json",
        "tasks/eigencode_assigned_tasks.json",
        "agent_activities.jsonl"
    ]
    
    missing_files = []
    for file_path in required_files:
        full_path = project_root / file_path
        if full_path.exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ Missing: {file_path}")
            missing_files.append(file_path)
    
    return len(missing_files) == 0

def test_simple_server():
    """Test the simple MCP test server"""
    print("\n🔍 Testing simple MCP server...")
    
    try:
        # Import the simple server
        sys.path.insert(0, str(Path.cwd()))
        from simple_mcp_test import app
        print("✅ Simple server imports successfully")
        
        # Test resource listing
        async def test_resources():
            try:
                resources = await app._resource_handlers['']()
                print(f"✅ Simple server resources: {len(resources)} available")
                for resource in resources:
                    print(f"   - {resource.uri}: {resource.name}")
                return True
            except Exception as e:
                print(f"❌ Simple server resource error: {e}")
                return False
        
        # Run the async test
        result = asyncio.run(test_resources())
        return result
        
    except Exception as e:
        print(f"❌ Simple server failed: {e}")
        return False

def test_karen_server():
    """Test the full Karen MCP server"""
    print("\n🔍 Testing Karen MCP server...")
    
    try:
        # Set up environment
        project_root = Path.cwd()
        os.environ["KAREN_PROJECT_ROOT"] = str(project_root)
        
        # Import Karen server
        sys.path.insert(0, str(project_root))
        from mcp_karen_monitor import KarenAgentMonitor
        print("✅ Karen server imports successfully")
        
        # Create monitor instance
        monitor = KarenAgentMonitor()
        print(f"✅ Karen monitor created")
        print(f"   Project root: {monitor.project_root}")
        
        # Test resource methods
        async def test_karen_resources():
            try:
                # Test agent status
                status_result = await monitor._get_agent_status()
                print("✅ Agent status method works")
                
                # Test task progress
                progress_result = await monitor._get_task_progress()
                print("✅ Task progress method works")
                
                # Test recent activities
                activities_result = await monitor._get_recent_activities()
                print("✅ Recent activities method works")
                
                return True
                
            except Exception as e:
                print(f"❌ Karen server method error: {e}")
                import traceback
                traceback.print_exc()
                return False
        
        # Run the async test
        result = asyncio.run(test_karen_resources())
        return result
        
    except Exception as e:
        print(f"❌ Karen server failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_server_startup():
    """Test that servers can actually start up"""
    print("\n🔍 Testing server startup...")
    
    project_root = Path.cwd()
    
    # Test simple server startup
    print("Testing simple_mcp_test.py startup...")
    try:
        proc = subprocess.Popen(
            [sys.executable, "simple_mcp_test.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(project_root),
            env={**os.environ, "KAREN_PROJECT_ROOT": str(project_root)}
        )
        
        # Give it a moment to start
        import time
        time.sleep(2)
        
        if proc.poll() is None:
            print("✅ Simple server started successfully")
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
            startup_simple = True
        else:
            stdout, stderr = proc.communicate()
            print("❌ Simple server exited immediately")
            if stderr:
                print(f"   Error: {stderr}")
            startup_simple = False
            
    except Exception as e:
        print(f"❌ Simple server startup failed: {e}")
        startup_simple = False
    
    # Test Karen server startup
    print("Testing mcp_karen_monitor.py startup...")
    try:
        proc = subprocess.Popen(
            [sys.executable, "mcp_karen_monitor.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(project_root),
            env={**os.environ, "KAREN_PROJECT_ROOT": str(project_root)}
        )
        
        # Give it a moment to start
        time.sleep(2)
        
        if proc.poll() is None:
            print("✅ Karen server started successfully")
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
            startup_karen = True
        else:
            stdout, stderr = proc.communicate()
            print("❌ Karen server exited immediately")
            if stderr:
                print(f"   Error: {stderr}")
            startup_karen = False
            
    except Exception as e:
        print(f"❌ Karen server startup failed: {e}")
        startup_karen = False
    
    return startup_simple and startup_karen

def main():
    """Run all MCP server tests"""
    print("🧪 Karen AI MCP Server Test Suite")
    print("=" * 50)
    
    # Set project root
    project_root = Path(__file__).parent.resolve()
    os.environ["KAREN_PROJECT_ROOT"] = str(project_root)
    print(f"📁 Project root: {project_root}")
    
    # Run tests
    tests = [
        ("MCP SDK Imports", test_mcp_imports),
        ("Project Files", test_project_files),
        ("Simple Server", test_simple_server),
        ("Karen Server", test_karen_server),
        ("Server Startup", test_server_startup)
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
    print(f"\n{'='*50}")
    print("📊 Test Results Summary")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:8} {test_name}")
        if result:
            passed += 1
    
    print(f"\n📈 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! MCP servers should work.")
    elif passed >= total - 1:
        print("⚠️  Most tests passed. Minor issues may exist.")
    else:
        print("❌ Multiple failures. MCP servers need fixes.")
    
    # Recommendations
    print("\n💡 Recommendations:")
    if passed < total:
        print("1. Fix the failing tests above")
        print("2. Check Claude Desktop logs for specific errors")
        print("3. Ensure MCP SDK is installed: pip install 'mcp[cli]'")
        print("4. Verify all project files exist")
    
    print("5. Test in Claude: 'Can you access the karen-test server?'")

if __name__ == "__main__":
    main()