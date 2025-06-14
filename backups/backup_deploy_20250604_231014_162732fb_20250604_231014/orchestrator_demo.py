#!/usr/bin/env python3
"""
Orchestrator Agent Demonstration
Shows how to use the AgentCommunication system for coordination
"""
import time
import logging
from datetime import datetime

# Import the orchestrator
from src.orchestrator import get_orchestrator_instance
from src.agent_communication import AgentCommunication

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Demonstrate the Orchestrator Agent coordination capabilities"""
    print("🎯 Orchestrator Agent Demonstration")
    print("=" * 50)
    
    # Initialize orchestrator
    print("\n1. Initializing Orchestrator...")
    orchestrator = get_orchestrator_instance()
    print(f"✅ Orchestrator initialized with communication system")
    
    # Check agent health
    print("\n2. Checking agent health status...")
    statuses = orchestrator.check_all_agent_health()
    
    print(f"Found {len(statuses)} agents:")
    for agent, status in statuses.items():
        print(f"  - {agent}: {status.get('status', 'unknown')}")
    
    # Monitor all agent statuses every 5 minutes (demonstration)
    print("\n3. Agent Status Monitoring Example:")
    print("Checking for agents in error state...")
    
    for agent, status in statuses.items():
        if status.get('status') == 'error':
            print(f"🚨 Agent '{agent}' is in error state")
            print(f"   Error details: {status.get('details', 'No details')}")
            
            # Handle agent failure
            orchestrator.comm.send_message(agent, 'restart_request', {
                'reason': 'error_detected',
                'previous_error': status.get('details'),
                'orchestrator_initiated': True
            })
            print(f"   Sent restart request to '{agent}'")
    
    # Coordinate workflow phases
    print("\n4. Workflow Coordination Example:")
    print("Starting Phase 1: Analysis...")
    
    # Start analysis phase
    orchestrator.comm.send_message('archaeologist', 'start_analysis', {
        'focus_areas': ['email_flow', 'celery_patterns', 'api_integrations'],
        'orchestrator_initiated': True,
        'timestamp': datetime.now().isoformat()
    })
    print("✅ Sent analysis task to archaeologist")
    
    # Wait for completion (simplified for demo)
    print("⏳ Waiting for archaeologist to complete analysis...")
    max_wait = 60  # 1 minute for demo
    waited = 0
    
    while waited < max_wait:
        archaeologist_status = orchestrator.comm.get_all_agent_statuses().get('archaeologist', {})
        if archaeologist_status.get('status') == 'completed':
            print("✅ Archaeologist completed analysis!")
            break
        time.sleep(5)
        waited += 5
        print(f"   Still waiting... ({waited}s)")
    else:
        print("⏰ Analysis taking longer than expected (this is normal)")
    
    # Start development phase
    print("\nStarting Phase 2: Development...")
    
    engineers = ['sms_engineer', 'phone_engineer', 'memory_engineer']
    for engineer in engineers:
        orchestrator.comm.send_message(engineer, 'start_development', {
            'knowledge_base': '/autonomous-agents/shared-knowledge/',
            'preserve_features': ['email', 'calendar'],
            'templates_path': '/autonomous-agents/shared-knowledge/templates/',
            'orchestrator_initiated': True
        })
        print(f"✅ Sent development task to '{engineer}'")
    
    # Handle inter-agent dependencies
    print("\n5. Inter-Agent Communication Example:")
    print("SMS engineer needs info from archaeologist...")
    
    orchestrator.coordinate_inter_agent_request(
        requesting_agent='sms_engineer',
        target_agent='archaeologist', 
        info_type='celery_task_patterns',
        params={'format': 'json', 'include_examples': True}
    )
    print("✅ Coordinated information request between agents")
    
    # Get system overview
    print("\n6. System Overview:")
    overview = orchestrator.get_system_overview()
    
    print(f"Orchestrator Status: {overview['orchestrator_status']}")
    print(f"Registered Agents: {len(overview['registered_agents'])}")
    print(f"Available Workflows: {overview['available_workflows']}")
    print(f"Timestamp: {overview['timestamp']}")
    
    print("\nAgent Status Summary:")
    for agent, status in overview['agent_statuses'].items():
        status_emoji = {
            'idle': '😴',
            'busy': '🔄', 
            'completed': '✅',
            'error': '❌',
            'analyzing': '🔍',
            'processing_sms': '📱',
            'processing_voice': '🎤',
            'maintenance': '🔧',
            'testing': '🧪'
        }.get(status.get('status'), '❓')
        
        print(f"  {status_emoji} {agent}: {status.get('status', 'unknown')}")
        if details := status.get('details'):
            if phase := details.get('phase'):
                print(f"      Phase: {phase}")
            if progress := details.get('progress'):
                print(f"      Progress: {progress}%")
    
    # Execute a full workflow
    print("\n7. Full Workflow Execution:")
    print("Executing 'full_system_scan' workflow...")
    
    workflow_result = orchestrator.execute_workflow('full_system_scan', {
        'focus_areas': ['email_flow', 'celery_patterns'],
        'preserve_features': ['email', 'calendar'],
        'test_suites': ['unit', 'integration']
    })
    
    if workflow_result.get('success'):
        print("✅ Workflow completed successfully!")
    else:
        print(f"❌ Workflow failed: {workflow_result.get('error')}")
    
    print(f"Workflow duration: {workflow_result.get('started_at')} to {workflow_result.get('completed_at')}")
    
    print("\n🎯 Orchestrator demonstration complete!")
    print("\nKey Features Demonstrated:")
    print("✅ Agent health monitoring")
    print("✅ Multi-phase workflow coordination") 
    print("✅ Inter-agent communication")
    print("✅ Error handling and recovery")
    print("✅ System overview and status tracking")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Demonstration interrupted by user")
    except Exception as e:
        logger.error(f"Demonstration failed: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")