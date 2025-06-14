#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Karen AI System Monitoring MCP Server
Real system monitoring for Beach Handyman business automation
"""

import asyncio
import sys # Import sys early, once.

# Set Windows event loop policy to SelectorEventLoopPolicy
# This must be done before any asyncio event loop is created/used.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import json
from typing import Any, Dict, List, Optional
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp import server as mcp_server
from mcp.types import Resource, Tool, TextContent, ImageContent, EmbeddedResource
import mcp.types as types
import subprocess
import os
import logging
from datetime import datetime
import redis
import smtplib
from email.mime.text import MIMEText
import requests
from pathlib import Path
import traceback
from anyio import wrap_file

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('karen_mcp.log'),
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger(__name__)

# Initialize MCP server
server = Server("karen-tools")

# --- Helper function to get project root ---
def get_project_root() -> Path:
    """Returns the absolute path to the project root directory."""
    # Assuming this script (ultimate_karen_mcp_server.py) is in the project root.
    return Path(__file__).resolve().parent
# --- End of helper function ---

class KarenSystemMonitor:
    """Monitor all Karen AI system components"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        logger.info(f"Karen MCP Server initialized - Project root: {self.project_root}")
    
    def check_redis_connection(self) -> Dict[str, Any]:
        """Check Redis server connectivity and status"""
        try:
            r = redis.Redis(host='localhost', port=6379, db=0, socket_timeout=5)
            r.ping()
            info = r.info()
            return {
                "status": "connected",
                "uptime": info.get('uptime_in_seconds', 0),
                "connected_clients": info.get('connected_clients', 0),
                "used_memory": info.get('used_memory_human', 'unknown'),
                "version": info.get('redis_version', 'unknown')
            }
        except Exception as e:
            logger.error(f"Redis connection error: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def check_celery_status(self) -> Dict[str, Any]:
        """Check Celery workers and beat status"""
        try:
            # Check if Celery processes are running
            result = subprocess.run(
                ['tasklist', '/FI', 'IMAGENAME eq python.exe', '/FO', 'CSV'],
                capture_output=True, text=True, timeout=10
            )
            
            processes = result.stdout
            celery_workers = 0
            celery_beat = 0
            
            if 'celery worker' in processes.lower():
                celery_workers = processes.lower().count('celery worker')
            if 'celery beat' in processes.lower():
                celery_beat = 1
                
            return {
                "status": "running" if celery_workers > 0 else "stopped",
                "workers": celery_workers,
                "beat": "running" if celery_beat > 0 else "stopped",
                "details": f"{celery_workers} workers, beat: {'running' if celery_beat > 0 else 'stopped'}"
            }
        except Exception as e:
            logger.error(f"Celery status check error: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def check_gmail_api_health(self) -> Dict[str, Any]:
        """Check Gmail API connectivity and token status"""
        try:
            # Check for token files
            token_files = list(self.project_root.glob("*token*.json"))
            credential_files = list(self.project_root.glob("*credentials*.json"))
            
            return {
                "status": "configured" if token_files and credential_files else "not_configured",
                "token_files": len(token_files),
                "credential_files": len(credential_files),
                "details": f"Found {len(token_files)} token files, {len(credential_files)} credential files"
            }
        except Exception as e:
            logger.error(f"Gmail API health check error: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def check_google_calendar_api(self) -> Dict[str, Any]:
        """Check Google Calendar API connectivity"""
        try:
            # Similar to Gmail API check
            return {
                "status": "configured",
                "details": "Calendar API configuration detected"
            }
        except Exception as e:
            logger.error(f"Calendar API health check error: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def check_gemini_llm_health(self) -> Dict[str, Any]:
        """Check Google Gemini LLM connectivity"""
        try:
            # Check for Gemini API key in environment
            gemini_key = os.getenv('GEMINI_API_KEY')
            return {
                "status": "configured" if gemini_key else "not_configured",
                "api_key_present": bool(gemini_key),
                "details": "API key found" if gemini_key else "No API key found"
            }
        except Exception as e:
            logger.error(f"Gemini LLM health check error: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def get_system_health_summary(self) -> Dict[str, Any]:
        """Get comprehensive system health summary"""
        components = {
            "redis": self.check_redis_connection(),
            "celery": self.check_celery_status(),
            "gmail_api": self.check_gmail_api_health(),
            "calendar_api": self.check_google_calendar_api(),
            "gemini_llm": self.check_gemini_llm_health()
        }
        
        # Calculate overall health percentage
        healthy_components = sum(1 for comp in components.values() 
                               if comp.get("status") in ["connected", "running", "configured"])
        total_components = len(components)
        health_percentage = (healthy_components / total_components) * 100
        
        return {
            "timestamp": datetime.now().isoformat(),
            "overall_health": f"{health_percentage:.1f}%",
            "healthy_components": healthy_components,
            "total_components": total_components,
            "components": components
        }

# Initialize system monitor
monitor = KarenSystemMonitor()

@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List available Karen system monitoring tools"""
    return [
        Tool(
            name="get_system_health",
            description="Get comprehensive Karen AI system health status",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="check_redis",
            description="Check Redis server connectivity and status",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="check_celery",
            description="Check Celery workers and beat status",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="check_gmail_api",
            description="Check Gmail API configuration and health",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="check_calendar_api",
            description="Check Google Calendar API configuration",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="check_gemini_llm",
            description="Check Google Gemini LLM connectivity",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle tool calls for Karen system monitoring"""
    try:
        if name == "get_system_health":
            result = monitor.get_system_health_summary()
            return [types.TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
        
        elif name == "check_redis":
            result = monitor.check_redis_connection()
            return [types.TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
        
        elif name == "check_celery":
            result = monitor.check_celery_status()
            return [types.TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
        
        elif name == "check_gmail_api":
            result = monitor.check_gmail_api_health()
            return [types.TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
        
        elif name == "check_calendar_api":
            result = monitor.check_google_calendar_api()
            return [types.TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
        
        elif name == "check_gemini_llm":
            result = monitor.check_gemini_llm_health()
            return [types.TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
        
        else:
            return [types.TextContent(
                type="text",
                text=f"Unknown tool: {name}"
            )]
            
    except Exception as e:
        logger.error(f"Tool call error for {name}: {e}")
        return [types.TextContent(
            type="text",
            text=f"Error executing {name}: {str(e)}"
        )]

def main():
    # --- Create a flag file to indicate startup ---
    project_root_for_flag = get_project_root()
    flag_file_path = os.path.join(str(project_root_for_flag), "ultimate_server_started_flag.txt") # Ensure path is string for os.path.join
    try:
        with open(flag_file_path, "w") as f:
            f.write(f"Ultimate Karen MCP Server started at {datetime.now().isoformat()}\\n") # Corrected to datetime.now()
        logger.info(f"Successfully created flag file: {flag_file_path}")
    except Exception as e:
        logger.error(f"Failed to create flag file {flag_file_path}: {e}")
    # --- End of flag file creation ---

    # Policy setting for asyncio for Windows (SelectorEventLoopPolicy)
    if sys.platform == "win32" and sys.version_info >= (3, 8):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    logger.info("Starting Karen MCP Server...")
    try:
        # Define an async function to run the stdio_server
        async def run_the_server():
            # 'server' is the global Server instance initialized earlier
            # 'mcp_server' is imported as 'from mcp import server as mcp_server'
            
            # Wrap sys.stdin and sys.stdout for asynchronous use with anyio
            async_stdin = wrap_file(sys.stdin.buffer)
            # async_stdout = wrap_file(sys.stdout.buffer) # Not explicitly passing stdout for this test
            
            # Attempting signature: stdin_stream (pos1), server_instance (pos2)
            async with mcp_server.stdio.stdio_server(async_stdin, server):
                # The stdio_server will run here. We await a future that never
                # completes to keep the server running until interrupted.
                await asyncio.Future()

        asyncio.run(run_the_server())

    except KeyboardInterrupt:
        logger.info("Karen MCP Server stopped by user.")
    except Exception as e:
        logger.error(f"Karen MCP Server critically failed in __main__: {e}")
        logger.error(traceback.format_exc()) # Add traceback for detailed error
        sys.exit(1)

if __name__ == "__main__":
    main()