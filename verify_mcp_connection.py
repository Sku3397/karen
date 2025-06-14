#!/usr/bin/env python3
"""
Verify MCP server connection returns real Karen data vs fake agents
"""
import asyncio
import json
import sys
from pathlib import Path

def test_local_real_mcp_server():
    """Test the real Karen MCP server locally"""
    try:
        from karen_mcp_server import KarenSystemMonitor
        
        async def test():
            monitor = KarenSystemMonitor()
            status = await monitor.get_system_health_summary()
            
            print("🔍 TESTING REAL KAREN MCP SERVER:")
            print("=" * 50)
            
            # This should return REAL component data
            response_text = str(status)
            print("Real server response:", json.dumps(status, indent=2))
            
            # Check for fake agent indicators (should NOT be present)
            fake_indicators = [
                "Orchestrator", "Memory Engineer", "SMS Engineer", 
                "Phone Engineer", "Test Engineer", "Archaeologist"
            ]
            
            has_fake_data = any(indicator in response_text for indicator in fake_indicators)
            
            if has_fake_data:
                print("❌ ERROR: Real server returning fake agent data!")
                return False
            else:
                print("✅ SUCCESS: Real server returning component data")
                print(f"   Overall Status: {status.get('overall_status', 'unknown')}")
                print(f"   Health: {status.get('health_percentage', 0)}%")
                return True
                
        return asyncio.run(test())
        
    except Exception as e:
        print(f"❌ ERROR testing real MCP server: {e}")
        return False

def test_fake_agent_monitor():
    """Test if the fake agent monitor is active"""
    try:
        from mcp_agent_monitor import KarenAgentMonitor
        
        async def test():
            monitor = KarenAgentMonitor()
            # Try to get agent status (this will return fake agents)
            result = await monitor._get_agent_status()
            
            print("\\n🔍 TESTING FAKE AGENT MONITOR:")
            print("=" * 50)
            
            response_text = result.text
            print("Fake monitor response preview:", response_text[:500] + "...")
            
            # Check for fake agent indicators (SHOULD be present if this is the fake server)
            fake_indicators = [
                "Orchestrator", "Memory Engineer", "SMS Engineer", 
                "Phone Engineer", "Test Engineer", "Archaeologist"
            ]
            
            has_fake_data = any(indicator in response_text for indicator in fake_indicators)
            
            if has_fake_data:
                print("❌ CONFIRMED: This is the FAKE MCP server!")
                print("   Contains fake agents:", [i for i in fake_indicators if i in response_text])
                return True
            else:
                print("✅ This monitor doesn't contain fake agent data")
                return False
                
        return asyncio.run(test())
        
    except Exception as e:
        print(f"❌ ERROR testing fake agent monitor: {e}")
        return False

def check_autonomous_state_file():
    """Check what's in the autonomous_state.json file"""
    state_file = Path("autonomous_state.json")
    
    print("\\n🔍 CHECKING AUTONOMOUS STATE FILE:")
    print("=" * 50)
    
    if state_file.exists():
        with open(state_file, 'r') as f:
            state = json.load(f)
        
        print(f"File exists with {len(state.get('agents', []))} agents:")
        
        for agent in state.get('agents', []):
            agent_name = agent.get('name', 'unknown')
            print(f"   - {agent_name}")
            
            # Check if this is a fake agent
            fake_indicators = [
                "orchestrator", "memory_engineer", "sms_engineer", 
                "phone_engineer", "test_engineer", "archaeologist"
            ]
            
            if any(indicator in agent_name.lower() for indicator in fake_indicators):
                print(f"     ❌ FAKE AGENT DETECTED: {agent_name}")
        
        return state
    else:
        print("   No autonomous_state.json file found")
        return None

def main():
    """Main verification function"""
    print("🚨 KAREN MCP SERVER VERIFICATION")
    print("=" * 60)
    
    # Check what's in the state file (source of fake data)
    state = check_autonomous_state_file()
    
    # Test the real Karen MCP server
    real_server_ok = test_local_real_mcp_server()
    
    # Test if fake agent monitor is accessible
    fake_server_active = test_fake_agent_monitor()
    
    print("\\n📊 VERIFICATION RESULTS:")
    print("=" * 50)
    
    if fake_server_active:
        print("❌ PROBLEM: Fake MCP server (mcp_agent_monitor.py) is accessible")
        print("   Action needed: Disable/remove fake server")
    
    if real_server_ok:
        print("✅ GOOD: Real Karen MCP server is working")
    else:
        print("❌ PROBLEM: Real Karen MCP server has issues")
    
    print("\\n🎯 RECOMMENDATIONS:")
    if fake_server_active:
        print("1. 🚨 URGENT: Rename/disable mcp_agent_monitor.py")
        print("2. 🔧 Update MCP configuration to use karen_mcp_server.py")
        print("3. 🧹 Clean up autonomous_state.json fake agent data")
    
    if real_server_ok:
        print("4. ✅ Real server is ready - just need to redirect connections")
    
    return not fake_server_active and real_server_ok

if __name__ == "__main__":
    success = main()
    if not success:
        print("\\n🚨 ACTION REQUIRED: Fix MCP server configuration!")
        sys.exit(1)
    else:
        print("\\n🎉 SUCCESS: MCP server verification complete!") 