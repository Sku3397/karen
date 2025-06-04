"""
Memory Client for Karen AI - Vector Database Integration
Handles conversation memory across different communication mediums (email, SMS, voice)
"""

import os
import json
import hashlib
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np
from chromadb import Client, Settings
from chromadb.config import Settings as ChromaSettings
import chromadb

from .agent_communication import AgentCommunication
from .config import USE_MEMORY_SYSTEM, PROJECT_ROOT

logger = logging.getLogger(__name__)

@dataclass
class ConversationEntry:
    """Represents a single conversation entry across any medium"""
    id: str
    conversation_id: str  # Links related messages
    medium: str  # email, sms, voice
    timestamp: datetime
    sender: str
    recipient: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationEntry':
        """Create from dictionary"""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)

class MemoryClient:
    """Manages conversation memory using vector database"""
    
    def __init__(self):
        self.enabled = USE_MEMORY_SYSTEM
        self.agent_comm = AgentCommunication('memory_engineer')
        
        if not self.enabled:
            logger.info("Memory system is disabled via USE_MEMORY_SYSTEM=False")
            return
            
        # Initialize ChromaDB
        self.memory_dir = Path(PROJECT_ROOT) / 'memory_storage'
        self.memory_dir.mkdir(exist_ok=True)
        
        try:
            self.client = chromadb.PersistentClient(
                path=str(self.memory_dir),
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Create collections for different memory types
            self.conversations_collection = self.client.get_or_create_collection(
                name="conversations",
                metadata={"description": "Cross-medium conversation history"}
            )
            
            self.context_collection = self.client.get_or_create_collection(
                name="context",
                metadata={"description": "Conversation context and patterns"}
            )
            
            logger.info("Memory client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize memory client: {e}")
            self.enabled = False
    
    def _generate_conversation_id(self, sender: str, recipient: str) -> str:
        """Generate a consistent conversation ID for participants"""
        participants = sorted([sender.lower(), recipient.lower()])
        content = f"{participants[0]}:{participants[1]}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def _extract_email_content(self, email_data: Dict[str, Any]) -> str:
        """Extract meaningful content from email data"""
        subject = email_data.get('subject', '')
        body = email_data.get('body', '') or email_data.get('body_text', '')
        
        # Combine subject and body
        content = f"Subject: {subject}\n{body}" if subject else body
        return content.strip()
    
    async def store_email_conversation(self, email_data: Dict[str, Any], reply_content: str = None) -> Optional[str]:
        """Store email conversation in memory"""
        if not self.enabled:
            return None
            
        try:
            sender = email_data.get('sender', '')
            recipient = email_data.get('recipient', email_data.get('to', ''))
            content = self._extract_email_content(email_data)
            
            conversation_id = self._generate_conversation_id(sender, recipient)
            
            # Store incoming email
            entry_id = f"email_{email_data.get('id', datetime.now().isoformat())}"
            entry = ConversationEntry(
                id=entry_id,
                conversation_id=conversation_id,
                medium='email',
                timestamp=email_data.get('received_date_dt', datetime.now()),
                sender=sender,
                recipient=recipient,
                content=content,
                metadata={
                    'email_id': email_data.get('id'),
                    'subject': email_data.get('subject', ''),
                    'thread_id': email_data.get('threadId'),
                    'direction': 'incoming'
                }
            )
            
            await self._store_entry(entry)
            
            # Store reply if provided
            if reply_content:
                reply_id = f"email_reply_{entry_id}"
                reply_entry = ConversationEntry(
                    id=reply_id,
                    conversation_id=conversation_id,
                    medium='email',
                    timestamp=datetime.now(),
                    sender=recipient,  # Karen is sending
                    recipient=sender,  # Original sender receives
                    content=reply_content,
                    metadata={
                        'reply_to': entry_id,
                        'direction': 'outgoing'
                    }
                )
                await self._store_entry(reply_entry)
            
            # Notify memory engineer
            await self._notify_memory_engineer('email_stored', {
                'conversation_id': conversation_id,
                'entry_count': 2 if reply_content else 1,
                'participants': [sender, recipient]
            })
            
            return conversation_id
            
        except Exception as e:
            logger.error(f"Error storing email conversation: {e}")
            return None
    
    async def store_sms_conversation(self, sms_data: Dict[str, Any]) -> Optional[str]:
        """Store SMS conversation in memory"""
        if not self.enabled:
            return None
            
        try:
            sender = sms_data.get('from', '')
            recipient = sms_data.get('to', '')
            content = sms_data.get('body', '')
            
            conversation_id = self._generate_conversation_id(sender, recipient)
            
            entry_id = f"sms_{sms_data.get('sid', datetime.now().isoformat())}"
            entry = ConversationEntry(
                id=entry_id,
                conversation_id=conversation_id,
                medium='sms',
                timestamp=sms_data.get('date_created', datetime.now()),
                sender=sender,
                recipient=recipient,
                content=content,
                metadata={
                    'sms_sid': sms_data.get('sid'),
                    'direction': sms_data.get('direction', 'unknown')
                }
            )
            
            await self._store_entry(entry)
            
            await self._notify_memory_engineer('sms_stored', {
                'conversation_id': conversation_id,
                'participants': [sender, recipient]
            })
            
            return conversation_id
            
        except Exception as e:
            logger.error(f"Error storing SMS conversation: {e}")
            return None
    
    async def _store_entry(self, entry: ConversationEntry):
        """Store a conversation entry in the vector database"""
        if not self.enabled:
            return
            
        # Generate embedding for content (simplified - in production use proper embedding model)
        embedding = self._simple_embedding(entry.content)
        entry.embedding = embedding
        
        # Store in ChromaDB
        self.conversations_collection.add(
            ids=[entry.id],
            documents=[entry.content],
            embeddings=[embedding],
            metadatas=[{
                'conversation_id': entry.conversation_id,
                'medium': entry.medium,
                'timestamp': entry.timestamp.isoformat(),
                'sender': entry.sender,
                'recipient': entry.recipient,
                **entry.metadata
            }]
        )
        
        logger.debug(f"Stored conversation entry: {entry.id}")
    
    def _simple_embedding(self, text: str) -> List[float]:
        """Generate simple embedding for text (placeholder for proper embedding model)"""
        # This is a very simple hash-based embedding for demonstration
        # In production, use proper embedding models like OpenAI, Sentence Transformers, etc.
        import hashlib
        hash_obj = hashlib.sha256(text.encode())
        hash_hex = hash_obj.hexdigest()
        
        # Convert to 384-dimensional vector (common embedding size)
        embedding = []
        for i in range(0, len(hash_hex), 2):
            val = int(hash_hex[i:i+2], 16) / 255.0  # Normalize to 0-1
            embedding.append(val)
        
        # Pad or truncate to 384 dimensions
        while len(embedding) < 384:
            embedding.append(0.0)
        embedding = embedding[:384]
        
        return embedding
    
    async def get_conversation_history(self, participants: List[str], limit: int = 50) -> List[ConversationEntry]:
        """Retrieve conversation history between participants"""
        if not self.enabled:
            return []
        
        try:
            conversation_id = self._generate_conversation_id(participants[0], participants[1])
            
            results = self.conversations_collection.query(
                where={"conversation_id": conversation_id},
                n_results=limit
            )
            
            entries = []
            for i, doc in enumerate(results['documents']):
                metadata = results['metadatas'][i]
                entry = ConversationEntry(
                    id=results['ids'][i],
                    conversation_id=metadata['conversation_id'],
                    medium=metadata['medium'],
                    timestamp=datetime.fromisoformat(metadata['timestamp']),
                    sender=metadata['sender'],
                    recipient=metadata['recipient'],
                    content=doc,
                    metadata={k: v for k, v in metadata.items() 
                             if k not in ['conversation_id', 'medium', 'timestamp', 'sender', 'recipient']}
                )
                entries.append(entry)
            
            # Sort by timestamp
            entries.sort(key=lambda x: x.timestamp)
            return entries
            
        except Exception as e:
            logger.error(f"Error retrieving conversation history: {e}")
            return []
    
    async def search_conversations(self, query: str, limit: int = 10) -> List[ConversationEntry]:
        """Search conversations by content similarity"""
        if not self.enabled:
            return []
        
        try:
            query_embedding = self._simple_embedding(query)
            
            results = self.conversations_collection.query(
                query_embeddings=[query_embedding],
                n_results=limit
            )
            
            entries = []
            for i, doc in enumerate(results['documents']):
                metadata = results['metadatas'][i]
                entry = ConversationEntry(
                    id=results['ids'][i],
                    conversation_id=metadata['conversation_id'],
                    medium=metadata['medium'],
                    timestamp=datetime.fromisoformat(metadata['timestamp']),
                    sender=metadata['sender'],
                    recipient=metadata['recipient'],
                    content=doc,
                    metadata={k: v for k, v in metadata.items() 
                             if k not in ['conversation_id', 'medium', 'timestamp', 'sender', 'recipient']}
                )
                entries.append(entry)
            
            return entries
            
        except Exception as e:
            logger.error(f"Error searching conversations: {e}")
            return []
    
    async def get_conversation_context(self, sender: str, recipient: str) -> Dict[str, Any]:
        """Get contextual information about a conversation"""
        if not self.enabled:
            return {}
        
        try:
            history = await self.get_conversation_history([sender, recipient], limit=10)
            
            if not history:
                return {
                    'is_new_conversation': True,
                    'message_count': 0,
                    'last_interaction': None,
                    'primary_medium': None
                }
            
            # Analyze conversation patterns
            mediums = [entry.medium for entry in history]
            primary_medium = max(set(mediums), key=mediums.count)
            
            return {
                'is_new_conversation': False,
                'message_count': len(history),
                'last_interaction': history[-1].timestamp,
                'primary_medium': primary_medium,
                'recent_topics': self._extract_topics(history[-5:]),
                'conversation_summary': self._generate_summary(history[-10:])
            }
            
        except Exception as e:
            logger.error(f"Error getting conversation context: {e}")
            return {}
    
    def _extract_topics(self, entries: List[ConversationEntry]) -> List[str]:
        """Extract key topics from recent conversation entries"""
        # Simple keyword extraction (in production, use proper NLP)
        all_text = ' '.join([entry.content for entry in entries])
        words = all_text.lower().split()
        
        # Filter common words and extract potential topics
        common_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'this', 'that', 'these', 'those'}
        
        topics = []
        for word in words:
            if len(word) > 3 and word not in common_words:
                if word not in topics:
                    topics.append(word)
                if len(topics) >= 10:
                    break
        
        return topics
    
    def _generate_summary(self, entries: List[ConversationEntry]) -> str:
        """Generate a brief summary of recent conversation"""
        if not entries:
            return ""
        
        # Simple summary generation (in production, use proper summarization)
        total_messages = len(entries)
        mediums = list(set([entry.medium for entry in entries]))
        timespan = entries[-1].timestamp - entries[0].timestamp
        
        return f"Last {total_messages} messages over {timespan.days} days via {', '.join(mediums)}"
    
    async def _notify_memory_engineer(self, event_type: str, data: Dict[str, Any]):
        """Notify the memory engineer agent about memory events"""
        try:
            self.agent_comm.send_message(
                to_agent='memory_engineer',
                message_type='memory_event',
                content={
                    'event_type': event_type,
                    'timestamp': datetime.now().isoformat(),
                    'data': data
                }
            )
        except Exception as e:
            logger.error(f"Failed to notify memory engineer: {e}")
    
    async def cleanup_old_memories(self, days_to_keep: int = 90):
        """Clean up old conversation memories"""
        if not self.enabled:
            return
        
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            # Query old entries
            results = self.conversations_collection.query(
                where={"timestamp": {"$lt": cutoff_date.isoformat()}},
                n_results=1000  # Process in batches
            )
            
            if results['ids']:
                self.conversations_collection.delete(ids=results['ids'])
                logger.info(f"Cleaned up {len(results['ids'])} old conversation entries")
                
                await self._notify_memory_engineer('cleanup_completed', {
                    'entries_removed': len(results['ids']),
                    'cutoff_date': cutoff_date.isoformat()
                })
        
        except Exception as e:
            logger.error(f"Error during memory cleanup: {e}")

# Global instance
memory_client = MemoryClient()

async def store_email_memory(email_data: Dict[str, Any], reply_content: str = None) -> Optional[str]:
    """Convenience function for storing email conversations"""
    return await memory_client.store_email_conversation(email_data, reply_content)

async def get_conversation_context(sender: str, recipient: str) -> Dict[str, Any]:
    """Convenience function for getting conversation context"""
    return await memory_client.get_conversation_context(sender, recipient)

async def search_memory(query: str, limit: int = 10) -> List[ConversationEntry]:
    """Convenience function for searching memory"""
    return await memory_client.search_conversations(query, limit)