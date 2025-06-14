#!/usr/bin/env python3
"""
Agent Coordination Protocols for Karen AI Multi-Agent MCP Development

Implements conflict-free work assignment, resource management, and communication
protocols for seamless multi-agent collaboration.
"""

import json
import time
import threading
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class TaskPriority(Enum):
    CRITICAL = "critical"
    HIGH = "high" 
    MEDIUM = "medium"
    LOW = "low"

class TaskStatus(Enum):
    PENDING = "pending"
    CLAIMED = "claimed"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"

class ResourceType(Enum):
    FILE = "file"
    DIRECTORY = "directory"
    CONFIG = "config"
    TEST_ENV = "test_env"
    API_ENDPOINT = "api_endpoint"

@dataclass
class CoordinationTask:
    id: str
    title: str
    description: str
    priority: TaskPriority
    status: TaskStatus
    created_by: str
    assigned_to: Optional[str]
    created_at: str
    updated_at: str
    deadline: Optional[str]
    dependencies: List[str]
    required_resources: List[str]
    tags: List[str]
    estimated_duration_minutes: int
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'priority': self.priority.value,
            'status': self.status.value,
            'created_by': self.created_by,
            'assigned_to': self.assigned_to,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'deadline': self.deadline,
            'dependencies': self.dependencies,
            'required_resources': self.required_resources,
            'tags': self.tags,
            'estimated_duration_minutes': self.estimated_duration_minutes
        }

@dataclass
class ResourceClaim:
    resource_id: str
    resource_type: ResourceType
    claimed_by: str
    claimed_at: str
    expires_at: str
    operation: str
    exclusive: bool = True

@dataclass
class AgentCapability:
    agent_id: str
    capabilities: List[str]
    current_load: int
    max_concurrent_tasks: int
    specializations: List[str]
    availability_hours: Tuple[int, int] = (0, 23)

class CoordinationProtocols:
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.base_path = Path("/workspace/autonomous-agents")
        self.coordination_path = self.base_path / "troubleshooting" / "coordination"
        self.locks_path = self.base_path / "troubleshooting" / "resource-locks"
        
        # Task and resource tracking
        self.active_tasks: Dict[str, CoordinationTask] = {}
        self.resource_claims: Dict[str, ResourceClaim] = {}
        self.agent_capabilities: Dict[str, AgentCapability] = {}
        
        # Coordination state
        self.claimed_resources: Set[str] = set()
        self.current_tasks: Set[str] = set()
        self.last_heartbeat = datetime.now()
        
        # Initialize coordination infrastructure
        self._initialize_coordination_files()
        self._load_existing_state()
        
        # Start coordination monitoring
        self.monitoring = True
        threading.Thread(target=self._monitor_coordination, daemon=True).start()
        
    def _initialize_coordination_files(self):
        """Initialize coordination infrastructure files"""
        self.coordination_path.mkdir(parents=True, exist_ok=True)
        self.locks_path.mkdir(parents=True, exist_ok=True)
        
        # Create agent registry file if it doesn't exist
        agent_registry_file = self.coordination_path / "agent_registry.json"
        if not agent_registry_file.exists():
            with open(agent_registry_file, 'w') as f:
                json.dump({}, f, indent=2)
                
        # Create task queue file if it doesn't exist
        task_queue_file = self.coordination_path / "task_queue.json"
        if not task_queue_file.exists():
            with open(task_queue_file, 'w') as f:
                json.dump({"tasks": []}, f, indent=2)
                
    def _load_existing_state(self):
        """Load existing coordination state"""
        try:
            # Load active tasks
            task_queue_file = self.coordination_path / "task_queue.json"
            with open(task_queue_file, 'r') as f:
                data = json.load(f)
                for task_data in data.get("tasks", []):
                    task = CoordinationTask(
                        id=task_data['id'],
                        title=task_data['title'],
                        description=task_data['description'],
                        priority=TaskPriority(task_data['priority']),
                        status=TaskStatus(task_data['status']),
                        created_by=task_data['created_by'],
                        assigned_to=task_data.get('assigned_to'),
                        created_at=task_data['created_at'],
                        updated_at=task_data['updated_at'],
                        deadline=task_data.get('deadline'),
                        dependencies=task_data['dependencies'],
                        required_resources=task_data['required_resources'],
                        tags=task_data['tags'],
                        estimated_duration_minutes=task_data['estimated_duration_minutes']
                    )
                    self.active_tasks[task.id] = task
                    
            # Load agent capabilities
            agent_registry_file = self.coordination_path / "agent_registry.json"
            with open(agent_registry_file, 'r') as f:
                agent_data = json.load(f)
                for agent_id, capability_data in agent_data.items():
                    self.agent_capabilities[agent_id] = AgentCapability(
                        agent_id=agent_id,
                        capabilities=capability_data['capabilities'],
                        current_load=capability_data['current_load'],
                        max_concurrent_tasks=capability_data['max_concurrent_tasks'],
                        specializations=capability_data['specializations']
                    )
                    
        except Exception as e:
            logger.error(f"Error loading coordination state: {e}")
            
    def register_agent_capabilities(self, capabilities: List[str], specializations: List[str], max_concurrent: int = 3):
        """Register this agent's capabilities"""
        capability = AgentCapability(
            agent_id=self.agent_id,
            capabilities=capabilities,
            current_load=len(self.current_tasks),
            max_concurrent_tasks=max_concurrent,
            specializations=specializations
        )
        
        self.agent_capabilities[self.agent_id] = capability
        self._save_agent_registry()
        
        logger.info(f"Registered capabilities for {self.agent_id}: {capabilities}")
        
    def create_coordination_task(self, title: str, description: str, priority: TaskPriority, 
                               required_resources: List[str], tags: List[str], 
                               estimated_duration: int, dependencies: List[str] = None) -> str:
        """Create a new coordination task"""
        task_id = f"{self.agent_id}_{int(time.time() * 1000)}"
        timestamp = datetime.now().isoformat()
        
        task = CoordinationTask(
            id=task_id,
            title=title,
            description=description,
            priority=priority,
            status=TaskStatus.PENDING,
            created_by=self.agent_id,
            assigned_to=None,
            created_at=timestamp,
            updated_at=timestamp,
            deadline=None,
            dependencies=dependencies or [],
            required_resources=required_resources,
            tags=tags,
            estimated_duration_minutes=estimated_duration
        )
        
        self.active_tasks[task_id] = task
        self._save_task_queue()
        
        logger.info(f"Created coordination task {task_id}: {title}")
        return task_id
        
    def claim_task(self, task_id: str) -> bool:
        """Claim a task for execution"""
        if task_id not in self.active_tasks:
            logger.warning(f"Task {task_id} not found")
            return False
            
        task = self.active_tasks[task_id]
        
        # Check if task is available
        if task.status != TaskStatus.PENDING:
            logger.warning(f"Task {task_id} is not available (status: {task.status})")
            return False
            
        # Check dependencies
        if not self._check_dependencies_satisfied(task):
            logger.info(f"Dependencies not satisfied for task {task_id}")
            return False
            
        # Check resource availability
        if not self._check_resources_available(task):
            logger.info(f"Required resources not available for task {task_id}")
            return False
            
        # Check agent capacity
        if len(self.current_tasks) >= self.agent_capabilities[self.agent_id].max_concurrent_tasks:
            logger.info(f"Agent {self.agent_id} at capacity, cannot claim task {task_id}")
            return False
            
        # Claim the task
        task.assigned_to = self.agent_id
        task.status = TaskStatus.CLAIMED
        task.updated_at = datetime.now().isoformat()
        
        self.current_tasks.add(task_id)
        self._save_task_queue()
        
        # Claim required resources
        for resource in task.required_resources:
            self.claim_resource(resource, ResourceType.FILE, f"task_{task_id}", exclusive=True, duration_minutes=task.estimated_duration_minutes)
            
        logger.info(f"Claimed task {task_id}")
        return True
        
    def start_task(self, task_id: str) -> bool:
        """Start working on a claimed task"""
        if task_id not in self.active_tasks:
            return False
            
        task = self.active_tasks[task_id]
        
        if task.assigned_to != self.agent_id or task.status != TaskStatus.CLAIMED:
            logger.warning(f"Cannot start task {task_id} - not properly claimed")
            return False
            
        task.status = TaskStatus.IN_PROGRESS
        task.updated_at = datetime.now().isoformat()
        self._save_task_queue()
        
        logger.info(f"Started task {task_id}")
        return True
        
    def complete_task(self, task_id: str, results: Dict = None) -> bool:
        """Mark a task as completed"""
        if task_id not in self.active_tasks:
            return False
            
        task = self.active_tasks[task_id]
        
        if task.assigned_to != self.agent_id:
            logger.warning(f"Cannot complete task {task_id} - not assigned to this agent")
            return False
            
        task.status = TaskStatus.COMPLETED
        task.updated_at = datetime.now().isoformat()
        
        # Release claimed resources
        for resource in task.required_resources:
            self.release_resource(resource)
            
        self.current_tasks.discard(task_id)
        self._save_task_queue()
        
        # Save results if provided
        if results:
            results_file = self.coordination_path / f"results_{task_id}.json"
            with open(results_file, 'w') as f:
                json.dump({
                    "task_id": task_id,
                    "completed_by": self.agent_id,
                    "completed_at": datetime.now().isoformat(),
                    "results": results
                }, f, indent=2)
                
        logger.info(f"Completed task {task_id}")
        return True
        
    def fail_task(self, task_id: str, reason: str) -> bool:
        """Mark a task as failed"""
        if task_id not in self.active_tasks:
            return False
            
        task = self.active_tasks[task_id]
        
        if task.assigned_to != self.agent_id:
            return False
            
        task.status = TaskStatus.FAILED
        task.updated_at = datetime.now().isoformat()
        
        # Release claimed resources
        for resource in task.required_resources:
            self.release_resource(resource)
            
        self.current_tasks.discard(task_id)
        self._save_task_queue()
        
        # Save failure reason
        failure_file = self.coordination_path / f"failure_{task_id}.json"
        with open(failure_file, 'w') as f:
            json.dump({
                "task_id": task_id,
                "failed_by": self.agent_id,
                "failed_at": datetime.now().isoformat(),
                "reason": reason
            }, f, indent=2)
            
        logger.warning(f"Failed task {task_id}: {reason}")
        return True
        
    def claim_resource(self, resource_id: str, resource_type: ResourceType, operation: str, 
                      exclusive: bool = True, duration_minutes: int = 30) -> bool:
        """Claim a resource for exclusive or shared access"""
        resource_hash = hashlib.md5(resource_id.encode()).hexdigest()
        lock_file = self.locks_path / f"{resource_hash}.json"
        
        # Check if resource is already claimed
        if lock_file.exists():
            try:
                with open(lock_file, 'r') as f:
                    existing_claim = json.load(f)
                    
                expires_at = datetime.fromisoformat(existing_claim['expires_at'])
                if datetime.now() < expires_at:
                    if exclusive or existing_claim['exclusive']:
                        logger.warning(f"Resource {resource_id} already claimed by {existing_claim['claimed_by']}")
                        return False
            except Exception as e:
                logger.error(f"Error checking resource claim: {e}")
                
        # Create new claim
        claim = ResourceClaim(
            resource_id=resource_id,
            resource_type=resource_type,
            claimed_by=self.agent_id,
            claimed_at=datetime.now().isoformat(),
            expires_at=(datetime.now() + timedelta(minutes=duration_minutes)).isoformat(),
            operation=operation,
            exclusive=exclusive
        )
        
        with open(lock_file, 'w') as f:
            json.dump(asdict(claim), f, indent=2)
            
        self.claimed_resources.add(resource_id)
        logger.info(f"Claimed resource {resource_id} for {operation}")
        return True
        
    def release_resource(self, resource_id: str) -> bool:
        """Release a claimed resource"""
        resource_hash = hashlib.md5(resource_id.encode()).hexdigest()
        lock_file = self.locks_path / f"{resource_hash}.json"
        
        if lock_file.exists():
            try:
                with open(lock_file, 'r') as f:
                    claim_data = json.load(f)
                    
                if claim_data['claimed_by'] == self.agent_id:
                    lock_file.unlink()
                    self.claimed_resources.discard(resource_id)
                    logger.info(f"Released resource {resource_id}")
                    return True
                else:
                    logger.warning(f"Cannot release resource {resource_id} - not claimed by this agent")
                    return False
            except Exception as e:
                logger.error(f"Error releasing resource: {e}")
                return False
                
        return False
        
    def get_available_tasks(self) -> List[CoordinationTask]:
        """Get list of tasks available for claiming"""
        available = []
        
        for task in self.active_tasks.values():
            if (task.status == TaskStatus.PENDING and 
                self._check_dependencies_satisfied(task) and
                self._check_agent_capable(task) and
                self._check_resources_available(task)):
                available.append(task)
                
        # Sort by priority and creation time
        available.sort(key=lambda t: (t.priority.value, t.created_at))
        return available
        
    def _check_dependencies_satisfied(self, task: CoordinationTask) -> bool:
        """Check if task dependencies are satisfied"""
        for dep_id in task.dependencies:
            if dep_id in self.active_tasks:
                dep_task = self.active_tasks[dep_id]
                if dep_task.status != TaskStatus.COMPLETED:
                    return False
        return True
        
    def _check_agent_capable(self, task: CoordinationTask) -> bool:
        """Check if this agent is capable of handling the task"""
        if self.agent_id not in self.agent_capabilities:
            return True  # Assume capable if not registered
            
        agent_caps = self.agent_capabilities[self.agent_id]
        
        # Check if any task tags match agent capabilities
        for tag in task.tags:
            if tag in agent_caps.capabilities or tag in agent_caps.specializations:
                return True
                
        return False
        
    def _check_resources_available(self, task: CoordinationTask) -> bool:
        """Check if required resources are available"""
        for resource in task.required_resources:
            resource_hash = hashlib.md5(resource.encode()).hexdigest()
            lock_file = self.locks_path / f"{resource_hash}.json"
            
            if lock_file.exists():
                try:
                    with open(lock_file, 'r') as f:
                        claim_data = json.load(f)
                        
                    expires_at = datetime.fromisoformat(claim_data['expires_at'])
                    if datetime.now() < expires_at and claim_data['exclusive']:
                        return False
                except Exception:
                    pass
                    
        return True
        
    def _save_task_queue(self):
        """Save task queue to filesystem"""
        task_queue_file = self.coordination_path / "task_queue.json"
        tasks_data = [task.to_dict() for task in self.active_tasks.values()]
        
        with open(task_queue_file, 'w') as f:
            json.dump({"tasks": tasks_data}, f, indent=2)
            
    def _save_agent_registry(self):
        """Save agent registry to filesystem"""
        agent_registry_file = self.coordination_path / "agent_registry.json"
        registry_data = {}
        
        for agent_id, capability in self.agent_capabilities.items():
            registry_data[agent_id] = {
                "capabilities": capability.capabilities,
                "current_load": capability.current_load,
                "max_concurrent_tasks": capability.max_concurrent_tasks,
                "specializations": capability.specializations
            }
            
        with open(agent_registry_file, 'w') as f:
            json.dump(registry_data, f, indent=2)
            
    def _monitor_coordination(self):
        """Monitor coordination state and cleanup expired resources"""
        while self.monitoring:
            try:
                # Update heartbeat
                self.last_heartbeat = datetime.now()
                
                # Cleanup expired resource claims
                current_time = datetime.now()
                expired_resources = []
                
                for lock_file in self.locks_path.glob("*.json"):
                    try:
                        with open(lock_file, 'r') as f:
                            claim_data = json.load(f)
                            
                        expires_at = datetime.fromisoformat(claim_data['expires_at'])
                        if current_time > expires_at:
                            expired_resources.append(lock_file)
                    except Exception:
                        expired_resources.append(lock_file)
                        
                # Remove expired locks
                for lock_file in expired_resources:
                    try:
                        lock_file.unlink()
                        logger.info(f"Cleaned up expired resource lock: {lock_file.name}")
                    except Exception as e:
                        logger.error(f"Error cleaning up lock file: {e}")
                        
                # Update agent load
                if self.agent_id in self.agent_capabilities:
                    self.agent_capabilities[self.agent_id].current_load = len(self.current_tasks)
                    self._save_agent_registry()
                    
                time.sleep(30)  # Monitor every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in coordination monitoring: {e}")
                time.sleep(60)
                
    def get_coordination_status(self) -> Dict:
        """Get current coordination status"""
        return {
            "agent_id": self.agent_id,
            "active_tasks": len(self.current_tasks),
            "claimed_resources": len(self.claimed_resources),
            "available_tasks": len(self.get_available_tasks()),
            "last_heartbeat": self.last_heartbeat.isoformat(),
            "capabilities": self.agent_capabilities.get(self.agent_id, {})
        }
        
    def stop_monitoring(self):
        """Stop coordination monitoring"""
        self.monitoring = False
        
        # Release all claimed resources
        for resource in list(self.claimed_resources):
            self.release_resource(resource)
            
        logger.info(f"Stopped coordination monitoring for {self.agent_id}")

def create_coordination_client(agent_id: str, capabilities: List[str], specializations: List[str]) -> CoordinationProtocols:
    """Factory function to create a coordination client for an agent"""
    client = CoordinationProtocols(agent_id)
    client.register_agent_capabilities(capabilities, specializations)
    return client