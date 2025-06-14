import json
import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

class AgentActivityLogger:
    """
    Logger for tracking agent activities across the autonomous agent system.
    Provides structured logging for agent operations, task completion, and performance metrics.
    """
    
    def __init__(self, log_dir: str = "logs/agents"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup standard Python logger
        self.logger = logging.getLogger(f"agent_activity")
        if not self.logger.handlers:
            handler = logging.FileHandler(self.log_dir / "agent_activity.log")
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def log_activity(
        self, 
        agent_name: str, 
        activity_type: str, 
        details: Dict[str, Any],
        level: str = "INFO"
    ) -> None:
        """
        Log an agent activity with structured data.
        
        Args:
            agent_name: Name of the agent (e.g., "sms_engineer", "memory_engineer")
            activity_type: Type of activity (e.g., "code_enhancement", "task_completion")
            details: Dictionary containing activity details
            level: Log level (DEBUG, INFO, WARNING, ERROR)
        """
        timestamp = datetime.utcnow().isoformat()
        
        # Create structured log entry
        log_entry = {
            "timestamp": timestamp,
            "agent_name": agent_name,
            "activity_type": activity_type,
            "details": details
        }
        
        # Log to standard logger
        log_message = f"[{agent_name}] {activity_type}: {json.dumps(details, indent=2)}"
        getattr(self.logger, level.lower())(log_message)
        
        # Save structured log to JSON file for agent consumption
        self._save_structured_log(agent_name, log_entry)
    
    def _save_structured_log(self, agent_name: str, log_entry: Dict[str, Any]) -> None:
        """Save structured log entry to agent-specific JSON file."""
        agent_log_file = self.log_dir / f"{agent_name}_activity.json"
        
        # Load existing logs or create new list
        logs = []
        if agent_log_file.exists():
            try:
                with open(agent_log_file, 'r') as f:
                    logs = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                logs = []
        
        # Add new log entry
        logs.append(log_entry)
        
        # Keep only last 1000 entries to prevent file bloat
        if len(logs) > 1000:
            logs = logs[-1000:]
        
        # Save updated logs
        with open(agent_log_file, 'w') as f:
            json.dump(logs, f, indent=2, default=str)
    
    def get_agent_activities(
        self, 
        agent_name: str, 
        activity_type: Optional[str] = None,
        limit: int = 100
    ) -> list:
        """
        Retrieve recent activities for a specific agent.
        
        Args:
            agent_name: Name of the agent
            activity_type: Filter by activity type (optional)
            limit: Maximum number of activities to return
            
        Returns:
            List of activity dictionaries
        """
        agent_log_file = self.log_dir / f"{agent_name}_activity.json"
        
        if not agent_log_file.exists():
            return []
        
        try:
            with open(agent_log_file, 'r') as f:
                logs = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []
        
        # Filter by activity type if specified
        if activity_type:
            logs = [log for log in logs if log.get("activity_type") == activity_type]
        
        # Return most recent entries up to limit
        return logs[-limit:] if logs else []
    
    def log_task_completion(
        self, 
        agent_name: str, 
        task_id: str, 
        success: bool, 
        duration_seconds: float,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log task completion with standard metrics."""
        task_details = {
            "task_id": task_id,
            "success": success,
            "duration_seconds": duration_seconds,
            "status": "completed" if success else "failed"
        }
        
        if details:
            task_details.update(details)
        
        self.log_activity(
            agent_name=agent_name,
            activity_type="task_completion",
            details=task_details,
            level="INFO" if success else "WARNING"
        )
    
    def log_performance_metric(
        self, 
        agent_name: str, 
        metric_name: str, 
        metric_value: float,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log performance metrics for agent monitoring."""
        metric_details = {
            "metric_name": metric_name,
            "metric_value": metric_value,
            "context": context or {}
        }
        
        self.log_activity(
            agent_name=agent_name,
            activity_type="performance_metric",
            details=metric_details
        )
    
    def log_error(
        self, 
        agent_name: str, 
        error_type: str, 
        error_message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log agent errors with context."""
        error_details = {
            "error_type": error_type,
            "error_message": error_message,
            "context": context or {}
        }
        
        self.log_activity(
            agent_name=agent_name,
            activity_type="error",
            details=error_details,
            level="ERROR"
        )