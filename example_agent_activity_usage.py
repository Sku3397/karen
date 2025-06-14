#!/usr/bin/env python3
"""
Example usage of AgentActivityLogger in Karen's agent system.
This demonstrates how to use the logger in your agent code.
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.agent_activity_logger import AgentActivityLogger

def example_sms_engineer_usage():
    """Example of how the SMS Engineer would use the activity logger."""
    print("=== SMS Engineer Agent Activity Logging Example ===")
    
    # Initialize logger (this would be done in the agent's __init__)
    logger = AgentActivityLogger()
    
    # Log initialization
    logger.log_activity(
        agent_name="sms_engineer",
        activity_type="initialization",
        details={
            "twilio_configured": True,
            "phone_number": "+1234567890",
            "llm_enabled": True,
            "timestamp": datetime.now().isoformat()
        }
    )
    print("✓ Logged SMS Engineer initialization")
    
    # Log SMS processing
    logger.log_activity(
        agent_name="sms_engineer",
        activity_type="sms_processing",
        details={
            "messages_processed": 5,
            "successful_responses": 4,
            "failed_responses": 1,
            "average_response_time": 1.2,
            "emergency_messages": 0
        }
    )
    print("✓ Logged SMS processing batch")
    
    # Log task completion
    logger.log_task_completion(
        agent_name="sms_engineer",
        task_id="sms_integrate_nlp",
        success=True,
        duration_seconds=45.6,
        details={
            "files_modified": ["src/sms_config.py", "src/sms_integration.py"],
            "tests_run": ["test_sms_integration.py"],
            "accuracy_improvement": "12%"
        }
    )
    print("✓ Logged task completion")
    
    # Log performance metric
    logger.log_performance_metric(
        agent_name="sms_engineer",
        metric_name="response_accuracy",
        metric_value=0.89,
        context={
            "measurement_period": "last_24_hours",
            "total_messages": 156,
            "model_version": "gemini-1.5"
        }
    )
    print("✓ Logged performance metric")

def example_memory_engineer_usage():
    """Example of how the Memory Engineer would use the activity logger."""
    print("\n=== Memory Engineer Agent Activity Logging Example ===")
    
    logger = AgentActivityLogger()
    
    # Log memory system enhancement
    logger.log_activity(
        agent_name="memory_engineer",
        activity_type="code_enhancement",
        details={
            "files_modified": [
                "src/memory_embeddings_manager.py",
                "src/intelligent_memory_system.py"
            ],
            "description": "Enhanced cross-medium memory linking with vector embeddings",
            "tests_run": ["test_memory_cross_medium.py"],
            "results": {
                "success": True,
                "memory_accuracy": "94%",
                "link_success_rate": "87%"
            }
        }
    )
    print("✓ Logged memory system enhancement")
    
    # Log memory pattern discovery
    logger.log_activity(
        agent_name="memory_engineer", 
        activity_type="pattern_discovery",
        details={
            "pattern_type": "conversation_context",
            "medium": "email_to_sms",
            "confidence": 0.92,
            "customer_id": "customer_456",
            "context_preserved": True
        }
    )
    print("✓ Logged pattern discovery")

def example_orchestrator_usage():
    """Example of how the Orchestrator would use the activity logger."""
    print("\n=== Orchestrator Agent Activity Logging Example ===")
    
    logger = AgentActivityLogger()
    
    # Log workflow coordination
    logger.log_activity(
        agent_name="orchestrator",
        activity_type="workflow_coordination",
        details={
            "phase": "development_phase",
            "active_agents": ["sms_engineer", "memory_engineer", "test_engineer"],
            "tasks_assigned": 8,
            "tasks_completed": 6,
            "tasks_in_progress": 2,
            "estimated_completion": "2 hours"
        }
    )
    print("✓ Logged workflow coordination")
    
    # Log agent health monitoring
    logger.log_activity(
        agent_name="orchestrator",
        activity_type="health_monitoring",
        details={
            "agents_monitored": 5,
            "healthy_agents": 4,
            "degraded_agents": 1,
            "failed_agents": 0,
            "degraded_agent_details": {
                "agent": "phone_engineer",
                "issue": "high_latency",
                "action": "performance_optimization_requested"
            }
        }
    )
    print("✓ Logged health monitoring")

def view_logged_activities():
    """Show how to retrieve and view logged activities."""
    print("\n=== Viewing Logged Activities ===")
    
    logger = AgentActivityLogger()
    
    # Get all recent activities for SMS engineer
    sms_activities = logger.get_agent_activities("sms_engineer", limit=5)
    print(f"SMS Engineer has {len(sms_activities)} recent activities:")
    for activity in sms_activities[-2:]:  # Show last 2
        print(f"  - {activity['activity_type']}: {activity['timestamp']}")
    
    # Get only task completions
    task_completions = logger.get_agent_activities(
        "sms_engineer", 
        activity_type="task_completion"
    )
    print(f"SMS Engineer has {len(task_completions)} task completions")
    
    # Get orchestrator activities
    orchestrator_activities = logger.get_agent_activities("orchestrator")
    print(f"Orchestrator has {len(orchestrator_activities)} recent activities")

def main():
    """Run all examples."""
    print("AgentActivityLogger Usage Examples")
    print("=" * 50)
    
    # Run examples
    example_sms_engineer_usage()
    example_memory_engineer_usage() 
    example_orchestrator_usage()
    view_logged_activities()
    
    print("\n" + "=" * 50)
    print("✅ All examples completed successfully!")
    print("\nTo integrate this into your agents:")
    print("1. Import: from src.agent_activity_logger import AgentActivityLogger")
    print("2. Initialize: activity_logger = AgentActivityLogger()")
    print("3. Use: activity_logger.log_activity(agent_name, activity_type, details)")
    print("\nCheck logs/agents/ directory for the generated log files.")

if __name__ == "__main__":
    main()