#!/usr/bin/env python3
"""
Test script to verify AgentCommunication system is working
"""
import time
import logging
from datetime import datetime

from src.agent_communication import AgentCommunication

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_basic_communication():
    """Test basic agent communication functionality"""
    print("🧪 Testing AgentCommunication System")
    print("=" * 40)
    
    try:
        # Initialize communication for orchestrator
        print("\n1. Initializing orchestrator communication...")
        orchestrator_comm = AgentCommunication('orchestrator')
        print("✅ Orchestrator communication initialized")
        
        # Update orchestrator status
        print("\n2. Updating orchestrator status...")
        orchestrator_comm.update_status('active', 100, {
            'phase': 'monitoring',
            'last_health_check': datetime.now().isoformat()
        })
        print("✅ Status updated")
        
        # Send a test message
        print("\n3. Sending test message to archaeologist...")
        orchestrator_comm.send_message('archaeologist', 'test_message', {
            'content': 'Hello from orchestrator!',
            'timestamp': datetime.now().isoformat(),
            'test': True
        })
        print("✅ Message sent")
        
        # Check all agent statuses
        print("\n4. Checking all agent statuses...")
        statuses = orchestrator_comm.get_all_agent_statuses()
        
        if statuses:
            print(f"Found {len(statuses)} agent(s):")
            for agent, status in statuses.items():
                print(f"  - {agent}: {status.get('status', 'unknown')} "
                      f"({status.get('timestamp', 'no timestamp')})")
        else:
            print("No agent statuses found")
        
        # Share some knowledge
        print("\n5. Sharing knowledge...")
        orchestrator_comm.share_knowledge('system_test', {
            'test_result': 'success',
            'components_tested': ['redis', 'filesystem', 'status_updates'],
            'timestamp': datetime.now().isoformat()
        })
        print("✅ Knowledge shared")
        
        # Read any pending messages
        print("\n6. Reading pending messages...")
        messages = orchestrator_comm.read_messages()
        
        if messages:
            print(f"Found {len(messages)} message(s):")
            for msg in messages:
                print(f"  - From: {msg.get('from', 'unknown')}")
                print(f"    Type: {msg.get('type', 'unknown')}")
                print(f"    Content: {msg.get('content', {})}")
        else:
            print("No messages found")
        
        print("\n✅ Communication system test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Communication test failed: {e}")
        logger.error("Communication test failed", exc_info=True)
        return False

def test_multi_agent_simulation():
    """Simulate multiple agents communicating"""
    print("\n🎭 Multi-Agent Communication Simulation")
    print("=" * 40)
    
    try:
        # Create multiple agent communications
        agents = {}
        agent_names = ['archaeologist', 'sms_engineer', 'phone_engineer']
        
        for name in agent_names:
            print(f"Initializing {name}...")
            agents[name] = AgentCommunication(name)
            
            # Set initial status
            agents[name].update_status('idle', 0, {
                'initialized_at': datetime.now().isoformat(),
                'capabilities': f"{name}_capabilities"
            })
        
        print("✅ All agents initialized")
        
        # Simulate archaeologist starting analysis
        print("\nSimulating analysis phase...")
        agents['archaeologist'].update_status('analyzing', 25, {
            'phase': 'scanning_codebase',
            'files_processed': 15
        })
        
        # Archaeologist sends findings to engineers
        for engineer in ['sms_engineer', 'phone_engineer']:
            agents['archaeologist'].send_message(engineer, 'analysis_findings', {
                'patterns_found': ['error_handling', 'async_patterns'],
                'templates_available': True,
                'knowledge_base_updated': True
            })
        
        print("✅ Analysis findings shared")
        
        # Engineers respond
        time.sleep(1)  # Brief delay
        
        agents['sms_engineer'].update_status('developing', 50, {
            'phase': 'implementing_sms_handler',
            'using_patterns': True
        })
        
        agents['phone_engineer'].update_status('developing', 30, {
            'phase': 'implementing_voice_handler', 
            'using_patterns': True
        })
        
        # Check final status
        print("\nFinal agent statuses:")
        for name in agent_names:
            statuses = agents[name].get_all_agent_statuses()
            status = statuses.get(name, {})
            print(f"  {name}: {status.get('status', 'unknown')} "
                  f"({status.get('progress', 0)}%)")
        
        print("\n✅ Multi-agent simulation completed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Multi-agent simulation failed: {e}")
        logger.error("Multi-agent simulation failed", exc_info=True)
        return False

if __name__ == "__main__":
    print("🚀 Starting AgentCommunication Tests")
    
    # Run basic communication test
    basic_test_result = test_basic_communication()
    
    # Run multi-agent simulation
    if basic_test_result:
        multi_agent_result = test_multi_agent_simulation()
    else:
        print("⏭️  Skipping multi-agent test due to basic test failure")
        multi_agent_result = False
    
    # Summary
    print("\n📊 Test Results Summary:")
    print(f"Basic Communication: {'✅ PASS' if basic_test_result else '❌ FAIL'}")
    print(f"Multi-Agent Simulation: {'✅ PASS' if multi_agent_result else '❌ FAIL'}")
    
    if basic_test_result and multi_agent_result:
        print("\n🎉 All tests passed! Communication system is ready.")
    else:
        print("\n⚠️  Some tests failed. Check logs for details.")