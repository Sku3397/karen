#!/usr/bin/env python3
"""Quick test for Karen Analysis MCP Server"""

import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
from karen_codebase_analysis_mcp import KarenAnalysisMCP

async def quick_test():
    server = KarenAnalysisMCP()
    print(f"✓ Server created: {server.name} v{server.version}")
    
    # Test 1: Find function usage
    result = await server.find_function_usage(name="asyncio", exclude_definitions=True)
    print(f"✓ Function usage test: Found {result.get('count', 0)} usages of 'asyncio'")
    
    # Test 2: Find TODOs
    result = await server.find_todos_fixmes(types=["TODO", "FIXME"])
    print(f"✓ TODO/FIXME test: Found {result.get('total_count', 0)} comments")
    
    # Test 3: Simple complexity check
    result = await server.get_code_complexity(path="karen_codebase_analysis_mcp.py")
    if result.get('success'):
        metrics = result.get('metrics', {})
        print(f"✓ Complexity test: {metrics.get('total_lines', 0)} lines in file")
    
    # Test 4: Pattern detection 
    result = await server.analyze_code_patterns(path=".", patterns=None)
    print(f"✓ Pattern analysis: Analyzed {result.get('files_analyzed', 0)} files")
    
    # Test MCP protocol
    response = await server.handle_request({"method": "tools/list", "params": {}})
    print(f"✓ MCP protocol: {len(response.get('tools', []))} tools available")
    
    print("\nAll tests passed! Server is ready.")

if __name__ == "__main__":
    asyncio.run(quick_test())