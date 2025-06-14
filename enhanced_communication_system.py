#!/usr/bin/env python3
"""
Enhanced Communication System for Karen AI Multi-Agent Troubleshooting

Implements standardized messaging, broadcast capabilities, and solution sharing
for seamless multi-agent collaboration during troubleshooting operations.
"""

import json
import time
import threading
import hashlib
import redis
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import uuid

logger = logging.getLogger(__name__)

class MessageType(Enum):
    ISSUE_REPORT = "issue_report"
    SOLUTION_SHARE = "solution_share"
    HELP_REQUEST = "help_request"
    STATUS_UPDATE = "status_update"
    RESOURCE_REQUEST = "resource_request"
    COLLABORATION_INVITE = "collaboration_invite"
    BROADCAST = "broadcast"
    ESCALATION = "escalation"
    KNOWLEDGE_SHARE = "knowledge_share"

class MessagePriority(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class SolutionCategory(Enum):
    MCP_INTEGRATION = "mcp_integration"
    TESTING = "testing"
    PERFORMANCE = "performance"
    CONFIGURATION = "configuration"
    DEPENDENCY = "dependency"
    DEPLOYMENT = "deployment"

@dataclass
class EnhancedMessage:
    id: str
    type: MessageType
    priority: MessagePriority
    from_agent: str
    to_agent: Optional[str]  # None for broadcast
    timestamp: str
    subject: str
    content: Dict[str, Any]
    tags: List[str]
    requires_response: bool = False
    response_deadline: Optional[str] = None
    thread_id: Optional[str] = None
    
    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type.value,
            'priority': self.priority.value,
            'from': self.from_agent,
            'to': self.to_agent,
            'timestamp': self.timestamp,
            'subject': self.subject,
            'content': self.content,
            'tags': self.tags,
            'requires_response': self.requires_response,
            'response_deadline': self.response_deadline,
            'thread_id': self.thread_id
        }

@dataclass
class SharedSolution:
    id: str
    category: SolutionCategory
    title: str
    description: str
    problem_patterns: List[str]
    solution_steps: List[str]
    code_snippets: Dict[str, str]
    validation_steps: List[str]
    author: str
    created_at: str
    effectiveness_score: float
    validated_by: List[str]
    tags: List[str]
    
    def to_dict(self):
        return asdict(self)

@dataclass
class BroadcastMessage:
    id: str
    title: str
    content: str
    priority: MessagePriority
    tags: List[str]
    from_agent: str
    timestamp: str
    expires_at: str
    target_agents: Optional[List[str]] = None  # None for all agents

class EnhancedCommunicationSystem:
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.base_path = Path("/workspace/autonomous-agents")
        self.communication_path = self.base_path / "communication"
        self.troubleshooting_path = self.base_path / "troubleshooting"
        self.knowledge_path = self.troubleshooting_path / "knowledge-base"
        
        # Message handling
        self.inbox_path = self.communication_path / "inbox" / agent_id
        self.outbox_path = self.communication_path / "outbox" / agent_id
        self.broadcast_path = self.communication_path / "broadcasts"
        self.solutions_path = self.knowledge_path / "solutions"
        
        # State tracking
        self.processed_messages: Set[str] = set()
        self.subscribed_tags: Set[str] = set()
        self.message_handlers: Dict[MessageType, Callable] = {}
        self.collaboration_sessions: Dict[str, Dict] = {}
        
        # Redis for real-time communication
        try:
            self.redis_client = redis.Redis(host='localhost', port=6379, db=1)
            self.redis_client.ping()
            self.redis_available = True
        except:
            logger.warning("Redis not available, using file-based messaging only")
            self.redis_client = None
            self.redis_available = False
            
        # Initialize directories and state
        self._initialize_communication_infrastructure()
        self._load_processed_messages()
        
        # Start message monitoring
        self.monitoring = True
        threading.Thread(target=self._monitor_messages, daemon=True).start()
        if self.redis_available:
            threading.Thread(target=self._monitor_redis_channels, daemon=True).start()
            
    def _initialize_communication_infrastructure(self):
        """Initialize communication directory structure"""
        directories = [
            self.inbox_path,
            self.outbox_path,
            self.broadcast_path,
            self.solutions_path,
            self.knowledge_path / "patterns",
            self.knowledge_path / "best-practices",
            self.communication_path / "threads"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            
    def _load_processed_messages(self):
        """Load list of previously processed messages"""
        processed_file = self.inbox_path / "processed_messages.json"
        if processed_file.exists():
            try:
                with open(processed_file, 'r') as f:
                    self.processed_messages = set(json.load(f))
            except Exception as e:
                logger.error(f"Error loading processed messages: {e}")
                
    def _save_processed_messages(self):
        """Save list of processed messages"""
        processed_file = self.inbox_path / "processed_messages.json"
        with open(processed_file, 'w') as f:
            json.dump(list(self.processed_messages), f)
            
    def register_message_handler(self, message_type: MessageType, handler: Callable):
        """Register a handler for specific message types"""
        self.message_handlers[message_type] = handler
        logger.info(f"Registered handler for {message_type.value} messages")
        
    def subscribe_to_tags(self, tags: List[str]):
        """Subscribe to specific tags for filtering messages"""
        self.subscribed_tags.update(tags)
        logger.info(f"Subscribed to tags: {tags}")
        
    def send_message(self, to_agent: str, message_type: MessageType, subject: str, 
                    content: Dict[str, Any], priority: MessagePriority = MessagePriority.MEDIUM,
                    tags: List[str] = None, requires_response: bool = False,
                    response_deadline_minutes: int = None) -> str:
        """Send a message to another agent"""
        message_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        response_deadline = None
        if requires_response and response_deadline_minutes:
            deadline = datetime.now() + timedelta(minutes=response_deadline_minutes)
            response_deadline = deadline.isoformat()
            
        message = EnhancedMessage(
            id=message_id,
            type=message_type,
            priority=priority,
            from_agent=self.agent_id,
            to_agent=to_agent,
            timestamp=timestamp,
            subject=subject,
            content=content,
            tags=tags or [],
            requires_response=requires_response,
            response_deadline=response_deadline
        )
        
        # Save to outbox
        outbox_file = self.outbox_path / f"{message_id}.json"
        with open(outbox_file, 'w') as f:
            json.dump(message.to_dict(), f, indent=2)
            
        # Send to recipient's inbox
        recipient_inbox = self.communication_path / "inbox" / to_agent
        recipient_inbox.mkdir(parents=True, exist_ok=True)
        
        inbox_file = recipient_inbox / f"{message_id}.json"
        with open(inbox_file, 'w') as f:
            json.dump(message.to_dict(), f, indent=2)
            
        # Send via Redis if available for real-time delivery
        if self.redis_available:
            self.redis_client.publish(f"agent:{to_agent}", json.dumps(message.to_dict()))
            
        logger.info(f"Sent {message_type.value} message to {to_agent}: {subject}")
        return message_id
        
    def broadcast_message(self, title: str, content: str, priority: MessagePriority,
                         tags: List[str] = None, target_agents: List[str] = None,
                         expires_hours: int = 24) -> str:
        """Broadcast a message to multiple agents"""
        broadcast_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        expires_at = (datetime.now() + timedelta(hours=expires_hours)).isoformat()
        
        broadcast = BroadcastMessage(
            id=broadcast_id,
            title=title,
            content=content,
            priority=priority,
            tags=tags or [],
            from_agent=self.agent_id,
            timestamp=timestamp,
            expires_at=expires_at,
            target_agents=target_agents
        )
        
        # Save broadcast
        broadcast_file = self.broadcast_path / f"{broadcast_id}.json"
        with open(broadcast_file, 'w') as f:
            json.dump(asdict(broadcast), f, indent=2)
            
        # Deliver to target agents (or all if no targets specified)
        if target_agents:
            recipients = target_agents
        else:
            # Get all known agents
            recipients = [d.name for d in (self.communication_path / "inbox").iterdir() if d.is_dir()]
            
        for agent in recipients:
            if agent == self.agent_id:
                continue
                
            agent_inbox = self.communication_path / "inbox" / agent
            agent_inbox.mkdir(parents=True, exist_ok=True)
            
            # Create broadcast notification
            notification = {
                "id": str(uuid.uuid4()),
                "type": "broadcast",
                "priority": priority.value,
                "from": self.agent_id,
                "to": agent,
                "timestamp": timestamp,
                "subject": f"Broadcast: {title}",
                "content": {
                    "broadcast_id": broadcast_id,
                    "title": title,
                    "content": content,
                    "tags": tags or []
                },
                "tags": ["broadcast"] + (tags or [])
            }
            
            notification_file = agent_inbox / f"broadcast_{broadcast_id}.json"
            with open(notification_file, 'w') as f:
                json.dump(notification, f, indent=2)
                
        # Broadcast via Redis if available
        if self.redis_available:
            self.redis_client.publish("broadcasts", json.dumps(asdict(broadcast)))
            
        logger.info(f"Broadcast message '{title}' to {len(recipients)} agents")
        return broadcast_id
        
    def share_solution(self, category: SolutionCategory, title: str, description: str,
                      problem_patterns: List[str], solution_steps: List[str],
                      code_snippets: Dict[str, str] = None, validation_steps: List[str] = None,
                      tags: List[str] = None) -> str:
        """Share a solution with the knowledge base"""
        solution_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        solution = SharedSolution(
            id=solution_id,
            category=category,
            title=title,
            description=description,
            problem_patterns=problem_patterns,
            solution_steps=solution_steps,
            code_snippets=code_snippets or {},
            validation_steps=validation_steps or [],
            author=self.agent_id,
            created_at=timestamp,
            effectiveness_score=0.0,
            validated_by=[],
            tags=tags or []
        )
        
        # Save solution to knowledge base
        solution_file = self.solutions_path / f"{solution_id}.json"
        with open(solution_file, 'w') as f:
            json.dump(solution.to_dict(), f, indent=2)
            
        # Broadcast solution availability
        self.broadcast_message(
            title=f"New Solution: {title}",
            content=f"New solution for {category.value} shared by {self.agent_id}",
            priority=MessagePriority.MEDIUM,
            tags=["solution", category.value] + (tags or [])
        )
        
        logger.info(f"Shared solution: {title}")
        return solution_id
        
    def search_solutions(self, query: str, category: SolutionCategory = None,
                        tags: List[str] = None) -> List[SharedSolution]:
        """Search for solutions in the knowledge base"""
        solutions = []
        
        for solution_file in self.solutions_path.glob("*.json"):
            try:
                with open(solution_file, 'r') as f:
                    solution_data = json.load(f)
                    
                solution = SharedSolution(**solution_data)
                
                # Apply filters
                if category and solution.category != category:
                    continue
                    
                if tags and not any(tag in solution.tags for tag in tags):
                    continue
                    
                # Check query match
                query_lower = query.lower()
                if (query_lower in solution.title.lower() or
                    query_lower in solution.description.lower() or
                    any(query_lower in pattern.lower() for pattern in solution.problem_patterns)):
                    solutions.append(solution)
                    
            except Exception as e:
                logger.error(f"Error loading solution {solution_file}: {e}")
                
        # Sort by effectiveness score
        solutions.sort(key=lambda s: s.effectiveness_score, reverse=True)
        return solutions
        
    def request_help(self, subject: str, description: str, tags: List[str] = None,
                    preferred_agents: List[str] = None, urgency: MessagePriority = MessagePriority.MEDIUM) -> str:
        """Request help from other agents"""
        content = {
            "description": description,
            "tags": tags or [],
            "context": {
                "current_task": getattr(self, 'current_task', None),
                "error_details": getattr(self, 'last_error', None),
                "attempted_solutions": getattr(self, 'attempted_solutions', [])
            }
        }
        
        if preferred_agents:
            # Send to specific agents
            message_ids = []
            for agent in preferred_agents:
                msg_id = self.send_message(
                    to_agent=agent,
                    message_type=MessageType.HELP_REQUEST,
                    subject=subject,
                    content=content,
                    priority=urgency,
                    tags=["help"] + (tags or []),
                    requires_response=True,
                    response_deadline_minutes=30
                )
                message_ids.append(msg_id)
            return message_ids[0]
        else:
            # Broadcast help request
            return self.broadcast_message(
                title=f"Help Requested: {subject}",
                content=f"Agent {self.agent_id} needs help: {description}",
                priority=urgency,
                tags=["help"] + (tags or [])
            )
            
    def start_collaboration_session(self, participants: List[str], topic: str,
                                   objectives: List[str]) -> str:
        """Start a collaborative troubleshooting session"""
        session_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        session = {
            "id": session_id,
            "topic": topic,
            "objectives": objectives,
            "participants": participants + [self.agent_id],
            "organizer": self.agent_id,
            "started_at": timestamp,
            "status": "active",
            "shared_workspace": f"/workspace/autonomous-agents/troubleshooting/collaboration/{session_id}",
            "messages": []
        }
        
        self.collaboration_sessions[session_id] = session
        
        # Create shared workspace
        workspace_path = Path(session["shared_workspace"])
        workspace_path.mkdir(parents=True, exist_ok=True)
        
        # Save session info
        session_file = workspace_path / "session_info.json"
        with open(session_file, 'w') as f:
            json.dump(session, f, indent=2)
            
        # Invite participants
        for participant in participants:
            self.send_message(
                to_agent=participant,
                message_type=MessageType.COLLABORATION_INVITE,
                subject=f"Collaboration Invitation: {topic}",
                content={
                    "session_id": session_id,
                    "topic": topic,
                    "objectives": objectives,
                    "workspace": session["shared_workspace"]
                },
                priority=MessagePriority.HIGH,
                tags=["collaboration"],
                requires_response=True,
                response_deadline_minutes=15
            )
            
        logger.info(f"Started collaboration session: {topic}")
        return session_id
        
    def _monitor_messages(self):
        """Monitor incoming messages and process them"""
        while self.monitoring:
            try:
                # Process new messages in inbox
                for message_file in self.inbox_path.glob("*.json"):
                    if message_file.name.startswith("processed_"):
                        continue
                        
                    message_id = message_file.stem
                    if message_id in self.processed_messages:
                        continue
                        
                    try:
                        with open(message_file, 'r') as f:
                            message_data = json.load(f)
                            
                        self._process_message(message_data)
                        self.processed_messages.add(message_id)
                        
                        # Mark as processed
                        processed_file = self.inbox_path / f"processed_{message_file.name}"
                        message_file.rename(processed_file)
                        
                    except Exception as e:
                        logger.error(f"Error processing message {message_file}: {e}")
                        
                # Clean up old processed messages
                self._cleanup_old_messages()
                
                time.sleep(2)  # Check every 2 seconds
                
            except Exception as e:
                logger.error(f"Error monitoring messages: {e}")
                time.sleep(5)
                
    def _monitor_redis_channels(self):
        """Monitor Redis channels for real-time messages"""
        if not self.redis_available:
            return
            
        pubsub = self.redis_client.pubsub()
        pubsub.subscribe(f"agent:{self.agent_id}", "broadcasts")
        
        while self.monitoring:
            try:
                message = pubsub.get_message(timeout=1)
                if message and message['type'] == 'message':
                    try:
                        message_data = json.loads(message['data'])
                        self._process_message(message_data)
                    except Exception as e:
                        logger.error(f"Error processing Redis message: {e}")
                        
            except Exception as e:
                logger.error(f"Error monitoring Redis channels: {e}")
                time.sleep(5)
                
    def _process_message(self, message_data: Dict):
        """Process an incoming message"""
        try:
            message_type = MessageType(message_data['type'])
            
            # Check if message matches subscribed tags
            if self.subscribed_tags:
                message_tags = set(message_data.get('tags', []))
                if not message_tags.intersection(self.subscribed_tags):
                    return
                    
            # Call registered handler if available
            if message_type in self.message_handlers:
                try:
                    self.message_handlers[message_type](message_data)
                except Exception as e:
                    logger.error(f"Error in message handler for {message_type}: {e}")
            else:
                # Default processing
                self._default_message_processing(message_data)
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            
    def _default_message_processing(self, message_data: Dict):
        """Default message processing for unhandled message types"""
        message_type = message_data['type']
        from_agent = message_data['from']
        subject = message_data['subject']
        
        logger.info(f"Received {message_type} from {from_agent}: {subject}")
        
        # Handle common message types
        if message_type == "help_request":
            self._handle_help_request(message_data)
        elif message_type == "collaboration_invite":
            self._handle_collaboration_invite(message_data)
        elif message_type == "solution_share":
            self._handle_solution_share(message_data)
            
    def _handle_help_request(self, message_data: Dict):
        """Handle incoming help requests"""
        logger.info(f"Help request from {message_data['from']}: {message_data['subject']}")
        
        # TODO: Implement intelligent help matching based on capabilities
        # For now, just log the request
        
    def _handle_collaboration_invite(self, message_data: Dict):
        """Handle collaboration invitations"""
        content = message_data['content']
        session_id = content['session_id']
        topic = content['topic']
        
        logger.info(f"Collaboration invite for: {topic}")
        
        # Auto-accept collaboration invites (can be made smarter)
        self.send_message(
            to_agent=message_data['from'],
            message_type=MessageType.STATUS_UPDATE,
            subject="Collaboration Accepted",
            content={
                "session_id": session_id,
                "status": "accepted",
                "ready_at": datetime.now().isoformat()
            },
            priority=MessagePriority.HIGH
        )
        
    def _handle_solution_share(self, message_data: Dict):
        """Handle solution sharing notifications"""
        logger.info(f"New solution shared: {message_data['subject']}")
        
    def _cleanup_old_messages(self):
        """Clean up old processed messages"""
        cutoff_time = datetime.now() - timedelta(days=7)
        
        for processed_file in self.inbox_path.glob("processed_*.json"):
            file_time = datetime.fromtimestamp(processed_file.stat().st_mtime)
            if file_time < cutoff_time:
                try:
                    processed_file.unlink()
                except Exception as e:
                    logger.error(f"Error cleaning up old message: {e}")
                    
        # Save updated processed messages list
        self._save_processed_messages()
        
    def get_communication_stats(self) -> Dict:
        """Get communication statistics"""
        return {
            "agent_id": self.agent_id,
            "messages_processed": len(self.processed_messages),
            "active_collaboration_sessions": len(self.collaboration_sessions),
            "subscribed_tags": list(self.subscribed_tags),
            "redis_available": self.redis_available,
            "solutions_shared": len(list(self.solutions_path.glob("*.json")))
        }
        
    def stop_monitoring(self):
        """Stop message monitoring"""
        self.monitoring = False
        logger.info(f"Stopped communication monitoring for {self.agent_id}")

def create_communication_client(agent_id: str, subscribed_tags: List[str] = None) -> EnhancedCommunicationSystem:
    """Factory function to create a communication client for an agent"""
    client = EnhancedCommunicationSystem(agent_id)
    if subscribed_tags:
        client.subscribe_to_tags(subscribed_tags)
    return client