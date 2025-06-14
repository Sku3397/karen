#!/usr/bin/env python3
"""
Simple MCP Test Server for Claude Desktop
This minimal server tests if MCP is working at all
"""
import asyncio
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from mcp.server import Server
    from mcp.types import Resource, TextContent
    from mcp.server.stdio import stdio_server
except ImportError as e:
    logger.error(f"MCP SDK not available: {e}")
    logger.info("Install with: pip install 'mcp[cli]'")
    sys.exit(1)

# Create the server
app = Server("karen-test-server")

@app.list_resources()
async def list_resources():
    """List available test resources"""
    return [
        Resource(
            uri="test://status",
            name="Test Status",
            description="Simple test to verify MCP is working",
            mimeType="text/plain"
        ),
        Resource(
            uri="test://karen-info",
            name="Karen Info",
            description="Basic information about Karen AI",
            mimeType="application/json"
        )
    ]

@app.read_resource()
async def read_resource(uri: str):
    """Read a specific resource"""
    if uri == "test://status":
        return TextContent(text="✅ MCP is working! Karen AI test server is operational.")
    
    elif uri == "test://karen-info":
        import json
        info = {
            "name": "Karen AI",
            "status": "MCP Test Server Active",
            "description": "Multi-agent AI assistant for handyman services",
            "mcp_test": "SUCCESS",
            "message": "If you can see this, MCP is working correctly!"
        }
        return TextContent(text=json.dumps(info, indent=2))
    
    else:
        raise ValueError(f"Unknown resource: {uri}")

async def main():
    """Main server loop"""
    logger.info("Starting Karen AI MCP Test Server...")
    
    try:
        async with stdio_server() as (read_stream, write_stream):
            logger.info("Test server ready - MCP connection established")
            await app.run(
                read_stream, 
                write_stream, 
                app.create_initialization_options()
            )
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)