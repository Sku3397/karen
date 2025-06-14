"""
Orchestrator Agent - Central coordinator for all agents in Karen AI Secretary
Instance ID: ORCHESTRATOR-001
Domain: Task assignment, agent communication, master control
"""
import os
import time
import json
import logging
import asyncio
import threading
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
import queue
import uuid

# Import agent communication system
from .agent_communication import AgentCommunication

# Import for admin notifications
from .email_client import EmailClient
from .config import ADMIN_EMAIL_ADDRESS, SECRETARY_EMAIL_ADDRESS

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class TaskPriority(Enum):
    """Task priority levels"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4

class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class AgentType(Enum):
    """Available agent types"""
    ARCHAEOLOGIST = "archaeologist"
    SMS_ENGINEER = "sms_engineer"
    PHONE_ENGINEER = "phone_engineer"
    MEMORY_ENGINEER = "memory_engineer"
    TEST_ENGINEER = "test_engineer"
    SECURITY_AGENT = "security_agent"
    COMMUNICATIONS_AGENT = "communications_agent"
    DATABASE_AGENT = "database_agent"
    QA_AGENT = "qa_agent"

class WorkflowPhase(Enum):
    """Workflow execution phases"""
    ANALYSIS = "analysis"
    PLANNING = "planning"
    DEVELOPMENT = "development"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    MONITORING = "monitoring"

class AgentTask:
    """Represents a task assigned to an agent"""
    
    def __init__(self, task_id: str, agent_type: AgentType, task_type: str, 
                 description: str, priority: TaskPriority, params: Optional[Dict] = None):
        self.task_id = task_id
        self.agent_type = agent_type
        self.task_type = task_type
        self.description = description
        self.priority = priority
        self.params = params or {}
        self.status = TaskStatus.PENDING
        self.created_at = datetime.now()
        self.assigned_at = None
        self.started_at = None
        self.completed_at = None
        self.error_message = None
        self.retry_count = 0
        self.max_retries = 3
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary"""
        return {
            "task_id": self.task_id,
            "agent_type": self.agent_type.value,
            "task_type": self.task_type,
            "description": self.description,
            "priority": self.priority.value,
            "params": self.params,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "assigned_at": self.assigned_at.isoformat() if self.assigned_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries
        }

class AgentOrchestrator:
    """
    Central orchestrator that coordinates all agents in the Karen AI Secretary system
    Handles task assignment, inter-agent communication, and workflow management
    Instance ID: ORCHESTRATOR-001
    """
    
    def __init__(self):
        """Initialize the AgentOrchestrator"""
        logger.info("Initializing AgentOrchestrator ORCHESTRATOR-001")
        
        # Create logs directory structure
        self._setup_logging_directories()
        
        # Initialize communication system
        self.comm = AgentCommunication('orchestrator')
        
        # Task management
        self.task_queue = queue.PriorityQueue()
        self.active_tasks = {}  # task_id -> AgentTask
        self.completed_tasks = {}  # task_id -> AgentTask
        self.agent_assignments = {}  # agent_type -> List[task_id]
        
        # Agent registry and capabilities
        self.registered_agents = {
            AgentType.ARCHAEOLOGIST: {
                "capabilities": ["code_analysis", "pattern_detection", "documentation_creation"],
                "status": "available",
                "current_tasks": [],
                "last_heartbeat": None
            },
            AgentType.SMS_ENGINEER: {
                "capabilities": ["sms_implementation", "twilio_integration", "messaging_systems"],
                "status": "available", 
                "current_tasks": [],
                "last_heartbeat": None
            },
            AgentType.PHONE_ENGINEER: {
                "capabilities": ["voice_implementation", "call_handling", "telephony_systems"],
                "status": "available",
                "current_tasks": [],
                "last_heartbeat": None
            },
            AgentType.MEMORY_ENGINEER: {
                "capabilities": ["memory_systems", "chromadb_optimization", "data_storage"],
                "status": "available",
                "current_tasks": [],
                "last_heartbeat": None
            },
            AgentType.TEST_ENGINEER: {
                "capabilities": ["testing", "quality_assurance", "integration_testing"],
                "status": "available",
                "current_tasks": [],
                "last_heartbeat": None
            }
        }
        
        # Workflow definitions
        self.workflows = {
            'system_initialization': {
                'description': 'Initialize all system components',
                'phases': [
                    WorkflowPhase.ANALYSIS,
                    WorkflowPhase.PLANNING,
                    WorkflowPhase.DEVELOPMENT,
                    WorkflowPhase.TESTING
                ],
                'agents': {
                    WorkflowPhase.ANALYSIS: [AgentType.ARCHAEOLOGIST],
                    WorkflowPhase.PLANNING: [AgentType.ARCHAEOLOGIST],
                    WorkflowPhase.DEVELOPMENT: [
                        AgentType.SMS_ENGINEER, 
                        AgentType.PHONE_ENGINEER, 
                        AgentType.MEMORY_ENGINEER
                    ],
                    WorkflowPhase.TESTING: [AgentType.TEST_ENGINEER]
                }
            },
            'communication_enhancement': {
                'description': 'Enhance communication systems',
                'phases': [WorkflowPhase.DEVELOPMENT, WorkflowPhase.TESTING],
                'agents': {
                    WorkflowPhase.DEVELOPMENT: [AgentType.SMS_ENGINEER, AgentType.PHONE_ENGINEER],
                    WorkflowPhase.TESTING: [AgentType.TEST_ENGINEER]
                }
            },
            'system_optimization': {
                'description': 'Optimize system performance',
                'phases': [WorkflowPhase.ANALYSIS, WorkflowPhase.DEVELOPMENT, WorkflowPhase.TESTING],
                'agents': {
                    WorkflowPhase.ANALYSIS: [AgentType.ARCHAEOLOGIST],
                    WorkflowPhase.DEVELOPMENT: [AgentType.MEMORY_ENGINEER],
                    WorkflowPhase.TESTING: [AgentType.TEST_ENGINEER]
                }
            }
        }
        
        # Configuration
        self.health_check_interval = 300  # 5 minutes
        self.task_timeout = 1800  # 30 minutes
        self.max_concurrent_tasks_per_agent = 3
        
        # Email client for admin notifications
        try:
            self.email_client = EmailClient(
                email_address=SECRETARY_EMAIL_ADDRESS,
                token_file_path=os.getenv('SECRETARY_TOKEN_PATH', 'gmail_token_karen.json')
            )
        except Exception as e:
            logger.error(f"Failed to initialize email client: {e}")
            self.email_client = None
        
        # Start background processes
        self._start_background_processes()
        
        logger.info("AgentOrchestrator ORCHESTRATOR-001 initialized successfully")
    
    def _setup_logging_directories(self):
        """Create logging directory structure"""
        log_dirs = [
            "logs/agents",
            "logs/orchestrator", 
            "logs/tasks",
            "logs/workflows",
            "logs/system"
        ]
        
        for log_dir in log_dirs:
            Path(log_dir).mkdir(parents=True, exist_ok=True)
        
        # Set up orchestrator-specific logging
        orchestrator_handler = logging.FileHandler('logs/orchestrator/orchestrator.log')
        orchestrator_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        logger.addHandler(orchestrator_handler)
    
    def _start_background_processes(self):
        """Start background monitoring and processing threads"""
        # Task processor thread
        self.task_processor_thread = threading.Thread(
            target=self._task_processor_loop,
            daemon=True,
            name="TaskProcessor"
        )
        self.task_processor_thread.start()
        
        # Health monitor thread
        self.health_monitor_thread = threading.Thread(
            target=self._health_monitor_loop,
            daemon=True,
            name="HealthMonitor"
        )
        self.health_monitor_thread.start()
        
        # Task timeout monitor thread
        self.timeout_monitor_thread = threading.Thread(
            target=self._timeout_monitor_loop,
            daemon=True,
            name="TimeoutMonitor"
        )
        self.timeout_monitor_thread.start()
    
    def create_task(self, agent_type: AgentType, task_type: str, description: str,
                   priority: TaskPriority = TaskPriority.MEDIUM, 
                   params: Optional[Dict] = None) -> str:
        """Create a new task and add it to the queue"""
        task_id = f"{agent_type.value}_{task_type}_{datetime.now().timestamp()}_{uuid.uuid4().hex[:8]}"
        
        task = AgentTask(
            task_id=task_id,
            agent_type=agent_type,
            task_type=task_type,
            description=description,
            priority=priority,
            params=params
        )
        
        # Add to queue with priority (lower number = higher priority)
        self.task_queue.put((priority.value, datetime.now().timestamp(), task))
        self.active_tasks[task_id] = task
        
        logger.info(f"Created task {task_id}: {description}")
        
        # Log task creation
        self._log_task_event(task, "created")
        
        return task_id
    
    def assign_task_to_agent(self, task: AgentTask) -> bool:
        """Assign a task to the appropriate agent"""
        agent_type = task.agent_type
        
        # Check if agent is available and not overloaded
        agent_info = self.registered_agents.get(agent_type)
        if not agent_info:
            logger.error(f"Agent type {agent_type.value} not registered")
            return False
        
        if agent_info["status"] != "available":
            logger.warning(f"Agent {agent_type.value} not available: {agent_info['status']}")
            return False
        
        current_task_count = len(agent_info["current_tasks"])
        if current_task_count >= self.max_concurrent_tasks_per_agent:
            logger.warning(f"Agent {agent_type.value} overloaded: {current_task_count} tasks")
            return False
        
        # Assign the task
        task.status = TaskStatus.ASSIGNED
        task.assigned_at = datetime.now()
        
        # Update agent info
        agent_info["current_tasks"].append(task.task_id)
        if agent_type not in self.agent_assignments:
            self.agent_assignments[agent_type] = []
        self.agent_assignments[agent_type].append(task.task_id)
        
        # Send task to agent via communication system
        try:
            message_data = {
                "task_id": task.task_id,
                "task_type": task.task_type,
                "description": task.description,
                "params": task.params,
                "priority": task.priority.value
            }
            
            self.comm.send_message(agent_type.value, "task_assignment", message_data)
            
            logger.info(f"Assigned task {task.task_id} to {agent_type.value}")
            self._log_task_event(task, "assigned")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to assign task {task.task_id}: {e}")
            # Rollback assignment
            task.status = TaskStatus.PENDING
            task.assigned_at = None
            agent_info["current_tasks"].remove(task.task_id)
            self.agent_assignments[agent_type].remove(task.task_id)
            return False
    
    def _task_processor_loop(self):
        """Background loop to process tasks from the queue"""
        logger.info("Starting task processor loop")
        
        while True:
            try:
                # Get next task from queue (blocks until available)
                priority, timestamp, task = self.task_queue.get(timeout=10)
                
                logger.debug(f"Processing task {task.task_id} (priority {priority})")
                
                # Attempt to assign task
                if self.assign_task_to_agent(task):
                    logger.info(f"Successfully assigned task {task.task_id}")
                else:
                    # Put task back in queue to retry later
                    self.task_queue.put((priority, timestamp, task))
                    logger.warning(f"Failed to assign task {task.task_id}, will retry")
                    time.sleep(5)  # Wait before retrying
                
            except queue.Empty:
                # No tasks in queue, continue monitoring
                continue
            except Exception as e:
                logger.error(f"Error in task processor loop: {e}", exc_info=True)
                time.sleep(1)
    
    def _health_monitor_loop(self):
        """Background loop to monitor agent health"""
        logger.info("Starting health monitor loop")
        
        while True:
            try:
                self.check_all_agent_health()
                time.sleep(self.health_check_interval)
            except Exception as e:
                logger.error(f"Error in health monitor loop: {e}", exc_info=True)
                time.sleep(60)  # Wait longer on error
    
    def _timeout_monitor_loop(self):
        """Background loop to monitor task timeouts"""
        logger.info("Starting timeout monitor loop")
        
        while True:
            try:
                current_time = datetime.now()
                
                # Check for timed out tasks
                for task_id, task in list(self.active_tasks.items()):
                    if task.status in [TaskStatus.ASSIGNED, TaskStatus.IN_PROGRESS]:
                        if task.assigned_at:
                            elapsed = (current_time - task.assigned_at).total_seconds()
                            if elapsed > self.task_timeout:
                                logger.warning(f"Task {task_id} timed out after {elapsed}s")
                                self._handle_task_timeout(task)
                
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in timeout monitor loop: {e}", exc_info=True)
                time.sleep(60)
    
    def _handle_task_timeout(self, task: AgentTask):
        """Handle a task that has timed out"""
        task.status = TaskStatus.FAILED
        task.error_message = f"Task timed out after {self.task_timeout} seconds"
        task.completed_at = datetime.now()
        
        # Remove from agent's current tasks
        agent_info = self.registered_agents.get(task.agent_type)
        if agent_info and task.task_id in agent_info["current_tasks"]:
            agent_info["current_tasks"].remove(task.task_id)
        
        # Move to completed tasks
        self.completed_tasks[task.task_id] = task
        del self.active_tasks[task.task_id]
        
        self._log_task_event(task, "timeout")
        
        # Retry if not exceeded max retries
        if task.retry_count < task.max_retries:
            logger.info(f"Retrying timed out task {task.task_id} (attempt {task.retry_count + 1})")
            
            # Create new task instance with incremented retry count
            new_task = AgentTask(
                task_id=f"{task.task_id}_retry_{task.retry_count + 1}",
                agent_type=task.agent_type,
                task_type=task.task_type,
                description=task.description,
                priority=task.priority,
                params=task.params
            )
            new_task.retry_count = task.retry_count + 1
            
            # Add back to queue
            self.task_queue.put((task.priority.value, datetime.now().timestamp(), new_task))
            self.active_tasks[new_task.task_id] = new_task
    
    def complete_task(self, task_id: str, success: bool = True, 
                     result_data: Optional[Dict] = None, error_message: Optional[str] = None):
        """Mark a task as completed"""
        if task_id not in self.active_tasks:
            logger.warning(f"Attempted to complete unknown task: {task_id}")
            return False
        
        task = self.active_tasks[task_id]
        task.status = TaskStatus.COMPLETED if success else TaskStatus.FAILED
        task.completed_at = datetime.now()
        
        if error_message:
            task.error_message = error_message
        
        if result_data:
            task.params['result'] = result_data
        
        # Remove from agent's current tasks
        agent_info = self.registered_agents.get(task.agent_type)
        if agent_info and task_id in agent_info["current_tasks"]:
            agent_info["current_tasks"].remove(task_id)
        
        # Move to completed tasks
        self.completed_tasks[task_id] = task
        del self.active_tasks[task_id]
        
        status_str = "completed" if success else "failed"
        logger.info(f"Task {task_id} {status_str}")
        self._log_task_event(task, status_str)
        
        return True
    
    def check_all_agent_health(self) -> Dict[str, Dict[str, Any]]:
        """Check health status of all registered agents"""
        logger.debug("Performing health check on all agents")
        
        statuses = {}
        current_time = datetime.now()
        
        for agent_type, agent_info in self.registered_agents.items():
            try:
                # Get status from communication system
                agent_status = self.comm.get_agent_status(agent_type.value)
                
                # Update last heartbeat
                if agent_status:
                    agent_info["last_heartbeat"] = current_time
                    agent_info["status"] = agent_status.get("status", "unknown")
                else:
                    # Check if agent has been silent too long
                    if agent_info["last_heartbeat"]:
                        silence_duration = (current_time - agent_info["last_heartbeat"]).total_seconds()
                        if silence_duration > 600:  # 10 minutes
                            agent_info["status"] = "unresponsive"
                            logger.warning(f"Agent {agent_type.value} unresponsive for {silence_duration}s")
                    else:
                        agent_info["status"] = "unknown"
                
                statuses[agent_type.value] = {
                    "status": agent_info["status"],
                    "current_tasks": len(agent_info["current_tasks"]),
                    "capabilities": agent_info["capabilities"],
                    "last_heartbeat": agent_info["last_heartbeat"].isoformat() if agent_info["last_heartbeat"] else None
                }
                
                # Handle error status
                if agent_info["status"] == "error":
                    logger.error(f"Agent {agent_type.value} is in error state")
                    self._handle_agent_error(agent_type)
                
            except Exception as e:
                logger.error(f"Error checking health of {agent_type.value}: {e}")
                statuses[agent_type.value] = {"status": "error", "error": str(e)}
        
        # Log health check results
        with open(f"logs/system/health_check_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 'w') as f:
            json.dump(statuses, f, indent=2)
        
        return statuses
    
    def _handle_agent_error(self, agent_type: AgentType):
        """Handle an agent that is in error state"""
        agent_info = self.registered_agents[agent_type]
        
        # Attempt to restart the agent
        try:
            self.comm.send_message(agent_type.value, 'restart_request', {
                'reason': 'error_detected',
                'timestamp': datetime.now().isoformat()
            })
            
            # Reassign failed tasks
            failed_tasks = agent_info["current_tasks"].copy()
            agent_info["current_tasks"].clear()
            
            for task_id in failed_tasks:
                if task_id in self.active_tasks:
                    task = self.active_tasks[task_id]
                    task.status = TaskStatus.PENDING
                    task.assigned_at = None
                    # Put back in queue for reassignment
                    self.task_queue.put((task.priority.value, datetime.now().timestamp(), task))
                    logger.info(f"Reassigning task {task_id} due to agent error")
            
        except Exception as e:
            logger.error(f"Failed to handle error for agent {agent_type.value}: {e}")
    
    def execute_workflow(self, workflow_name: str, params: Optional[Dict[str, Any]] = None) -> str:
        """Execute a predefined workflow"""
        logger.info(f"Starting workflow: {workflow_name}")
        
        if workflow_name not in self.workflows:
            logger.error(f"Unknown workflow: {workflow_name}")
            raise ValueError(f"Unknown workflow: {workflow_name}")
        
        workflow = self.workflows[workflow_name]
        workflow_id = f"workflow_{workflow_name}_{datetime.now().timestamp()}"
        
        # Create workflow log
        workflow_log = {
            "workflow_id": workflow_id,
            "workflow_name": workflow_name,
            "description": workflow.get("description", ""),
            "started_at": datetime.now().isoformat(),
            "phases": {},
            "status": "running",
            "params": params or {}
        }
        
        try:
            # Execute each phase in sequence
            for phase in workflow['phases']:
                logger.info(f"Starting workflow phase: {phase.value}")
                
                phase_tasks = []
                phase_agents = workflow['agents'][phase]
                
                # Create tasks for this phase
                for agent_type in phase_agents:
                    task_id = self.create_task(
                        agent_type=agent_type,
                        task_type=f"workflow_{phase.value}",
                        description=f"Execute {phase.value} phase of {workflow_name} workflow",
                        priority=TaskPriority.HIGH,
                        params={
                            "workflow_id": workflow_id,
                            "phase": phase.value,
                            "workflow_params": params or {}
                        }
                    )
                    phase_tasks.append(task_id)
                
                # Wait for phase completion
                phase_start = datetime.now()
                phase_timeout = 3600  # 1 hour per phase
                
                while True:
                    # Check if all phase tasks are completed
                    completed_tasks = 0
                    failed_tasks = 0
                    
                    for task_id in phase_tasks:
                        if task_id in self.completed_tasks:
                            task = self.completed_tasks[task_id]
                            if task.status == TaskStatus.COMPLETED:
                                completed_tasks += 1
                            else:
                                failed_tasks += 1
                        elif task_id in self.active_tasks:
                            task = self.active_tasks[task_id]
                            if task.status == TaskStatus.FAILED:
                                failed_tasks += 1
                    
                    # Check completion
                    if completed_tasks == len(phase_tasks):
                        logger.info(f"Phase {phase.value} completed successfully")
                        workflow_log["phases"][phase.value] = {
                            "status": "completed",
                            "tasks": phase_tasks,
                            "completed_at": datetime.now().isoformat()
                        }
                        break
                    elif failed_tasks > 0:
                        logger.error(f"Phase {phase.value} failed with {failed_tasks} failed tasks")
                        workflow_log["phases"][phase.value] = {
                            "status": "failed",
                            "tasks": phase_tasks,
                            "failed_at": datetime.now().isoformat()
                        }
                        raise Exception(f"Phase {phase.value} failed")
                    
                    # Check timeout
                    if (datetime.now() - phase_start).total_seconds() > phase_timeout:
                        logger.error(f"Phase {phase.value} timed out")
                        workflow_log["phases"][phase.value] = {
                            "status": "timeout",
                            "tasks": phase_tasks,
                            "timeout_at": datetime.now().isoformat()
                        }
                        raise Exception(f"Phase {phase.value} timed out")
                    
                    time.sleep(10)  # Check every 10 seconds
            
            # Workflow completed successfully
            workflow_log["status"] = "completed"
            workflow_log["completed_at"] = datetime.now().isoformat()
            
            logger.info(f"Workflow {workflow_name} completed successfully")
            
        except Exception as e:
            logger.error(f"Workflow {workflow_name} failed: {e}")
            workflow_log["status"] = "failed"
            workflow_log["error"] = str(e)
            workflow_log["failed_at"] = datetime.now().isoformat()
        
        # Save workflow log
        with open(f"logs/workflows/{workflow_id}.json", 'w') as f:
            json.dump(workflow_log, f, indent=2)
        
        return workflow_id
    
    def get_system_overview(self) -> Dict[str, Any]:
        """Get complete system overview"""
        active_task_count = len(self.active_tasks)
        completed_task_count = len(self.completed_tasks)
        
        # Calculate task statistics
        task_stats = {
            "total_tasks": active_task_count + completed_task_count,
            "active_tasks": active_task_count,
            "completed_tasks": completed_task_count,
            "tasks_by_agent": {},
            "tasks_by_status": {}
        }
        
        # Count tasks by agent and status
        for task in list(self.active_tasks.values()) + list(self.completed_tasks.values()):
            agent_name = task.agent_type.value
            status = task.status.value
            
            task_stats["tasks_by_agent"][agent_name] = task_stats["tasks_by_agent"].get(agent_name, 0) + 1
            task_stats["tasks_by_status"][status] = task_stats["tasks_by_status"].get(status, 0) + 1
        
        return {
            "orchestrator_id": "ORCHESTRATOR-001",
            "status": "active",
            "uptime": datetime.now().isoformat(),
            "registered_agents": {
                agent_type.value: {
                    "status": info["status"],
                    "current_tasks": len(info["current_tasks"]),
                    "capabilities": info["capabilities"]
                }
                for agent_type, info in self.registered_agents.items()
            },
            "task_statistics": task_stats,
            "available_workflows": {
                name: workflow["description"] 
                for name, workflow in self.workflows.items()
            },
            "configuration": {
                "health_check_interval": self.health_check_interval,
                "task_timeout": self.task_timeout,
                "max_concurrent_tasks_per_agent": self.max_concurrent_tasks_per_agent
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def _log_task_event(self, task: AgentTask, event_type: str):
        """Log a task event to the task log"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "task_id": task.task_id,
            "agent_type": task.agent_type.value,
            "task_type": task.task_type,
            "event_type": event_type,
            "task_status": task.status.value,
            "description": task.description
        }
        
        # Append to daily task log
        log_file = f"logs/tasks/tasks_{datetime.now().strftime('%Y%m%d')}.jsonl"
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def coordinate_inter_agent_request(self, requesting_agent: str, target_agent: str,
                                     info_type: str, params: Optional[Dict[str, Any]] = None):
        """Coordinate information request between agents"""
        logger.info(f"Coordinating request from '{requesting_agent}' to '{target_agent}' for '{info_type}'")
        
        # Create coordination task
        coordination_id = f"coord_{datetime.now().timestamp()}_{uuid.uuid4().hex[:8]}"
        
        # Forward the request with orchestrator metadata
        message_data = {
            "coordination_id": coordination_id,
            "requesting_agent": requesting_agent,
            "needed_info": info_type,
            "params": params or {},
            "orchestrator_mediated": True,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            self.comm.send_message(target_agent, 'info_request', message_data)
            logger.info(f"Forwarded request {coordination_id} to {target_agent}")
            return coordination_id
        except Exception as e:
            logger.error(f"Failed to coordinate request {coordination_id}: {e}")
            return None

# Singleton instance
_orchestrator_instance = None

def get_orchestrator_instance() -> AgentOrchestrator:
    """Get or create the global orchestrator instance"""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = AgentOrchestrator()
    return _orchestrator_instance

def create_orchestrator_task(agent_type: str, task_type: str, description: str,
                           priority: str = "medium", params: Optional[Dict] = None) -> str:
    """Convenience function to create a task via the orchestrator"""
    orchestrator = get_orchestrator_instance()
    
    # Convert string parameters to enums
    agent_enum = AgentType(agent_type.lower())
    priority_enum = TaskPriority[priority.upper()]
    
    return orchestrator.create_task(
        agent_type=agent_enum,
        task_type=task_type,
        description=description,
        priority=priority_enum,
        params=params
    )