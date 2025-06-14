#!/usr/bin/env python3
"""
Minimal MCP server for testing Claude Desktop connection
"""
import asyncio
import mcp.types as types
from mcp.server import Server
from mcp.server.models import InitializationOptions # Ensure this is used
import mcp.server.stdio
import logging
import sys # For stderr
from pathlib import Path

# Setup logging for this minimal server
log_file_path = Path(__file__).parent / "test_minimal_mcp.log"
logging.basicConfig(
    filename=log_file_path,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filemode='w'
)
print("MinimalMCP: Logging to", log_file_path, file=sys.stderr)

app = Server("test-server")
print("MinimalMCP: Server object created.", file=sys.stderr)
logging.info("Minimal MCP Server: Server object created.")

@app.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    print("MinimalMCP: handle_list_tools called.", file=sys.stderr)
    logging.info("Minimal MCP Server: handle_list_tools called.")
    return [
        types.Tool(
            name="test_tool",
            description="A simple test tool",
            inputSchema={"type": "object", "properties": {}, "required": []}
        )
    ]

@app.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    print(f"MinimalMCP: handle_call_tool called with tool '{name}'.", file=sys.stderr)
    logging.info(f"Minimal MCP Server: handle_call_tool called with tool '{name}'.")
    if name == "test_tool":
        return [types.TextContent(type="text", text="✅ Test MCP server is working!")]
    else:
        return [types.TextContent(type="text", text=f"❌ Unknown tool: {name}")]

async def main():
    print("MinimalMCP: Main function started.", file=sys.stderr)
    logging.info("Minimal MCP Server: Main function started.")
    try:
        # Crucially, call get_capabilities() with no arguments as per user's minimal example spec
        # This is where ultimate_karen_mcp_server.py was failing with TypeError.
        # If this minimal server works, then the problem is specific to ultimate_karen_mcp_server.py's other details.
        # If this also fails with TypeError, then the mcp library API requires those args.
        capabilities_for_init = app.get_capabilities()
        print("MinimalMCP: app.get_capabilities() called successfully.", file=sys.stderr)
        logging.info("MinimalMCP: app.get_capabilities() called successfully.")

        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            print("MinimalMCP: Stdio server context entered.", file=sys.stderr)
            logging.info("Minimal MCP Server: Stdio server context entered.")
            await app.run(
                read_stream,
                write_stream,
                InitializationOptions( # From mcp.server.models
                    server_name="test-server",
                    server_version="1.0.0",
                    capabilities=capabilities_for_init # Pass the result here
                )
            )
            print("MinimalMCP: app.run finished.", file=sys.stderr)
            logging.info("Minimal MCP Server: app.run finished.")
    except Exception as e:
        print(f"MinimalMCP: Exception in main - {e}", file=sys.stderr)
        logging.error(f"Minimal MCP Server: Exception in main - {e}", exc_info=True)
        raise
    finally:
        print("MinimalMCP: Main function ending.", file=sys.stderr)
        logging.info("Minimal MCP Server: Main function ending.")


if __name__ == "__main__":
    print("MinimalMCP: Script execution started.", file=sys.stderr)
    logging.info("Minimal MCP Server: Script execution started.")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("MinimalMCP: Keyboard interrupt received. Exiting.", file=sys.stderr)
        logging.info("Minimal MCP Server: Keyboard interrupt received. Exiting.")
    except Exception as e:
        print(f"MinimalMCP: Exception in __main__ - {e}", file=sys.stderr)
        logging.error(f"Minimal MCP Server: Exception in __main__ - {e}", exc_info=True)
    finally:
        print("MinimalMCP: Script execution finished.", file=sys.stderr)
        logging.info("Minimal MCP Server: Script execution finished.") 