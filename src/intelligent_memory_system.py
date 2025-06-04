"""
Intelligent Memory System for Karen AI - Complete Integration
Master controller that orchestrates all memory components

This is the main interface for Karen's intelligent memory system that makes
conversations truly context-aware across all channels.

Components integrated:
- ChromaDB semantic embeddings (memory_embeddings_manager.py)
- Customer profile building (customer_profile_builder.py) 
- Context retrieval engine (context_retrieval_engine.py)
- Memory analytics (memory_analytics.py)
- Cross-channel identity resolution
"""

import os
import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
import logging

from memory_embeddings_manager import MemoryEmbeddingsManager, get_memory_manager
from customer_profile_builder import CustomerProfileBuilder, get_profile_builder, CustomerProfile
from context_retrieval_engine import ContextRetrievalEngine, get_context_engine, ContextSummary
from memory_analytics import MemoryAnalytics, get_memory_analytics

logger = logging.getLogger(__name__)

class IntelligentMemorySystem:
    """
    Master controller for Karen's intelligent memory system
    
    This is the SECRET SAUCE that makes Karen feel truly intelligent!
    """
    
    def __init__(self, persist_directory: str = "karen_memory"):
        """
        Initialize the complete intelligent memory system
        
        Args:
            persist_directory: Directory for ChromaDB persistence
        """
        self.persist_directory = persist_directory
        
        # Initialize core components
        logger.info("🧠 Initializing Intelligent Memory System...")
        
        self.memory_manager = get_memory_manager(persist_directory)
        self.profile_builder = get_profile_builder(self.memory_manager)
        self.context_engine = get_context_engine(self.memory_manager, self.profile_builder)
        self.analytics = get_memory_analytics(self.memory_manager, self.profile_builder)
        
        logger.info("✅ Intelligent Memory System initialized successfully")
    
    async def process_conversation(
        self,
        text: str,
        customer_phone: str = None,
        customer_email: str = None,
        customer_name: str = None,
        channel: str = "email",
        direction: str = "inbound",
        intent: str = None,
        sentiment: str = None,
        urgency: str = "normal"
    ) -> Tuple[str, ContextSummary, CustomerProfile]:
        """
        Process a new conversation with full intelligent memory integration
        
        This is the main entry point that makes Karen intelligent!
        
        Args:
            text: Conversation text content
            customer_phone: Customer phone number
            customer_email: Customer email address
            customer_name: Customer name
            channel: Communication channel (email, sms, phone, chat)
            direction: inbound or outbound
            intent: Classified intent (optional)
            sentiment: Detected sentiment (optional)
            urgency: Message urgency level
            
        Returns:
            (customer_id, context_summary, customer_profile)
        """
        try:
            logger.info(f"🔄 Processing {direction} {channel} conversation")
            
            # Step 1: Resolve customer identity across channels
            customer_id, confidence = self.profile_builder.identity_resolver.resolve_customer_identity(
                phone=customer_phone,
                email=customer_email,
                name=customer_name,
                confidence_threshold=0.7
            )
            
            # Step 2: Create new customer if not found
            if not customer_id:
                customer_id = self._generate_customer_id(customer_phone, customer_email, customer_name)
                logger.info(f"👤 Created new customer: {customer_id}")
            else:
                logger.info(f"👤 Identified existing customer: {customer_id} (confidence: {confidence:.2f})")
            
            # Step 3: Store conversation with semantic embeddings
            conversation_id = self.memory_manager.store_conversation(
                text=text,
                customer_id=customer_id,
                channel=channel,
                direction=direction,
                phone_number=customer_phone,
                email_address=customer_email,
                customer_name=customer_name,
                intent=intent,
                sentiment=sentiment,
                urgency=urgency
            )
            
            # Step 4: Build/update customer profile with automatic learning
            customer_profile = self.profile_builder.build_profile(
                customer_id=customer_id,
                phone=customer_phone,
                email=customer_email,
                name=customer_name
            )
            
            # Step 5: Get intelligent context for this interaction
            context_summary = self.context_engine.get_context_for_interaction(
                customer_id=customer_id,
                current_text=text,
                current_channel=channel,
                max_context_items=10
            )
            
            logger.info(f"✅ Conversation processed: {conversation_id}")
            logger.info(f"📊 Context: {len(context_summary.relevant_history)} items, {len(context_summary.conversation_threads)} threads")
            
            return customer_id, context_summary, customer_profile
            
        except Exception as e:
            logger.error(f"❌ Failed to process conversation: {e}")
            # Return minimal data on error
            fallback_customer_id = self._generate_customer_id(customer_phone, customer_email, customer_name)
            empty_context = ContextSummary(
                customer_profile=CustomerProfile(customer_id=fallback_customer_id),
                relevant_history=[],
                conversation_threads=[]
            )
            minimal_profile = CustomerProfile(customer_id=fallback_customer_id)
            return fallback_customer_id, empty_context, minimal_profile
    
    def get_conversation_context(
        self,
        customer_id: str,
        current_text: str,
        current_channel: str,
        max_context_items: int = 10
    ) -> ContextSummary:
        """
        Get intelligent context for an ongoing conversation
        
        Args:
            customer_id: Customer identifier
            current_text: Current conversation text
            current_channel: Current communication channel
            max_context_items: Maximum context items to return
            
        Returns:
            Complete context summary with relevant history and insights
        """
        return self.context_engine.get_context_for_interaction(
            customer_id=customer_id,
            current_text=current_text,
            current_channel=current_channel,
            max_context_items=max_context_items
        )
    
    def get_customer_profile(self, customer_id: str) -> CustomerProfile:
        """Get complete customer profile with learned preferences"""
        return self.profile_builder.build_profile(customer_id)
    
    def search_similar_conversations(
        self,
        query_text: str,
        customer_id: str = None,
        n_results: int = 10,
        min_relevance: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Search for semantically similar conversations
        
        Args:
            query_text: Text to search for
            customer_id: Optional customer filter
            n_results: Maximum results
            min_relevance: Minimum relevance score
            
        Returns:
            List of similar conversations with relevance scores
        """
        return self.memory_manager.search_similar(
            query_text=query_text,
            customer_id=customer_id,
            n_results=n_results,
            min_relevance=min_relevance
        )
    
    def analyze_customer_insights(self, customer_id: str) -> List[Dict[str, Any]]:
        """Generate behavioral insights for a specific customer"""
        insights = self.analytics.behavior_analyzer.analyze_customer_behavior(customer_id)
        return [
            {
                'type': insight.insight_type,
                'title': insight.title,
                'description': insight.description,
                'confidence': insight.confidence,
                'impact': insight.impact,
                'actionable': insight.actionable,
                'data_points': insight.data_points
            }
            for insight in insights
        ]
    
    def get_business_analytics(self, days_back: int = 30) -> Dict[str, Any]:
        """Generate comprehensive business analytics"""
        return self.analytics.generate_comprehensive_analytics()
    
    def identify_customer(
        self,
        phone: str = None,
        email: str = None,
        name: str = None
    ) -> Tuple[Optional[str], float]:
        """
        Identify customer across channels using multiple signals
        
        Returns:
            (customer_id, confidence_score) or (None, 0.0) if no match
        """
        return self.profile_builder.identity_resolver.resolve_customer_identity(
            phone=phone,
            email=email,
            name=name
        )
    
    def get_customer_conversation_history(
        self,
        customer_id: str,
        limit: int = 50,
        channel: str = None
    ) -> List[Dict[str, Any]]:
        """Get complete conversation history for a customer"""
        return self.memory_manager.get_customer_conversations(
            customer_id=customer_id,
            limit=limit,
            channel=channel
        )
    
    def generate_llm_context_prompt(
        self,
        customer_id: str,
        current_text: str,
        current_channel: str
    ) -> str:
        """
        Generate optimized context prompt for LLM processing
        
        This creates the perfect context for Karen's LLM to respond intelligently!
        
        Args:
            customer_id: Customer identifier
            current_text: Current conversation text
            current_channel: Current channel
            
        Returns:
            Formatted context prompt for LLM injection
        """
        try:
            context = self.get_conversation_context(
                customer_id=customer_id,
                current_text=current_text,
                current_channel=current_channel
            )
            
            # Build comprehensive LLM prompt
            prompt_parts = []
            
            # Customer context
            prompt_parts.append("=== CUSTOMER CONTEXT ===")
            prompt_parts.append(f"Customer: {context.customer_profile.primary_name or customer_id}")
            prompt_parts.append(f"Preferred communication: {context.customer_profile.contact_preferences.communication_style}")
            prompt_parts.append(f"Current mood: {context.customer_mood}")
            prompt_parts.append(f"Urgency level: {context.urgency_level}")
            prompt_parts.append(f"Suggested tone: {context.suggested_tone}")
            
            # Service history
            if context.customer_profile.service_history.total_requests > 0:
                prompt_parts.append(f"Service history: {context.customer_profile.service_history.total_requests} requests")
                if context.customer_profile.service_history.satisfaction_scores:
                    avg_sat = sum(context.customer_profile.service_history.satisfaction_scores) / len(context.customer_profile.service_history.satisfaction_scores)
                    prompt_parts.append(f"Satisfaction level: {avg_sat:.1f}/1.0")
            
            # Active conversation threads
            active_threads = [t for t in context.conversation_threads if t.status == 'active']
            if active_threads:
                prompt_parts.append("\n=== ACTIVE CONVERSATIONS ===")
                for thread in active_threads:
                    prompt_parts.append(f"• {thread.main_topic} (via {', '.join(thread.channels)})")
            
            # Relevant history
            if context.relevant_history:
                prompt_parts.append("\n=== RELEVANT HISTORY ===")
                for item in context.relevant_history[:5]:  # Top 5 most relevant
                    date_str = item.timestamp.strftime("%b %d")
                    preview = item.text[:150] + "..." if len(item.text) > 150 else item.text
                    prompt_parts.append(f"[{date_str}, {item.channel}] {preview}")
            
            # Behavioral insights
            insights = self.analyze_customer_insights(customer_id)
            high_impact_insights = [i for i in insights if i['impact'] in ['high', 'medium'] and i['actionable']]
            
            if high_impact_insights:
                prompt_parts.append("\n=== KEY INSIGHTS ===")
                for insight in high_impact_insights[:3]:  # Top 3 actionable insights
                    prompt_parts.append(f"• {insight['title']}: {insight['description']}")
            
            # Current context analysis
            prompt_parts.append(f"\n=== CURRENT SITUATION ===")
            prompt_parts.append(f"Topic: {context.current_topic}")
            prompt_parts.append(f"Channel: {current_channel}")
            
            if context.conversation_threads:
                recent_thread = context.conversation_threads[0]
                prompt_parts.append(f"Thread status: {recent_thread.status}")
            
            # Instructions for LLM
            prompt_parts.append("\n=== RESPONSE GUIDELINES ===")
            prompt_parts.append(f"• Use {context.suggested_tone} tone")
            prompt_parts.append(f"• Address customer as {context.customer_profile.primary_name or 'valued customer'}")
            prompt_parts.append("• Reference relevant history when appropriate")
            prompt_parts.append("• Be proactive about known issues or preferences")
            
            if context.urgency_level == 'high':
                prompt_parts.append("• URGENT: Prioritize immediate response and resolution")
            
            return "\n".join(prompt_parts)
            
        except Exception as e:
            logger.error(f"Failed to generate LLM context: {e}")
            return f"Customer {customer_id} - Basic conversation context"
    
    def update_conversation_metadata(
        self,
        conversation_id: str,
        intent: str = None,
        sentiment: str = None,
        resolution_status: str = None,
        satisfaction_score: float = None
    ) -> bool:
        """Update conversation metadata after processing"""
        updates = {}
        if intent:
            updates['intent'] = intent
        if sentiment:
            updates['sentiment'] = sentiment
        if resolution_status:
            updates['resolution_status'] = resolution_status
        if satisfaction_score is not None:
            updates['satisfaction_score'] = satisfaction_score
        
        return self.memory_manager.update_conversation_metadata(conversation_id, updates)
    
    def delete_customer_data(self, customer_id: str) -> int:
        """
        Delete all customer data (GDPR compliance)
        
        Returns:
            Number of conversations deleted
        """
        return self.memory_manager.delete_customer_data(customer_id)
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics"""
        memory_stats = self.memory_manager.get_collection_stats()
        
        # Add analytics summary
        analytics_report = self.analytics.generate_comprehensive_analytics()
        
        return {
            'memory_system': memory_stats,
            'business_metrics': analytics_report['summary_metrics'],
            'last_updated': datetime.now(timezone.utc).isoformat()
        }
    
    def _generate_customer_id(self, phone: str = None, email: str = None, name: str = None) -> str:
        """Generate a new customer ID"""
        import uuid
        
        # Create deterministic ID based on available info
        if email:
            base = email.lower()
        elif phone:
            base = ''.join(filter(str.isdigit, phone))
        elif name:
            base = name.lower().replace(' ', '_')
        else:
            base = 'unknown'
        
        # Add unique suffix
        unique_id = str(uuid.uuid4())[:8]
        return f"customer_{base}_{unique_id}".replace('@', '_').replace('.', '_')

# Convenience functions for easy initialization
def get_intelligent_memory_system(persist_directory: str = "karen_memory") -> IntelligentMemorySystem:
    """Get initialized intelligent memory system"""
    return IntelligentMemorySystem(persist_directory)

async def process_karen_conversation(
    text: str,
    customer_phone: str = None,
    customer_email: str = None,
    customer_name: str = None,
    channel: str = "email",
    direction: str = "inbound",
    **kwargs
) -> Dict[str, Any]:
    """
    High-level function to process any Karen conversation with full intelligence
    
    This is what makes Karen feel truly intelligent and context-aware!
    
    Returns:
        Complete response package with customer context and insights
    """
    # Initialize memory system
    memory_system = get_intelligent_memory_system()
    
    # Process the conversation
    customer_id, context, profile = await memory_system.process_conversation(
        text=text,
        customer_phone=customer_phone,
        customer_email=customer_email,
        customer_name=customer_name,
        channel=channel,
        direction=direction,
        **kwargs
    )
    
    # Generate LLM context
    llm_context = memory_system.generate_llm_context_prompt(
        customer_id=customer_id,
        current_text=text,
        current_channel=channel
    )
    
    # Get customer insights
    insights = memory_system.analyze_customer_insights(customer_id)
    
    return {
        'customer_id': customer_id,
        'customer_profile': {
            'name': profile.primary_name,
            'preferred_channel': profile.contact_preferences.preferred_channel,
            'communication_style': profile.contact_preferences.communication_style,
            'total_interactions': len(memory_system.get_customer_conversation_history(customer_id, limit=1000)),
            'satisfaction_score': sum(profile.service_history.satisfaction_scores) / len(profile.service_history.satisfaction_scores) if profile.service_history.satisfaction_scores else 0.5
        },
        'conversation_context': {
            'relevant_history_count': len(context.relevant_history),
            'active_threads': len([t for t in context.conversation_threads if t.status == 'active']),
            'current_mood': context.customer_mood,
            'urgency_level': context.urgency_level,
            'suggested_tone': context.suggested_tone
        },
        'llm_context_prompt': llm_context,
        'customer_insights': insights,
        'action_items': [
            insight for insight in insights 
            if insight['actionable'] and insight['impact'] in ['high', 'medium']
        ]
    }

if __name__ == "__main__":
    # Example usage demonstrating the full intelligent memory system
    import asyncio
    import logging
    
    logging.basicConfig(level=logging.INFO)
    
    async def demo_intelligent_memory():
        """Demonstrate the intelligent memory system capabilities"""
        
        print("🧠 Karen AI Intelligent Memory System Demo")
        print("=" * 50)
        
        # Initialize system
        memory_system = get_intelligent_memory_system()
        
        # Simulate a customer conversation across multiple channels
        
        # 1. First contact via email
        print("\n1. Processing first email contact...")
        result1 = await process_karen_conversation(
            text="Hi, I have a leaky faucet in my kitchen that needs fixing. Can you send someone today?",
            customer_email="john.smith@example.com",
            customer_name="John Smith",
            channel="email",
            direction="inbound",
            intent="service_request",
            sentiment="neutral",
            urgency="normal"
        )
        
        print(f"Customer ID: {result1['customer_id']}")
        print(f"Context items: {result1['conversation_context']['relevant_history_count']}")
        
        # 2. Follow-up via SMS
        print("\n2. Processing SMS follow-up...")
        result2 = await process_karen_conversation(
            text="When will the technician arrive? This is getting worse.",
            customer_phone="555-123-4567",
            customer_name="John Smith",  # Same customer, different channel
            channel="sms",
            direction="inbound",
            intent="inquiry",
            sentiment="negative",
            urgency="high"
        )
        
        print(f"Customer ID: {result2['customer_id']}")
        print(f"Identity linked: {result1['customer_id'] == result2['customer_id']}")
        print(f"Context items: {result2['conversation_context']['relevant_history_count']}")
        print(f"Mood detected: {result2['conversation_context']['current_mood']}")
        
        # 3. Show generated LLM context
        print("\n3. Generated LLM Context:")
        print("-" * 30)
        print(result2['llm_context_prompt'][:500] + "...")
        
        # 4. Show customer insights
        print("\n4. Customer Insights:")
        print("-" * 30)
        for insight in result2['customer_insights']:
            print(f"• {insight['title']}: {insight['description']}")
        
        # 5. System statistics
        print("\n5. System Statistics:")
        print("-" * 30)
        stats = memory_system.get_system_stats()
        print(f"Total conversations: {stats['memory_system'].get('total_conversations', 0)}")
        print(f"Total customers: {stats['memory_system'].get('customer_count', 0)}")
        print(f"Channels: {', '.join(stats['memory_system'].get('channels', []))}")
        
        print("\n✅ Demo completed! Karen's memory system is fully operational.")
    
    # Run the demo
    asyncio.run(demo_intelligent_memory())