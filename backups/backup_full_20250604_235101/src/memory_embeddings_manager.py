"""
Memory Embeddings Manager for Karen AI
Advanced ChromaDB-based conversation storage with semantic embeddings

Handles:
- Semantic embedding generation using sentence-transformers
- ChromaDB collection management with persistence
- Conversation storage with rich metadata
- Similarity search across all conversations
- Multi-modal conversation linking
"""

import os
import hashlib
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
import logging

logger = logging.getLogger(__name__)

class EmbeddingGenerator:
    """Generates semantic embeddings for conversation text"""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Initialize embedding generator
        
        Args:
            model_name: Sentence transformer model (fast and efficient)
        """
        self.model_name = model_name
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the sentence transformer model lazily"""
        try:
            logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            logger.info("✅ Embedding model loaded successfully")
        except Exception as e:
            logger.error(f"❌ Failed to load embedding model: {e}")
            raise
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate semantic embedding for text
        
        Args:
            text: Input text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        if not self.model:
            self._load_model()
        
        if not text or not text.strip():
            logger.warning("Empty text provided for embedding")
            return [0.0] * 384  # Return zero vector for MiniLM-L6-v2
        
        try:
            # Generate embedding
            embedding = self.model.encode(text.strip(), convert_to_tensor=False)
            
            # Convert to list of floats
            if isinstance(embedding, np.ndarray):
                return embedding.tolist()
            return list(embedding)
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return [0.0] * 384  # Fallback zero vector
    
    def batch_generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts efficiently
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        if not self.model:
            self._load_model()
        
        if not texts:
            return []
        
        try:
            # Filter out empty texts
            valid_texts = [text.strip() for text in texts if text and text.strip()]
            
            if not valid_texts:
                return [[0.0] * 384] * len(texts)
            
            # Generate embeddings in batch
            embeddings = self.model.encode(valid_texts, convert_to_tensor=False)
            
            # Convert to list format
            return [emb.tolist() if isinstance(emb, np.ndarray) else list(emb) 
                   for emb in embeddings]
            
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            return [[0.0] * 384] * len(texts)

class ConversationMetadata:
    """Schema for conversation metadata"""
    
    @staticmethod
    def create_metadata(
        customer_id: str,
        channel: str,
        direction: str,
        timestamp: datetime = None,
        phone_number: str = None,
        email_address: str = None,
        customer_name: str = None,
        intent: str = None,
        sentiment: str = None,
        urgency: str = "normal",
        tags: List[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create standardized metadata for conversation storage
        
        Args:
            customer_id: Unique customer identifier
            channel: Communication channel (email, sms, phone, chat)
            direction: inbound or outbound
            timestamp: When conversation occurred
            phone_number: Customer phone (for cross-channel linking)
            email_address: Customer email (for cross-channel linking)
            customer_name: Customer name (for identity resolution)
            intent: Classified intent (appointment, question, complaint, etc.)
            sentiment: Detected sentiment (positive, negative, neutral)
            urgency: Message urgency (low, normal, high, critical)
            tags: Additional tags for categorization
            **kwargs: Additional custom metadata
            
        Returns:
            Standardized metadata dictionary
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        
        metadata = {
            # Core identifiers
            "customer_id": customer_id,
            "channel": channel.lower(),
            "direction": direction.lower(),
            
            # Timestamp
            "timestamp": timestamp.isoformat(),
            "date": timestamp.date().isoformat(),
            "hour": timestamp.hour,
            "day_of_week": timestamp.weekday(),
            
            # Contact information (for cross-channel linking)
            "phone_number": ConversationMetadata._normalize_phone(phone_number) if phone_number else None,
            "email_address": email_address.lower() if email_address else None,
            "customer_name": customer_name.strip() if customer_name else None,
            
            # Content classification
            "intent": intent,
            "sentiment": sentiment,
            "urgency": urgency,
            "tags": tags or [],
            
            # System metadata
            "created_at": datetime.now(timezone.utc).isoformat(),
            "version": "1.0"
        }
        
        # Add custom metadata
        metadata.update(kwargs)
        
        # Remove None values
        return {k: v for k, v in metadata.items() if v is not None}
    
    @staticmethod
    def _normalize_phone(phone: str) -> str:
        """Normalize phone number for consistent storage"""
        if not phone:
            return None
        
        # Remove all non-digit characters
        digits_only = ''.join(filter(str.isdigit, phone))
        
        # Handle US numbers
        if len(digits_only) == 10:
            return f"+1{digits_only}"
        elif len(digits_only) == 11 and digits_only.startswith('1'):
            return f"+{digits_only}"
        else:
            return f"+{digits_only}"

class MemoryEmbeddingsManager:
    """Main manager for conversation embeddings and ChromaDB operations"""
    
    def __init__(self, persist_directory: str = "karen_memory", collection_name: str = "conversations"):
        """
        Initialize memory embeddings manager
        
        Args:
            persist_directory: Directory for ChromaDB persistence
            collection_name: Name of the ChromaDB collection
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.embedding_generator = EmbeddingGenerator()
        self.client = None
        self.collection = None
        
        self._initialize_chromadb()
    
    def _initialize_chromadb(self):
        """Initialize ChromaDB client and collection"""
        try:
            # Ensure persist directory exists
            os.makedirs(self.persist_directory, exist_ok=True)
            
            # Initialize ChromaDB client with persistence
            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "Karen AI conversation memory with semantic embeddings"}
            )
            
            logger.info(f"✅ ChromaDB initialized: {self.persist_directory}/{self.collection_name}")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize ChromaDB: {e}")
            raise
    
    def store_conversation(
        self,
        text: str,
        customer_id: str,
        channel: str,
        direction: str = "inbound",
        conversation_id: str = None,
        **metadata_kwargs
    ) -> str:
        """
        Store a conversation with semantic embedding
        
        Args:
            text: Conversation text content
            customer_id: Unique customer identifier
            channel: Communication channel
            direction: Message direction
            conversation_id: Optional custom conversation ID
            **metadata_kwargs: Additional metadata
            
        Returns:
            Unique document ID for the stored conversation
        """
        try:
            # Generate unique ID if not provided
            if not conversation_id:
                # Create deterministic ID based on content and metadata
                content_hash = hashlib.md5(
                    f"{customer_id}_{channel}_{text[:100]}_{datetime.now().isoformat()}".encode()
                ).hexdigest()
                conversation_id = f"conv_{content_hash}_{uuid.uuid4().hex[:8]}"
            
            # Generate embedding
            embedding = self.embedding_generator.generate_embedding(text)
            
            # Create metadata
            metadata = ConversationMetadata.create_metadata(
                customer_id=customer_id,
                channel=channel,
                direction=direction,
                **metadata_kwargs
            )
            
            # Store in ChromaDB
            self.collection.add(
                documents=[text],
                embeddings=[embedding],
                metadatas=[metadata],
                ids=[conversation_id]
            )
            
            logger.info(f"✅ Stored conversation: {conversation_id} for customer {customer_id}")
            return conversation_id
            
        except Exception as e:
            logger.error(f"❌ Failed to store conversation: {e}")
            raise
    
    def search_similar(
        self,
        query_text: str,
        n_results: int = 10,
        customer_id: str = None,
        channel: str = None,
        min_relevance: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Search for similar conversations using semantic similarity
        
        Args:
            query_text: Text to search for
            n_results: Maximum number of results
            customer_id: Optional customer filter
            channel: Optional channel filter
            min_relevance: Minimum relevance score (0-1)
            
        Returns:
            List of similar conversations with metadata and relevance scores
        """
        try:
            # Generate query embedding
            query_embedding = self.embedding_generator.generate_embedding(query_text)
            
            # Build where clause for filtering
            where_clause = {}
            if customer_id:
                where_clause["customer_id"] = customer_id
            if channel:
                where_clause["channel"] = channel.lower()
            
            # Search in ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where_clause if where_clause else None
            )
            
            # Process results
            conversations = []
            if results['documents'] and results['documents'][0]:
                for i in range(len(results['documents'][0])):
                    # Calculate relevance score (ChromaDB returns distances, convert to similarity)
                    distance = results['distances'][0][i] if results['distances'] else 1.0
                    relevance = max(0, 1 - distance)  # Convert distance to similarity
                    
                    if relevance >= min_relevance:
                        conversations.append({
                            'id': results['ids'][0][i],
                            'text': results['documents'][0][i],
                            'metadata': results['metadatas'][0][i],
                            'relevance_score': relevance
                        })
            
            # Sort by relevance
            conversations.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            logger.info(f"✅ Found {len(conversations)} similar conversations")
            return conversations
            
        except Exception as e:
            logger.error(f"❌ Failed to search conversations: {e}")
            return []
    
    def get_customer_conversations(
        self,
        customer_id: str,
        limit: int = 50,
        channel: str = None,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> List[Dict[str, Any]]:
        """
        Get all conversations for a specific customer
        
        Args:
            customer_id: Customer identifier
            limit: Maximum number of conversations
            channel: Optional channel filter
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            List of customer conversations
        """
        try:
            # Build where clause
            where_clause = {"customer_id": customer_id}
            if channel:
                where_clause["channel"] = channel.lower()
            
            # Get conversations
            results = self.collection.get(
                where=where_clause,
                limit=limit
            )
            
            conversations = []
            if results['documents']:
                for i in range(len(results['documents'])):
                    conversation = {
                        'id': results['ids'][i],
                        'text': results['documents'][i],
                        'metadata': results['metadatas'][i]
                    }
                    
                    # Date filtering if specified
                    if start_date or end_date:
                        conv_date = datetime.fromisoformat(
                            conversation['metadata']['timestamp'].replace('Z', '+00:00')
                        )
                        
                        if start_date and conv_date < start_date:
                            continue
                        if end_date and conv_date > end_date:
                            continue
                    
                    conversations.append(conversation)
            
            # Sort by timestamp (newest first)
            conversations.sort(
                key=lambda x: x['metadata']['timestamp'],
                reverse=True
            )
            
            logger.info(f"✅ Found {len(conversations)} conversations for customer {customer_id}")
            return conversations
            
        except Exception as e:
            logger.error(f"❌ Failed to get customer conversations: {e}")
            return []
    
    def update_conversation_metadata(self, conversation_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update metadata for an existing conversation
        
        Args:
            conversation_id: Conversation identifier
            updates: Metadata updates
            
        Returns:
            True if successful
        """
        try:
            # Get existing conversation
            result = self.collection.get(ids=[conversation_id])
            
            if not result['documents']:
                logger.warning(f"Conversation not found: {conversation_id}")
                return False
            
            # Update metadata
            existing_metadata = result['metadatas'][0]
            existing_metadata.update(updates)
            existing_metadata['updated_at'] = datetime.now(timezone.utc).isoformat()
            
            # Update in ChromaDB
            self.collection.update(
                ids=[conversation_id],
                metadatas=[existing_metadata]
            )
            
            logger.info(f"✅ Updated conversation metadata: {conversation_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to update conversation metadata: {e}")
            return False
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation (for privacy compliance)
        
        Args:
            conversation_id: Conversation identifier
            
        Returns:
            True if successful
        """
        try:
            self.collection.delete(ids=[conversation_id])
            logger.info(f"✅ Deleted conversation: {conversation_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to delete conversation: {e}")
            return False
    
    def delete_customer_data(self, customer_id: str) -> int:
        """
        Delete all data for a customer (right to be forgotten)
        
        Args:
            customer_id: Customer identifier
            
        Returns:
            Number of conversations deleted
        """
        try:
            # Get all customer conversations
            results = self.collection.get(
                where={"customer_id": customer_id}
            )
            
            if results['ids']:
                # Delete all conversations
                self.collection.delete(
                    where={"customer_id": customer_id}
                )
                
                deleted_count = len(results['ids'])
                logger.info(f"✅ Deleted {deleted_count} conversations for customer {customer_id}")
                return deleted_count
            
            return 0
            
        except Exception as e:
            logger.error(f"❌ Failed to delete customer data: {e}")
            return 0
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the conversation collection"""
        try:
            count = self.collection.count()
            
            # Get sample to analyze channels and customers
            sample_results = self.collection.get(limit=1000)
            
            channels = set()
            customers = set()
            
            if sample_results['metadatas']:
                for metadata in sample_results['metadatas']:
                    if 'channel' in metadata:
                        channels.add(metadata['channel'])
                    if 'customer_id' in metadata:
                        customers.add(metadata['customer_id'])
            
            return {
                'total_conversations': count,
                'channels': list(channels),
                'customer_count': len(customers),
                'persist_directory': self.persist_directory,
                'collection_name': self.collection_name
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get collection stats: {e}")
            return {}

# Convenience function for easy initialization
def get_memory_manager(persist_directory: str = "karen_memory") -> MemoryEmbeddingsManager:
    """Get initialized memory embeddings manager"""
    return MemoryEmbeddingsManager(persist_directory=persist_directory)

if __name__ == "__main__":
    # Example usage and testing
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize manager
    manager = get_memory_manager()
    
    # Store sample conversations
    conv1_id = manager.store_conversation(
        text="Hi, I need help with my kitchen faucet. It's leaking and I need someone to fix it.",
        customer_id="customer_123",
        channel="email",
        direction="inbound",
        email_address="john@example.com",
        phone_number="555-1234",
        customer_name="John Smith",
        intent="service_request",
        sentiment="neutral"
    )
    
    conv2_id = manager.store_conversation(
        text="The faucet repair went great! Thank you so much for the quick service.",
        customer_id="customer_123",
        channel="sms",
        direction="inbound",
        phone_number="555-1234",
        intent="feedback",
        sentiment="positive"
    )
    
    # Search for similar conversations
    similar = manager.search_similar("faucet repair service", n_results=5)
    print(f"Found {len(similar)} similar conversations")
    
    # Get customer conversation history
    history = manager.get_customer_conversations("customer_123")
    print(f"Customer has {len(history)} conversations")
    
    # Get collection statistics
    stats = manager.get_collection_stats()
    print(f"Collection stats: {stats}")