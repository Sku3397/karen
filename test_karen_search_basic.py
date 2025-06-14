#!/usr/bin/env python3
"""
Test script for Karen Codebase Search Basic MCP Server
"""

import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from karen_codebase_search_basic_mcp import KarenSearchBasicMCP


async def test_search_basic():
    """Test basic search functionality"""
    server = KarenSearchBasicMCP()
    print(f"Testing {server.name} v{server.version}")
    print("="*60)
    
    # Test 1: Search for a common pattern
    print("\n1. Testing search_codebase for 'def' in Python files:")
    result = await server.search_codebase(
        pattern="def",
        file_types=[".py"],
        max_results=5
    )
    print(f"Success: {result['success']}")
    print(f"Files searched: {result.get('files_searched', 0)}")
    print(f"Results found: {result.get('count', 0)}")
    if result.get('results'):
        print("First result:")
        print(f"  File: {result['results'][0]['file']}")
        print(f"  Line {result['results'][0]['line']}: {result['results'][0]['text']}")
    
    # Test 2: Find function definition
    print("\n2. Testing find_function_definition for 'main':")
    result = await server.find_function_definition(name="main")
    print(f"Success: {result['success']}")
    print(f"Definitions found: {result.get('count', 0)}")
    if result.get('definitions'):
        print("First definition:")
        print(f"  File: {result['definitions'][0]['file']}")
        print(f"  Line {result['definitions'][0]['line']}: {result['definitions'][0]['text']}")
    
    # Test 3: Find class definition
    print("\n3. Testing find_class_definition for 'KarenSearchBasicMCP':")
    result = await server.find_class_definition(name="KarenSearchBasicMCP")
    print(f"Success: {result['success']}")
    print(f"Definitions found: {result.get('count', 0)}")
    if result.get('definitions'):
        for defn in result['definitions']:
            print(f"  {defn['file']}:{defn['line']}")
    
    # Test 4: Search imports
    print("\n4. Testing search_imports for 'asyncio':")
    result = await server.search_imports(module_name="asyncio")
    print(f"Success: {result['success']}")
    print(f"Files importing asyncio: {result.get('file_count', 0)}")
    print(f"Total import statements: {result.get('total_imports', 0)}")
    if result.get('imports'):
        first_file = list(result['imports'].keys())[0]
        print(f"First file: {first_file}")
        print(f"  Import: {result['imports'][first_file][0]['text']}")
    
    print("\n" + "="*60)
    print("All tests completed!")


async def test_mcp_protocol():
    """Test MCP protocol handling"""
    server = KarenSearchBasicMCP()
    print("\nTesting MCP Protocol:")
    print("="*60)
    
    # Test initialize
    request = {"method": "initialize", "params": {}}
    response = await server.handle_request(request)
    print(f"Initialize response: {json.dumps(response, indent=2)}")
    
    # Test tools/list
    request = {"method": "tools/list", "params": {}}
    response = await server.handle_request(request)
    print(f"\nTools available: {len(response.get('tools', []))}")
    for tool in response.get('tools', []):
        print(f"  - {tool['name']}: {tool['description']}")
    
    # Test tools/call
    request = {
        "method": "tools/call",
        "params": {
            "name": "search_codebase",
            "arguments": {
                "pattern": "class",
                "file_types": [".py"],
                "max_results": 3
            }
        }
    }
    response = await server.handle_request(request)
    if 'error' in response:
        print(f"\nError: {response['error']}")
    else:
        content = response.get('content', [{}])[0].get('text', '{}')
        result = json.loads(content)
        print(f"\nSearch results: {result.get('count', 0)} matches found")


if __name__ == "__main__":
    print("Karen Codebase Search Basic MCP Server Test Suite")
    print("="*60)
    
    # Run tests
    asyncio.run(test_search_basic())
    asyncio.run(test_mcp_protocol())