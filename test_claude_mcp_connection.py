#!/usr/bin/env python3
"""
Test Claude Desktop MCP connection to real Karen server
"""
import subprocess
import sys
import time
import json
import os
from pathlib import Path

def test_karen_mcp_server():
    """Test if Karen MCP server is running and accessible"""
    try:
        # Test if Karen MCP server process is running
        result = subprocess.run(
            ['tasklist', '/FI', 'IMAGENAME eq python.exe'],
            capture_output=True,
            text=True
        )
        
        karen_processes = [
            line for line in result.stdout.split('\n')
            if 'karen_mcp_server' in line.lower()
        ]
        
        if karen_processes:
            print("✅ Karen MCP server process found:")
            for process in karen_processes:
                print(f"   {process.strip()}")
        else:
            print("❌ Karen MCP server process not found")
            print("   Start it with: python karen_mcp_server.py")
            return False
        
        # Test if server responds
        try:
            from karen_mcp_server import KarenSystemMonitor
            import asyncio
            
            async def test_response():
                monitor = KarenSystemMonitor()
                status = await monitor.get_system_health_summary()
                return status
            
            status = asyncio.run(test_response())
            
            print("✅ Karen MCP server responding:")
            print(f"   Overall Status: {status.get('overall_status', 'unknown')}")
            print(f"   Health: {status.get('health_percentage', 0)}%")
            print(f"   Components: {status.get('healthy_components', 0)}/{status.get('total_components', 0)}")
            
            return True
        except ImportError:
            print("⚠️  Cannot import karen_mcp_server module (but process is running)")
            return True  # Process exists, assume it's working
            
    except Exception as e:
        print(f"❌ Error testing Karen MCP server: {e}")
        return False

def check_claude_mcp_config():
    """Check Claude Desktop MCP configuration"""
    config_paths = [
        Path(os.environ.get('USERPROFILE', '')) / '.claude' / 'claude_desktop_config.json',
        Path(os.environ.get('APPDATA', '')) / 'Claude' / 'mcp.json',
        Path(os.environ.get('LOCALAPPDATA', '')) / 'Claude' / 'mcp.json',
        Path(os.environ.get('APPDATA', '')) / 'Anthropic' / 'Claude' / 'mcp.json',
    ]
    
    found_configs = []
    for config_path in config_paths:
        if config_path.exists():
            try:
                with open(config_path) as f:
                    config = json.load(f)
                found_configs.append({
                    'path': str(config_path),
                    'config': config
                })
                print(f"✅ Found Claude config: {config_path}")
                
                servers = config.get('mcpServers', {})
                if 'karen-tools' in servers:
                    print("   ✅ karen-tools server configured")
                    server_config = servers['karen-tools']
                    print(f"      Command: {server_config.get('command', 'Unknown')}")
                    print(f"      Args: {server_config.get('args', [])}")
                    print(f"      Working Dir: {server_config.get('cwd', 'Unknown')}")
                    
                    # Check if it's pointing to the real server
                    args = server_config.get('args', [])
                    if 'karen_mcp_server.py' in args:
                        print("   🎯 POINTS TO REAL SERVER: karen_mcp_server.py")
                    elif 'karen_monitor.py' in str(args):
                        print("   ⚠️  POINTS TO FAKE SERVER: karen_monitor.py")
                    else:
                        print(f"   ❓ Unknown server: {args}")
                        
                elif 'karen-agent-monitor' in servers:
                    print("   ❌ OLD fake server 'karen-agent-monitor' configured")
                    server_config = servers['karen-agent-monitor']
                    print(f"      Args: {server_config.get('args', [])}")
                else:
                    print("   ❌ karen-tools server NOT configured")
                    print(f"   Available servers: {list(servers.keys())}")
                    
            except Exception as e:
                print(f"❌ Error reading {config_path}: {e}")
    
    if not found_configs:
        print("❌ No Claude Desktop MCP configuration found")
        print("   Expected locations:")
        for path in config_paths:
            print(f"     {path}")
    
    return found_configs

def check_fake_data_sources():
    """Check for fake data sources that might interfere"""
    fake_sources = []
    
    # Check for autonomous_state.json (fake agents)
    autonomous_file = Path("autonomous_state.json")
    if autonomous_file.exists():
        try:
            with open(autonomous_file) as f:
                data = json.load(f)
            agents = data.get('agents', [])
            fake_agent_names = [agent.get('name', '') for agent in agents]
            if any(name in ['orchestrator', 'sms_engineer', 'memory_engineer'] for name in fake_agent_names):
                fake_sources.append({
                    'file': str(autonomous_file),
                    'type': 'fake_agents',
                    'agents': fake_agent_names
                })
        except:
            pass
    
    # Check for disabled fake servers
    fake_servers = [
        "mcp_with_tools.py.DISABLED_FAKE_SERVER",
        "mcp_agent_monitor.py.DISABLED"
    ]
    
    for server in fake_servers:
        if Path(server).exists():
            fake_sources.append({
                'file': server,
                'type': 'disabled_fake_server',
                'status': 'safely_disabled'
            })
    
    if fake_sources:
        print("📋 Fake Data Sources Found:")
        for source in fake_sources:
            if source['type'] == 'fake_agents':
                print(f"   ⚠️  {source['file']}: Contains fake agents {source['agents']}")
            elif source['type'] == 'disabled_fake_server':
                print(f"   ✅ {source['file']}: {source['status']}")
    else:
        print("✅ No fake data sources detected")
    
    return fake_sources

def test_mcp_server_connectivity():
    """Test direct connectivity to Karen MCP server"""
    print("🔧 Testing direct MCP server connectivity...")
    
    try:
        # Try to start the server briefly to test it works
        result = subprocess.run(
            [sys.executable, 'karen_mcp_server.py'],
            capture_output=True,
            text=True,
            timeout=5,  # Brief test
            cwd=Path.cwd()
        )
        
        if result.returncode == 0:
            print("✅ Karen MCP server starts successfully")
            return True
        else:
            print("❌ Karen MCP server failed to start:")
            print(f"   Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("✅ Karen MCP server is running (timed out as expected)")
        return True
    except Exception as e:
        print(f"❌ Error testing MCP server: {e}")
        return False

if __name__ == "__main__":
    print("🔍 TESTING CLAUDE DESKTOP MCP CONNECTION")
    print("=" * 50)
    
    print("\n1. Testing Karen MCP Server...")
    server_ok = test_karen_mcp_server()
    
    print("\n2. Checking Claude Desktop MCP Config...")
    configs = check_claude_mcp_config()
    
    print("\n3. Checking for Fake Data Sources...")
    fake_sources = check_fake_data_sources()
    
    print("\n4. Testing MCP Server Connectivity...")
    connectivity_ok = test_mcp_server_connectivity()
    
    print("\n" + "=" * 50)
    print("🎯 FINAL ASSESSMENT:")
    
    # Determine if Claude Desktop is configured correctly
    claude_configured_correctly = False
    for config in configs:
        servers = config['config'].get('mcpServers', {})
        if 'karen-tools' in servers:
            args = servers['karen-tools'].get('args', [])
            if 'karen_mcp_server.py' in args:
                claude_configured_correctly = True
                break
    
    if server_ok and claude_configured_correctly and connectivity_ok:
        print("🎉 SUCCESS: Claude Desktop should now connect to REAL Karen data!")
        print("   ✅ Karen MCP server running")
        print("   ✅ Claude Desktop configured correctly") 
        print("   ✅ Points to real karen_mcp_server.py")
        print("\n🚀 NEXT STEPS:")
        print("   1. Restart Claude Desktop")
        print("   2. Test MCP functions - should return Redis/Celery/Gmail data")
        print("   3. NO MORE fake 'Orchestrator'/'Memory Engineer' responses!")
        
    elif server_ok and connectivity_ok:
        print("⚠️  Karen server OK, but need to fix Claude Desktop config")
        print("   ✅ Karen MCP server running")
        print("   ❌ Claude Desktop config needs updating")
        
    elif claude_configured_correctly:
        print("⚠️  Claude config OK, but Karen server needs to be started")
        print("   ❌ Karen MCP server not running")
        print("   ✅ Claude Desktop configured correctly")
        print("   💡 Run: python karen_mcp_server.py")
        
    else:
        print("❌ Both Karen server and Claude config need attention")
        print("   📝 See detailed results above")
        
    print(f"\n📊 Fake Sources: {len(fake_sources)} detected")
    print(f"📁 Config Files: {len(configs)} found") 