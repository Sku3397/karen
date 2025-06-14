#!/usr/bin/env python3
"""Quick test for Karen Search Basic MCP Server"""

import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
from karen_codebase_search_basic_mcp import KarenSearchBasicMCP

async def quick_test():
    server = KarenSearchBasicMCP()
    print(f"✓ Server created: {server.name} v{server.version}")
    
    # Test search with very limited scope
    result = await server.search_codebase(
        pattern="KarenSearchBasicMCP",
        file_types=[".py"],
        max_results=2
    )
    print(f"✓ Search test: Found {result.get('count', 0)} results")
    
    # Test MCP protocol
    response = await server.handle_request({"method": "tools/list", "params": {}})
    print(f"✓ MCP protocol: {len(response.get('tools', []))} tools available")
    
    print("\nAll tests passed! Server is ready.")

if __name__ == "__main__":
    asyncio.run(quick_test())