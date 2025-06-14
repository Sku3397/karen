#!/usr/bin/env python
"""
Karen Tools MCP Server
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

# Add parent directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp import stdio
from mcp.types import Tool, TextContent

# Global server instance
server = stdio.StdioServer(name="karen-tools")

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

def check_gmail_api() -> Dict[str, Any]:
    """Check Gmail API configuration."""
    result = {
        "status": "unknown",
        "karen_oauth": False,
        "monitor_oauth": False,
        "tokens_found": []
    }
    
    # Check for OAuth token files
    token_files = [
        ("karen_oauth", "gmail_token_karensecretaryai.json"),
        ("monitor_oauth", "gmail_token_hello757handy.json")
    ]
    
    for key, token_file in token_files:
        token_path = PROJECT_ROOT / token_file
        if token_path.exists():
            result[key] = True
            result["tokens_found"].append(token_file)
            
            # Check token validity
            try:
                with open(token_path, 'r') as f:
                    token_data = json.load(f)
                    if 'expiry' in token_data:
                        result[f"{key}_expiry"] = token_data['expiry']
            except Exception:
                pass
    
    # Determine overall status
    if result["karen_oauth"] and result["monitor_oauth"]:
        result["status"] = "healthy"
    elif result["karen_oauth"] or result["monitor_oauth"]:
        result["status"] = "partial"
    else:
        result["status"] = "error"
    
    return result

def check_calendar_api() -> Dict[str, Any]:
    """Check Google Calendar API configuration."""
    result = {
        "status": "unknown",
        "oauth_configured": False,
        "calendar_id": None
    }
    
    # Check for calendar OAuth token
    calendar_token = PROJECT_ROOT / "calendar_token.json"
    if calendar_token.exists():
        result["oauth_configured"] = True
        
        try:
            with open(calendar_token, 'r') as f:
                token_data = json.load(f)
                if 'expiry' in token_data:
                    result["token_expiry"] = token_data['expiry']
        except Exception:
            pass
    
    # Check for calendar ID in environment or config
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        try:
            with open(env_path, 'r') as f:
                for line in f:
                    if 'CALENDAR_ID' in line and '=' in line:
                        cal_id = line.split('=', 1)[1].strip().strip('"\'')
                        if cal_id:
                            result["calendar_id"] = cal_id
                            break
        except Exception:
            pass
    
    # Determine status
    if result["oauth_configured"] and result["calendar_id"]:
        result["status"] = "healthy"
    elif result["oauth_configured"] or result["calendar_id"]:
        result["status"] = "partial"
    else:
        result["status"] = "error"
    
    return result

def check_gemini_llm() -> Dict[str, Any]:
    """Check Google Gemini LLM connectivity."""
    result = {
        "status": "unknown",
        "api_key_configured": False,
        "model": "gemini-pro"
    }
    
    # Check for API key in environment
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        try:
            with open(env_path, 'r') as f:
                for line in f:
                    if 'GEMINI_API_KEY' in line and '=' in line:
                        api_key = line.split('=', 1)[1].strip().strip('"\'')
                        if api_key and len(api_key) > 10:
                            result["api_key_configured"] = True
                            result["api_key_prefix"] = api_key[:8] + "..."
                            break
        except Exception:
            pass
    
    # Test connectivity if API key is configured
    if result["api_key_configured"]:
        try:
            # Simple test - just check if we can import the module
            import google.generativeai as genai
            result["status"] = "healthy"
            result["sdk_available"] = True
        except ImportError:
            result["status"] = "partial"
            result["sdk_available"] = False
            result["error"] = "Google Generative AI SDK not installed"
    else:
        result["status"] = "error"
        result["error"] = "API key not configured"
    
    return result

@server.register_tool
async def karen_system_health() -> List[TextContent]:
    """Get comprehensive Karen AI system health status."""
    health = {
        "timestamp": datetime.now().isoformat(),
        "components": {
            "redis": check_redis_connection(),
            "celery": check_celery_status(),
            "gmail_api": check_gmail_api(),
            "calendar_api": check_calendar_api(),
            "gemini_llm": check_gemini_llm()
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
        
        if component == "redis" and status["connected"]:
            output.append(f"  Version: {status['version']}")
            output.append(f"  Uptime: {status['uptime_seconds']} seconds")
            output.append(f"  Memory: {status['used_memory']}")
        elif component == "celery":
            output.append(f"  Workers: {status['workers']['count']} active")
            output.append(f"  Beat: {status['beat']['status']}")
        elif component == "gmail_api":
            output.append(f"  Karen OAuth: {'✓' if status['karen_oauth'] else '✗'}")
            output.append(f"  Monitor OAuth: {'✓' if status['monitor_oauth'] else '✗'}")
        elif component == "calendar_api":
            output.append(f"  OAuth: {'✓' if status['oauth_configured'] else '✗'}")
            output.append(f"  Calendar ID: {'✓' if status['calendar_id'] else '✗'}")
        elif component == "gemini_llm":
            output.append(f"  API Key: {'✓' if status['api_key_configured'] else '✗'}")
            if status.get('sdk_available') is not None:
                output.append(f"  SDK: {'✓' if status['sdk_available'] else '✗'}")
        
        if status.get("error"):
            output.append(f"  Error: {status['error']}")
        
        output.append("")
    
    return [TextContent(type="text", text="\n".join(output))]

@server.register_tool
async def karen_check_redis() -> List[TextContent]:
    """Check Redis server connectivity and status."""
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

@server.register_tool
async def karen_check_celery() -> List[TextContent]:
    """Check Celery workers and beat status."""
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

@server.register_tool
async def karen_check_gmail() -> List[TextContent]:
    """Check Gmail API configuration and health."""
    status = check_gmail_api()
    
    output = ["Gmail API Status:\n"]
    
    output.append(f"Overall status: {status['status']}")
    output.append(f"Karen secretary OAuth: {'✓ Configured' if status['karen_oauth'] else '✗ Not configured'}")
    output.append(f"Monitor account OAuth: {'✓ Configured' if status['monitor_oauth'] else '✗ Not configured'}")
    
    if status['tokens_found']:
        output.append(f"\nTokens found: {', '.join(status['tokens_found'])}")
    
    # Check token expiry
    for key in ['karen_oauth_expiry', 'monitor_oauth_expiry']:
        if key in status:
            output.append(f"{key.replace('_', ' ').title()}: {status[key]}")
    
    # Troubleshooting
    if status['status'] != 'healthy':
        output.append("\nSetup instructions:")
        if not status['karen_oauth']:
            output.append("1. Run: python setup_karen_oauth.py")
        if not status['monitor_oauth']:
            output.append("2. Run: python setup_monitor_oauth.py")
    
    return [TextContent(type="text", text="\n".join(output))]

@server.register_tool
async def karen_check_calendar() -> List[TextContent]:
    """Check Google Calendar API configuration."""
    status = check_calendar_api()
    
    output = ["Google Calendar API Status:\n"]
    
    output.append(f"Overall status: {status['status']}")
    output.append(f"OAuth configured: {'✓' if status['oauth_configured'] else '✗'}")
    output.append(f"Calendar ID: {'✓ ' + status['calendar_id'][:20] + '...' if status['calendar_id'] else '✗ Not configured'}")
    
    if 'token_expiry' in status:
        output.append(f"Token expiry: {status['token_expiry']}")
    
    # Troubleshooting
    if status['status'] != 'healthy':
        output.append("\nSetup instructions:")
        if not status['oauth_configured']:
            output.append("1. Run: python setup_calendar_oauth.py")
        if not status['calendar_id']:
            output.append("2. Add CALENDAR_ID to .env file")
    
    return [TextContent(type="text", text="\n".join(output))]

@server.register_tool
async def karen_check_gemini() -> List[TextContent]:
    """Check Google Gemini LLM connectivity."""
    status = check_gemini_llm()
    
    output = ["Google Gemini LLM Status:\n"]
    
    output.append(f"Status: {status['status']}")
    output.append(f"API Key: {'✓ Configured' if status['api_key_configured'] else '✗ Not configured'}")
    
    if status.get('api_key_prefix'):
        output.append(f"API Key prefix: {status['api_key_prefix']}")
    
    if status.get('sdk_available') is not None:
        output.append(f"SDK installed: {'✓' if status['sdk_available'] else '✗'}")
    
    output.append(f"Model: {status['model']}")
    
    if status.get('error'):
        output.append(f"\nError: {status['error']}")
    
    # Troubleshooting
    if status['status'] != 'healthy':
        output.append("\nSetup instructions:")
        if not status['api_key_configured']:
            output.append("1. Add GEMINI_API_KEY to .env file")
        if status.get('sdk_available') == False:
            output.append("2. Install SDK: pip install google-generativeai")
    
    return [TextContent(type="text", text="\n".join(output))]

# Tool definitions for registration
TOOLS = [
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
    ),
    Tool(
        name="karen_check_gmail",
        description="Check Gmail API configuration and OAuth status",
        inputSchema={"type": "object", "properties": {}}
    ),
    Tool(
        name="karen_check_calendar",
        description="Check Google Calendar API configuration",
        inputSchema={"type": "object", "properties": {}}
    ),
    Tool(
        name="karen_check_gemini",
        description="Check Google Gemini LLM connectivity",
        inputSchema={"type": "object", "properties": {}}
    )
]

@server.list_tools
async def list_tools() -> List[Tool]:
    """List available tools."""
    return TOOLS

async def main():
    """Run the MCP server."""
    async with server:
        await server.run()

if __name__ == "__main__":
    asyncio.run(main())