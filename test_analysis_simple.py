#!/usr/bin/env python3
"""Simple test for Karen Analysis MCP Server"""

import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
from karen_codebase_analysis_mcp import KarenAnalysisMCP

async def simple_test():
    server = KarenAnalysisMCP()
    print(f"✓ Server created: {server.name} v{server.version}")
    
    # Just test MCP protocol
    response = await server.handle_request({"method": "tools/list", "params": {}})
    tools = response.get('tools', [])
    print(f"✓ MCP protocol: {len(tools)} tools available")
    
    for tool in tools:
        print(f"  - {tool['name']}")
    
    print("\nServer is ready!")

if __name__ == "__main__":
    asyncio.run(simple_test())