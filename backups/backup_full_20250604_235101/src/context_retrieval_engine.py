"""
Context Retrieval Engine for Karen AI
Smart context retrieval and summarization for LLM prompts

Provides intelligent context for any customer interaction by:
- Retrieving relevant conversation history across all channels
- Scoring relevance based on recency, similarity, and importance
- Summarizing context for optimal LLM prompt construction
- Cross-channel conversation linking and threading
- Real-time context adaptation based on current conversation
"""

import re
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import numpy as np
from collections import defaultdict
import logging

from memory_embeddings_manager import MemoryEmbeddingsManager
from customer_profile_builder import CustomerProfileBuilder, CustomerProfile

logger = logging.getLogger(__name__)

@dataclass
class ContextItem:
    """Individual context item with relevance scoring"""
    conversation_id: str
    text: str
    channel: str
    timestamp: datetime
    direction: str
    
    # Relevance scores
    similarity_score: float = 0.0
    recency_score: float = 0.0
    importance_score: float = 0.0
    channel_relevance: float = 0.0
    
    # Computed final score
    final_score: float = 0.0
    
    # Metadata
    intent: str = None
    sentiment: str = None
    urgency: str = None
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []

@dataclass 
class ConversationThread:
    """Linked conversation thread across channels"""
    thread_id: str
    customer_id: str
    main_topic: str
    channels: List[str]
    start_time: datetime
    last_activity: datetime
    conversation_ids: List[str]
    status: str = "active"  # active, resolved, escalated
    
@dataclass
class ContextSummary:
    """Summarized context for LLM prompts"""
    customer_profile: CustomerProfile
    relevant_history: List[ContextItem]
    conversation_threads: List[ConversationThread]
    
    # Context insights
    current_topic: str = None
    customer_mood: str = "neutral"
    urgency_level: str = "normal"
    suggested_tone: str = "professional"
    
    # Formatted summaries
    short_summary: str = ""
    detailed_summary: str = ""
    llm_context: str = ""

class RelevanceScorer:
    """Calculates relevance scores for context items"""
    
    def __init__(self):
        self.weights = {
            'similarity': 0.4,
            'recency': 0.3,
            'importance': 0.2,
            'channel_relevance': 0.1
        }
    
    def score_similarity(self, query_text: str, context_text: str, embedding_similarity: float) -> float:
        """
        Score semantic similarity between query and context
        
        Args:
            query_text: Current query/conversation text
            context_text: Historical conversation text
            embedding_similarity: Cosine similarity from embeddings
            
        Returns:
            Similarity score (0-1)
        """
        # Base score from embeddings
        base_score = max(0, embedding_similarity)
        
        # Boost for keyword overlap
        query_words = set(re.findall(r'\b\w+\b', query_text.lower()))
        context_words = set(re.findall(r'\b\w+\b', context_text.lower()))
        
        if query_words and context_words:
            keyword_overlap = len(query_words & context_words) / len(query_words | context_words)
            base_score = min(1.0, base_score + keyword_overlap * 0.2)
        
        return base_score
    
    def score_recency(self, timestamp: datetime, decay_days: int = 30) -> float:
        """
        Score based on how recent the conversation is
        
        Args:
            timestamp: Conversation timestamp
            decay_days: Days for score to decay to 0.1
            
        Returns:
            Recency score (0-1)
        """
        now = datetime.now(timezone.utc)
        age_days = (now - timestamp).total_seconds() / 86400
        
        # Exponential decay
        if age_days <= 0:
            return 1.0
        elif age_days >= decay_days:
            return 0.1
        else:
            # Decay from 1.0 to 0.1 over decay_days
            decay_factor = np.exp(-age_days / (decay_days / 3))
            return max(0.1, decay_factor)
    
    def score_importance(self, metadata: Dict[str, Any]) -> float:
        """
        Score based on conversation importance indicators
        
        Args:
            metadata: Conversation metadata
            
        Returns:
            Importance score (0-1)
        """
        score = 0.5  # Base importance
        
        # Intent-based importance
        intent = metadata.get('intent', '').lower()
        if intent in ['complaint', 'escalation', 'emergency']:
            score += 0.4
        elif intent in ['service_request', 'appointment']:
            score += 0.3
        elif intent in ['feedback', 'question']:
            score += 0.1
        
        # Urgency-based importance
        urgency = metadata.get('urgency', 'normal').lower()
        if urgency == 'critical':
            score += 0.3
        elif urgency == 'high':
            score += 0.2
        elif urgency == 'low':
            score -= 0.1
        
        # Sentiment-based importance
        sentiment = metadata.get('sentiment', 'neutral').lower()
        if sentiment == 'negative':
            score += 0.2  # Negative feedback is important
        elif sentiment == 'positive':
            score += 0.1  # Positive feedback matters too
        
        # Direction-based importance
        if metadata.get('direction') == 'outbound':
            score += 0.1  # Our responses are important for context
        
        return min(1.0, max(0.0, score))
    
    def score_channel_relevance(self, current_channel: str, context_channel: str) -> float:
        """
        Score based on channel relevance to current conversation
        
        Args:
            current_channel: Channel of current conversation
            context_channel: Channel of historical conversation
            
        Returns:
            Channel relevance score (0-1)
        """
        if current_channel == context_channel:
            return 1.0
        
        # Channel similarity mapping
        channel_groups = {
            'text': ['sms', 'chat', 'whatsapp'],
            'voice': ['phone', 'voicemail', 'call'],
            'email': ['email'],
            'in_person': ['visit', 'appointment']
        }
        
        current_group = None
        context_group = None
        
        for group, channels in channel_groups.items():
            if current_channel.lower() in channels:
                current_group = group
            if context_channel.lower() in channels:
                context_group = group
        
        if current_group == context_group:
            return 0.8  # Same type of channel
        elif current_group and context_group:
            return 0.3  # Different channel types
        else:
            return 0.5  # Unknown channels
    
    def calculate_final_score(self, context_item: ContextItem) -> float:
        """Calculate weighted final relevance score"""
        final_score = (
            context_item.similarity_score * self.weights['similarity'] +
            context_item.recency_score * self.weights['recency'] +
            context_item.importance_score * self.weights['importance'] +
            context_item.channel_relevance * self.weights['channel_relevance']
        )
        
        context_item.final_score = final_score
        return final_score

class ConversationThreader:
    """Links related conversations across channels into threads"""
    
    def __init__(self):
        self.topic_keywords = {
            'plumbing': ['faucet', 'sink', 'pipe', 'leak', 'drain', 'toilet', 'water'],
            'electrical': ['outlet', 'light', 'switch', 'wire', 'electrical', 'power'],
            'appointment': ['schedule', 'appointment', 'time', 'date', 'available'],
            'payment': ['bill', 'payment', 'cost', 'price', 'invoice', 'charge'],
            'complaint': ['problem', 'issue', 'unsatisfied', 'wrong', 'bad', 'terrible']
        }
    
    def identify_threads(self, conversations: List[Dict[str, Any]]) -> List[ConversationThread]:
        """
        Identify conversation threads from historical conversations
        
        Args:
            conversations: List of conversations with metadata
            
        Returns:
            List of identified conversation threads
        """
        threads = []
        processed_convs = set()
        
        # Sort conversations by timestamp
        sorted_convs = sorted(
            conversations,
            key=lambda x: x['metadata'].get('timestamp', ''),
            reverse=True
        )
        
        for conv in sorted_convs:
            if conv['id'] in processed_convs:
                continue
            
            # Start a new thread
            thread = self._create_thread_from_conversation(conv, sorted_convs, processed_convs)
            if thread:
                threads.append(thread)
        
        return threads
    
    def _create_thread_from_conversation(
        self,
        seed_conv: Dict[str, Any],
        all_conversations: List[Dict[str, Any]],
        processed_convs: set
    ) -> Optional[ConversationThread]:
        """Create a conversation thread starting from a seed conversation"""
        
        thread_convs = [seed_conv]
        processed_convs.add(seed_conv['id'])
        
        # Identify main topic
        main_topic = self._identify_topic(seed_conv['text'])
        
        # Find related conversations
        seed_timestamp = datetime.fromisoformat(
            seed_conv['metadata']['timestamp'].replace('Z', '+00:00')
        )
        
        # Look for conversations within 7 days that share topic/intent
        for conv in all_conversations:
            if conv['id'] in processed_convs:
                continue
            
            conv_timestamp = datetime.fromisoformat(
                conv['metadata']['timestamp'].replace('Z', '+00:00')
            )
            
            # Time window check (within 7 days)
            time_diff = abs((seed_timestamp - conv_timestamp).total_seconds() / 86400)
            if time_diff > 7:
                continue
            
            # Topic similarity check
            conv_topic = self._identify_topic(conv['text'])
            if conv_topic == main_topic and main_topic != 'general':
                thread_convs.append(conv)
                processed_convs.add(conv['id'])
                continue
            
            # Intent similarity check
            if (seed_conv['metadata'].get('intent') == conv['metadata'].get('intent') and
                seed_conv['metadata'].get('intent') in ['service_request', 'complaint', 'appointment']):
                thread_convs.append(conv)
                processed_convs.add(conv['id'])
        
        # Only create thread if we have multiple conversations or important single conversation
        if len(thread_convs) > 1 or seed_conv['metadata'].get('intent') in ['service_request', 'complaint']:
            
            # Sort by timestamp
            thread_convs.sort(key=lambda x: x['metadata'].get('timestamp', ''))
            
            # Determine thread status
            status = self._determine_thread_status(thread_convs)
            
            thread = ConversationThread(
                thread_id=f"thread_{seed_conv['id'][:8]}",
                customer_id=seed_conv['metadata']['customer_id'],
                main_topic=main_topic,
                channels=list(set(conv['metadata'].get('channel', 'unknown') for conv in thread_convs)),
                start_time=datetime.fromisoformat(thread_convs[0]['metadata']['timestamp'].replace('Z', '+00:00')),
                last_activity=datetime.fromisoformat(thread_convs[-1]['metadata']['timestamp'].replace('Z', '+00:00')),
                conversation_ids=[conv['id'] for conv in thread_convs],
                status=status
            )
            
            return thread
        
        return None
    
    def _identify_topic(self, text: str) -> str:
        """Identify the main topic of a conversation"""
        text_lower = text.lower()
        
        for topic, keywords in self.topic_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return topic
        
        return 'general'
    
    def _determine_thread_status(self, conversations: List[Dict[str, Any]]) -> str:
        """Determine the status of a conversation thread"""
        
        # Check latest conversations for resolution indicators
        recent_convs = conversations[-3:]  # Last 3 conversations
        
        for conv in recent_convs:
            text = conv['text'].lower()
            sentiment = conv['metadata'].get('sentiment', 'neutral')
            
            # Resolution indicators
            if any(keyword in text for keyword in ['completed', 'fixed', 'resolved', 'done', 'thank you']):
                if sentiment == 'positive':
                    return 'resolved'
            
            # Escalation indicators
            if any(keyword in text for keyword in ['manager', 'supervisor', 'escalate', 'unacceptable']):
                return 'escalated'
        
        # Check if thread is recent (within 3 days)
        last_activity = datetime.fromisoformat(conversations[-1]['metadata']['timestamp'].replace('Z', '+00:00'))
        if (datetime.now(timezone.utc) - last_activity).days <= 3:
            return 'active'
        
        return 'inactive'

class ContextRetrievalEngine:
    """Main engine for smart context retrieval and summarization"""
    
    def __init__(self, memory_manager: MemoryEmbeddingsManager, profile_builder: CustomerProfileBuilder):
        self.memory_manager = memory_manager
        self.profile_builder = profile_builder
        self.relevance_scorer = RelevanceScorer()
        self.threader = ConversationThreader()
    
    def get_context_for_interaction(
        self,
        customer_id: str,
        current_text: str,
        current_channel: str,
        max_context_items: int = 10,
        context_window_days: int = 90
    ) -> ContextSummary:
        """
        Get comprehensive context for a customer interaction
        
        Args:
            customer_id: Customer identifier
            current_text: Current conversation text
            current_channel: Current communication channel
            max_context_items: Maximum context items to include
            context_window_days: Days to look back for context
            
        Returns:
            Complete context summary for LLM processing
        """
        try:
            logger.info(f"Retrieving context for customer {customer_id} on {current_channel}")
            
            # Get customer profile
            profile = self.profile_builder.build_profile(customer_id)
            
            # Get relevant conversation history
            start_date = datetime.now(timezone.utc) - timedelta(days=context_window_days)
            conversations = self.memory_manager.get_customer_conversations(
                customer_id=customer_id,
                limit=100,
                start_date=start_date
            )
            
            # Get semantically similar conversations
            similar_convs = self.memory_manager.search_similar(
                query_text=current_text,
                customer_id=customer_id,
                n_results=20,
                min_relevance=0.3
            )
            
            # Combine and deduplicate conversations
            all_relevant_convs = self._combine_conversations(conversations, similar_convs)
            
            # Score and rank context items
            context_items = self._score_context_items(
                all_relevant_convs,
                current_text,
                current_channel
            )
            
            # Select top context items
            top_context = sorted(context_items, key=lambda x: x.final_score, reverse=True)[:max_context_items]
            
            # Identify conversation threads
            threads = self.threader.identify_threads(all_relevant_convs)
            
            # Analyze current conversation context
            current_analysis = self._analyze_current_context(current_text, profile, top_context)
            
            # Build context summary
            summary = ContextSummary(
                customer_profile=profile,
                relevant_history=top_context,
                conversation_threads=threads,
                current_topic=current_analysis['topic'],
                customer_mood=current_analysis['mood'],
                urgency_level=current_analysis['urgency'],
                suggested_tone=current_analysis['suggested_tone']
            )
            
            # Generate formatted summaries
            self._generate_summaries(summary)
            
            logger.info(f"✅ Context retrieved: {len(top_context)} items, {len(threads)} threads")
            return summary
            
        except Exception as e:
            logger.error(f"❌ Failed to retrieve context: {e}")
            # Return minimal context on error
            return ContextSummary(
                customer_profile=CustomerProfile(customer_id=customer_id),
                relevant_history=[],
                conversation_threads=[]
            )
    
    def _combine_conversations(
        self,
        chronological_convs: List[Dict[str, Any]],
        similar_convs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Combine and deduplicate chronological and similar conversations"""
        
        seen_ids = set()
        combined = []
        
        # Add chronological conversations first (recent context is important)
        for conv in chronological_convs:
            if conv['id'] not in seen_ids:
                combined.append(conv)
                seen_ids.add(conv['id'])
        
        # Add similar conversations that weren't already included
        for conv in similar_convs:
            if conv['id'] not in seen_ids:
                combined.append(conv)
                seen_ids.add(conv['id'])
        
        return combined
    
    def _score_context_items(
        self,
        conversations: List[Dict[str, Any]],
        current_text: str,
        current_channel: str
    ) -> List[ContextItem]:
        """Score and convert conversations to context items"""
        
        context_items = []
        
        for conv in conversations:
            metadata = conv['metadata']
            
            # Create context item
            item = ContextItem(
                conversation_id=conv['id'],
                text=conv['text'],
                channel=metadata.get('channel', 'unknown'),
                timestamp=datetime.fromisoformat(metadata['timestamp'].replace('Z', '+00:00')),
                direction=metadata.get('direction', 'inbound'),
                intent=metadata.get('intent'),
                sentiment=metadata.get('sentiment'),
                urgency=metadata.get('urgency'),
                tags=metadata.get('tags', [])
            )
            
            # Calculate relevance scores
            item.similarity_score = self.relevance_scorer.score_similarity(
                current_text,
                conv['text'],
                conv.get('relevance_score', 0.5)  # From semantic search
            )
            
            item.recency_score = self.relevance_scorer.score_recency(item.timestamp)
            
            item.importance_score = self.relevance_scorer.score_importance(metadata)
            
            item.channel_relevance = self.relevance_scorer.score_channel_relevance(
                current_channel,
                item.channel
            )
            
            # Calculate final score
            self.relevance_scorer.calculate_final_score(item)
            
            context_items.append(item)
        
        return context_items
    
    def _analyze_current_context(
        self,
        current_text: str,
        profile: CustomerProfile,
        context_items: List[ContextItem]
    ) -> Dict[str, str]:
        """Analyze current conversation context for insights"""
        
        analysis = {
            'topic': 'general',
            'mood': 'neutral',
            'urgency': 'normal',
            'suggested_tone': 'professional'
        }
        
        text_lower = current_text.lower()
        
        # Topic identification
        topic_keywords = {
            'plumbing': ['faucet', 'sink', 'pipe', 'leak', 'drain', 'toilet', 'water'],
            'electrical': ['outlet', 'light', 'switch', 'wire', 'electrical', 'power'],
            'appointment': ['schedule', 'appointment', 'time', 'date', 'available'],
            'payment': ['bill', 'payment', 'cost', 'price', 'invoice', 'charge'],
            'complaint': ['problem', 'issue', 'unsatisfied', 'wrong', 'bad', 'terrible']
        }
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                analysis['topic'] = topic
                break
        
        # Mood analysis
        positive_indicators = ['thank', 'great', 'excellent', 'happy', 'satisfied']
        negative_indicators = ['problem', 'issue', 'bad', 'terrible', 'angry', 'frustrated']
        
        if any(word in text_lower for word in negative_indicators):
            analysis['mood'] = 'negative'
        elif any(word in text_lower for word in positive_indicators):
            analysis['mood'] = 'positive'
        
        # Urgency analysis
        urgent_indicators = ['urgent', 'emergency', 'asap', 'immediately', 'critical']
        if any(word in text_lower for word in urgent_indicators):
            analysis['urgency'] = 'high'
        
        # Tone suggestion based on profile and context
        if profile.contact_preferences.communication_style == 'casual':
            analysis['suggested_tone'] = 'friendly'
        elif analysis['mood'] == 'negative':
            analysis['suggested_tone'] = 'empathetic'
        elif analysis['urgency'] == 'high':
            analysis['suggested_tone'] = 'responsive'
        
        return analysis
    
    def _generate_summaries(self, context: ContextSummary):
        """Generate formatted context summaries for different use cases"""
        
        profile = context.customer_profile
        history = context.relevant_history
        threads = context.conversation_threads
        
        # Short summary (one sentence)
        if profile.primary_name:
            name_part = f"{profile.primary_name}"
        else:
            name_part = f"Customer {profile.customer_id[:8]}"
        
        history_count = len(history)
        if history_count > 0:
            last_interaction = history[0].timestamp.strftime("%b %d")
            context.short_summary = f"{name_part} - {history_count} previous interactions, last on {last_interaction}"
        else:
            context.short_summary = f"{name_part} - New customer, no previous interactions"
        
        # Detailed summary
        details = []
        
        # Customer info
        details.append(f"Customer: {name_part}")
        if profile.contact_preferences.preferred_channel:
            details.append(f"Preferred contact: {profile.contact_preferences.preferred_channel}")
        
        # Service history
        if profile.service_history.total_requests > 0:
            details.append(f"Service history: {profile.service_history.total_requests} requests")
            if profile.service_history.satisfaction_scores:
                avg_satisfaction = np.mean(profile.service_history.satisfaction_scores)
                details.append(f"Satisfaction: {avg_satisfaction:.1f}/1.0")
        
        # Recent context
        if history:
            recent_channels = set(item.channel for item in history[:3])
            details.append(f"Recent channels: {', '.join(recent_channels)}")
            
            if any(item.sentiment == 'negative' for item in history[:3]):
                details.append("⚠️ Recent negative feedback")
        
        context.detailed_summary = " | ".join(details)
        
        # LLM context (formatted for prompt injection)
        llm_parts = []
        
        # Customer profile context
        llm_parts.append(f"CUSTOMER PROFILE:")
        llm_parts.append(f"- Name: {profile.primary_name or 'Unknown'}")
        llm_parts.append(f"- Communication style: {profile.contact_preferences.communication_style}")
        llm_parts.append(f"- Current mood: {context.customer_mood}")
        llm_parts.append(f"- Suggested tone: {context.suggested_tone}")
        
        # Active threads context
        active_threads = [t for t in threads if t.status == 'active']
        if active_threads:
            llm_parts.append(f"\nACTIVE CONVERSATIONS:")
            for thread in active_threads:
                llm_parts.append(f"- {thread.main_topic} ({', '.join(thread.channels)})")
        
        # Recent relevant history
        if history:
            llm_parts.append(f"\nRECENT RELEVANT HISTORY:")
            for item in history[:5]:  # Top 5 most relevant
                date_str = item.timestamp.strftime("%b %d")
                llm_parts.append(f"- [{date_str}, {item.channel}] {item.text[:100]}...")
        
        context.llm_context = "\n".join(llm_parts)

# Convenience function
def get_context_engine(
    memory_manager: MemoryEmbeddingsManager = None,
    profile_builder: CustomerProfileBuilder = None
) -> ContextRetrievalEngine:
    """Get initialized context retrieval engine"""
    
    if memory_manager is None:
        from memory_embeddings_manager import get_memory_manager
        memory_manager = get_memory_manager()
    
    if profile_builder is None:
        from customer_profile_builder import get_profile_builder
        profile_builder = get_profile_builder(memory_manager)
    
    return ContextRetrievalEngine(memory_manager, profile_builder)

if __name__ == "__main__":
    # Example usage and testing
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize components
    from memory_embeddings_manager import get_memory_manager
    from customer_profile_builder import get_profile_builder
    
    memory_manager = get_memory_manager()
    profile_builder = get_profile_builder(memory_manager)
    context_engine = ContextRetrievalEngine(memory_manager, profile_builder)
    
    # Example: Get context for a customer inquiry
    context = context_engine.get_context_for_interaction(
        customer_id="customer_123",
        current_text="Hi, my kitchen faucet is still leaking after the repair last week",
        current_channel="email"
    )
    
    print("Context Summary:")
    print(f"Short: {context.short_summary}")
    print(f"Detailed: {context.detailed_summary}")
    print(f"\nLLM Context:\n{context.llm_context}")
    print(f"\nRelevant history: {len(context.relevant_history)} items")
    print(f"Conversation threads: {len(context.conversation_threads)}")