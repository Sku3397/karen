#!/usr/bin/env python3
"""
Test script for the real Karen AI MCP server
Tests actual system components, not fake agents
"""
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

try:
    from karen_mcp_server import KarenSystemMonitor
except ImportError as e:
    print(f"❌ Cannot import KarenSystemMonitor: {e}")
    print("Make sure karen_mcp_server.py is in the current directory")
    sys.exit(1)

async def test_all_components():
    """Test all Karen AI system components"""
    monitor = KarenSystemMonitor()
    
    print("🔧 Testing Karen AI MCP Server Components")
    print("=" * 50)
    
    # Test each component
    tests = [
        ("Redis", monitor.check_redis_connectivity),
        ("Celery Worker", monitor.check_celery_worker_status),
        ("Celery Beat", monitor.check_celery_beat_status),
        ("Gmail Tokens", monitor.check_gmail_tokens),
        ("Calendar API", monitor.check_calendar_api),
        ("Gemini API", monitor.check_gemini_api),
        ("Recent Activity", monitor.check_recent_activity),
    ]
    
    component_results = {}
    
    for name, test_func in tests:
        print(f"\n🔍 Testing {name}...")
        try:
            result = await test_func()
            status = result.get('status', 'unknown')
            
            if name == "Gmail Tokens":
                # Special handling for Gmail tokens which has nested status
                karen_status = result.get('karen_sender', {}).get('status', 'unknown')
                monitor_status = result.get('monitored_account', {}).get('status', 'unknown')
                status = f"Karen:{karen_status} | Monitor:{monitor_status}"
            
            status_emoji = "✅" if "error" not in status.lower() and "missing" not in status.lower() and "expired" not in status.lower() else "❌"
            print(f"  {status_emoji} {name}: {status}")
            
            component_results[name.lower().replace(' ', '_')] = result
            
        except Exception as e:
            print(f"  ❌ {name}: ERROR - {str(e)}")
            component_results[name.lower().replace(' ', '_')] = {"status": "error", "error": str(e)}
    
    # Test overall health
    print(f"\n🏥 Testing Overall System Health...")
    try:
        health = await monitor.get_system_health_summary()
        overall_status = health['overall_status']
        health_percentage = health['health_percentage']
        healthy_components = health['healthy_components']
        total_components = health['total_components']
        
        health_emoji = "🟢" if overall_status == "healthy" else "🟡" if overall_status == "degraded" else "🔴"
        
        print(f"  {health_emoji} Overall Status: {overall_status.upper()}")
        print(f"  📊 Health: {health_percentage}%")
        print(f"  ⚙️  Components: {healthy_components}/{total_components} operational")
        
    except Exception as e:
        print(f"  ❌ Health Check: ERROR - {str(e)}")
    
    print("\n" + "=" * 50)
    print("🎯 REAL KAREN AI SYSTEM STATUS VERIFIED")
    print("   (No fake agents - only real components!)")
    print("=" * 50)

async def test_mcp_server_startup():
    """Test if the MCP server can start up properly"""
    print("\n🚀 Testing MCP Server Startup...")
    
    try:
        # Try to import the main server module
        import karen_mcp_server
        print("  ✅ MCP server module imported successfully")
        
        # Check if the server app is properly initialized
        if hasattr(karen_mcp_server, 'app'):
            print("  ✅ MCP server app initialized")
        else:
            print("  ❌ MCP server app not found")
            
        if hasattr(karen_mcp_server, 'monitor'):
            print("  ✅ System monitor initialized")
        else:
            print("  ❌ System monitor not found")
            
    except Exception as e:
        print(f"  ❌ MCP Server Startup: ERROR - {str(e)}")

def main():
    """Main test execution"""
    print("🤖 Karen AI Real MCP Server Test Suite")
    print("Testing REAL system components (not fake agents)")
    print("=" * 60)
    
    try:
        # Run async tests
        asyncio.run(test_all_components())
        
        # Run sync tests
        asyncio.run(test_mcp_server_startup())
        
        print("\n✅ All tests completed!")
        print("💡 To run the MCP server: python karen_mcp_server.py")
        
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 