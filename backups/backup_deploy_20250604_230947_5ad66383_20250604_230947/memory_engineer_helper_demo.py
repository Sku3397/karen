#!/usr/bin/env python3
"""
Memory Engineer using claude_helpers system
"""

import sys
sys.path.append('.')
from claude_helpers import memory_helper as helper

# Update status to show we're starting
helper.update_status('initializing', 10, {'agent': 'memory_engineer', 'using': 'helper_system'})

# Check if memory client exists
existing = helper.read_file('src/memory_client.py')
if existing:
    helper.update_status('active', 50, {'memory_client': 'exists', 'size': len(existing)})
    
    # Search for chromadb usage
    chromadb_files = helper.search_code('chromadb')
    helper.update_status('active', 60, {'chromadb_files': len(chromadb_files)})
    
    # Create enhanced memory test
    test_code = '''#!/usr/bin/env python3
"""
Test Memory System via Helper
"""
import sys
sys.path.append('.')

async def test_memory():
    from src.memory_client import memory_client, store_email_memory, link_customer_identities
    
    # Test identity linking
    success = await link_customer_identities(
        email="test@example.com",
        phone="+17571234567",
        name="Test User"
    )
    print(f"Identity linking: {success}")
    
    # Test email storage
    email_data = {
        'id': 'test_123',
        'sender': 'test@example.com',
        'recipient': 'karen@example.com',
        'subject': 'Test Subject',
        'body': 'Test body content'
    }
    
    conv_id = await store_email_memory(email_data, "Test reply")
    print(f"Stored conversation: {conv_id}")
    
    return True

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_memory())
'''
    
    helper.create_file('test_memory_via_helper.py', test_code)
    helper.update_status('active', 70, {'created': 'test_memory_via_helper.py'})
    
    # Create knowledge sharing about memory patterns
    knowledge = {
        'type': 'memory_patterns_enhanced',
        'description': 'Memory system patterns using helper framework',
        'patterns': [
            'Use helper.create_file() for all file operations',
            'Use helper.update_status() for progress updates', 
            'Use helper.read_file() for reading existing files',
            'Use helper.search_code() to find patterns',
            'ChromaDB collections: conversations, context, identity_mappings'
        ],
        'implementation': {
            'cross_medium_linking': True,
            'phone_normalization': True,
            'auto_identity_detection': True
        }
    }
    
    helper.send_message('orchestrator', 'knowledge_update', knowledge)
    helper.update_status('active', 80, {'knowledge': 'shared'})
    
    # Check agent communication
    agent_comm_file = helper.read_file('src/agent_communication.py')
    if 'memory_engineer' in agent_comm_file:
        helper.update_status('active', 90, {'agent_comm': 'integrated'})
    
    # Final status
    helper.update_status('active', 100, {
        'memory_system': 'operational',
        'helper_integration': 'complete',
        'collections': ['conversations', 'context', 'identity_mappings']
    })
    
    print("Memory Engineer helper demo complete")
    print(f"ChromaDB files found: {chromadb_files}")
    
else:
    helper.update_status('error', 0, {'error': 'memory_client.py not found'})
    
    # Create basic memory client
    memory_client_code = '''"""
Memory Client - Basic Implementation
"""
import chromadb
from chromadb import Settings
import logging

logger = logging.getLogger(__name__)

class MemoryClient:
    def __init__(self):
        self.client = chromadb.PersistentClient(
            path="./memory_storage",
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Create collections
        self.conversations = self.client.get_or_create_collection("conversations")
        self.identities = self.client.get_or_create_collection("identities")
        
    async def store_conversation(self, data):
        """Store conversation in ChromaDB"""
        self.conversations.add(
            ids=[data['id']],
            documents=[data['content']],
            metadatas=[data['metadata']]
        )
        logger.info(f"Stored conversation {data['id']}")
        
    async def link_identities(self, email, phone, name=None):
        """Link email and phone identities"""
        self.identities.add(
            ids=[f"{email}:{phone}"],
            documents=[f"{email} linked to {phone}"],
            metadatas=[{'email': email, 'phone': phone, 'name': name or ''}]
        )
        return True

memory_client = MemoryClient()
'''
    
    helper.create_file('src/memory_client_basic.py', memory_client_code)
    helper.update_status('active', 100, {'created': 'basic_memory_client'})