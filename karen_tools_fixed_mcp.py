#!/usr/bin/env python3
"""
Karen Tools MCP Server - Fixed Version
System monitoring tools for Karen AI business automation
"""

import os
import sys
import json
import asyncio
from typing import List, Dict, Any, Optional
import subprocess
import redis
import requests
from datetime import datetime
from pathlib import Path

try:
    from mcp.server import Server
    from mcp.types import Tool, TextContent, CallToolResult
    from mcp.server.stdio import stdio_server
except ImportError as e:
    print(f"ERROR: {e}", file=sys.stderr)
    print("Please install MCP: pip install mcp-python", file=sys.stderr)
    sys.exit(1)

# Create server instance
app = Server("karen-tools")

# Project root
PROJECT_ROOT = Path("/workspace")

def check_redis_connection() -> Dict[str, Any]:
    """Check Redis connectivity."""
    try:
        r = redis.Redis(host='localhost', port=6379, db=0, socket_connect_timeout=2)
        r.ping()
        info = r.info()
        return {
            "status": "healthy",
            "connected": True,
            "version": info.get("redis_version", "unknown"),
            "uptime_seconds": info.get("uptime_in_seconds", 0),
            "connected_clients": info.get("connected_clients", 0),
            "used_memory": info.get("used_memory_human", "unknown")
        }
    except redis.ConnectionError:
        return {
            "status": "error",
            "connected": False,
            "error": "Cannot connect to Redis server"
        }
    except Exception as e:
        return {
            "status": "error",
            "connected": False,
            "error": str(e)
        }

def check_celery_status() -> Dict[str, Any]:
    """Check Celery workers and beat status."""
    result = {
        "workers": {"status": "unknown", "count": 0},
        "beat": {"status": "unknown"},
        "tasks": []
    }
    
    try:
        # Check Celery workers
        worker_output = subprocess.run(
            ["celery", "-A", "src.celery_app:celery_app", "inspect", "active_queues"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if worker_output.returncode == 0:
            result["workers"]["status"] = "healthy"
            # Count workers from output
            worker_lines = [line for line in worker_output.stdout.split('\n') if '-> celery@' in line]
            result["workers"]["count"] = len(worker_lines)
        else:
            result["workers"]["status"] = "error"
            result["workers"]["error"] = "No active workers found"
        
        # Check Celery beat
        beat_pid_file = PROJECT_ROOT / "celerybeat.pid"
        if beat_pid_file.exists():
            try:
                with open(beat_pid_file, 'r') as f:
                    pid = int(f.read().strip())
                # Check if process is running
                os.kill(pid, 0)
                result["beat"]["status"] = "healthy"
                result["beat"]["pid"] = pid
            except (OSError, ValueError):
                result["beat"]["status"] = "error"
                result["beat"]["error"] = "Beat process not running"
        else:
            result["beat"]["status"] = "error"
            result["beat"]["error"] = "Beat PID file not found"
        
    except subprocess.TimeoutExpired:
        result["workers"]["status"] = "error"
        result["workers"]["error"] = "Timeout checking workers"
    except Exception as e:
        result["workers"]["status"] = "error"
        result["workers"]["error"] = str(e)
    
    return result

# Tool definitions
@app.list_tools()
async def list_tools():
    """List available tools."""
    return [
        Tool(
            name="karen_system_health",
            description="Get comprehensive Karen AI system health status",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="karen_check_redis",
            description="Check Redis server connectivity and status",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="karen_check_celery",
            description="Check Celery workers and beat scheduler status",
            inputSchema={"type": "object", "properties": {}}
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls."""
    
    if name == "karen_system_health":
        health = {
            "timestamp": datetime.now().isoformat(),
            "components": {
                "redis": check_redis_connection(),
                "celery": check_celery_status()
            }
        }
        
        # Calculate overall health
        statuses = [comp["status"] for comp in health["components"].values()]
        if all(s == "healthy" for s in statuses):
            health["overall_status"] = "healthy"
        elif any(s == "error" for s in statuses):
            health["overall_status"] = "degraded"
        else:
            health["overall_status"] = "partial"
        
        # Format output
        output = [f"Karen AI System Health Report\n{'-' * 40}"]
        output.append(f"Timestamp: {health['timestamp']}")
        output.append(f"Overall Status: {health['overall_status'].upper()}\n")
        
        for component, status in health["components"].items():
            output.append(f"{component.replace('_', ' ').title()}:")
            output.append(f"  Status: {status['status']}")
            
            if component == "redis" and status.get("connected"):
                output.append(f"  Version: {status['version']}")
                output.append(f"  Uptime: {status['uptime_seconds']} seconds")
                output.append(f"  Memory: {status['used_memory']}")
            elif component == "celery":
                output.append(f"  Workers: {status['workers']['count']} active")
                output.append(f"  Beat: {status['beat']['status']}")
            
            if status.get("error"):
                output.append(f"  Error: {status['error']}")
            
            output.append("")
        
        return [TextContent(type="text", text="\n".join(output))]
    
    elif name == "karen_check_redis":
        status = check_redis_connection()
        
        output = ["Redis Status:\n"]
        
        if status["connected"]:
            output.append("✓ Connected successfully")
            output.append(f"Version: {status['version']}")
            output.append(f"Uptime: {status['uptime_seconds']} seconds")
            output.append(f"Connected clients: {status['connected_clients']}")
            output.append(f"Memory usage: {status['used_memory']}")
        else:
            output.append("✗ Connection failed")
            output.append(f"Error: {status['error']}")
            output.append("\nTroubleshooting:")
            output.append("1. Check if Redis is running: docker ps | grep redis")
            output.append("2. Start Redis: docker-compose up -d redis")
            output.append("3. Check Redis logs: docker-compose logs redis")
        
        return [TextContent(type="text", text="\n".join(output))]
    
    elif name == "karen_check_celery":
        status = check_celery_status()
        
        output = ["Celery Status:\n"]
        
        # Workers status
        output.append(f"Workers: {status['workers']['status']}")
        if status['workers']['count'] > 0:
            output.append(f"  Active workers: {status['workers']['count']}")
        else:
            output.append("  No active workers found")
        
        if status['workers'].get('error'):
            output.append(f"  Error: {status['workers']['error']}")
        
        # Beat status
        output.append(f"\nBeat Scheduler: {status['beat']['status']}")
        if status['beat'].get('pid'):
            output.append(f"  PID: {status['beat']['pid']}")
        
        if status['beat'].get('error'):
            output.append(f"  Error: {status['beat']['error']}")
        
        # Troubleshooting
        if status['workers']['status'] != 'healthy' or status['beat']['status'] != 'healthy':
            output.append("\nTroubleshooting:")
            output.append("1. Start Celery worker: celery -A src.celery_app:celery_app worker -l INFO")
            output.append("2. Start Celery beat: celery -A src.celery_app:celery_app beat -l INFO")
            output.append("3. Check Docker: docker-compose up -d karen-worker karen-beat")
        
        return [TextContent(type="text", text="\n".join(output))]
    
    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]

async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Server error: {e}", file=sys.stderr)
        sys.exit(1)