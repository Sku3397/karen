#!/usr/bin/env python3
"""
Test script to demonstrate the troubleshooting system in action
"""

import json
import time
from pathlib import Path
from enhanced_communication_system import create_communication_client, MessageType, MessagePriority, SolutionCategory
from knowledge_management_system import create_knowledge_manager, KnowledgeType
from testing_coordination_system import create_testing_coordinator, TestType, TestEnvironment

def test_communication_system():
    """Test the communication system"""
    print("\n🧪 Testing Communication System...")
    
    # Create communication client for test agent
    comm_client = create_communication_client(
        agent_id="test_demo_agent",
        subscribed_tags=["troubleshooting", "demo"]
    )
    
    # Test 1: Report an issue
    print("  📤 Reporting test issue...")
    issue_id = comm_client.send_message(
        to_agent="troubleshooting_orchestrator",
        message_type=MessageType.ISSUE_REPORT,
        subject="Demo MCP Connection Issue",
        content={
            "description": "Cannot connect to demo MCP server",
            "error_details": "Connection refused on port 8080",
            "affected_resources": ["demo-config.json"],
            "tags": ["demo", "connection"]
        },
        priority=MessagePriority.MEDIUM
    )
    print(f"  ✅ Issue reported with ID: {issue_id}")
    
    # Test 2: Share a solution
    print("  📤 Sharing demo solution...")
    solution_id = comm_client.share_solution(
        category=SolutionCategory.MCP_INTEGRATION,
        title="Demo: Fix MCP Port Conflicts",
        description="How to resolve port conflicts in demo environment",
        problem_patterns=["port already in use", "connection refused"],
        solution_steps=[
            "Check for running processes on port",
            "Kill conflicting process",
            "Update configuration with new port"
        ],
        tags=["demo", "port_conflict"]
    )
    print(f"  ✅ Solution shared with ID: {solution_id}")
    
    # Test 3: Broadcast message
    print("  📢 Broadcasting demo message...")
    broadcast_id = comm_client.broadcast_message(
        title="Demo System Test",
        content="Testing the troubleshooting system broadcast functionality",
        priority=MessagePriority.LOW,
        tags=["demo", "test"]
    )
    print(f"  ✅ Broadcast sent with ID: {broadcast_id}")
    
    return comm_client

def test_knowledge_management():
    """Test the knowledge management system"""
    print("\n🧠 Testing Knowledge Management...")
    
    knowledge_mgr = create_knowledge_manager("test_demo_agent")
    
    # Test 1: Create knowledge entry
    print("  📝 Creating demo knowledge entry...")
    entry_id = knowledge_mgr.create_knowledge_entry(
        entry_type=KnowledgeType.TROUBLESHOOTING_PATTERN,
        title="Demo: Common MCP Setup Issues",
        description="Common problems when setting up MCP servers",
        content={
            "steps": [
                "Verify Node.js installation",
                "Check port availability", 
                "Validate configuration syntax",
                "Test basic connectivity"
            ],
            "tools_required": ["node", "lsof", "curl"],
            "estimated_time_minutes": 15
        },
        tags=["demo", "mcp", "setup"]
    )
    print(f"  ✅ Knowledge entry created: {entry_id}")
    
    # Test 2: Search knowledge
    print("  🔍 Searching knowledge base...")
    results = knowledge_mgr.search_knowledge(
        query="MCP connection problems",
        tags=["demo"]
    )
    print(f"  ✅ Found {len(results)} relevant entries")
    for entry, score in results[:2]:
        print(f"    - {entry.title} (relevance: {score:.2f})")
    
    # Test 3: Pattern matching
    print("  🎯 Testing pattern matching...")
    matches = knowledge_mgr.find_matching_patterns(
        issue_description="MCP server won't start, getting port conflict error"
    )
    print(f"  ✅ Found {len(matches)} pattern matches")
    for match in matches[:2]:
        print(f"    - Pattern: {match.pattern_id} (confidence: {match.confidence_score:.2f})")
    
    return knowledge_mgr

def test_testing_coordination():
    """Test the testing coordination system"""
    print("\n🧪 Testing Coordination System...")
    
    test_coord = create_testing_coordinator("test_demo_agent")
    
    # Test 1: Register test suite
    print("  📋 Registering demo test suite...")
    suite_id = test_coord.register_test_suite(
        name="Demo Integration Tests",
        test_type=TestType.INTEGRATION,
        environment=TestEnvironment.LOCAL,
        test_files=["demo_test.py"],
        required_resources=["demo_config"],
        estimated_duration=5
    )
    print(f"  ✅ Test suite registered: {suite_id}")
    
    # Test 2: Schedule test execution
    print("  ⏰ Scheduling test execution...")
    execution_id = test_coord.schedule_test_execution(suite_id)
    print(f"  ✅ Test scheduled: {execution_id}")
    
    # Test 3: Check status
    print("  📊 Checking testing status...")
    status = test_coord.get_testing_status()
    print(f"  ✅ Registered suites: {status['registered_suites']}")
    print(f"  ✅ Queued executions: {status['queued_executions']}")
    
    return test_coord

def check_system_files():
    """Check that system files are properly created"""
    print("\n📁 Checking System Files...")
    
    base_path = Path("/workspace/autonomous-agents")
    expected_paths = [
        base_path / "troubleshooting",
        base_path / "troubleshooting" / "issues",
        base_path / "troubleshooting" / "solutions", 
        base_path / "troubleshooting" / "knowledge-base",
        base_path / "communication" / "inbox" / "troubleshooting-orchestrator"
    ]
    
    for path in expected_paths:
        if path.exists():
            print(f"  ✅ {path}")
        else:
            print(f"  ❌ {path} (missing)")
            
    # Check for key system files
    system_files = [
        "/workspace/troubleshooting_orchestrator.py",
        "/workspace/agent_coordination_protocols.py",
        "/workspace/enhanced_communication_system.py",
        "/workspace/testing_coordination_system.py",
        "/workspace/knowledge_management_system.py",
        "/workspace/integrated_troubleshooting_launcher.py"
    ]
    
    print("\n📄 System Files:")
    for file_path in system_files:
        if Path(file_path).exists():
            print(f"  ✅ {Path(file_path).name}")
        else:
            print(f"  ❌ {Path(file_path).name} (missing)")

def demonstrate_workflow():
    """Demonstrate a complete troubleshooting workflow"""
    print("\n🎬 Demonstrating Complete Workflow...")
    print("=" * 50)
    
    # Step 1: Agent encounters an issue
    print("1️⃣ Agent encounters MCP tool development issue...")
    
    comm_client = create_communication_client("demo_mcp_developer")
    
    # Report the issue
    issue_response = comm_client.send_message(
        to_agent="troubleshooting_orchestrator",
        message_type=MessageType.ISSUE_REPORT,
        subject="MCP Tool Schema Validation Error",
        content={
            "description": "New file operations tool failing schema validation",
            "error_details": "ValidationError: 'inputSchema' is required",
            "affected_resources": ["src/tools/file_ops.py"],
            "context": {
                "tool_name": "file_operations",
                "mcp_version": "1.0.0"
            }
        },
        priority=MessagePriority.HIGH,
        requires_response=True
    )
    
    print(f"   📤 Issue reported: {issue_response}")
    
    # Step 2: Search knowledge base for solutions
    print("2️⃣ Searching knowledge base for similar issues...")
    
    knowledge_mgr = create_knowledge_manager("demo_mcp_developer")
    results = knowledge_mgr.search_knowledge(
        query="MCP schema validation inputSchema",
        entry_type=KnowledgeType.TROUBLESHOOTING_PATTERN
    )
    
    print(f"   🔍 Found {len(results)} potential solutions")
    
    # Step 3: If no solution found, agent develops one
    print("3️⃣ No existing solution found, developing new solution...")
    
    solution_id = comm_client.share_solution(
        category=SolutionCategory.MCP_INTEGRATION,
        title="Fix MCP Tool Missing inputSchema",
        description="How to properly define inputSchema for MCP tools",
        problem_patterns=["inputSchema is required", "schema validation", "ValidationError"],
        solution_steps=[
            "Add inputSchema property to tool definition",
            "Define parameter types and descriptions",
            "Validate schema with MCP validator",
            "Test tool execution"
        ],
        code_snippets={
            "example_schema": '''
{
  "name": "file_operations",
  "description": "Perform file operations",
  "inputSchema": {
    "type": "object",
    "properties": {
      "operation": {
        "type": "string", 
        "enum": ["read", "write", "delete"]
      },
      "file_path": {
        "type": "string",
        "description": "Path to the file"
      }
    },
    "required": ["operation", "file_path"]
  }
}
'''
        },
        validation_steps=[
            "Run MCP schema validator",
            "Test tool with sample parameters",
            "Verify in Claude Desktop"
        ]
    )
    
    print(f"   💡 Solution created and shared: {solution_id}")
    
    # Step 4: Test the solution
    print("4️⃣ Setting up coordinated testing...")
    
    test_coord = create_testing_coordinator("demo_mcp_developer")
    suite_id = test_coord.register_test_suite(
        name="MCP Schema Validation Tests",
        test_type=TestType.INTEGRATION,
        environment=TestEnvironment.ISOLATED,
        test_files=["tests/test_schema_validation.py"],
        required_resources=["mcp_server", "test_tools"]
    )
    
    execution_id = test_coord.schedule_test_execution(suite_id)
    print(f"   🧪 Test execution scheduled: {execution_id}")
    
    # Step 5: Knowledge base learns from success
    print("5️⃣ Recording successful resolution...")
    
    knowledge_mgr.record_learning_event(
        event_type="issue_resolved",
        context={
            "issue_description": "MCP tool schema validation error",
            "solution_steps": [
                "Added inputSchema property",
                "Defined parameter types",
                "Validated with MCP validator"
            ],
            "resolution_time_minutes": 15,
            "tools_used": ["mcp_validator", "schema_editor"]
        },
        outcome="success"
    )
    
    print("   📚 Learning event recorded for future reference")
    
    print("\n✅ Workflow Complete! The troubleshooting system has:")
    print("   • Coordinated issue resolution without conflicts")
    print("   • Built knowledge base for future similar issues") 
    print("   • Scheduled safe testing in isolated environment")
    print("   • Learned patterns to automate future resolutions")

def main():
    """Main test function"""
    print("🔧 KAREN AI TROUBLESHOOTING SYSTEM - DEMONSTRATION")
    print("=" * 60)
    
    try:
        # Check system files
        check_system_files()
        
        # Test individual components
        comm_client = test_communication_system()
        knowledge_mgr = test_knowledge_management()
        test_coord = test_testing_coordination()
        
        # Demonstrate complete workflow
        demonstrate_workflow()
        
        print("\n🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
        print("\nThe troubleshooting system is ready for use.")
        print("Start it with: python launch_troubleshooting_system.py")
        
        # Show usage summary
        print("\n📋 QUICK USAGE SUMMARY:")
        print("• Report issues: MessageType.ISSUE_REPORT to troubleshooting_orchestrator")
        print("• Request help: request_help() with description and tags")
        print("• Share solutions: share_solution() with steps and validation")
        print("• Coordinate testing: register_test_suite() then schedule_test_execution()")
        print("• Search knowledge: search_knowledge() with query and filters")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
        
    return 0

if __name__ == "__main__":
    exit(main())