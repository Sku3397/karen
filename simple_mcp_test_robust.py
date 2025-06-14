#!/usr/bin/env python3
"""
Robust Simple MCP Test Server for Claude Desktop
This version has better error handling and logging
"""
import asyncio
import sys
import logging
import os
import traceback
from pathlib import Path

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr),
        logging.FileHandler('mcp_simple_debug.log', mode='w')
    ]
)
logger = logging.getLogger(__name__)

# Log startup
logger.info("=== Karen AI Simple MCP Test Server Starting ===")
logger.info(f"Python version: {sys.version}")
logger.info(f"Working directory: {os.getcwd()}")
logger.info(f"KAREN_PROJECT_ROOT: {os.getenv('KAREN_PROJECT_ROOT', 'Not set')}")

try:
    from mcp.server import Server
    from mcp.types import Resource, TextContent
    from mcp.server.stdio import stdio_server
    logger.info("✅ MCP SDK imports successful")
except ImportError as e:
    logger.error(f"❌ MCP SDK not available: {e}")
    logger.error("Install with: pip install 'mcp[cli]'")
    sys.exit(1)

# Create the server with error handling
try:
    app = Server("karen-test-server")
    logger.info("✅ MCP Server created")
except Exception as e:
    logger.error(f"❌ Failed to create MCP server: {e}")
    sys.exit(1)

@app.list_resources()
async def list_resources():
    """List available test resources"""
    logger.info("📋 Resource list requested")
    try:
        resources = [
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
            ),
            Resource(
                uri="test://debug",
                name="Debug Info",
                description="Debug information for troubleshooting",
                mimeType="application/json"
            )
        ]
        logger.info(f"✅ Returning {len(resources)} resources")
        return resources
    except Exception as e:
        logger.error(f"❌ Error listing resources: {e}")
        logger.error(traceback.format_exc())
        raise

@app.read_resource()
async def read_resource(uri: str):
    """Read a specific resource"""
    logger.info(f"📖 Resource read requested: {uri}")
    
    try:
        if uri == "test://status":
            message = "✅ MCP is working! Karen AI test server is operational."
            logger.info("✅ Status resource accessed successfully")
            return TextContent(text=message)
        
        elif uri == "test://karen-info":
            import json
            info = {
                "name": "Karen AI",
                "status": "MCP Test Server Active",
                "description": "Multi-agent AI assistant for handyman services",
                "mcp_test": "SUCCESS",
                "message": "If you can see this, MCP is working correctly!",
                "project_root": os.getenv("KAREN_PROJECT_ROOT", "Not set"),
                "python_version": sys.version,
                "working_directory": os.getcwd()
            }
            logger.info("✅ Karen info resource accessed successfully")
            return TextContent(text=json.dumps(info, indent=2))
        
        elif uri == "test://debug":
            import json
            debug_info = {
                "server_name": "karen-test-server",
                "timestamp": str(asyncio.get_event_loop().time()),
                "environment": dict(os.environ),
                "python_path": sys.path,
                "current_directory": os.getcwd(),
                "karen_project_root": os.getenv("KAREN_PROJECT_ROOT"),
                "mcp_working": True
            }
            logger.info("✅ Debug resource accessed successfully")
            return TextContent(text=json.dumps(debug_info, indent=2))
        
        else:
            error_msg = f"Unknown resource: {uri}"
            logger.error(f"❌ {error_msg}")
            raise ValueError(error_msg)
            
    except Exception as e:
        logger.error(f"❌ Error reading resource {uri}: {e}")
        logger.error(traceback.format_exc())
        raise

async def main():
    """Main server loop with enhanced error handling"""
    logger.info("🚀 Starting Karen AI MCP Test Server...")
    
    try:
        async with stdio_server() as (read_stream, write_stream):
            logger.info("✅ MCP stdio connection established")
            logger.info("🎯 Test server ready - waiting for requests...")
            
            await app.run(
                read_stream, 
                write_stream, 
                app.create_initialization_options()
            )
            
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped by user (Ctrl+C)")
    except Exception as e:
        logger.error(f"❌ Server error: {e}")
        logger.error(traceback.format_exc())
        raise

if __name__ == "__main__":
    try:
        # Set up environment
        if not os.getenv("KAREN_PROJECT_ROOT"):
            project_root = Path(__file__).parent.resolve()
            os.environ["KAREN_PROJECT_ROOT"] = str(project_root)
            logger.info(f"📁 Set KAREN_PROJECT_ROOT to: {project_root}")
        
        logger.info("🎬 Starting main server loop...")
        asyncio.run(main())
        
    except KeyboardInterrupt:
        logger.info("👋 Server stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)