#!/usr/bin/env python3
"""
Ultra Minimal MCP Server - Absolute bare bones test
This is the simplest possible MCP server to test if MCP works at all
"""

import asyncio
import sys

# Minimal logging to file
def log(msg):
    with open("ultra_minimal_mcp.log", "a") as f:
        f.write(f"{msg}\n")
        f.flush()

log("=== Ultra Minimal MCP Server Starting ===")

try:
    from mcp.server import Server
    from mcp.types import Resource, TextContent
    from mcp.server.stdio import stdio_server
    log("✅ MCP imports successful")
except ImportError as e:
    log(f"❌ MCP import failed: {e}")
    sys.exit(1)

# Create server
app = Server("ultra-minimal")
log("✅ Server created")

@app.list_resources()
async def list_resources():
    log("📋 Resources requested")
    return [
        Resource(
            uri="minimal://test",
            name="Minimal Test",
            description="Ultra simple test",
            mimeType="text/plain"
        )
    ]

@app.read_resource()
async def read_resource(uri: str):
    log(f"📖 Resource requested: {uri}")
    if uri == "minimal://test":
        return TextContent(text="✅ Ultra minimal MCP server is working!")
    raise ValueError(f"Unknown resource: {uri}")

async def main():
    log("🚀 Starting server...")
    try:
        async with stdio_server() as (read_stream, write_stream):
            log("✅ stdio connection established")
            await app.run(read_stream, write_stream, app.create_initialization_options())
    except Exception as e:
        log(f"❌ Server error: {e}")
        raise

if __name__ == "__main__":
    log("🎬 Main starting...")
    try:
        asyncio.run(main())
    except Exception as e:
        log(f"💥 Fatal error: {e}")
        sys.exit(1)