#!/usr/bin/env python3
"""
Karen AI MCP Server - Corrected Implementation
Provides real status monitoring for the Karen handyman business automation system
"""

import asyncio
import json
import os
import sys
import subprocess
import redis
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import mcp.types as types
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio

# Add the src directory to Python path
sys.path.append(str(Path(__file__).parent / "src"))

class KarenSystemMonitor:
    """Real system monitoring for Karen AI components"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.env_file = self.project_root / ".env"
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, str]:
        """Load configuration from .env file"""
        config = {}
        if self.env_file.exists():
            with open(self.env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        config[key.strip()] = value.strip()
        return config
    
    async def check_redis_connectivity(self) -> Dict[str, Any]:
        """Check Redis connection and basic info"""
        try:
            redis_url = self.config.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
            r = redis.from_url(redis_url)
            
            # Test connection
            await asyncio.get_event_loop().run_in_executor(None, r.ping)
            
            # Get Redis info
            info = await asyncio.get_event_loop().run_in_executor(None, r.info)
            
            return {
                "status": "connected",
                "redis_version": info.get('redis_version'),
                "connected_clients": info.get('connected_clients'),
                "used_memory_human": info.get('used_memory_human'),
                "total_connections_received": info.get('total_connections_received'),
                "url": redis_url.split('@')[-1] if '@' in redis_url else redis_url  # Hide credentials
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "url": self.config.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
            }
    
    async def check_celery_worker_status(self) -> Dict[str, Any]:
        """Check if Celery worker processes are running"""
        try:
            # Check for running processes
            result = subprocess.run(
                ['ps', 'aux'], 
                capture_output=True, 
                text=True,
                timeout=10
            )
            
            celery_processes = [
                line for line in result.stdout.split('\n')
                if 'celery' in line and 'src.celery_app' in line and 'worker' in line
            ]
            
            worker_count = len(celery_processes)
            
            # Try to get worker stats via Redis if available
            worker_stats = {}
            try:
                redis_url = self.config.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
                r = redis.from_url(redis_url)
                
                # Check for active workers in Celery
                inspect_result = subprocess.run(
                    [sys.executable, '-m', 'celery', '-A', 'src.celery_app:celery_app', 'inspect', 'active'],
                    capture_output=True,
                    text=True,
                    timeout=15,
                    cwd=self.project_root
                )
                
                if inspect_result.returncode == 0:
                    worker_stats["active_tasks"] = "Available" if inspect_result.stdout.strip() else "No active tasks"
                
            except Exception as e:
                worker_stats["inspect_error"] = str(e)
            
            return {
                "status": "running" if worker_count > 0 else "stopped",
                "worker_processes": worker_count,
                "process_details": celery_processes[:3],  # Show first 3 processes
                "worker_stats": worker_stats
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def check_celery_beat_status(self) -> Dict[str, Any]:
        """Check if Celery Beat scheduler is running"""
        try:
            # Check for running beat process
            result = subprocess.run(
                ['ps', 'aux'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            beat_processes = [
                line for line in result.stdout.split('\n')
                if 'celery' in line and 'src.celery_app' in line and 'beat' in line
            ]
            
            # Check for beat schedule database
            schedule_db = self.project_root / "celerybeat-schedule.sqlite3"
            schedule_exists = schedule_db.exists()
            
            schedule_info = {}
            if schedule_exists:
                stat = schedule_db.stat()
                schedule_info = {
                    "last_modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "size_bytes": stat.st_size
                }
            
            return {
                "status": "running" if len(beat_processes) > 0 else "stopped",
                "beat_processes": len(beat_processes),
                "schedule_database": {
                    "exists": schedule_exists,
                    **schedule_info
                },
                "process_details": beat_processes[:1] if beat_processes else []
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def check_gmail_tokens(self) -> Dict[str, Any]:
        """Check Gmail API token validity for both accounts"""
        token_status = {}
        
        # Check Karen's sending account token
        karen_token_path = self.project_root / self.config.get('SECRETARY_TOKEN_PATH', 'gmail_token_karen.json')
        token_status['karen_sender'] = await self._check_single_gmail_token(
            karen_token_path, 
            self.config.get('SECRETARY_EMAIL_ADDRESS', 'karensecretaryai@gmail.com')
        )
        
        # Check monitored account token
        monitor_token_path = self.project_root / self.config.get('MONITORED_EMAIL_TOKEN_PATH', 'gmail_token_monitor.json')
        token_status['monitored_account'] = await self._check_single_gmail_token(
            monitor_token_path,
            self.config.get('MONITORED_EMAIL_ACCOUNT', 'hello@757handy.com')
        )
        
        return token_status
    
    async def _check_single_gmail_token(self, token_path: Path, email: str) -> Dict[str, Any]:
        """Check a single Gmail token's validity"""
        try:
            if not token_path.exists():
                return {
                    "status": "missing",
                    "email": email,
                    "token_path": str(token_path)
                }
            
            # Load and validate token
            creds = Credentials.from_authorized_user_file(str(token_path))
            
            if not creds.valid:
                if creds.expired and creds.refresh_token:
                    try:
                        creds.refresh(Request())
                        # Save refreshed token
                        with open(token_path, 'w') as f:
                            f.write(creds.to_json())
                        status = "refreshed"
                    except Exception as refresh_error:
                        return {
                            "status": "expired",
                            "email": email,
                            "error": str(refresh_error)
                        }
                else:
                    return {
                        "status": "invalid",
                        "email": email,
                        "has_refresh_token": bool(creds.refresh_token)
                    }
            else:
                status = "valid"
            
            # Test API access
            try:
                service = build('gmail', 'v1', credentials=creds)
                profile = service.users().getProfile(userId='me').execute()
                
                return {
                    "status": status,
                    "email": email,
                    "profile_email": profile.get('emailAddress'),
                    "messages_total": profile.get('messagesTotal', 0),
                    "threads_total": profile.get('threadsTotal', 0)
                }
            except Exception as api_error:
                return {
                    "status": "api_error",
                    "email": email,
                    "error": str(api_error)
                }
                
        except Exception as e:
            return {
                "status": "error",
                "email": email,
                "error": str(e)
            }
    
    async def check_calendar_api(self) -> Dict[str, Any]:
        """Check Google Calendar API connectivity"""
        try:
            calendar_token_path = self.project_root / self.config.get('GOOGLE_CALENDAR_TOKEN_PATH', 'gmail_token_monitor.json')
            
            if not calendar_token_path.exists():
                return {
                    "status": "token_missing",
                    "token_path": str(calendar_token_path)
                }
            
            creds = Credentials.from_authorized_user_file(str(calendar_token_path))
            
            if not creds.valid:
                if creds.expired and creds.refresh_token:
                    creds.refresh(Request())
            
            service = build('calendar', 'v3', credentials=creds)
            
            # Test API access
            calendar_id = self.config.get('CALENDAR_ID', 'primary')
            calendar = service.calendars().get(calendarId=calendar_id).execute()
            
            # Get recent events
            now = datetime.utcnow().isoformat() + 'Z'
            events_result = service.events().list(
                calendarId=calendar_id,
                timeMin=now,
                maxResults=5,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            return {
                "status": "connected",
                "calendar_name": calendar.get('summary'),
                "calendar_id": calendar_id,
                "timezone": calendar.get('timeZone'),
                "upcoming_events": len(events_result.get('items', []))
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def check_gemini_api(self) -> Dict[str, Any]:
        """Check Google Gemini API connectivity"""
        try:
            api_key = self.config.get('GEMINI_API_KEY')
            if not api_key:
                return {
                    "status": "no_api_key",
                    "error": "GEMINI_API_KEY not found in configuration"
                }
            
            # Test API with a simple request
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content("Hello, this is a test.")
            
            return {
                "status": "connected",
                "model": "gemini-pro",
                "test_response_length": len(response.text) if response.text else 0
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def check_recent_activity(self) -> Dict[str, Any]:
        """Check recent system activity from logs"""
        try:
            activity = {}
            
            # Check Celery worker logs
            worker_log = self.project_root / "celery_worker_debug_logs_new.txt"
            if worker_log.exists():
                stat = worker_log.stat()
                activity['worker_log'] = {
                    "last_modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "size_bytes": stat.st_size,
                    "recent_activity": stat.st_mtime > (datetime.now().timestamp() - 3600)  # Within last hour
                }
            
            # Check Celery beat logs
            beat_log = self.project_root / "celery_beat_logs_new.txt"
            if beat_log.exists():
                stat = beat_log.stat()
                activity['beat_log'] = {
                    "last_modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "size_bytes": stat.st_size,
                    "recent_activity": stat.st_mtime > (datetime.now().timestamp() - 3600)
                }
            
            return {
                "status": "checked",
                "activity": activity
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def get_system_health_summary(self) -> Dict[str, Any]:
        """Get overall system health summary"""
        redis_status = await self.check_redis_connectivity()
        worker_status = await self.check_celery_worker_status()
        beat_status = await self.check_celery_beat_status()
        gmail_status = await self.check_gmail_tokens()
        calendar_status = await self.check_calendar_api()
        gemini_status = await self.check_gemini_api()
        activity_status = await self.check_recent_activity()
        
        # Calculate overall health
        critical_components = [
            redis_status['status'] in ['connected'],
            worker_status['status'] in ['running'],
            beat_status['status'] in ['running'],
            gmail_status['karen_sender']['status'] in ['valid', 'refreshed'],
            gmail_status['monitored_account']['status'] in ['valid', 'refreshed'],
            calendar_status['status'] in ['connected'],
            gemini_status['status'] in ['connected']
        ]
        
        healthy_components = sum(critical_components)
        total_components = len(critical_components)
        health_percentage = (healthy_components / total_components) * 100
        
        overall_status = "healthy" if health_percentage >= 85 else "degraded" if health_percentage >= 50 else "critical"
        
        return {
            "overall_status": overall_status,
            "health_percentage": round(health_percentage, 1),
            "healthy_components": healthy_components,
            "total_components": total_components,
            "timestamp": datetime.now().isoformat(),
            "components": {
                "redis": redis_status,
                "celery_worker": worker_status,
                "celery_beat": beat_status,
                "gmail_tokens": gmail_status,
                "calendar_api": calendar_status,
                "gemini_api": gemini_status,
                "recent_activity": activity_status
            }
        }


# Initialize the MCP server
app = Server("karen-tools")
monitor = KarenSystemMonitor()

@app.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools for Karen AI system monitoring"""
    return [
        types.Tool(
            name="get_karen_status",
            description="Get comprehensive status of the Karen AI handyman business automation system",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        types.Tool(
            name="get_component_status",
            description="Get detailed status of a specific Karen AI system component",
            inputSchema={
                "type": "object",
                "properties": {
                    "component": {
                        "type": "string",
                        "enum": ["redis", "celery_worker", "celery_beat", "gmail", "calendar", "gemini", "activity"],
                        "description": "The system component to check"
                    }
                },
                "required": ["component"]
            }
        )
    ]

@app.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """Handle tool calls for Karen AI system monitoring"""
    
    if name == "get_karen_status":
        try:
            status = await monitor.get_system_health_summary()
            
            # Format the response
            overall = status['overall_status'].upper()
            health = status['health_percentage']
            
            status_emoji = "🟢" if overall == "HEALTHY" else "🟡" if overall == "DEGRADED" else "🔴"
            
            response = f"""🔧 Karen AI Handyman Business System Status

{status_emoji} **Overall Status: {overall}** ({health}% healthy)
📊 Components: {status['healthy_components']}/{status['total_components']} operational
🕐 Last Check: {status['timestamp']}

**Core Components:**
🔗 Redis Broker: {status['components']['redis']['status'].title()}
⚙️  Celery Worker: {status['components']['celery_worker']['status'].title()}
📅 Celery Beat: {status['components']['celery_beat']['status'].title()}
📧 Gmail APIs: Karen({status['components']['gmail_tokens']['karen_sender']['status']}) | Monitor({status['components']['gmail_tokens']['monitored_account']['status']})
📅 Calendar API: {status['components']['calendar_api']['status'].title()}
🤖 Gemini LLM: {status['components']['gemini_api']['status'].title()}

**System Details:**
- **Redis**: {status['components']['redis'].get('redis_version', 'Unknown')} | {status['components']['redis'].get('connected_clients', '?')} clients
- **Workers**: {status['components']['celery_worker'].get('worker_processes', 0)} running
- **Schedule DB**: {'✓' if status['components']['celery_beat'].get('schedule_database', {}).get('exists') else '✗'} exists
- **Gmail Tokens**: {status['components']['gmail_tokens']['karen_sender'].get('email', 'Unknown')} / {status['components']['gmail_tokens']['monitored_account'].get('email', 'Unknown')}

This is the REAL Karen AI system for handyman business automation! 🛠️"""

            return [types.TextContent(type="text", text=response)]
            
        except Exception as e:
            return [types.TextContent(type="text", text=f"❌ Error getting Karen AI status: {str(e)}")]
    
    elif name == "get_component_status":
        component = arguments.get("component")
        
        try:
            if component == "redis":
                status = await monitor.check_redis_connectivity()
            elif component == "celery_worker":
                status = await monitor.check_celery_worker_status()
            elif component == "celery_beat":
                status = await monitor.check_celery_beat_status()
            elif component == "gmail":
                status = await monitor.check_gmail_tokens()
            elif component == "calendar":
                status = await monitor.check_calendar_api()
            elif component == "gemini":
                status = await monitor.check_gemini_api()
            elif component == "activity":
                status = await monitor.check_recent_activity()
            else:
                return [types.TextContent(type="text", text=f"❌ Unknown component: {component}")]
            
            formatted_status = json.dumps(status, indent=2)
            return [types.TextContent(type="text", text=f"📊 **{component.title()} Status:**\n```json\n{formatted_status}\n```")]
            
        except Exception as e:
            return [types.TextContent(type="text", text=f"❌ Error checking {component}: {str(e)}")]
    
    else:
        return [types.TextContent(type="text", text=f"❌ Unknown tool: {name}")]


async def main():
    """Run the Karen AI MCP server"""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="karen-tools",
                server_version="1.0.0",
                capabilities=app.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(main())