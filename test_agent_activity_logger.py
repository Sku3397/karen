#!/usr/bin/env python3
"""
Test script for the AgentActivityLogger integration.
"""

import sys
import os
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# Test imports
from src.agent_activity_logger import AgentActivityLogger

def test_logger_basic_functionality():
    """Test basic logger functionality."""
    print("Testing AgentActivityLogger basic functionality...")
    
    logger = AgentActivityLogger()
    
    # Test logging different types of activities
    print("✓ Logger initialized successfully")
    
    # Test initialization activity
    logger.log_activity(
        agent_name="test_agent",
        activity_type="initialization",
        details={
            "component": "test_component",
            "status": "initialized",
            "config": {"test_param": "test_value"}
        }
    )
    print("✓ Initialization activity logged")
    
    # Test task completion
    logger.log_task_completion(
        agent_name="test_agent",
        task_id="test_task_001",
        success=True,
        duration_seconds=1.5,
        details={"result": "test completed successfully"}
    )
    print("✓ Task completion logged")
    
    # Test performance metric
    logger.log_performance_metric(
        agent_name="test_agent",
        metric_name="response_time",
        metric_value=0.25,
        context={"operation": "test_operation"}
    )
    print("✓ Performance metric logged")
    
    # Test error logging
    logger.log_error(
        agent_name="test_agent",
        error_type="TestError",
        error_message="This is a test error",
        context={"test_context": "error_simulation"}
    )
    print("✓ Error logged")
    
    # Test retrieving activities
    activities = logger.get_agent_activities("test_agent", limit=10)
    print(f"✓ Retrieved {len(activities)} activities for test_agent")
    
    # Test filtering by activity type
    init_activities = logger.get_agent_activities("test_agent", activity_type="initialization")
    print(f"✓ Retrieved {len(init_activities)} initialization activities")
    
    return True

def test_logger_with_agents():
    """Test logger integration with actual agent imports."""
    print("\nTesting logger integration with agents...")
    
    try:
        # Test SMS Engineer Agent
        from src.sms_engineer_agent import activity_logger as sms_logger
        print("✓ SMS Engineer Agent logger imported successfully")
        
        # Test Orchestrator Agent
        from src.orchestrator_agent import activity_logger as orchestrator_logger
        print("✓ Orchestrator Agent logger imported successfully")
        
        # Test Communication Agent
        from src.communication_agent import activity_logger as comm_logger
        print("✓ Communication Agent logger imported successfully")
        
        # Test Task Management Agent
        from src.task_management_agent import activity_logger as task_logger
        print("✓ Task Management Agent logger imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"✗ Error importing agent loggers: {e}")
        return False

def test_log_file_creation():
    """Test that log files are created properly."""
    print("\nTesting log file creation...")
    
    logger = AgentActivityLogger()
    
    # Log some test activities
    logger.log_activity(
        agent_name="test_file_agent",
        activity_type="file_test",
        details={"test": "log file creation"}
    )
    
    # Check if files were created
    log_dir = Path("logs/agents")
    
    if log_dir.exists():
        print(f"✓ Log directory exists: {log_dir}")
        
        activity_log = log_dir / "agent_activity.log"
        if activity_log.exists():
            print(f"✓ Activity log file exists: {activity_log}")
        else:
            print(f"✗ Activity log file not found: {activity_log}")
            
        json_log = log_dir / "test_file_agent_activity.json"
        if json_log.exists():
            print(f"✓ JSON log file exists: {json_log}")
            
            # Try to read the JSON log
            import json
            with open(json_log, 'r') as f:
                data = json.load(f)
                print(f"✓ JSON log contains {len(data)} entries")
        else:
            print(f"✗ JSON log file not found: {json_log}")
            
        return True
    else:
        print(f"✗ Log directory not found: {log_dir}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("AgentActivityLogger Integration Test")
    print("=" * 60)
    
    tests = [
        test_logger_basic_functionality,
        test_logger_with_agents,
        test_log_file_creation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
                print(f"✓ {test.__name__} PASSED")
            else:
                print(f"✗ {test.__name__} FAILED")
        except Exception as e:
            print(f"✗ {test.__name__} ERROR: {e}")
    
    print("\n" + "=" * 60)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! AgentActivityLogger integration is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please review the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())