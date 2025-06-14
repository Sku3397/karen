# mcp_agent_monitor_simple.py
import asyncio
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any

try:
    from mcp.server import Server
    from mcp.types import Resource, Tool, TextContent
except ImportError:
    print("MCP not installed. Installing...")
    import subprocess
    subprocess.check_call(["pip", "install", "mcp"])
    from mcp.server import Server
    from mcp.types import Resource, Tool, TextContent

class KarenAgentMonitor:
    """Simple MCP Server for monitoring Karen AI agents"""
    
    def __init__(self):
        self.server = Server("karen-agent-monitor")
        self.project_root = Path(os.getenv("KAREN_PROJECT_ROOT", "."))
        self.setup_handlers()
        
    def setup_handlers(self):
        """Set up MCP handlers"""
        
        @self.server.list_resources()
        async def handle_list_resources():
            """List available monitoring resources"""
            return [
                Resource(
                    uri="karen://status",
                    name="Agent Status",
                    description="Current status of all agents"
                ),
                Resource(
                    uri="karen://tasks",
                    name="Task Progress",
                    description="Task completion progress"
                ),
                Resource(
                    uri="karen://activities",
                    name="Recent Activities",
                    description="Recent agent activities"
                )
            ]
        
        @self.server.read_resource()
        async def handle_read_resource(uri: str):
            """Read a specific resource"""
            
            if uri == "karen://status":
                return await self._get_status()
            elif uri == "karen://tasks":
                return await self._get_tasks()
            elif uri == "karen://activities":
                return await self._get_activities()
            else:
                return TextContent(text=f"Unknown resource: {uri}")
    
    async def _get_status(self):
        """Get agent status"""
        status_file = self.project_root / "autonomous_state.json"
        if status_file.exists():
            with open(status_file, 'r') as f:
                data = json.load(f)
            return TextContent(text=json.dumps(data, indent=2))
        return TextContent(text="No status file found")
    
    async def _get_tasks(self):
        """Get task progress"""
        task_file = self.project_root / "tasks" / "eigencode_assigned_tasks.json"
        if task_file.exists():
            with open(task_file, 'r') as f:
                tasks = json.load(f)
            
            total = len(tasks)
            completed = len([t for t in tasks if t.get('status') in ['completed', 'done']])
            pending = len([t for t in tasks if t.get('status') == 'pending'])
            in_progress = len([t for t in tasks if t.get('status') == 'in_progress'])
            
            summary = {
                "total_tasks": total,
                "completed": completed,
                "pending": pending,
                "in_progress": in_progress,
                "completion_rate": f"{(completed/total*100):.1f}%" if total > 0 else "0%"
            }
            
            return TextContent(text=json.dumps(summary, indent=2))
        return TextContent(text="No task file found")
    
    async def _get_activities(self):
        """Get recent activities"""
        activity_file = self.project_root / "agent_activities.jsonl"
        if activity_file.exists():
            activities = []
            with open(activity_file, 'r') as f:
                for line in f:
                    try:
                        activities.append(json.loads(line.strip()))
                    except:
                        pass
            
            # Get last 10 activities
            recent = activities[-10:]
            return TextContent(text=json.dumps(recent, indent=2))
        return TextContent(text="No activities found")
    
    async def run(self):
        """Run the MCP server"""
        from mcp.server.stdio import stdio_server
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="karen-agent-monitor",
                    server_version="1.0.0"
                )
            )

if __name__ == "__main__":
    monitor = KarenAgentMonitor()
    asyncio.run(monitor.run())