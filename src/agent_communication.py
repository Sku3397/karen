import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import redis
from pathlib import Path

class AgentCommunication:
    """Inter-agent communication system using Redis and filesystem"""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.redis_client = redis.from_url(os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'))
        # Use project root for communication directory
        project_root = Path(__file__).parent.parent
        self.comm_dir = project_root / 'autonomous-agents' / 'communication'
        self.ensure_directories()
    
    def ensure_directories(self):
        """Create communication directories if they don't exist"""
        # Agent-specific inbox and its processed sub-directory
        agent_inbox_path = self.comm_dir / 'inbox' / self.agent_name
        agent_inbox_path.mkdir(parents=True, exist_ok=True)
        (agent_inbox_path / 'processed').mkdir(parents=True, exist_ok=True)

        # Top-level shared directories (as implied by usage in other methods)
        (self.comm_dir / 'outbox').mkdir(parents=True, exist_ok=True) # As per spec, though unused by current methods
        (self.comm_dir / 'status').mkdir(parents=True, exist_ok=True)
        (self.comm_dir / 'knowledge-base').mkdir(parents=True, exist_ok=True)

        # The `send_message` method creates the target agent's inbox if it doesn't exist.
        # So no need to pre-create all agent inboxes here.

    def send_message(self, to_agent: str, message_type: str, content: Dict):
        """Send message to another agent"""
        message = {
            'from': self.agent_name,
            'to': to_agent,
            'type': message_type,
            'content': content,
            'timestamp': datetime.now().isoformat()
        }
        
        # Use Redis for real-time messaging (Pub/Sub for notification)
        pubsub_channel = f"agent_channel_{to_agent}"
        try:
            self.redis_client.publish(pubsub_channel, json.dumps(message))
        except Exception as e:
            print(f"Error publishing message to Redis Pub/Sub channel {pubsub_channel} for agent {to_agent}: {e}")

        # Add to Redis list for inbox processing
        redis_list_key = f"agent_inbox_list:{to_agent}"
        try:
            self.redis_client.lpush(redis_list_key, json.dumps(message))
        except Exception as e:
            print(f"Error LPUSHing message to Redis list {redis_list_key} for agent {to_agent}: {e}")
            # Fallback: If Redis list push fails, ensure it is definitely on disk as the primary alternative.
            # The current logic already writes to disk unconditionally later, which covers this.

        # Also save to filesystem for persistence
        inbox_path = self.comm_dir / 'inbox' / to_agent
        inbox_path.mkdir(parents=True, exist_ok=True) # Ensure target agent's inbox exists
        
        filename = f"{self.agent_name}_to_{to_agent}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.json"
        with open(inbox_path / filename, 'w') as f:
            json.dump(message, f, indent=2)
    
    def read_messages(self) -> List[Dict]:
        """Read all unread messages for this agent from its Redis list inbox and then filesystem inbox."""
        all_messages: List[Dict] = [] # Explicit type
        # processed_message_ids_from_redis = set() # For future deduplication if complex scenarios arise

        # 1. Read from Redis List Inbox
        redis_list_key = f"agent_inbox_list:{self.agent_name}"
        try:
            # Atomically get all messages and clear the list to avoid race conditions with multiple workers (if any)
            # or to ensure messages are definitively removed once fetched.
            # Using a pipeline for atomicity of lrange and del.
            pipe = self.redis_client.pipeline()
            pipe.lrange(redis_list_key, 0, -1)  # Get all items
            pipe.delete(redis_list_key)         # Delete the list
            redis_messages_raw, _ = pipe.execute()

            if redis_messages_raw:
                for raw_message in reversed(redis_messages_raw): # LPUSH/LRANGE means newest is at head (index 0). Reverse to get chronological.
                                                                 # If using RPOP in a loop, no reverse needed for chronological.
                                                                 # Let's assume LPUSH -> newest at head. If processing order matters, consider RPOP or reversing LRANGE results.
                                                                 # For typical inbox, newest last (append) or oldest first (pop from other end).
                                                                 # LPUSH adds to left (head). LRANGE 0 -1 gets all, left to right.
                                                                 # To process in order of arrival (oldest first), assuming LPUSH = newest first:
                                                                 # Option A: LRANGE then reverse the client-side list. (current choice)
                                                                 # Option B: Use RPOPLPUSH to a temporary list then process, or multiple RPOP.
                    try:
                        message_data = json.loads(raw_message.decode('utf-8') if isinstance(raw_message, bytes) else raw_message)
                        all_messages.append(message_data)
                    except json.JSONDecodeError as e:
                        print(f"Error decoding JSON from Redis message for agent {self.agent_name}: {raw_message}, error: {e}")
        except Exception as e:
            print(f"Error reading messages from Redis list {redis_list_key} for agent {self.agent_name}: {e}")

        # 2. Read from Filesystem Inbox
        inbox_path = self.comm_dir / 'inbox' / self.agent_name
        if inbox_path.exists():
            processed_dir = inbox_path / 'processed'
            processed_dir.mkdir(parents=True, exist_ok=True)
            
            for msg_file in inbox_path.glob('*.json'):
                if msg_file.is_file(): # Ensure it's a file, not the 'processed' directory
                    try:
                        with open(msg_file, 'r') as f:
                            message_data = json.load(f)
                        # Basic deduplication could be added here if messages had unique IDs and were reliably written to both Redis & FS
                        # For now, appending all; assumes Redis clear + FS move prevents most duplicates in practice.
                        all_messages.append(message_data)
                        
                        # Move to processed
                        msg_file.rename(processed_dir / msg_file.name)
                    except Exception as e:
                        # Handle cases like file being moved or deleted during processing, or JSON errors
                        print(f"Error processing message file {msg_file.name}: {e}") 
                        # Optionally log this error properly
                        pass # Continue to next file
        
        return all_messages
    
    def update_status(self, status: str, progress: int, details: Dict = None):
        """Update agent's current status"""
        status_data = {
            'agent': self.agent_name,
            'status': status,
            'progress': progress,
            'details': details or {},
            'timestamp': datetime.now().isoformat()
        }
        
        # Update in Redis for real-time monitoring
        self.redis_client.setex(
            f"agent_status_{self.agent_name}",
            300,  # 5 minute TTL
            json.dumps(status_data)
        )
        
        # Save to filesystem
        status_file = self.comm_dir / 'status' / f'{self.agent_name}_status.json'
        with open(status_file, 'w') as f:
            json.dump(status_data, f, indent=2)
    
    def share_knowledge(self, knowledge_type: str, content: Dict):
        """Share learned patterns or discoveries with all agents"""
        knowledge = {
            'contributor': self.agent_name,
            'type': knowledge_type,
            'content': content,
            'timestamp': datetime.now().isoformat()
        }
        
        kb_dir = self.comm_dir / 'knowledge-base'
        kb_dir.mkdir(parents=True, exist_ok=True) # Ensure it exists
        filename = f"{knowledge_type}_{self.agent_name}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.json"
        
        with open(kb_dir / filename, 'w') as f:
            json.dump(knowledge, f, indent=2)
        
        # Notify all agents via Redis (e.g., a dashboard could listen to this)
        self.redis_client.publish('knowledge_updates', json.dumps({
            'type': 'new_knowledge',
            'file': str(kb_dir / filename), # Send full path or relative as needed
            'contributor': self.agent_name
        }))
    
    def get_all_agent_statuses(self) -> Dict[str, Dict]:
        """Get current status of all agents from filesystem"""
        statuses = {}
        status_dir = self.comm_dir / 'status'
        
        if status_dir.exists():
            for status_file in status_dir.glob('*_status.json'):
                if status_file.is_file():
                    with open(status_file, 'r') as f:
                        try:
                            data = json.load(f)
                            statuses[data['agent']] = data
                        except json.JSONDecodeError:
                            print(f"Warning: Could not decode JSON from status file: {status_file.name}")
                            # Optionally log this error
        
        return statuses

    def listen_for_messages(self, callback, channels: Optional[List[str]] = None):
        """Listen to Redis pub/sub channels for real-time messages."""
        if channels is None:
            channels = [f"agent_channel_{self.agent_name}", "knowledge_updates"]

        pubsub = self.redis_client.pubsub()
        for channel in channels:
            pubsub.subscribe(channel)
        
        print(f"{self.agent_name} listening for messages on channels: {', '.join(channels)}")
        for message in pubsub.listen():
            if message['type'] == 'message':
                try:
                    data = json.loads(message['data'])
                    callback(message['channel'], data)
                except json.JSONDecodeError:
                    print(f"Error decoding JSON from Redis message: {message['data']}")
                except Exception as e:
                    print(f"Error in message callback: {e}")

    def broadcast_emergency_alert(self, system_component: str, reported_status: str, alert_details: Optional[Dict] = None, action_request: str = 'STOP_ALL_WORK'):
        """Broadcast an emergency alert to other agents and a dedicated Redis channel."""
        emergency_msg_content = {
            'severity': 'CRITICAL',
            'system_component': system_component,
            'reported_status': reported_status,
            'details': alert_details or {},
            'detected_by': self.agent_name,
            'detected_at': datetime.now().isoformat(),
            'action_request': action_request
        }

        # Define a list of agents to notify. 
        # This could be externalized to a config file or managed by an orchestrator in a more advanced setup.
        # For now, using the list from the user's example, excluding the sender itself.
        agents_to_notify = ['orchestrator', 'sms_engineer', 'phone_engineer', 'memory_engineer', 'test_engineer']
        
        print(f"EMERGENCY BROADCAST by {self.agent_name}: System {system_component} reported as {reported_status}. Action: {action_request}")

        for agent_name in agents_to_notify:
            if agent_name != self.agent_name: # Avoid sending to self, though send_message doesn't prevent it
                try:
                    self.send_message(
                        to_agent=agent_name, 
                        message_type='emergency_alert', # Using a more generic type than 'emergency_stop'
                        content=emergency_msg_content
                    )
                    print(f"Sent emergency alert to {agent_name}")
                except Exception as e:
                    print(f"Failed to send emergency alert to {agent_name}: {e}")
            
        # Also use Redis pub/sub for immediate global notification
        try:
            self.redis_client.publish('karen_emergency_channel', json.dumps(emergency_msg_content))
            print(f"Published emergency alert to Redis channel 'karen_emergency_channel'")
        except Exception as e:
            print(f"Failed to publish emergency alert to Redis: {e}") 