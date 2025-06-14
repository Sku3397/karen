#!/usr/bin/env python3
"""
Collaborative Troubleshooting Orchestrator for Karen AI Multi-Agent MCP Development

This orchestrator coordinates troubleshooting across multiple agents to prevent conflicts
and ensure efficient problem resolution using eigencode communication patterns.
"""

import json
import time
import uuid
import logging
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
from enum import Enum
import redis
import fcntl
import hashlib

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/workspace/logs/troubleshooting_orchestrator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class IssueStatus(Enum):
    REPORTED = "reported"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    TESTING = "testing"
    RESOLVED = "resolved"
    CLOSED = "closed"

class IssuePriority(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class TroubleshootingIssue:
    id: str
    title: str
    description: str
    priority: IssuePriority
    status: IssueStatus
    reporter_agent: str
    assigned_agent: Optional[str]
    created_at: str
    updated_at: str
    tags: List[str]
    affected_resources: List[str]
    solution_id: Optional[str] = None
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'priority': self.priority.value,
            'status': self.status.value,
            'reporter_agent': self.reporter_agent,
            'assigned_agent': self.assigned_agent,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'tags': self.tags,
            'affected_resources': self.affected_resources,
            'solution_id': self.solution_id
        }

@dataclass
class Solution:
    id: str
    issue_id: str
    description: str
    implementation_steps: List[str]
    test_results: Dict
    created_by: str
    created_at: str
    validated_by: List[str]
    effectiveness_score: float
    
    def to_dict(self):
        return asdict(self)

@dataclass
class ResourceLock:
    resource_path: str
    locked_by: str
    locked_at: str
    expires_at: str
    operation: str

class TroubleshootingOrchestrator:
    def __init__(self):
        self.base_path = Path("/workspace/autonomous-agents")
        self.troubleshooting_path = self.base_path / "troubleshooting"
        self.communication_path = self.base_path / "communication"
        self.inbox_path = self.communication_path / "inbox" / "troubleshooting-orchestrator"
        
        # Initialize Redis for real-time coordination
        try:
            self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
            self.redis_client.ping()
        except:
            logger.warning("Redis not available, using file-based coordination only")
            self.redis_client = None
        
        # Active issues and solutions
        self.active_issues: Dict[str, TroubleshootingIssue] = {}
        self.solutions: Dict[str, Solution] = {}
        self.resource_locks: Dict[str, ResourceLock] = {}
        
        # Agent capabilities and status
        self.agent_capabilities = {
            "mcp_codebase_tools": ["mcp_tools", "python", "testing", "integration"],
            "business_intelligence": ["metrics", "reporting", "data_analysis", "performance"],
            "testing_agent": ["test_automation", "validation", "integration_testing"],
            "troubleshooting_orchestrator": ["coordination", "conflict_resolution", "workflow"]
        }
        
        self.agent_status = {}
        self.running = False
        
        # Initialize directories
        self._initialize_directories()
        self._load_existing_data()
        
    def _initialize_directories(self):
        """Create necessary directory structure"""
        directories = [
            self.troubleshooting_path / "issues",
            self.troubleshooting_path / "solutions", 
            self.troubleshooting_path / "testing-results",
            self.troubleshooting_path / "coordination",
            self.troubleshooting_path / "knowledge-base",
            self.troubleshooting_path / "resource-locks",
            self.inbox_path
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            
    def _load_existing_data(self):
        """Load existing issues and solutions from filesystem"""
        # Load issues
        issues_path = self.troubleshooting_path / "issues"
        for issue_file in issues_path.glob("*.json"):
            try:
                with open(issue_file, 'r') as f:
                    issue_data = json.load(f)
                    issue = TroubleshootingIssue(
                        id=issue_data['id'],
                        title=issue_data['title'],
                        description=issue_data['description'],
                        priority=IssuePriority(issue_data['priority']),
                        status=IssueStatus(issue_data['status']),
                        reporter_agent=issue_data['reporter_agent'],
                        assigned_agent=issue_data.get('assigned_agent'),
                        created_at=issue_data['created_at'],
                        updated_at=issue_data['updated_at'],
                        tags=issue_data['tags'],
                        affected_resources=issue_data['affected_resources'],
                        solution_id=issue_data.get('solution_id')
                    )
                    self.active_issues[issue.id] = issue
            except Exception as e:
                logger.error(f"Failed to load issue from {issue_file}: {e}")
                
        # Load solutions
        solutions_path = self.troubleshooting_path / "solutions"
        for solution_file in solutions_path.glob("*.json"):
            try:
                with open(solution_file, 'r') as f:
                    solution_data = json.load(f)
                    solution = Solution(**solution_data)
                    self.solutions[solution.id] = solution
            except Exception as e:
                logger.error(f"Failed to load solution from {solution_file}: {e}")
                
    def start(self):
        """Start the troubleshooting orchestrator"""
        logger.info("Starting Troubleshooting Orchestrator")
        self.running = True
        
        # Start monitoring threads
        threading.Thread(target=self._monitor_agent_communications, daemon=True).start()
        threading.Thread(target=self._process_issue_queue, daemon=True).start()
        threading.Thread(target=self._monitor_resource_locks, daemon=True).start()
        threading.Thread(target=self._update_agent_status, daemon=True).start()
        
        # Send startup message
        self._send_message_to_orchestrator({
            "type": "troubleshooting_orchestrator_started",
            "capabilities": ["issue_coordination", "conflict_resolution", "testing_orchestration"],
            "status": "active"
        })
        
        logger.info("Troubleshooting Orchestrator started successfully")
        
    def stop(self):
        """Stop the orchestrator"""
        self.running = False
        logger.info("Troubleshooting Orchestrator stopped")
        
    def _monitor_agent_communications(self):
        """Monitor agent inboxes for troubleshooting requests"""
        agent_inboxes = [
            self.communication_path / "inbox" / "mcp_codebase_tools",
            self.communication_path / "inbox" / "business_intelligence", 
            self.communication_path / "inbox" / "testing_agent",
            self.inbox_path
        ]
        
        processed_messages = set()
        
        while self.running:
            try:
                for inbox in agent_inboxes:
                    if not inbox.exists():
                        continue
                        
                    for message_file in inbox.glob("*.json"):
                        message_id = message_file.name
                        if message_id in processed_messages:
                            continue
                            
                        try:
                            with open(message_file, 'r') as f:
                                message = json.load(f)
                                
                            if self._is_troubleshooting_message(message):
                                self._process_troubleshooting_message(message)
                                processed_messages.add(message_id)
                                
                        except Exception as e:
                            logger.error(f"Error processing message {message_file}: {e}")
                            
                time.sleep(2)  # Check every 2 seconds
                
            except Exception as e:
                logger.error(f"Error monitoring communications: {e}")
                time.sleep(5)
                
    def _is_troubleshooting_message(self, message: Dict) -> bool:
        """Check if message is related to troubleshooting"""
        troubleshooting_types = [
            "issue_report", "test_failure", "integration_error", 
            "performance_issue", "resource_conflict", "help_request"
        ]
        return message.get("type") in troubleshooting_types
        
    def _process_troubleshooting_message(self, message: Dict):
        """Process troubleshooting-related messages"""
        message_type = message.get("type")
        
        if message_type == "issue_report":
            self._create_issue_from_message(message)
        elif message_type == "test_failure":
            self._handle_test_failure(message)
        elif message_type == "integration_error":
            self._handle_integration_error(message)
        elif message_type == "resource_conflict":
            self._resolve_resource_conflict(message)
        elif message_type == "help_request":
            self._handle_help_request(message)
            
    def _create_issue_from_message(self, message: Dict):
        """Create a new troubleshooting issue from agent message"""
        issue_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        # Determine priority based on message content
        priority = IssuePriority.MEDIUM
        if "critical" in message.get("content", {}).get("description", "").lower():
            priority = IssuePriority.CRITICAL
        elif "urgent" in message.get("content", {}).get("description", "").lower():
            priority = IssuePriority.HIGH
            
        issue = TroubleshootingIssue(
            id=issue_id,
            title=message.get("content", {}).get("title", "Untitled Issue"),
            description=message.get("content", {}).get("description", ""),
            priority=priority,
            status=IssueStatus.REPORTED,
            reporter_agent=message.get("from", "unknown"),
            assigned_agent=None,
            created_at=timestamp,
            updated_at=timestamp,
            tags=message.get("content", {}).get("tags", []),
            affected_resources=message.get("content", {}).get("affected_resources", [])
        )
        
        self.active_issues[issue_id] = issue
        self._save_issue(issue)
        self._assign_issue(issue)
        
        logger.info(f"Created issue {issue_id}: {issue.title}")
        
    def _assign_issue(self, issue: TroubleshootingIssue):
        """Assign issue to most appropriate agent"""
        # Find best agent based on capabilities and current workload
        best_agent = self._find_best_agent_for_issue(issue)
        
        if best_agent:
            issue.assigned_agent = best_agent
            issue.status = IssueStatus.ASSIGNED
            issue.updated_at = datetime.now().isoformat()
            
            self._save_issue(issue)
            self._notify_agent_of_assignment(best_agent, issue)
            
            logger.info(f"Assigned issue {issue.id} to {best_agent}")
        else:
            logger.warning(f"No suitable agent found for issue {issue.id}")
            
    def _find_best_agent_for_issue(self, issue: TroubleshootingIssue) -> Optional[str]:
        """Find the best agent to handle an issue based on capabilities"""
        # Score agents based on capability match
        agent_scores = {}
        
        for agent, capabilities in self.agent_capabilities.items():
            score = 0
            
            # Check tag overlap
            for tag in issue.tags:
                if tag in capabilities:
                    score += 2
                    
            # Check description keywords
            description_lower = issue.description.lower()
            for capability in capabilities:
                if capability in description_lower:
                    score += 1
                    
            # Penalize for current workload
            current_workload = len([i for i in self.active_issues.values() 
                                 if i.assigned_agent == agent and i.status in [IssueStatus.ASSIGNED, IssueStatus.IN_PROGRESS]])
            score -= current_workload
            
            if score > 0:
                agent_scores[agent] = score
                
        return max(agent_scores.items(), key=lambda x: x[1])[0] if agent_scores else None
        
    def _notify_agent_of_assignment(self, agent: str, issue: TroubleshootingIssue):
        """Notify agent of issue assignment"""
        message = {
            "from": "troubleshooting_orchestrator",
            "to": agent,
            "type": "issue_assignment",
            "timestamp": datetime.now().isoformat(),
            "content": {
                "issue": issue.to_dict(),
                "priority": issue.priority.value,
                "resources_needed": issue.affected_resources,
                "collaboration_needed": len(issue.affected_resources) > 1
            }
        }
        
        self._send_message_to_agent(agent, message)
        
    def _process_issue_queue(self):
        """Process pending issues and coordinate resolution"""
        while self.running:
            try:
                # Check for stale assignments
                for issue in self.active_issues.values():
                    if issue.status == IssueStatus.ASSIGNED:
                        assigned_time = datetime.fromisoformat(issue.updated_at)
                        if datetime.now() - assigned_time > timedelta(minutes=30):
                            logger.warning(f"Issue {issue.id} assignment is stale, reassigning")
                            self._assign_issue(issue)
                            
                    elif issue.status == IssueStatus.IN_PROGRESS:
                        # Check for progress updates
                        in_progress_time = datetime.fromisoformat(issue.updated_at)
                        if datetime.now() - in_progress_time > timedelta(hours=2):
                            self._request_status_update(issue)
                            
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error processing issue queue: {e}")
                time.sleep(30)
                
    def _request_status_update(self, issue: TroubleshootingIssue):
        """Request status update from assigned agent"""
        if not issue.assigned_agent:
            return
            
        message = {
            "from": "troubleshooting_orchestrator",
            "to": issue.assigned_agent,
            "type": "status_update_request",
            "timestamp": datetime.now().isoformat(),
            "content": {
                "issue_id": issue.id,
                "last_update": issue.updated_at,
                "request_reason": "long_running_task"
            }
        }
        
        self._send_message_to_agent(issue.assigned_agent, message)
        
    def _monitor_resource_locks(self):
        """Monitor and manage resource locks to prevent conflicts"""
        while self.running:
            try:
                current_time = datetime.now()
                expired_locks = []
                
                for resource_path, lock in self.resource_locks.items():
                    expires_at = datetime.fromisoformat(lock.expires_at)
                    if current_time > expires_at:
                        expired_locks.append(resource_path)
                        
                # Release expired locks
                for resource_path in expired_locks:
                    self._release_resource_lock(resource_path)
                    logger.info(f"Released expired lock on {resource_path}")
                    
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error monitoring resource locks: {e}")
                time.sleep(60)
                
    def acquire_resource_lock(self, resource_path: str, agent: str, operation: str, duration_minutes: int = 30) -> bool:
        """Acquire a lock on a resource for an agent"""
        if resource_path in self.resource_locks:
            current_lock = self.resource_locks[resource_path]
            expires_at = datetime.fromisoformat(current_lock.expires_at)
            
            if datetime.now() < expires_at:
                logger.warning(f"Resource {resource_path} already locked by {current_lock.locked_by}")
                return False
                
        # Create new lock
        lock = ResourceLock(
            resource_path=resource_path,
            locked_by=agent,
            locked_at=datetime.now().isoformat(),
            expires_at=(datetime.now() + timedelta(minutes=duration_minutes)).isoformat(),
            operation=operation
        )
        
        self.resource_locks[resource_path] = lock
        self._save_resource_lock(lock)
        
        logger.info(f"Acquired lock on {resource_path} for {agent}")
        return True
        
    def _release_resource_lock(self, resource_path: str):
        """Release a resource lock"""
        if resource_path in self.resource_locks:
            del self.resource_locks[resource_path]
            
            # Remove lock file
            lock_file = self.troubleshooting_path / "resource-locks" / f"{hashlib.md5(resource_path.encode()).hexdigest()}.json"
            if lock_file.exists():
                lock_file.unlink()
                
    def _save_resource_lock(self, lock: ResourceLock):
        """Save resource lock to filesystem"""
        lock_file = self.troubleshooting_path / "resource-locks" / f"{hashlib.md5(lock.resource_path.encode()).hexdigest()}.json"
        with open(lock_file, 'w') as f:
            json.dump(asdict(lock), f, indent=2)
            
    def _save_issue(self, issue: TroubleshootingIssue):
        """Save issue to filesystem"""
        issue_file = self.troubleshooting_path / "issues" / f"{issue.id}.json"
        with open(issue_file, 'w') as f:
            json.dump(issue.to_dict(), f, indent=2)
            
    def _save_solution(self, solution: Solution):
        """Save solution to filesystem"""
        solution_file = self.troubleshooting_path / "solutions" / f"{solution.id}.json"
        with open(solution_file, 'w') as f:
            json.dump(solution.to_dict(), f, indent=2)
            
    def _send_message_to_agent(self, agent: str, message: Dict):
        """Send message to specific agent"""
        agent_inbox = self.communication_path / "inbox" / agent
        agent_inbox.mkdir(parents=True, exist_ok=True)
        
        message_file = agent_inbox / f"troubleshooting_{int(time.time() * 1000)}.json"
        with open(message_file, 'w') as f:
            json.dump(message, f, indent=2)
            
    def _send_message_to_orchestrator(self, message: Dict):
        """Send message to main orchestrator"""
        orchestrator_inbox = self.communication_path / "inbox" / "orchestrator"
        orchestrator_inbox.mkdir(parents=True, exist_ok=True)
        
        message_file = orchestrator_inbox / f"troubleshooting_{int(time.time() * 1000)}.json"
        with open(message_file, 'w') as f:
            json.dump({
                "from": "troubleshooting_orchestrator",
                "to": "orchestrator", 
                "timestamp": datetime.now().isoformat(),
                **message
            }, f, indent=2)
            
    def _update_agent_status(self):
        """Update agent status tracking"""
        while self.running:
            try:
                # Check agent activity by looking at recent messages
                current_time = datetime.now()
                
                for agent in self.agent_capabilities.keys():
                    agent_inbox = self.communication_path / "inbox" / agent
                    if not agent_inbox.exists():
                        continue
                        
                    # Check for recent activity
                    recent_activity = False
                    for message_file in agent_inbox.glob("*.json"):
                        file_time = datetime.fromtimestamp(message_file.stat().st_mtime)
                        if current_time - file_time < timedelta(minutes=10):
                            recent_activity = True
                            break
                            
                    self.agent_status[agent] = {
                        "last_seen": current_time.isoformat(),
                        "active": recent_activity,
                        "assigned_issues": len([i for i in self.active_issues.values() if i.assigned_agent == agent])
                    }
                    
                time.sleep(60)  # Update every minute
                
            except Exception as e:
                logger.error(f"Error updating agent status: {e}")
                time.sleep(60)
                
    def get_troubleshooting_status(self) -> Dict:
        """Get current troubleshooting status"""
        return {
            "active_issues": len([i for i in self.active_issues.values() if i.status != IssueStatus.CLOSED]),
            "resolved_issues": len([i for i in self.active_issues.values() if i.status == IssueStatus.RESOLVED]),
            "agent_status": self.agent_status,
            "resource_locks": len(self.resource_locks),
            "solutions_available": len(self.solutions)
        }

def main():
    """Main entry point"""
    orchestrator = TroubleshootingOrchestrator()
    
    try:
        orchestrator.start()
        
        # Keep running
        while orchestrator.running:
            time.sleep(10)
            
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    finally:
        orchestrator.stop()

if __name__ == "__main__":
    main()