"""
Agent Task System - Enhanced task management for Karen AI Secretary
Handles task queuing, distribution, and execution coordination
Instance ID: ORCHESTRATOR-001 Domain
"""
import os
import json
import time
import logging
import threading
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from pathlib import Path
import queue
import uuid
from enum import Enum

# Import orchestrator components
from src.orchestrator import AgentOrchestrator, get_orchestrator_instance, TaskPriority, AgentType

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class TaskExecutionMode(Enum):
    """Task execution modes"""
    IMMEDIATE = "immediate"
    SCHEDULED = "scheduled"
    BATCH = "batch"
    CONDITIONAL = "conditional"

class TaskDependency:
    """Represents a task dependency"""
    
    def __init__(self, task_id: str, dependency_type: str = "completion"):
        self.task_id = task_id
        self.dependency_type = dependency_type  # completion, data, approval
        self.created_at = datetime.now()

class ConditionalTask:
    """Task that executes based on conditions"""
    
    def __init__(self, task_data: Dict[str, Any], condition_func: Callable[[], bool], 
                 condition_description: str):
        self.task_data = task_data
        self.condition_func = condition_func
        self.condition_description = condition_description
        self.created_at = datetime.now()
        self.last_check = None
        self.check_interval = 300  # 5 minutes default

class TaskBatch:
    """Group of related tasks"""
    
    def __init__(self, batch_id: str, batch_name: str, task_ids: List[str], 
                 execution_order: str = "parallel"):
        self.batch_id = batch_id
        self.batch_name = batch_name
        self.task_ids = task_ids
        self.execution_order = execution_order  # parallel, sequential, priority
        self.created_at = datetime.now()
        self.started_at = None
        self.completed_at = None
        self.status = "pending"

class AgentTaskSystem:
    """
    Enhanced task management system that works with the AgentOrchestrator
    Provides advanced task queuing, scheduling, and dependency management
    """
    
    def __init__(self):
        """Initialize the Agent Task System"""
        logger.info("Initializing AgentTaskSystem")
        
        # Get orchestrator instance
        self.orchestrator = get_orchestrator_instance()
        
        # Task scheduling and dependency management
        self.scheduled_tasks = {}  # task_id -> (execution_time, task_data)
        self.conditional_tasks = {}  # task_id -> ConditionalTask
        self.task_dependencies = {}  # task_id -> List[TaskDependency]
        self.task_batches = {}  # batch_id -> TaskBatch
        self.task_templates = {}  # template_name -> task_template
        
        # Task execution tracking
        self.execution_history = []
        self.task_metrics = {
            "total_tasks_created": 0,
            "total_tasks_completed": 0,
            "total_tasks_failed": 0,
            "average_execution_time": 0,
            "tasks_by_agent": {},
            "tasks_by_priority": {}
        }
        
        # Configuration
        self.max_batch_size = 10
        self.default_task_timeout = 1800  # 30 minutes
        self.cleanup_interval = 3600  # 1 hour
        
        # Start background processes
        self._start_background_processes()
        
        logger.info("AgentTaskSystem initialized successfully")
    
    def _start_background_processes(self):
        """Start background monitoring and processing threads"""
        # Scheduled task processor
        self.scheduler_thread = threading.Thread(
            target=self._scheduled_task_processor,
            daemon=True,
            name="TaskScheduler"
        )
        self.scheduler_thread.start()
        
        # Conditional task monitor
        self.conditional_monitor_thread = threading.Thread(
            target=self._conditional_task_monitor,
            daemon=True,
            name="ConditionalTaskMonitor"
        )
        self.conditional_monitor_thread.start()
        
        # Dependency resolver
        self.dependency_resolver_thread = threading.Thread(
            target=self._dependency_resolver,
            daemon=True,
            name="DependencyResolver"
        )
        self.dependency_resolver_thread.start()
        
        # Cleanup thread
        self.cleanup_thread = threading.Thread(
            target=self._cleanup_completed_tasks,
            daemon=True,
            name="TaskCleanup"
        )
        self.cleanup_thread.start()
    
    def create_task_from_template(self, template_name: str, agent_type: str, 
                                params: Optional[Dict] = None, 
                                priority: str = "medium") -> str:
        """Create a task from a predefined template"""
        if template_name not in self.task_templates:
            raise ValueError(f"Unknown task template: {template_name}")
        
        template = self.task_templates[template_name]
        
        # Merge template params with provided params
        task_params = template.get("default_params", {}).copy()
        if params:
            task_params.update(params)
        
        # Create the task
        task_id = self.orchestrator.create_task(
            agent_type=AgentType(agent_type.lower()),
            task_type=template["task_type"],
            description=template["description"].format(**task_params),
            priority=TaskPriority[priority.upper()],
            params=task_params
        )
        
        logger.info(f"Created task {task_id} from template {template_name}")
        self._update_metrics("task_created", agent_type, priority)
        
        return task_id
    
    def create_scheduled_task(self, agent_type: str, task_type: str, description: str,
                            execution_time: datetime, priority: str = "medium",
                            params: Optional[Dict] = None) -> str:
        """Create a task to be executed at a specific time"""
        
        task_data = {
            "agent_type": agent_type,
            "task_type": task_type,
            "description": description,
            "priority": priority,
            "params": params or {}
        }
        
        task_id = f"scheduled_{agent_type}_{task_type}_{datetime.now().timestamp()}_{uuid.uuid4().hex[:8]}"
        
        self.scheduled_tasks[task_id] = (execution_time, task_data)
        
        logger.info(f"Scheduled task {task_id} for execution at {execution_time}")
        
        return task_id
    
    def create_conditional_task(self, agent_type: str, task_type: str, description: str,
                              condition_func: Callable[[], bool], condition_description: str,
                              priority: str = "medium", params: Optional[Dict] = None,
                              check_interval: int = 300) -> str:
        """Create a task that executes when a condition is met"""
        
        task_data = {
            "agent_type": agent_type,
            "task_type": task_type,
            "description": description,
            "priority": priority,
            "params": params or {}
        }
        
        task_id = f"conditional_{agent_type}_{task_type}_{datetime.now().timestamp()}_{uuid.uuid4().hex[:8]}"
        
        conditional_task = ConditionalTask(task_data, condition_func, condition_description)
        conditional_task.check_interval = check_interval
        
        self.conditional_tasks[task_id] = conditional_task
        
        logger.info(f"Created conditional task {task_id}: {condition_description}")
        
        return task_id
    
    def create_task_batch(self, batch_name: str, tasks: List[Dict[str, Any]], 
                         execution_order: str = "parallel") -> str:
        """Create a batch of related tasks"""
        
        batch_id = f"batch_{batch_name}_{datetime.now().timestamp()}_{uuid.uuid4().hex[:8]}"
        task_ids = []
        
        # Create all tasks in the batch
        for task_spec in tasks:
            if len(task_ids) >= self.max_batch_size:
                logger.warning(f"Batch {batch_id} exceeds max size {self.max_batch_size}")
                break
            
            task_id = self.orchestrator.create_task(
                agent_type=AgentType(task_spec["agent_type"].lower()),
                task_type=task_spec["task_type"],
                description=task_spec["description"],
                priority=TaskPriority[task_spec.get("priority", "medium").upper()],
                params=task_spec.get("params", {})
            )
            
            task_ids.append(task_id)
        
        # Create batch record
        batch = TaskBatch(batch_id, batch_name, task_ids, execution_order)
        self.task_batches[batch_id] = batch
        
        logger.info(f"Created task batch {batch_id} with {len(task_ids)} tasks")
        
        return batch_id
    
    def add_task_dependency(self, task_id: str, depends_on_task_id: str, 
                          dependency_type: str = "completion"):
        """Add a dependency between tasks"""
        
        if task_id not in self.task_dependencies:
            self.task_dependencies[task_id] = []
        
        dependency = TaskDependency(depends_on_task_id, dependency_type)
        self.task_dependencies[task_id].append(dependency)
        
        logger.info(f"Added dependency: task {task_id} depends on {depends_on_task_id} ({dependency_type})")
    
    def create_task_template(self, template_name: str, task_type: str, description: str,
                           default_params: Optional[Dict] = None, 
                           required_params: Optional[List[str]] = None):
        """Create a reusable task template"""
        
        template = {
            "task_type": task_type,
            "description": description,
            "default_params": default_params or {},
            "required_params": required_params or [],
            "created_at": datetime.now().isoformat()
        }
        
        self.task_templates[template_name] = template
        
        logger.info(f"Created task template: {template_name}")
    
    def _scheduled_task_processor(self):
        """Background processor for scheduled tasks"""
        logger.info("Starting scheduled task processor")
        
        while True:
            try:
                current_time = datetime.now()
                tasks_to_execute = []
                
                # Find tasks ready for execution
                for task_id, (execution_time, task_data) in list(self.scheduled_tasks.items()):
                    if current_time >= execution_time:
                        tasks_to_execute.append((task_id, task_data))
                
                # Execute ready tasks
                for task_id, task_data in tasks_to_execute:
                    logger.info(f"Executing scheduled task: {task_id}")
                    
                    try:
                        # Create the actual task
                        actual_task_id = self.orchestrator.create_task(
                            agent_type=AgentType(task_data["agent_type"].lower()),
                            task_type=task_data["task_type"],
                            description=task_data["description"],
                            priority=TaskPriority[task_data["priority"].upper()],
                            params=task_data["params"]
                        )
                        
                        # Remove from scheduled tasks
                        del self.scheduled_tasks[task_id]
                        
                        logger.info(f"Scheduled task {task_id} executed as {actual_task_id}")
                        
                    except Exception as e:
                        logger.error(f"Failed to execute scheduled task {task_id}: {e}")
                        # Remove failed task from schedule
                        del self.scheduled_tasks[task_id]
                
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in scheduled task processor: {e}", exc_info=True)
                time.sleep(60)
    
    def _conditional_task_monitor(self):
        """Background monitor for conditional tasks"""
        logger.info("Starting conditional task monitor")
        
        while True:
            try:
                current_time = datetime.now()
                tasks_to_execute = []
                
                # Check conditions for all conditional tasks
                for task_id, conditional_task in list(self.conditional_tasks.items()):
                    # Check if it's time to evaluate the condition
                    if (conditional_task.last_check is None or 
                        (current_time - conditional_task.last_check).total_seconds() >= conditional_task.check_interval):
                        
                        conditional_task.last_check = current_time
                        
                        try:
                            # Evaluate the condition
                            if conditional_task.condition_func():
                                tasks_to_execute.append((task_id, conditional_task))
                                logger.info(f"Condition met for task {task_id}: {conditional_task.condition_description}")
                                
                        except Exception as e:
                            logger.error(f"Error evaluating condition for task {task_id}: {e}")
                
                # Execute tasks whose conditions are met
                for task_id, conditional_task in tasks_to_execute:
                    try:
                        task_data = conditional_task.task_data
                        
                        # Create the actual task
                        actual_task_id = self.orchestrator.create_task(
                            agent_type=AgentType(task_data["agent_type"].lower()),
                            task_type=task_data["task_type"],
                            description=task_data["description"],
                            priority=TaskPriority[task_data["priority"].upper()],
                            params=task_data["params"]
                        )
                        
                        # Remove from conditional tasks
                        del self.conditional_tasks[task_id]
                        
                        logger.info(f"Conditional task {task_id} executed as {actual_task_id}")
                        
                    except Exception as e:
                        logger.error(f"Failed to execute conditional task {task_id}: {e}")
                        # Remove failed task
                        del self.conditional_tasks[task_id]
                
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in conditional task monitor: {e}", exc_info=True)
                time.sleep(60)
    
    def _dependency_resolver(self):
        """Background processor for task dependencies"""
        logger.info("Starting dependency resolver")
        
        while True:
            try:
                # Check for tasks with resolved dependencies
                tasks_to_release = []
                
                for task_id, dependencies in list(self.task_dependencies.items()):
                    # Check if task is still pending (not yet started)
                    if task_id in self.orchestrator.active_tasks:
                        task = self.orchestrator.active_tasks[task_id]
                        
                        # Only check dependencies for pending tasks
                        if task.status.value == "pending":
                            all_dependencies_met = True
                            
                            for dependency in dependencies:
                                dep_task_id = dependency.task_id
                                
                                # Check if dependency is completed
                                if dependency.dependency_type == "completion":
                                    if dep_task_id not in self.orchestrator.completed_tasks:
                                        all_dependencies_met = False
                                        break
                                    
                                    dep_task = self.orchestrator.completed_tasks[dep_task_id]
                                    if dep_task.status.value != "completed":
                                        all_dependencies_met = False
                                        break
                            
                            if all_dependencies_met:
                                tasks_to_release.append(task_id)
                
                # Release tasks with satisfied dependencies
                for task_id in tasks_to_release:
                    logger.info(f"Dependencies satisfied for task {task_id}, releasing for execution")
                    # Dependencies are satisfied, task can proceed normally
                    del self.task_dependencies[task_id]
                
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in dependency resolver: {e}", exc_info=True)
                time.sleep(60)
    
    def _cleanup_completed_tasks(self):
        """Background cleanup of old completed tasks"""
        logger.info("Starting task cleanup processor")
        
        while True:
            try:
                current_time = datetime.now()
                cleanup_age = timedelta(hours=24)  # Keep completed tasks for 24 hours
                
                # Clean up old execution history
                self.execution_history = [
                    entry for entry in self.execution_history
                    if current_time - datetime.fromisoformat(entry["timestamp"]) < cleanup_age
                ]
                
                # Archive old completed tasks
                archive_tasks = []
                for task_id, task in list(self.orchestrator.completed_tasks.items()):
                    if current_time - task.completed_at > cleanup_age:
                        archive_tasks.append((task_id, task))
                
                if archive_tasks:
                    # Save to archive file
                    archive_file = f"logs/tasks/archived_tasks_{current_time.strftime('%Y%m%d')}.json"
                    archive_data = {
                        "archived_at": current_time.isoformat(),
                        "tasks": [task.to_dict() for _, task in archive_tasks]
                    }
                    
                    with open(archive_file, 'w') as f:
                        json.dump(archive_data, f, indent=2)
                    
                    # Remove from active memory
                    for task_id, _ in archive_tasks:
                        del self.orchestrator.completed_tasks[task_id]
                    
                    logger.info(f"Archived {len(archive_tasks)} completed tasks to {archive_file}")
                
                time.sleep(self.cleanup_interval)
                
            except Exception as e:
                logger.error(f"Error in task cleanup: {e}", exc_info=True)
                time.sleep(3600)  # Wait longer on error
    
    def _update_metrics(self, event_type: str, agent_type: str = None, priority: str = None):
        """Update task metrics"""
        if event_type == "task_created":
            self.task_metrics["total_tasks_created"] += 1
            
            if agent_type:
                agent_key = f"tasks_by_agent.{agent_type}"
                if agent_type not in self.task_metrics["tasks_by_agent"]:
                    self.task_metrics["tasks_by_agent"][agent_type] = 0
                self.task_metrics["tasks_by_agent"][agent_type] += 1
            
            if priority:
                if priority not in self.task_metrics["tasks_by_priority"]:
                    self.task_metrics["tasks_by_priority"][priority] = 0
                self.task_metrics["tasks_by_priority"][priority] += 1
        
        elif event_type == "task_completed":
            self.task_metrics["total_tasks_completed"] += 1
        
        elif event_type == "task_failed":
            self.task_metrics["total_tasks_failed"] += 1
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive task system status"""
        return {
            "task_system_status": "active",
            "scheduled_tasks": len(self.scheduled_tasks),
            "conditional_tasks": len(self.conditional_tasks),
            "task_dependencies": len(self.task_dependencies),
            "task_batches": len(self.task_batches),
            "task_templates": len(self.task_templates),
            "metrics": self.task_metrics,
            "orchestrator_status": self.orchestrator.get_system_overview(),
            "timestamp": datetime.now().isoformat()
        }
    
    def cancel_scheduled_task(self, task_id: str) -> bool:
        """Cancel a scheduled task"""
        if task_id in self.scheduled_tasks:
            del self.scheduled_tasks[task_id]
            logger.info(f"Cancelled scheduled task: {task_id}")
            return True
        return False
    
    def cancel_conditional_task(self, task_id: str) -> bool:
        """Cancel a conditional task"""
        if task_id in self.conditional_tasks:
            del self.conditional_tasks[task_id]
            logger.info(f"Cancelled conditional task: {task_id}")
            return True
        return False
    
    def get_task_batch_status(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a task batch"""
        if batch_id not in self.task_batches:
            return None
        
        batch = self.task_batches[batch_id]
        
        # Check status of all tasks in batch
        completed_tasks = 0
        failed_tasks = 0
        active_tasks = 0
        
        for task_id in batch.task_ids:
            if task_id in self.orchestrator.completed_tasks:
                task = self.orchestrator.completed_tasks[task_id]
                if task.status.value == "completed":
                    completed_tasks += 1
                else:
                    failed_tasks += 1
            elif task_id in self.orchestrator.active_tasks:
                active_tasks += 1
        
        # Determine overall batch status
        if completed_tasks == len(batch.task_ids):
            batch_status = "completed"
        elif failed_tasks > 0:
            batch_status = "partial_failure"
        elif active_tasks > 0:
            batch_status = "in_progress"
        else:
            batch_status = "pending"
        
        return {
            "batch_id": batch_id,
            "batch_name": batch.batch_name,
            "status": batch_status,
            "total_tasks": len(batch.task_ids),
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "active_tasks": active_tasks,
            "execution_order": batch.execution_order,
            "created_at": batch.created_at.isoformat(),
            "started_at": batch.started_at.isoformat() if batch.started_at else None,
            "completed_at": batch.completed_at.isoformat() if batch.completed_at else None
        }

# Global instance
_task_system_instance = None

def get_task_system_instance() -> AgentTaskSystem:
    """Get or create the global task system instance"""
    global _task_system_instance
    if _task_system_instance is None:
        _task_system_instance = AgentTaskSystem()
    return _task_system_instance

# Convenience functions
def create_task_template(template_name: str, task_type: str, description: str,
                        default_params: Optional[Dict] = None, 
                        required_params: Optional[List[str]] = None):
    """Create a task template"""
    task_system = get_task_system_instance()
    return task_system.create_task_template(
        template_name, task_type, description, default_params, required_params
    )

def create_scheduled_task(agent_type: str, task_type: str, description: str,
                         execution_time: datetime, priority: str = "medium",
                         params: Optional[Dict] = None) -> str:
    """Create a scheduled task"""
    task_system = get_task_system_instance()
    return task_system.create_scheduled_task(
        agent_type, task_type, description, execution_time, priority, params
    )

def create_task_batch(batch_name: str, tasks: List[Dict[str, Any]], 
                     execution_order: str = "parallel") -> str:
    """Create a task batch"""
    task_system = get_task_system_instance()
    return task_system.create_task_batch(batch_name, tasks, execution_order)