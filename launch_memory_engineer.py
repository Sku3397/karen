#!/usr/bin/env python3
"""
Launch script for Memory Engineer
Monitors memory events and manages conversation memory across all mediums
"""

import sys
import os
import asyncio
import json
import logging
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.agent_communication import AgentCommunication
from src.memory_client import memory_client
from src.agent_activity_logger import AgentActivityLogger

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
activity_logger = AgentActivityLogger()

class MemoryEngineer:
    """Memory Engineer agent that monitors and processes memory events"""
    
    def __init__(self):
        self.agent_comm = AgentCommunication('memory_engineer')
        self.running = False
        
        # Log initialization
        activity_logger.log_activity(
            agent_name="memory_engineer",
            activity_type="initialization",
            details={
                "agent_communication": "initialized",
                "memory_client_enabled": memory_client.enabled,
                "timestamp": datetime.now().isoformat()
            }
        )
        
    async def start(self):
        """Start the Memory Engineer"""
        logger.info("Starting Memory Engineer...")
        
        # Update status
        self.agent_comm.update_status('initializing', 10, {
            'memory_system': 'chromadb' if memory_client.enabled else 'disabled',
            'start_time': datetime.now().isoformat()
        })
        
        if not memory_client.enabled:
            logger.warning("Memory system is disabled. Set USE_MEMORY_SYSTEM=True to enable full functionality.")
        
        self.running = True
        
        # Start processing loop
        await self.process_messages()
        
    async def process_messages(self):
        """Main message processing loop"""
        
        self.agent_comm.update_status('active', 100, {
            'monitoring': True,
            'collections': ['conversations', 'context', 'identity_mappings']
        })
        
        logger.info("Memory Engineer is now active and monitoring...")
        
        while self.running:
            try:
                # Check for new messages
                messages = self.agent_comm.read_messages()
                
                if messages:
                    logger.info(f"Processing {len(messages)} new messages")
                    
                    for msg in messages:
                        await self.handle_message(msg)
                
                # Sleep for a bit before next check
                await asyncio.sleep(5)
                
            except KeyboardInterrupt:
                logger.info("Received interrupt signal")
                break
            except Exception as e:
                logger.error(f"Error in message processing loop: {e}")
                await asyncio.sleep(10)  # Wait longer on error
        
        logger.info("Memory Engineer shutting down...")
        self.agent_comm.update_status('stopped', 0, {
            'stop_time': datetime.now().isoformat()
        })
    
    async def handle_message(self, message):
        """Handle individual messages"""
        try:
            msg_type = message.get('message_type', '')
            content = message.get('content', {})
            
            logger.debug(f"Handling message type: {msg_type}")
            
            if msg_type == 'memory_event':
                await self.handle_memory_event(content)
            elif msg_type == 'query':
                await self.handle_query(message)
            elif msg_type == 'link_identities':
                await self.handle_identity_linking(content)
            elif msg_type == 'cleanup_request':
                await self.handle_cleanup_request(content)
            else:
                logger.warning(f"Unknown message type: {msg_type}")
                
        except Exception as e:
            logger.error(f"Error handling message: {e}")
    
    async def handle_memory_event(self, event_data):
        """Handle memory storage events"""
        event_type = event_data.get('event_type', '')
        data = event_data.get('data', {})
        
        logger.info(f"Memory event: {event_type}")
        
        # Log different event types
        if event_type == 'email_stored':
            conversation_id = data.get('conversation_id')
            participants = data.get('participants', [])
            logger.info(f"Email conversation stored: {conversation_id}, participants: {participants}")
            
        elif event_type == 'sms_stored':
            conversation_id = data.get('conversation_id')
            has_linked = data.get('has_linked_identity', False)
            logger.info(f"SMS conversation stored: {conversation_id}, linked identity: {has_linked}")
            
        elif event_type == 'voice_stored':
            conversation_id = data.get('conversation_id')
            duration = data.get('duration', 0)
            logger.info(f"Voice conversation stored: {conversation_id}, duration: {duration}s")
            
        elif event_type == 'cleanup_completed':
            entries_removed = data.get('entries_removed', 0)
            logger.info(f"Memory cleanup completed: {entries_removed} entries removed")
    
    async def handle_query(self, message):
        """Handle memory query requests"""
        query_type = message.get('content', {}).get('query_type', '')
        from_agent = message.get('from_agent', '')
        
        logger.info(f"Processing query '{query_type}' from {from_agent}")
        
        # TODO: Implement specific query handlers
        # For now, send a placeholder response
        self.agent_comm.send_message(
            to_agent=from_agent,
            message_type='query_response',
            content={
                'query_type': query_type,
                'status': 'not_implemented',
                'message': 'Query handling not yet implemented'
            }
        )
    
    async def handle_identity_linking(self, content):
        """Handle identity linking requests"""
        email = content.get('email', '')
        phone = content.get('phone', '')
        name = content.get('name', '')
        
        if email and phone:
            success = await memory_client.link_identities(email, phone, name)
            logger.info(f"Identity linking {'successful' if success else 'failed'}: {email} <-> {phone}")
    
    async def handle_cleanup_request(self, content):
        """Handle memory cleanup requests"""
        days_to_keep = content.get('days_to_keep', 90)
        
        logger.info(f"Starting memory cleanup, keeping last {days_to_keep} days")
        await memory_client.cleanup_old_memories(days_to_keep)

async def main():
    """Main entry point"""
    engineer = MemoryEngineer()
    
    try:
        await engineer.start()
    except KeyboardInterrupt:
        logger.info("Memory Engineer stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise

if __name__ == "__main__":
    print("=== Karen AI Memory Engineer ===")
    print("Monitors and manages conversation memory across all communication mediums")
    print("Press Ctrl+C to stop\n")
    
    asyncio.run(main())