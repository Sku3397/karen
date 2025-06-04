#!/usr/bin/env python3
"""
Test script to initialize and test the Memory Engineer using AgentCommunication.
This script verifies that the memory system is properly integrated with the agent communication framework.
"""

import sys
import os
import time
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Add project root and src to path
PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / 'src'
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(SRC_DIR))

try:
    from src.agent_communication import AgentCommunication
    from src.memory_client import MemoryClient, memory_client, ConversationEntry
    from src.config import USE_MEMORY_SYSTEM
    from dotenv import load_dotenv
except ImportError as e:
    print(f"Error importing modules: {e}")
    print(f"Make sure you're running from the project root and all dependencies are installed")
    sys.exit(1)

# Load environment variables
env_path = PROJECT_ROOT / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

logger = logging.getLogger('memory_engineer_test')

class MemoryEngineerTest:
    """Test class for Memory Engineer initialization and functionality"""
    
    def __init__(self):
        self.agent_name = 'memory_engineer'
        self.test_agent_name = 'test_memory_client'
        
        # Initialize agent communication for the memory engineer
        self.memory_comm = AgentCommunication(self.agent_name)
        
        # Initialize a test client to send messages to memory engineer
        self.test_comm = AgentCommunication(self.test_agent_name)
        
        # Initialize memory client
        self.memory_client = MemoryClient()
        
        logger.info(f"Initialized test with memory system enabled: {USE_MEMORY_SYSTEM}")
    
    def test_agent_communication_setup(self):
        """Test that agent communication is properly set up"""
        logger.info("Testing agent communication setup...")
        
        # Update status for memory engineer
        self.memory_comm.update_status(
            status='testing', 
            progress=10, 
            details={'message': 'Testing memory engineer initialization'}
        )
        
        # Check if status was saved
        statuses = self.memory_comm.get_all_agent_statuses()
        if self.agent_name in statuses:
            logger.info(f"[PASS] Memory engineer status updated successfully: {statuses[self.agent_name]['status']}")
            return True
        else:
            logger.error("[FAIL] Failed to update memory engineer status")
            return False
    
    def test_message_sending(self):
        """Test sending messages to memory engineer"""
        logger.info("Testing message sending to memory engineer...")
        
        test_message = {
            'action': 'store_conversation',
            'data': {
                'conversation_type': 'email',
                'participants': ['test@example.com', 'karen@757handy.com'],
                'content': 'This is a test conversation for memory storage'
            }
        }
        
        try:
            self.test_comm.send_message(
                to_agent=self.agent_name,
                message_type='memory_request',
                content=test_message
            )
            logger.info("[PASS] Message sent to memory engineer successfully")
            return True
        except Exception as e:
            logger.error(f"[FAIL] Failed to send message to memory engineer: {e}")
            return False
    
    def test_message_reading(self):
        """Test reading messages from memory engineer inbox"""
        logger.info("Testing message reading from memory engineer inbox...")
        
        try:
            messages = self.memory_comm.read_messages()
            logger.info(f"[PASS] Read {len(messages)} messages from memory engineer inbox")
            
            if messages:
                for i, msg in enumerate(messages):
                    logger.info(f"  Message {i+1}: Type={msg.get('type')}, From={msg.get('from')}")
            
            return True
        except Exception as e:
            logger.error(f"[FAIL] Failed to read messages from memory engineer inbox: {e}")
            return False
    
    async def test_memory_client_functionality(self):
        """Test memory client functionality"""
        logger.info("Testing memory client functionality...")
        
        if not USE_MEMORY_SYSTEM:
            logger.warning("[SKIP] Memory system is disabled - skipping memory client tests")
            return True
        
        try:
            # Test storing an email conversation
            test_email_data = {
                'id': 'test_email_123',
                'sender': 'client@example.com',
                'recipient': 'karen@757handy.com',
                'subject': 'Test appointment request',
                'body': 'Hi, I need to schedule a plumbing appointment for next week.',
                'received_date_dt': datetime.now()
            }
            
            reply_content = "Thank you for contacting us. I'll help you schedule that appointment."
            
            conversation_id = await self.memory_client.store_email_conversation(
                test_email_data, 
                reply_content
            )
            
            if conversation_id:
                logger.info(f"[PASS] Email conversation stored with ID: {conversation_id}")
            else:
                logger.warning("[WARN] Email conversation storage returned None")
            
            # Test retrieving conversation history
            participants = ['client@example.com', 'karen@757handy.com']
            history = await self.memory_client.get_conversation_history(participants, limit=10)
            
            logger.info(f"[PASS] Retrieved {len(history)} conversation entries")
            
            # Test getting conversation context
            context = await self.memory_client.get_conversation_context(
                'client@example.com', 
                'karen@757handy.com'
            )
            
            logger.info(f"[PASS] Retrieved conversation context: {context}")
            
            # Test searching conversations
            search_results = await self.memory_client.search_conversations('appointment', limit=5)
            logger.info(f"[PASS] Search found {len(search_results)} matching conversations")
            
            return True
            
        except Exception as e:
            logger.error(f"[FAIL] Memory client test failed: {e}")
            return False
    
    def test_knowledge_sharing(self):
        """Test knowledge sharing functionality"""
        logger.info("Testing knowledge sharing...")
        
        try:
            self.memory_comm.share_knowledge(
                knowledge_type='memory_pattern',
                content={
                    'pattern_type': 'conversation_frequency',
                    'observation': 'Clients tend to follow up within 24 hours if no response',
                    'confidence': 0.85,
                    'sample_size': 100
                }
            )
            logger.info("[PASS] Knowledge shared successfully")
            return True
        except Exception as e:
            logger.error(f"[FAIL] Failed to share knowledge: {e}")
            return False
    
    async def run_all_tests(self):
        """Run all tests and report results"""
        logger.info("[START] Starting Memory Engineer initialization tests...")
        
        test_results = {}
        
        # Test agent communication setup
        test_results['communication_setup'] = self.test_agent_communication_setup()
        
        # Test message sending
        test_results['message_sending'] = self.test_message_sending()
        
        # Wait a moment for message to be processed
        time.sleep(1)
        
        # Test message reading
        test_results['message_reading'] = self.test_message_reading()
        
        # Test memory client functionality
        test_results['memory_client'] = await self.test_memory_client_functionality()
        
        # Test knowledge sharing
        test_results['knowledge_sharing'] = self.test_knowledge_sharing()
        
        # Report results
        logger.info("\n" + "="*50)
        logger.info("TEST RESULTS SUMMARY")
        logger.info("="*50)
        
        passed = 0
        total = len(test_results)
        
        for test_name, result in test_results.items():
            status = "[PASS]" if result else "[FAIL]"
            logger.info(f"{test_name}: {status}")
            if result:
                passed += 1
        
        logger.info("="*50)
        logger.info(f"Tests passed: {passed}/{total}")
        
        if passed == total:
            logger.info("[SUCCESS] All tests passed! Memory Engineer is properly initialized.")
        else:
            logger.warning(f"[WARNING] {total - passed} test(s) failed. Check the logs above for details.")
        
        return passed == total

def main():
    """Main test function"""
    logger.info("[TEST] Memory Engineer Initialization Test")
    logger.info(f"Project root: {PROJECT_ROOT}")
    logger.info(f"Memory system enabled: {USE_MEMORY_SYSTEM}")
    
    # Check Redis connectivity
    try:
        from redis import Redis
        redis_url = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
        redis_client = Redis.from_url(redis_url)
        redis_client.ping()
        logger.info(f"[PASS] Redis connection successful at {redis_url}")
    except Exception as e:
        logger.error(f"[FAIL] Redis connection failed: {e}")
        logger.error("Make sure Redis is running (e.g., docker run -d --name karen-redis -p 6379:6379 redis)")
        return False
    
    # Run tests
    test_runner = MemoryEngineerTest()
    
    try:
        # Run async tests
        result = asyncio.run(test_runner.run_all_tests())
        return result
    except Exception as e:
        logger.error(f"[FAIL] Test execution failed: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)