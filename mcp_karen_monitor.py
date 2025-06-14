#!/usr/bin/env python3
"""
Karen AI Agent Monitor - MCP Server
Provides real-time monitoring of Karen AI agent system via Model Context Protocol
"""

import asyncio
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from mcp.server import Server
    from mcp.types import Resource, Tool, TextContent
    from mcp.server.models import InitializationOptions
    from mcp.server.stdio import stdio_server
except ImportError as e:
    logger.error(f"MCP SDK not installed: {e}")
    logger.info("Install with: pip install 'mcp[cli]'")
    sys.exit(1)

class KarenAgentMonitor:
    """MCP Server for monitoring Karen AI agents in real-time"""
    
    def __init__(self):
        self.server = Server("karen-agent-monitor")
        self.project_root = Path(os.getenv("KAREN_PROJECT_ROOT", "."))
        logger.info(f"Monitoring Karen project at: {self.project_root}")
        self.setup_handlers()
        
    def setup_handlers(self):
        """Set up MCP resource and tool handlers"""
        
        @self.server.list_resources()
        async def handle_list_resources():
            """List all available monitoring resources"""
            return [
                Resource(
                    uri="karen://agents/status",
                    name="Agent Status",
                    description="Current status and health of all Karen AI agents",
                    mimeType="application/json"
                ),
                Resource(
                    uri="karen://tasks/progress",
                    name="Task Progress",
                    description="Overall progress on eigencode assigned tasks",
                    mimeType="application/json"
                ),
                Resource(
                    uri="karen://activities/recent",
                    name="Recent Activities",
                    description="Latest agent activities and actions",
                    mimeType="application/json"
                ),
                Resource(
                    uri="karen://system/health",
                    name="System Health",
                    description="Overall system health and service status",
                    mimeType="application/json"
                ),
                Resource(
                    uri="karen://logs/latest",
                    name="Latest Logs",
                    description="Most recent system and agent logs",
                    mimeType="application/json"
                ),
                Resource(
                    uri="karen://files/recent",
                    name="Recent File Changes",
                    description="Files modified in the last 24 hours",
                    mimeType="application/json"
                )
            ]
        
        @self.server.read_resource()
        async def handle_read_resource(uri: str):
            """Read a specific monitoring resource"""
            try:
                if uri == "karen://agents/status":
                    return await self._get_agent_status()
                elif uri == "karen://tasks/progress":
                    return await self._get_task_progress()
                elif uri == "karen://activities/recent":
                    return await self._get_recent_activities()
                elif uri == "karen://system/health":
                    return await self._get_system_health()
                elif uri == "karen://logs/latest":
                    return await self._get_latest_logs()
                elif uri == "karen://files/recent":
                    return await self._get_recent_files()
                else:
                    return TextContent(text=f"❌ Unknown resource: {uri}")
            except Exception as e:
                logger.error(f"Error reading resource {uri}: {e}")
                return TextContent(text=f"❌ Error reading {uri}: {str(e)}")
        
        @self.server.list_tools()
        async def handle_list_tools():
            """List available monitoring tools"""
            return [
                Tool(
                    name="refresh_status",
                    description="Force refresh of all agent monitoring data",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                Tool(
                    name="get_agent_details",
                    description="Get detailed information about a specific agent",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "agent_name": {
                                "type": "string",
                                "description": "Name of the agent (e.g., sms_engineer, test_engineer)"
                            }
                        },
                        "required": ["agent_name"]
                    }
                ),
                Tool(
                    name="analyze_performance",
                    description="Analyze agent performance over a time period",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "hours": {
                                "type": "integer",
                                "description": "Number of hours to analyze (default: 24)",
                                "default": 24
                            }
                        }
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict):
            """Handle tool calls"""
            try:
                if name == "refresh_status":
                    await self._refresh_all_data()
                    return TextContent(text="✅ Agent monitoring data refreshed")
                
                elif name == "get_agent_details":
                    agent_name = arguments.get("agent_name")
                    if not agent_name:
                        return TextContent(text="❌ Agent name is required")
                    details = await self._get_agent_details(agent_name)
                    return TextContent(text=json.dumps(details, indent=2))
                
                elif name == "analyze_performance":
                    hours = arguments.get("hours", 24)
                    analysis = await self._analyze_performance(hours)
                    return TextContent(text=json.dumps(analysis, indent=2))
                
                else:
                    return TextContent(text=f"❌ Unknown tool: {name}")
                    
            except Exception as e:
                logger.error(f"Error calling tool {name}: {e}")
                return TextContent(text=f"❌ Error executing {name}: {str(e)}")
    
    async def _get_agent_status(self) -> TextContent:
        """Get current status of all Karen AI agents"""
        try:
            status_file = self.project_root / "autonomous_state.json"
            
            if not status_file.exists():
                return TextContent(text=json.dumps({
                    "error": "No autonomous_state.json found",
                    "agents": [],
                    "timestamp": datetime.now().isoformat(),
                    "system_status": "❌ Not running"
                }, indent=2))
            
            with open(status_file, 'r') as f:
                status_data = json.load(f)
            
            # Enhance with additional metrics
            enhanced_status = {
                "timestamp": datetime.now().isoformat(),
                "system_status": "✅ Running",
                "agents": [],
                "summary": {
                    "total_agents": 0,
                    "active_agents": 0,
                    "idle_agents": 0,
                    "error_agents": 0
                }
            }
            
            for agent in status_data.get('agents', []):
                agent_info = {
                    **agent,
                    "pending_tasks": await self._count_pending_tasks(agent['name']),
                    "last_activity": await self._get_last_activity(agent['name']),
                    "health_status": self._assess_agent_health(agent)
                }
                enhanced_status["agents"].append(agent_info)
                
                # Update summary
                enhanced_status["summary"]["total_agents"] += 1
                status = agent.get('status', 'unknown')
                if status in ['working', 'active']:
                    enhanced_status["summary"]["active_agents"] += 1
                elif status == 'idle':
                    enhanced_status["summary"]["idle_agents"] += 1
                elif status in ['error', 'failed']:
                    enhanced_status["summary"]["error_agents"] += 1
            
            return TextContent(text=json.dumps(enhanced_status, indent=2))
            
        except Exception as e:
            logger.error(f"Error getting agent status: {e}")
            return TextContent(text=json.dumps({
                "error": f"Failed to read agent status: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }, indent=2))
    
    async def _get_task_progress(self) -> TextContent:
        """Get task progress and completion metrics"""
        try:
            task_file = self.project_root / "tasks" / "eigencode_assigned_tasks.json"
            
            if not task_file.exists():
                return TextContent(text=json.dumps({
                    "error": "No task file found",
                    "total_tasks": 0,
                    "timestamp": datetime.now().isoformat()
                }, indent=2))
            
            with open(task_file, 'r') as f:
                tasks = json.load(f)
            
            # Calculate comprehensive statistics
            total = len(tasks)
            by_status = {}
            by_priority = {}
            by_agent = {}
            stuck_tasks = []
            
            for task in tasks:
                status = task.get('status', 'unknown')
                priority = task.get('priority', 'unknown')
                agent = task.get('assigned_to', 'unassigned')
                
                by_status[status] = by_status.get(status, 0) + 1
                by_priority[priority] = by_priority.get(priority, 0) + 1
                by_agent[agent] = by_agent.get(agent, 0) + 1
                
                # Check for stuck tasks
                if status == 'in_progress' and 'started_at' in task:
                    try:
                        started = datetime.fromisoformat(task['started_at'])
                        duration = datetime.now() - started
                        if duration > timedelta(hours=2):
                            stuck_tasks.append({
                                'id': task.get('id', 'unknown'),
                                'description': task.get('description', 'No description')[:100],
                                'assigned_to': agent,
                                'duration_hours': round(duration.total_seconds() / 3600, 1)
                            })
                    except:
                        pass
            
            # Calculate completion rate
            completed = by_status.get('completed', 0) + by_status.get('done', 0)
            completion_rate = (completed / total * 100) if total > 0 else 0
            
            # Estimate completion time based on recent progress
            estimated_completion = "Unknown"
            if total > 0 and completed > 0:
                remaining = total - completed
                # Simple estimation based on current rate
                if remaining > 0:
                    days_remaining = remaining / max(completed / 7, 1)  # Assume 7 days of work
                    estimated_date = datetime.now() + timedelta(days=days_remaining)
                    estimated_completion = estimated_date.strftime("%Y-%m-%d")
            
            progress_data = {
                "timestamp": datetime.now().isoformat(),
                "total_tasks": total,
                "completed": completed,
                "in_progress": by_status.get('in_progress', 0),
                "pending": by_status.get('pending', 0),
                "completion_rate": f"{completion_rate:.1f}%",
                "estimated_completion": estimated_completion,
                "breakdown": {
                    "by_status": by_status,
                    "by_priority": by_priority,
                    "by_agent": by_agent
                },
                "issues": {
                    "stuck_tasks": stuck_tasks,
                    "unassigned_tasks": by_agent.get('unassigned', 0)
                }
            }
            
            return TextContent(text=json.dumps(progress_data, indent=2))
            
        except Exception as e:
            logger.error(f"Error getting task progress: {e}")
            return TextContent(text=json.dumps({
                "error": f"Failed to read task progress: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }, indent=2))
    
    async def _get_recent_activities(self) -> TextContent:
        """Get recent agent activities"""
        try:
            activity_file = self.project_root / "agent_activities.jsonl"
            
            if not activity_file.exists():
                return TextContent(text=json.dumps({
                    "error": "No activity log found",
                    "activities": [],
                    "timestamp": datetime.now().isoformat()
                }, indent=2))
            
            activities = []
            with open(activity_file, 'r') as f:
                for line in f:
                    try:
                        activity = json.loads(line.strip())
                        activities.append(activity)
                    except:
                        continue
            
            # Get last 50 activities and group by agent
            recent_activities = activities[-50:]
            by_agent = {}
            
            for activity in recent_activities:
                agent = activity.get('agent', 'unknown')
                if agent not in by_agent:
                    by_agent[agent] = []
                by_agent[agent].append(activity)
            
            # Calculate activity metrics
            now = datetime.now()
            last_hour = [a for a in recent_activities 
                        if self._parse_timestamp(a.get('timestamp')) > now - timedelta(hours=1)]
            
            activity_data = {
                "timestamp": datetime.now().isoformat(),
                "total_activities": len(activities),
                "recent_count": len(recent_activities),
                "last_hour_count": len(last_hour),
                "by_agent": by_agent,
                "recent_activities": recent_activities[-10:]  # Last 10 for quick view
            }
            
            return TextContent(text=json.dumps(activity_data, indent=2))
            
        except Exception as e:
            logger.error(f"Error getting activities: {e}")
            return TextContent(text=json.dumps({
                "error": f"Failed to read activities: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }, indent=2))
    
    async def _get_system_health(self) -> TextContent:
        """Get overall system health metrics"""
        try:
            health = {
                "timestamp": datetime.now().isoformat(),
                "services": {},
                "metrics": {},
                "alerts": []
            }
            
            # Check Redis
            try:
                import redis
                r = redis.Redis(host='localhost', port=6379, socket_connect_timeout=1)
                r.ping()
                health["services"]["redis"] = "✅ Running"
            except:
                health["services"]["redis"] = "❌ Not accessible"
                health["alerts"].append("Redis service not accessible")
            
            # Check Celery
            celery_beat_pid = self.project_root / "celerybeat.pid"
            if celery_beat_pid.exists():
                health["services"]["celery_beat"] = "✅ Running"
            else:
                health["services"]["celery_beat"] = "⚠️ Not running"
                health["alerts"].append("Celery Beat not running")
            
            # Check agent status
            status_file = self.project_root / "autonomous_state.json"
            if status_file.exists():
                with open(status_file, 'r') as f:
                    status = json.load(f)
                active_agents = sum(1 for a in status.get('agents', []) 
                                  if a.get('status') in ['working', 'active'])
                health["metrics"]["active_agents"] = active_agents
                health["services"]["autonomous_system"] = "✅ Running"
            else:
                health["services"]["autonomous_system"] = "❌ Not running"
                health["metrics"]["active_agents"] = 0
                health["alerts"].append("Autonomous system not running")
            
            # Check disk space
            try:
                disk_usage = os.statvfs(self.project_root)
                free_space_gb = (disk_usage.f_frsize * disk_usage.f_bavail) / (1024**3)
                health["metrics"]["free_disk_space_gb"] = round(free_space_gb, 2)
                
                if free_space_gb < 1:
                    health["alerts"].append("Low disk space (< 1GB free)")
            except:
                health["metrics"]["free_disk_space_gb"] = "Unknown"
            
            # Check recent errors in logs
            error_count = await self._count_recent_errors()
            health["metrics"]["recent_errors"] = error_count
            if error_count > 10:
                health["alerts"].append(f"High error count: {error_count} errors in last hour")
            
            # Overall health assessment
            if not health["alerts"]:
                health["overall_status"] = "✅ Healthy"
            elif len(health["alerts"]) == 1:
                health["overall_status"] = "⚠️ Warning"
            else:
                health["overall_status"] = "❌ Critical"
            
            return TextContent(text=json.dumps(health, indent=2))
            
        except Exception as e:
            logger.error(f"Error getting system health: {e}")
            return TextContent(text=json.dumps({
                "error": f"Failed to assess system health: {str(e)}",
                "timestamp": datetime.now().isoformat(),
                "overall_status": "❌ Unknown"
            }, indent=2))
    
    async def _get_latest_logs(self) -> TextContent:
        """Get latest log entries from various sources"""
        try:
            log_sources = [
                ("Autonomous System", self.project_root / "logs" / "autonomous_system.log"),
                ("Celery Worker", self.project_root / "celery_worker_debug_logs.txt"),
                ("Agent Activities", self.project_root / "logs" / "agents" / "agent_activity.log"),
                ("Email Agent", self.project_root / "logs" / "email_agent_activity.log")
            ]
            
            all_logs = {
                "timestamp": datetime.now().isoformat(),
                "sources": {}
            }
            
            for source_name, log_file in log_sources:
                if log_file.exists():
                    try:
                        with open(log_file, 'r') as f:
                            lines = f.readlines()
                            recent_lines = [line.strip() for line in lines[-20:] if line.strip()]
                            all_logs["sources"][source_name] = {
                                "file": str(log_file.relative_to(self.project_root)),
                                "recent_entries": recent_lines,
                                "total_lines": len(lines)
                            }
                    except Exception as e:
                        all_logs["sources"][source_name] = {
                            "error": f"Could not read log: {str(e)}"
                        }
                else:
                    all_logs["sources"][source_name] = {
                        "status": "Log file not found"
                    }
            
            return TextContent(text=json.dumps(all_logs, indent=2))
            
        except Exception as e:
            logger.error(f"Error getting logs: {e}")
            return TextContent(text=json.dumps({
                "error": f"Failed to read logs: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }, indent=2))
    
    async def _get_recent_files(self) -> TextContent:
        """Get recently modified files"""
        try:
            cutoff = datetime.now() - timedelta(hours=24)
            recent_files = []
            
            # Check src directory for Python files
            src_dir = self.project_root / "src"
            if src_dir.exists():
                for file_path in src_dir.rglob("*.py"):
                    if any(skip in str(file_path) for skip in ['__pycache__', '.git', 'node_modules']):
                        continue
                    
                    try:
                        stat = file_path.stat()
                        mod_time = datetime.fromtimestamp(stat.st_mtime)
                        
                        if mod_time > cutoff:
                            recent_files.append({
                                "file": str(file_path.relative_to(self.project_root)),
                                "modified": mod_time.isoformat(),
                                "size": stat.st_size,
                                "type": "Python"
                            })
                    except:
                        continue
            
            # Check for other important files
            for pattern in ["*.md", "*.json", "*.yml", "*.yaml"]:
                for file_path in self.project_root.glob(pattern):
                    try:
                        stat = file_path.stat()
                        mod_time = datetime.fromtimestamp(stat.st_mtime)
                        
                        if mod_time > cutoff:
                            recent_files.append({
                                "file": str(file_path.relative_to(self.project_root)),
                                "modified": mod_time.isoformat(),
                                "size": stat.st_size,
                                "type": "Config/Doc"
                            })
                    except:
                        continue
            
            # Sort by modification time
            recent_files.sort(key=lambda x: x['modified'], reverse=True)
            
            file_data = {
                "timestamp": datetime.now().isoformat(),
                "total_recent_files": len(recent_files),
                "files": recent_files[:30]  # Top 30 most recent
            }
            
            return TextContent(text=json.dumps(file_data, indent=2))
            
        except Exception as e:
            logger.error(f"Error getting recent files: {e}")
            return TextContent(text=json.dumps({
                "error": f"Failed to scan recent files: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }, indent=2))
    
    # Helper methods
    async def _count_pending_tasks(self, agent_name: str) -> int:
        """Count pending tasks for a specific agent"""
        try:
            task_file = self.project_root / "tasks" / "eigencode_assigned_tasks.json"
            if task_file.exists():
                with open(task_file, 'r') as f:
                    tasks = json.load(f)
                return sum(1 for t in tasks 
                          if t.get('assigned_to') == agent_name and t.get('status') == 'pending')
        except:
            pass
        return 0
    
    async def _get_last_activity(self, agent_name: str) -> str:
        """Get last activity timestamp for an agent"""
        try:
            activity_file = self.project_root / "agent_activities.jsonl"
            if activity_file.exists():
                with open(activity_file, 'r') as f:
                    for line in reversed(list(f)):
                        try:
                            activity = json.loads(line.strip())
                            if activity.get('agent') == agent_name:
                                return activity.get('timestamp', 'Unknown')
                        except:
                            continue
        except:
            pass
        return "No activity recorded"
    
    def _assess_agent_health(self, agent: Dict) -> str:
        """Assess the health status of an agent"""
        status = agent.get('status', 'unknown')
        last_seen = agent.get('last_seen')
        
        if status in ['error', 'failed']:
            return "❌ Error"
        elif status in ['working', 'active']:
            return "✅ Healthy"
        elif status == 'idle':
            return "⚠️ Idle"
        else:
            return "❓ Unknown"
    
    def _parse_timestamp(self, timestamp_str: Optional[str]) -> datetime:
        """Parse timestamp string safely"""
        if not timestamp_str:
            return datetime.min
        try:
            return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except:
            return datetime.min
    
    async def _count_recent_errors(self) -> int:
        """Count recent error entries in logs"""
        error_count = 0
        cutoff = datetime.now() - timedelta(hours=1)
        
        try:
            log_file = self.project_root / "logs" / "autonomous_system.log"
            if log_file.exists():
                with open(log_file, 'r') as f:
                    for line in f:
                        if 'ERROR' in line.upper() or 'EXCEPTION' in line.upper():
                            error_count += 1
        except:
            pass
        
        return error_count
    
    async def _refresh_all_data(self):
        """Force refresh of all monitoring data"""
        # Could trigger data collection if needed
        logger.info("Refreshing monitoring data")
    
    async def _get_agent_details(self, agent_name: str) -> Dict:
        """Get detailed information about a specific agent"""
        details = {
            "name": agent_name,
            "timestamp": datetime.now().isoformat(),
            "status": "unknown",
            "current_task": None,
            "task_counts": {
                "pending": 0,
                "in_progress": 0,
                "completed": 0
            },
            "recent_activities": [],
            "performance": {}
        }
        
        # Get status from autonomous_state.json
        try:
            status_file = self.project_root / "autonomous_state.json"
            if status_file.exists():
                with open(status_file, 'r') as f:
                    status = json.load(f)
                for agent in status.get('agents', []):
                    if agent['name'] == agent_name:
                        details['status'] = agent.get('status', 'unknown')
                        details['current_task'] = agent.get('current_task')
                        details['last_seen'] = agent.get('last_seen')
                        break
        except:
            pass
        
        # Get task counts
        try:
            task_file = self.project_root / "tasks" / "eigencode_assigned_tasks.json"
            if task_file.exists():
                with open(task_file, 'r') as f:
                    tasks = json.load(f)
                for status_name in ['pending', 'in_progress', 'completed', 'done']:
                    count = sum(1 for t in tasks 
                              if t.get('assigned_to') == agent_name and t.get('status') == status_name)
                    if status_name == 'done':
                        details['task_counts']['completed'] += count
                    else:
                        details['task_counts'][status_name] = count
        except:
            pass
        
        # Get recent activities
        try:
            activity_file = self.project_root / "agent_activities.jsonl"
            if activity_file.exists():
                activities = []
                with open(activity_file, 'r') as f:
                    for line in f:
                        try:
                            activity = json.loads(line.strip())
                            if activity.get('agent') == agent_name:
                                activities.append(activity)
                        except:
                            continue
                details['recent_activities'] = activities[-10:]  # Last 10 activities
        except:
            pass
        
        return details
    
    async def _analyze_performance(self, hours: int) -> Dict:
        """Analyze agent performance over specified time period"""
        cutoff = datetime.now() - timedelta(hours=hours)
        analysis = {
            "period": f"Last {hours} hours",
            "start_time": cutoff.isoformat(),
            "end_time": datetime.now().isoformat(),
            "metrics": {
                "total_activities": 0,
                "activities_per_hour": 0,
                "by_agent": {},
                "files_modified": 0,
                "tasks_completed": 0
            }
        }
        
        # Analyze activities
        try:
            activity_file = self.project_root / "agent_activities.jsonl"
            if activity_file.exists():
                activities = []
                with open(activity_file, 'r') as f:
                    for line in f:
                        try:
                            activity = json.loads(line.strip())
                            activity_time = self._parse_timestamp(activity.get('timestamp'))
                            if activity_time > cutoff:
                                activities.append(activity)
                        except:
                            continue
                
                analysis['metrics']['total_activities'] = len(activities)
                analysis['metrics']['activities_per_hour'] = len(activities) / hours if hours > 0 else 0
                
                # Group by agent
                by_agent = {}
                for activity in activities:
                    agent = activity.get('agent', 'unknown')
                    by_agent[agent] = by_agent.get(agent, 0) + 1
                analysis['metrics']['by_agent'] = by_agent
        except:
            pass
        
        # Analyze file changes
        try:
            files_changed = 0
            src_dir = self.project_root / "src"
            if src_dir.exists():
                for file_path in src_dir.rglob("*.py"):
                    try:
                        stat = file_path.stat()
                        mod_time = datetime.fromtimestamp(stat.st_mtime)
                        if mod_time > cutoff:
                            files_changed += 1
                    except:
                        continue
            analysis['metrics']['files_modified'] = files_changed
        except:
            pass
        
        return analysis
    
    async def run(self):
        """Run the MCP server using stdio transport"""
        logger.info("Starting Karen Agent Monitor MCP Server...")
        
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="karen-agent-monitor",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=None,
                        experimental_capabilities={}
                    )
                )
            )

def main():
    """Main entry point"""
    try:
        monitor = KarenAgentMonitor()
        asyncio.run(monitor.run())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()