# Mock AgentCommunication - File-based implementation without Redis dependency
# Temporary solution until Redis is available in the environment

import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import uuid

logger = logging.getLogger(__name__)

class MockAgentCommunication:
    """
    File-based AgentCommunication implementation without Redis dependency.
    
    Uses filesystem for:
    - Status tracking (JSON files)
    - Message passing (JSON files in inbox directories)
    - Knowledge sharing (JSON files in knowledge-base)
    
    This allows agents to function without Redis until it's available.
    """
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        
        # Use current project structure
        project_root = Path(__file__).parent.parent.parent
        self.comm_dir = project_root / 'autonomous-agents' / 'communication'
        
        # Ensure directories exist
        self.ensure_directories()
        
        logger.info(f"MockAgentCommunication initialized for {agent_name}")
    
    def ensure_directories(self):
        """Create communication directories if they don't exist"""
        # Agent-specific inbox
        agent_inbox_path = self.comm_dir / 'inbox' / self.agent_name
        agent_inbox_path.mkdir(parents=True, exist_ok=True)
        (agent_inbox_path / 'processed').mkdir(parents=True, exist_ok=True)

        # Shared directories
        (self.comm_dir / 'status').mkdir(parents=True, exist_ok=True)
        (self.comm_dir / 'knowledge-base').mkdir(parents=True, exist_ok=True)
        (self.comm_dir / 'outbox').mkdir(parents=True, exist_ok=True)
    
    def update_status(self, status: str, progress: int, details: Dict[str, Any] = None):
        """Update agent status using JSON file"""
        try:
            status_data = {
                'agent': self.agent_name,
                'status': status,
                'progress': progress,
                'details': details or {},
                'timestamp': datetime.now().isoformat()
            }
            
            status_file = self.comm_dir / 'status' / f'{self.agent_name}_status.json'
            with open(status_file, 'w') as f:
                json.dump(status_data, f, indent=2)
            
            logger.debug(f"Updated status for {self.agent_name}: {status} ({progress}%)")
            
        except Exception as e:
            logger.error(f"Failed to update status for {self.agent_name}: {e}")
    
    def send_message(self, to_agent: str, message_type: str, content: Dict[str, Any]):
        """Send message to another agent via filesystem"""
        try:
            message = {
                'from': self.agent_name,
                'to': to_agent,
                'type': message_type,
                'content': content,
                'timestamp': datetime.now().isoformat(),
                'id': str(uuid.uuid4())
            }
            
            # Create target agent's inbox if needed
            inbox_path = self.comm_dir / 'inbox' / to_agent
            inbox_path.mkdir(parents=True, exist_ok=True)
            
            # Save message with timestamp in filename
            filename = f"{self.agent_name}_to_{to_agent}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.json"
            message_file = inbox_path / filename
            
            with open(message_file, 'w') as f:
                json.dump(message, f, indent=2)
            
            logger.info(f"Sent message '{message_type}' from {self.agent_name} to {to_agent}")
            
        except Exception as e:
            logger.error(f"Failed to send message from {self.agent_name} to {to_agent}: {e}")
    
    def read_messages(self) -> List[Dict[str, Any]]:
        """Read messages from agent's inbox"""
        try:
            messages = []
            inbox_path = self.comm_dir / 'inbox' / self.agent_name
            
            if not inbox_path.exists():
                return messages
            
            processed_dir = inbox_path / 'processed'
            processed_dir.mkdir(exist_ok=True)
            
            # Read all JSON message files
            for msg_file in inbox_path.glob('*.json'):
                if msg_file.is_file():
                    try:
                        with open(msg_file, 'r') as f:
                            message_data = json.load(f)
                        messages.append(message_data)
                        
                        # Move to processed directory
                        processed_file = processed_dir / msg_file.name
                        msg_file.rename(processed_file)
                        
                    except Exception as e:
                        logger.error(f"Error processing message file {msg_file.name}: {e}")
            
            if messages:
                logger.debug(f"Retrieved {len(messages)} messages for {self.agent_name}")
            
            return messages
            
        except Exception as e:
            logger.error(f"Failed to read messages for {self.agent_name}: {e}")
            return []
    
    def share_knowledge(self, knowledge_type: str, content: Dict[str, Any]):
        """Share knowledge via filesystem"""
        try:
            knowledge = {
                'contributor': self.agent_name,
                'type': knowledge_type,
                'content': content,
                'timestamp': datetime.now().isoformat()
            }
            
            kb_dir = self.comm_dir / 'knowledge-base'
            kb_dir.mkdir(parents=True, exist_ok=True)
            
            filename = f"{knowledge_type}_{self.agent_name}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.json"
            kb_file = kb_dir / filename
            
            with open(kb_file, 'w') as f:
                json.dump(knowledge, f, indent=2)
            
            logger.info(f"Shared knowledge '{knowledge_type}' from {self.agent_name}")
            
        except Exception as e:
            logger.error(f"Failed to share knowledge from {self.agent_name}: {e}")
    
    def get_knowledge(self, knowledge_type: str, max_items: int = 10) -> List[Dict[str, Any]]:
        """Retrieve shared knowledge by type"""
        try:
            knowledge_items = []
            kb_dir = self.comm_dir / 'knowledge-base'
            
            if not kb_dir.exists():
                return knowledge_items
            
            # Find knowledge files matching the type
            pattern = f"{knowledge_type}_*.json"
            for kb_file in kb_dir.glob(pattern):
                if kb_file.is_file():
                    try:
                        with open(kb_file, 'r') as f:
                            knowledge_data = json.load(f)
                        knowledge_items.append(knowledge_data)
                    except Exception as e:
                        logger.error(f"Error reading knowledge file {kb_file.name}: {e}")
            
            # Sort by timestamp (newest first) and limit
            knowledge_items.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            return knowledge_items[:max_items]
            
        except Exception as e:
            logger.error(f"Failed to get knowledge '{knowledge_type}' for {self.agent_name}: {e}")
            return []
    
    def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get status of another agent"""
        try:
            status_file = self.comm_dir / 'status' / f'{agent_id}_status.json'
            
            if status_file.exists():
                with open(status_file, 'r') as f:
                    return json.load(f)
            else:
                logger.debug(f"No status file found for agent {agent_id}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get status for agent {agent_id}: {e}")
            return None
    
    def get_all_agent_statuses(self) -> Dict[str, Dict[str, Any]]:
        """Get current status of all agents"""
        try:
            statuses = {}
            status_dir = self.comm_dir / 'status'
            
            if status_dir.exists():
                for status_file in status_dir.glob('*_status.json'):
                    if status_file.is_file():
                        try:
                            with open(status_file, 'r') as f:
                                data = json.load(f)
                                agent_name = data.get('agent')
                                if agent_name:
                                    statuses[agent_name] = data
                        except Exception as e:
                            logger.error(f"Error reading status file {status_file.name}: {e}")
            
            return statuses
            
        except Exception as e:
            logger.error(f"Failed to get all agent statuses: {e}")
            return {}
    
    def cleanup_old_files(self, days_old: int = 7):
        """Clean up old message and knowledge files"""
        try:
            from datetime import timedelta
            cutoff_time = datetime.now() - timedelta(days=days_old)
            
            # Clean old processed messages
            processed_dirs = list((self.comm_dir / 'inbox').glob('*/processed'))
            for processed_dir in processed_dirs:
                if processed_dir.is_dir():
                    for old_file in processed_dir.glob('*.json'):
                        if old_file.stat().st_mtime < cutoff_time.timestamp():
                            old_file.unlink()
                            logger.debug(f"Cleaned up old file: {old_file.name}")
            
            logger.info(f"Cleanup completed for files older than {days_old} days")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


# Alias for compatibility with existing code
AgentCommunication = MockAgentCommunication

# Usage example:
"""
# In Celery tasks or agent code:
from shared_knowledge.templates.mock_agent_communication import AgentCommunication

# Initialize communication
comm = AgentCommunication('my_agent')

# Update status
comm.update_status('processing', 50, {'current_task': 'analyzing_data'})

# Send message to another agent
comm.send_message('orchestrator', 'task_update', {
    'status': 'in_progress',
    'details': 'Processing user request'
})

# Read incoming messages
messages = comm.read_messages()
for msg in messages:
    print(f"Received {msg['type']} from {msg['from']}: {msg['content']}")

# Share knowledge
comm.share_knowledge('pattern_discovery', {
    'pattern_name': 'email_classification',
    'accuracy': 0.95,
    'details': 'Improved classification algorithm'
})

# Get knowledge
patterns = comm.get_knowledge('pattern_discovery', max_items=5)
for pattern in patterns:
    print(f"Pattern from {pattern['contributor']}: {pattern['content']}")
"""