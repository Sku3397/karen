#!/usr/bin/env python3
"""
Simple Learning System Integration Example
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

def demonstrate_integration():
    """Show how learning system integrates with agent communication"""
    print("🔗 Learning System Integration Example")
    print("=" * 50)
    
    try:
        from src.learning_system import get_learning_system_instance
        from src.agent_communication import AgentCommunication
        
        # Initialize both systems
        learning_system = get_learning_system_instance()
        agent_comm = AgentCommunication("learning_integration_agent")
        
        print("✅ Both systems initialized successfully")
        
        # Simulate a task completion
        learning_system.analyze_task_completion(
            task_id="integration_test_001",
            agent="sms_engineer", 
            success=True,
            completion_time=45.2,
            task_data={
                'task_type': 'sms_response',
                'required_skills': ['SMS_MANAGEMENT'],
                'priority': 'medium'
            }
        )
        
        # Get insights
        insights = learning_system.get_learning_insights()
        workload = agent_comm.get_agent_workload_report()
        
        print(f"\n📊 Learning System Status:")
        print(f"   System Health: {insights['system_health']['status']}")
        print(f"   Patterns Learned: {insights['learning_progress']['total_patterns_learned']}")
        
        print(f"\n🔧 Agent Communication Status:")
        print(f"   Active Agents: {len(workload['agents'])}")
        print(f"   System Load: {workload['system_load_percent']:.1f}%")
        
        # Generate improvements
        improvements = learning_system.generate_architecture_improvements()
        print(f"\n💡 Architecture Improvements: {len(improvements)}")
        
        for improvement in improvements[:2]:
            print(f"   • {improvement.title}")
            print(f"     Priority: {improvement.priority}")
        
        print("\n✅ Integration demonstration complete!")
        
    except Exception as e:
        print(f"❌ Error during integration: {e}")

if __name__ == "__main__":
    demonstrate_integration() 