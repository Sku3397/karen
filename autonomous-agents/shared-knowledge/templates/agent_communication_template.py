"""
AgentCommunication Implementation Template
=========================================

This template implements the AgentCommunication class referenced throughout
Karen's Celery tasks. This is a missing critical component that needs to be
implemented for proper agent coordination.

Current References in Karen System:
- src/celery_app.py:219, 269, 348, etc.
- All agent tasks expect this class to exist

Implementation Approach:
- Redis-based message passing between agents
- Status tracking with timestamps
- Knowledge sharing with structured data
- Error handling and recovery
"""

import json
import logging
import time
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import redis
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class AgentMessage:
    """Structured message between agents."""
    id: str
    sender: str
    recipient: str
    message_type: str
    content: Dict[str, Any]
    timestamp: str
    ttl_seconds: int = 3600  # 1 hour default TTL

@dataclass  
class AgentStatus:
    """Agent status information."""
    agent_id: str
    status: str  # 'idle', 'processing', 'completed', 'error'
    progress: int  # 0-100
    metadata: Dict[str, Any]
    timestamp: str
    last_heartbeat: str

@dataclass
class KnowledgeItem:
    """Shared knowledge item."""
    id: str
    knowledge_type: str
    data: Dict[str, Any]
    created_by: str
    timestamp: str
    tags: List[str] = None
    ttl_seconds: int = 86400  # 24 hours default TTL

class AgentCommunication:
    """
    Agent communication system for Karen's multi-agent architecture.
    
    Features:
    - Redis-based message passing
    - Status tracking and heartbeat monitoring
    - Knowledge sharing between agents
    - Persistent agent registry
    - Error handling and recovery
    
    Redis Key Structure:
    - agent:status:{agent_id} - Agent status
    - agent:messages:{agent_id} - Agent inbox
    - agent:knowledge:{knowledge_type} - Shared knowledge
    - agent:registry - Active agent registry
    """
    
    def __init__(self, agent_id: str, redis_url: str = None):
        """
        Initialize agent communication.
        
        Args:
            agent_id: Unique identifier for this agent
            redis_url: Redis connection URL (defaults to Karen's Celery broker)
        """
        self.agent_id = agent_id
        
        # Use Karen's Redis configuration
        if not redis_url:
            import os
            redis_url = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
        
        try:
            # Parse Redis URL for connection
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            
            # Test connection
            self.redis_client.ping()
            logger.info(f"AgentCommunication initialized for {agent_id} with Redis at {redis_url}")
            
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis for agent {agent_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error initializing AgentCommunication for {agent_id}: {e}")
            raise
        
        # Register this agent
        self._register_agent()
        
        # Initialize heartbeat
        self._update_heartbeat()
    
    def _register_agent(self):
        """Register agent in the active agent registry."""
        try:
            registry_key = "agent:registry"
            agent_info = {
                'agent_id': self.agent_id,
                'registered_at': datetime.now(timezone.utc).isoformat(),
                'status': 'active'
            }
            
            # Add to registry (Redis set for uniqueness)
            self.redis_client.hset(registry_key, self.agent_id, json.dumps(agent_info))
            logger.debug(f"Registered agent {self.agent_id} in registry")
            
        except Exception as e:
            logger.error(f"Failed to register agent {self.agent_id}: {e}")
    
    def _update_heartbeat(self):
        """Update agent heartbeat timestamp."""
        try:
            heartbeat_key = f"agent:heartbeat:{self.agent_id}"
            self.redis_client.setex(
                heartbeat_key,
                300,  # 5 minute TTL
                datetime.now(timezone.utc).isoformat()
            )
        except Exception as e:
            logger.warning(f"Failed to update heartbeat for {self.agent_id}: {e}")
    
    def update_status(self, status: str, progress: int, metadata: Dict[str, Any] = None):
        """
        Update agent status.
        
        Args:
            status: Status string ('idle', 'processing', 'completed', 'error')
            progress: Progress percentage (0-100)
            metadata: Additional status metadata
        """
        try:
            agent_status = AgentStatus(
                agent_id=self.agent_id,
                status=status,
                progress=progress,
                metadata=metadata or {},
                timestamp=datetime.now(timezone.utc).isoformat(),
                last_heartbeat=datetime.now(timezone.utc).isoformat()
            )
            
            status_key = f"agent:status:{self.agent_id}"
            self.redis_client.setex(
                status_key,
                3600,  # 1 hour TTL
                json.dumps(asdict(agent_status))
            )
            
            # Update heartbeat
            self._update_heartbeat()
            
            logger.debug(f"Updated status for {self.agent_id}: {status} ({progress}%)")
            
        except Exception as e:
            logger.error(f"Failed to update status for {self.agent_id}: {e}")
    
    def send_message(self, recipient: str, message_type: str, content: Dict[str, Any], ttl_seconds: int = 3600):
        """
        Send message to another agent.
        
        Args:
            recipient: Target agent ID
            message_type: Type of message ('request', 'response', 'notification', etc.)
            content: Message content
            ttl_seconds: Message TTL in seconds
        """
        try:
            message = AgentMessage(
                id=str(uuid.uuid4()),
                sender=self.agent_id,
                recipient=recipient,
                message_type=message_type,
                content=content,
                timestamp=datetime.now(timezone.utc).isoformat(),
                ttl_seconds=ttl_seconds
            )
            
            # Add to recipient's inbox
            inbox_key = f"agent:messages:{recipient}"
            message_data = json.dumps(asdict(message))
            
            # Use Redis list for message queue
            self.redis_client.lpush(inbox_key, message_data)
            self.redis_client.expire(inbox_key, ttl_seconds)
            
            logger.info(f"Sent message '{message_type}' from {self.agent_id} to {recipient}")
            
        except Exception as e:
            logger.error(f"Failed to send message from {self.agent_id} to {recipient}: {e}")
    
    def read_messages(self, max_messages: int = 10) -> List[Dict[str, Any]]:
        """
        Read messages from agent's inbox.
        
        Args:
            max_messages: Maximum number of messages to retrieve
            
        Returns:
            List of message dictionaries
        """
        try:
            inbox_key = f"agent:messages:{self.agent_id}"
            
            # Get messages from inbox (Redis list)
            raw_messages = self.redis_client.lrange(inbox_key, 0, max_messages - 1)
            
            messages = []
            for raw_msg in raw_messages:
                try:
                    message_data = json.loads(raw_msg)
                    
                    # Check if message has expired
                    msg_timestamp = datetime.fromisoformat(message_data['timestamp'].replace('Z', '+00:00'))
                    age_seconds = (datetime.now(timezone.utc) - msg_timestamp).total_seconds()
                    
                    if age_seconds < message_data.get('ttl_seconds', 3600):
                        messages.append(message_data)
                    else:
                        # Remove expired message
                        self.redis_client.lrem(inbox_key, 1, raw_msg)
                        
                except json.JSONDecodeError as e:
                    logger.warning(f"Invalid message format in inbox: {e}")
                    # Remove invalid message
                    self.redis_client.lrem(inbox_key, 1, raw_msg)
            
            if messages:
                logger.debug(f"Retrieved {len(messages)} messages for {self.agent_id}")
                
                # Remove processed messages from inbox
                for _ in range(len(messages)):
                    self.redis_client.rpop(inbox_key)
            
            return messages
            
        except Exception as e:
            logger.error(f"Failed to read messages for {self.agent_id}: {e}")
            return []
    
    def share_knowledge(self, knowledge_type: str, data: Dict[str, Any], tags: List[str] = None, ttl_seconds: int = 86400):
        """
        Share knowledge with other agents.
        
        Args:
            knowledge_type: Type of knowledge ('pattern', 'discovery', 'config', etc.)
            data: Knowledge data
            tags: Optional tags for categorization
            ttl_seconds: Knowledge TTL in seconds (default 24 hours)
        """
        try:
            knowledge_item = KnowledgeItem(
                id=str(uuid.uuid4()),
                knowledge_type=knowledge_type,
                data=data,
                created_by=self.agent_id,
                timestamp=datetime.now(timezone.utc).isoformat(),
                tags=tags or [],
                ttl_seconds=ttl_seconds
            )
            
            # Store in knowledge base
            knowledge_key = f"agent:knowledge:{knowledge_type}"
            knowledge_data = json.dumps(asdict(knowledge_item))
            
            # Use Redis hash for knowledge storage
            self.redis_client.hset(knowledge_key, knowledge_item.id, knowledge_data)
            self.redis_client.expire(knowledge_key, ttl_seconds)
            
            # Also add to global knowledge index
            index_key = "agent:knowledge:index"
            index_entry = {
                'knowledge_type': knowledge_type,
                'id': knowledge_item.id,
                'created_by': self.agent_id,
                'timestamp': knowledge_item.timestamp,
                'tags': tags or []
            }
            self.redis_client.lpush(index_key, json.dumps(index_entry))
            self.redis_client.ltrim(index_key, 0, 999)  # Keep last 1000 entries
            
            logger.info(f"Shared knowledge '{knowledge_type}' from {self.agent_id}")
            
        except Exception as e:
            logger.error(f"Failed to share knowledge from {self.agent_id}: {e}")
    
    def get_knowledge(self, knowledge_type: str, max_items: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieve shared knowledge by type.
        
        Args:
            knowledge_type: Type of knowledge to retrieve
            max_items: Maximum number of items to return
            
        Returns:
            List of knowledge items
        """
        try:
            knowledge_key = f"agent:knowledge:{knowledge_type}"
            
            # Get all knowledge items of this type
            raw_items = self.redis_client.hgetall(knowledge_key)
            
            knowledge_items = []
            for item_id, raw_data in raw_items.items():
                try:
                    item_data = json.loads(raw_data)
                    
                    # Check if item has expired
                    item_timestamp = datetime.fromisoformat(item_data['timestamp'].replace('Z', '+00:00'))
                    age_seconds = (datetime.now(timezone.utc) - item_timestamp).total_seconds()
                    
                    if age_seconds < item_data.get('ttl_seconds', 86400):
                        knowledge_items.append(item_data)
                    else:
                        # Remove expired item
                        self.redis_client.hdel(knowledge_key, item_id)
                        
                except json.JSONDecodeError as e:
                    logger.warning(f"Invalid knowledge item format: {e}")
                    self.redis_client.hdel(knowledge_key, item_id)
            
            # Sort by timestamp (newest first) and limit
            knowledge_items.sort(key=lambda x: x['timestamp'], reverse=True)
            
            return knowledge_items[:max_items]
            
        except Exception as e:
            logger.error(f"Failed to get knowledge '{knowledge_type}' for {self.agent_id}: {e}")
            return []
    
    def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of another agent.
        
        Args:
            agent_id: Target agent ID
            
        Returns:
            Agent status dictionary or None if not found
        """
        try:
            status_key = f"agent:status:{agent_id}"
            raw_status = self.redis_client.get(status_key)
            
            if raw_status:
                return json.loads(raw_status)
            else:
                logger.debug(f"No status found for agent {agent_id}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get status for agent {agent_id}: {e}")
            return None
    
    def get_active_agents(self) -> List[Dict[str, Any]]:
        """
        Get list of active agents.
        
        Returns:
            List of active agent information
        """
        try:
            registry_key = "agent:registry"
            raw_agents = self.redis_client.hgetall(registry_key)
            
            active_agents = []
            for agent_id, raw_data in raw_agents.items():
                try:
                    agent_info = json.loads(raw_data)
                    
                    # Check heartbeat to determine if agent is truly active
                    heartbeat_key = f"agent:heartbeat:{agent_id}"
                    heartbeat = self.redis_client.get(heartbeat_key)
                    
                    if heartbeat:
                        agent_info['last_heartbeat'] = heartbeat
                        agent_info['status'] = 'active'
                    else:
                        agent_info['status'] = 'inactive'
                    
                    active_agents.append(agent_info)
                    
                except json.JSONDecodeError:
                    logger.warning(f"Invalid agent registry entry for {agent_id}")
                    self.redis_client.hdel(registry_key, agent_id)
            
            return active_agents
            
        except Exception as e:
            logger.error(f"Failed to get active agents: {e}")
            return []
    
    def cleanup_expired_data(self):
        """Clean up expired messages and knowledge items."""
        try:
            # This is handled automatically by Redis TTL, but can be called manually
            logger.debug(f"Cleanup requested by {self.agent_id}")
            
            # Could implement additional cleanup logic here if needed
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired data: {e}")
    
    def shutdown(self):
        """Gracefully shutdown agent communication."""
        try:
            # Update status to offline
            self.update_status('offline', 0, {'shutdown_time': datetime.now(timezone.utc).isoformat()})
            
            # Remove from registry
            registry_key = "agent:registry"
            self.redis_client.hdel(registry_key, self.agent_id)
            
            logger.info(f"Agent {self.agent_id} communication shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during agent communication shutdown: {e}")


# Usage Example for Karen's Celery Tasks:
"""
# In src/celery_app.py tasks:

@celery_app.task(name='example_agent_task', bind=True)
def example_agent_task(self):
    task_logger = self.get_logger()
    comm = AgentCommunication('example_agent')
    
    try:
        # Update status
        comm.update_status('processing', 10, {'phase': 'starting', 'task_id': self.request.id})
        
        # Read messages from other agents
        messages = comm.read_messages()
        for msg in messages:
            task_logger.info(f"Received: {msg['message_type']} from {msg['sender']}")
            # Process message...
        
        # Do main work...
        time.sleep(5)  # Simulate work
        
        # Share discovery
        comm.share_knowledge('pattern_discovery', {
            'pattern_name': 'example_pattern',
            'discovered_at': datetime.now().isoformat(),
            'details': 'Pattern details here'
        })
        
        # Send notification to another agent
        comm.send_message('orchestrator', 'task_complete', {
            'task_id': self.request.id,
            'result': 'success'
        })
        
        # Update final status
        comm.update_status('completed', 100, {'phase': 'finished'})
        
    except Exception as e:
        task_logger.error(f"Task failed: {e}", exc_info=True)
        comm.update_status('error', 0, {'error': str(e)})
        raise
"""