#!/usr/bin/env python3
"""
Demo script showing how to use the troubleshooting system
"""

import json
import time
from datetime import datetime
from pathlib import Path

def send_test_issue():
    """Send a test issue to the troubleshooting system"""
    # Create agent inbox for demo
    agent_name = "demo_mcp_agent"
    ts_inbox = Path("/workspace/autonomous-agents/communication/inbox/troubleshooting-orchestrator")
    ts_inbox.mkdir(parents=True, exist_ok=True)
    
    # Send issue report
    issue_message = {
        "from": agent_name,
        "to": "troubleshooting_orchestrator", 
        "type": "issue_report",
        "timestamp": datetime.now().isoformat(),
        "subject": "MCP Tool Schema Validation Failed",
        "content": {
            "title": "MCP Tool Schema Validation Failed",
            "description": "New file_operations tool is failing schema validation with 'inputSchema is required' error",
            "error_details": "ValidationError: 'inputSchema' is a required property",
            "affected_resources": ["src/tools/file_operations.py", "mcp-server-config.json"],
            "tags": ["mcp", "schema", "validation", "tools"],
            "context": {
                "tool_name": "file_operations",
                "mcp_version": "1.0.0",
                "last_working": "never"
            }
        }
    }
    
    # Write message to troubleshooting inbox
    message_file = ts_inbox / f"issue_report_{int(time.time() * 1000)}.json"
    with open(message_file, 'w') as f:
        json.dump(issue_message, f, indent=2)
        
    print(f"📤 Sent issue report: {issue_message['subject']}")
    return message_file

def send_help_request():
    """Send a help request to the troubleshooting system"""
    ts_inbox = Path("/workspace/autonomous-agents/communication/inbox/troubleshooting-orchestrator")
    
    help_message = {
        "from": "demo_mcp_agent",
        "to": "troubleshooting_orchestrator",
        "type": "help_request", 
        "timestamp": datetime.now().isoformat(),
        "subject": "Need Redis Configuration Help",
        "content": {
            "description": "Having trouble configuring Redis for MCP tool testing. Getting authentication errors.",
            "tags": ["redis", "configuration", "authentication"],
            "preferred_agents": ["mcp_codebase_tools"],
            "urgency": "medium"
        }
    }
    
    message_file = ts_inbox / f"help_request_{int(time.time() * 1000)}.json"
    with open(message_file, 'w') as f:
        json.dump(help_message, f, indent=2)
        
    print(f"🆘 Sent help request: {help_message['subject']}")
    return message_file

def share_solution():
    """Share a solution with the troubleshooting system"""
    ts_inbox = Path("/workspace/autonomous-agents/communication/inbox/troubleshooting-orchestrator")
    
    solution_message = {
        "from": "demo_mcp_agent",
        "to": "troubleshooting_orchestrator",
        "type": "solution_share",
        "timestamp": datetime.now().isoformat(),
        "subject": "Solution: Fix MCP Schema Validation",
        "content": {
            "title": "Fix MCP Tool Missing inputSchema",
            "description": "How to properly add inputSchema to MCP tools",
            "category": "mcp_integration",
            "problem_patterns": [
                "inputSchema is required",
                "schema validation failed",
                "ValidationError"
            ],
            "solution_steps": [
                "Add inputSchema property to tool definition",
                "Define parameter types and descriptions", 
                "Validate schema with MCP validator",
                "Test tool execution with sample parameters"
            ],
            "code_snippets": {
                "example_schema": '''
{
  "name": "file_operations",
  "description": "Perform file operations",
  "inputSchema": {
    "type": "object",
    "properties": {
      "operation": {
        "type": "string",
        "enum": ["read", "write", "delete"],
        "description": "The operation to perform"
      },
      "file_path": {
        "type": "string", 
        "description": "Path to the target file"
      }
    },
    "required": ["operation", "file_path"]
  }
}
'''
            },
            "validation_steps": [
                "Run MCP schema validator",
                "Test with Claude Desktop",
                "Verify tool parameters work correctly"
            ],
            "tags": ["mcp", "schema", "validation", "tools"]
        }
    }
    
    message_file = ts_inbox / f"solution_share_{int(time.time() * 1000)}.json"
    with open(message_file, 'w') as f:
        json.dump(solution_message, f, indent=2)
        
    print(f"💡 Shared solution: {solution_message['subject']}")
    return message_file

def check_responses():
    """Check for responses from the troubleshooting system"""
    demo_inbox = Path("/workspace/autonomous-agents/communication/inbox/demo_mcp_agent")
    
    if demo_inbox.exists():
        response_files = list(demo_inbox.glob("*.json"))
        if response_files:
            print(f"\n📨 Received {len(response_files)} responses:")
            for response_file in response_files:
                try:
                    with open(response_file, 'r') as f:
                        response = json.load(f)
                    print(f"  • {response.get('type', 'unknown')}: {response.get('subject', 'No subject')}")
                except Exception as e:
                    print(f"  • Error reading {response_file}: {e}")
        else:
            print("\n📭 No responses yet")
    else:
        print("\n📭 No inbox created yet")

def check_system_activity():
    """Check troubleshooting system activity"""
    print("\n🔍 Checking System Activity:")
    
    # Check if issues were created
    issues_path = Path("/workspace/autonomous-agents/troubleshooting/issues")
    if issues_path.exists():
        issue_files = list(issues_path.glob("*.json"))
        print(f"  📋 Issues created: {len(issue_files)}")
        for issue_file in issue_files[-3:]:  # Show last 3
            try:
                with open(issue_file, 'r') as f:
                    issue = json.load(f)
                print(f"    - {issue.get('title', 'Untitled')} [{issue.get('status', 'unknown')}]")
            except:
                pass
    
    # Check if solutions were saved
    solutions_path = Path("/workspace/autonomous-agents/troubleshooting/solutions")
    if solutions_path.exists():
        solution_files = list(solutions_path.glob("*.json"))
        print(f"  💡 Solutions shared: {len(solution_files)}")
        for solution_file in solution_files[-3:]:  # Show last 3
            try:
                with open(solution_file, 'r') as f:
                    solution = json.load(f)
                print(f"    - {solution.get('title', 'Untitled')} by {solution.get('author', 'unknown')}")
            except:
                pass

def main():
    """Demo the troubleshooting system"""
    print("🔧 TROUBLESHOOTING SYSTEM DEMO")
    print("=" * 40)
    
    print("\n1️⃣ Sending test issue...")
    send_test_issue()
    
    print("\n2️⃣ Requesting help...")
    send_help_request()
    
    print("\n3️⃣ Sharing solution...")
    share_solution()
    
    print("\n⏳ Waiting for system to process messages...")
    time.sleep(5)
    
    check_responses()
    check_system_activity()
    
    print("\n✅ Demo complete!")
    print("\nThe troubleshooting system is now:")
    print("• Processing issues from agents")
    print("• Assigning problems to capable agents")
    print("• Building knowledge base from solutions")
    print("• Facilitating agent collaboration")
    print("\nAgents can start using it by sending JSON messages to:")
    print("/workspace/autonomous-agents/communication/inbox/troubleshooting-orchestrator/")

if __name__ == "__main__":
    main()