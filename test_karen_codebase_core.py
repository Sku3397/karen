#!/usr/bin/env python3
"""Test script for Karen Codebase Core MCP Server"""

import json
import subprocess
import sys
import os

def send_request(proc, request):
    """Send request to MCP server and get response"""
    proc.stdin.write(json.dumps(request).encode() + b'\n')
    proc.stdin.flush()
    response = proc.stdout.readline()
    return json.loads(response)

def test_mcp_server():
    """Test the MCP server functionality"""
    print("Starting Karen Codebase Core MCP Server tests...")
    
    # Start the server
    proc = subprocess.Popen(
        [sys.executable, "karen_codebase_core_mcp.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=False
    )
    
    try:
        # Test 1: Initialize
        print("\n1. Testing initialize...")
        response = send_request(proc, {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"protocolVersion": "2024-11-05"}
        })
        print(f"Response: {json.dumps(response, indent=2)}")
        
        # Test 2: List tools
        print("\n2. Testing tools/list...")
        response = send_request(proc, {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        })
        print(f"Available tools: {len(response.get('tools', []))}")
        for tool in response.get('tools', []):
            print(f"  - {tool['name']}: {tool['description']}")
        
        # Test 3: File exists
        print("\n3. Testing file_exists...")
        response = send_request(proc, {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "file_exists",
                "arguments": {"path": "README.md"}
            }
        })
        result = json.loads(response['content'][0]['text'])
        print(f"README.md exists: {result['exists']}")
        
        # Test 4: List directory
        print("\n4. Testing list_directory...")
        response = send_request(proc, {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "list_directory",
                "arguments": {
                    "path": ".",
                    "filter_types": [".py"],
                    "recursive": False
                }
            }
        })
        result = json.loads(response['content'][0]['text'])
        print(f"Python files in root: {result['count']}")
        
        # Test 5: Read file
        print("\n5. Testing read_file...")
        response = send_request(proc, {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {
                "name": "read_file",
                "arguments": {"path": "README.md"}
            }
        })
        result = json.loads(response['content'][0]['text'])
        if result['success']:
            print(f"README.md: {result['lines']} lines, {result['size']} bytes")
        
        # Test 6: Get file info
        print("\n6. Testing get_file_info...")
        response = send_request(proc, {
            "jsonrpc": "2.0",
            "id": 6,
            "method": "tools/call",
            "params": {
                "name": "get_file_info",
                "arguments": {"path": "src"}
            }
        })
        result = json.loads(response['content'][0]['text'])
        if result['success']:
            print(f"src/ directory: {result.get('item_count', 0)} items")
        
        # Test 7: Create and delete test directory
        print("\n7. Testing create_directory and delete_file...")
        test_dir = "test_mcp_temp"
        
        # Create
        response = send_request(proc, {
            "jsonrpc": "2.0",
            "id": 7,
            "method": "tools/call",
            "params": {
                "name": "create_directory",
                "arguments": {"path": test_dir}
            }
        })
        result = json.loads(response['content'][0]['text'])
        print(f"Created directory: {result['created']}")
        
        # Delete
        response = send_request(proc, {
            "jsonrpc": "2.0",
            "id": 8,
            "method": "tools/call",
            "params": {
                "name": "delete_file",
                "arguments": {"path": test_dir}
            }
        })
        result = json.loads(response['content'][0]['text'])
        print(f"Deleted directory: {result['success']}")
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        proc.terminate()
        proc.wait()

if __name__ == "__main__":
    test_mcp_server()