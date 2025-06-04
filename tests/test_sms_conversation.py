"""
Comprehensive tests for SMS conversation threading system
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from src.sms_conversation_manager import (
    ConversationManager, ConversationThread, ConversationMessage, 
    ConversationState, MessageType, get_conversation_manager
)
from src.sms_templates import SMSTemplateSystem, get_template_system

class TestConversationMessage:
    """Test ConversationMessage dataclass"""
    
    def test_message_creation(self):
        """Test creating a conversation message"""
        message = ConversationMessage(
            message_id="msg_123",
            phone_number="+17575551234",
            content="Hello, I need help",
            direction="inbound",
            timestamp=datetime.now(),
            message_type=MessageType.GREETING,
            metadata={"source": "twilio"}
        )
        
        assert message.message_id == "msg_123"
        assert message.phone_number == "+17575551234"
        assert message.direction == "inbound"
        assert message.message_type == MessageType.GREETING
    
    def test_message_to_dict(self):
        """Test converting message to dictionary"""
        now = datetime.now()
        message = ConversationMessage(
            message_id="msg_123",
            phone_number="+17575551234",
            content="Hello",
            direction="inbound",
            timestamp=now,
            message_type=MessageType.GREETING,
            metadata={}
        )
        
        data = message.to_dict()
        assert data["message_id"] == "msg_123"
        assert data["timestamp"] == now.isoformat()
        assert data["message_type"] == "greeting"

class TestConversationThread:
    """Test ConversationThread dataclass"""
    
    def test_thread_creation(self):
        """Test creating a conversation thread"""
        now = datetime.now()
        thread = ConversationThread(
            conversation_id="conv_123",
            phone_number="+17575551234",
            state=ConversationState.INITIAL_CONTACT,
            created_at=now,
            last_activity=now,
            messages=[],
            context={},
            customer_info={}
        )
        
        assert thread.conversation_id == "conv_123"
        assert thread.state == ConversationState.INITIAL_CONTACT
        assert len(thread.messages) == 0
    
    def test_thread_to_dict(self):
        """Test converting thread to dictionary"""
        now = datetime.now()
        thread = ConversationThread(
            conversation_id="conv_123",
            phone_number="+17575551234",
            state=ConversationState.INITIAL_CONTACT,
            created_at=now,
            last_activity=now,
            messages=[],
            context={"intent": "greeting"},
            customer_info={"name": "John"}
        )
        
        data = thread.to_dict()
        assert data["conversation_id"] == "conv_123"
        assert data["state"] == "initial"
        assert data["context"]["intent"] == "greeting"

class TestConversationManager:
    """Test ConversationManager functionality"""
    
    def setup_method(self):
        """Setup for each test"""
        # Use memory storage for tests
        with patch('redis.Redis') as mock_redis:
            mock_redis.side_effect = Exception("Redis not available")
            self.manager = ConversationManager()
        
        self.test_phone = "+17575551234"
    
    def test_manager_initialization(self):
        """Test manager initialization"""
        assert self.manager is not None
        assert not self.manager.redis_available
        assert hasattr(self.manager, '_memory_storage')
    
    def test_start_new_conversation(self):
        """Test starting a new conversation"""
        initial_message = "Hi, I need a plumber"
        
        conversation = self.manager.start_conversation(
            self.test_phone, 
            initial_message,
            customer_info={"name": "John Smith"}
        )
        
        assert conversation is not None
        assert conversation.phone_number == self.test_phone
        assert conversation.state == ConversationState.GATHERING_INFO  # Should transition from initial
        assert len(conversation.messages) == 1
        assert conversation.messages[0].content == initial_message
        assert conversation.customer_info["name"] == "John Smith"
    
    def test_add_message_to_existing_conversation(self):
        """Test adding message to existing conversation"""
        # Start conversation
        conversation = self.manager.start_conversation(self.test_phone, "Hi there")
        
        # Add inbound message
        updated_conv = self.manager.add_message(
            self.test_phone,
            "I need my sink fixed",
            "inbound"
        )
        
        assert len(updated_conv.messages) == 2
        assert updated_conv.messages[-1].content == "I need my sink fixed"
        assert updated_conv.state == ConversationState.GATHERING_INFO
    
    def test_add_outbound_message(self):
        """Test adding outbound message"""
        # Start conversation
        self.manager.start_conversation(self.test_phone, "Hi")
        
        # Add outbound response
        conversation = self.manager.add_message(
            self.test_phone,
            "I'd be happy to help! What type of plumbing issue?",
            "outbound"
        )
        
        assert len(conversation.messages) == 2
        assert conversation.messages[-1].direction == "outbound"
    
    def test_get_conversation_context(self):
        """Test getting conversation context"""
        # Start conversation with multiple messages
        self.manager.start_conversation(self.test_phone, "I need plumbing help")
        self.manager.add_message(self.test_phone, "My sink is leaking", "inbound")
        self.manager.add_message(self.test_phone, "I can help with that!", "outbound")
        
        context = self.manager.get_context(self.test_phone)
        
        assert context["has_conversation"] is True
        assert context["message_count"] == 3
        assert len(context["recent_messages"]) == 3
        assert "sink is leaking" in context["conversation_summary"]
    
    def test_context_for_nonexistent_conversation(self):
        """Test getting context for phone number with no conversation"""
        context = self.manager.get_context("+15551234567")
        
        assert context["has_conversation"] is False
        assert context["message_count"] == 0
        assert len(context["recent_messages"]) == 0
    
    def test_close_conversation(self):
        """Test closing a conversation"""
        # Start conversation
        self.manager.start_conversation(self.test_phone, "Hi")
        
        # Close it
        success = self.manager.close_conversation(self.test_phone, "customer_satisfied")
        
        assert success is True
        
        # Should not be able to get it anymore
        conversation = self.manager.get_active_conversation(self.test_phone)
        assert conversation is None
    
    def test_conversation_expiration(self):
        """Test conversation expiration logic"""
        # Start conversation
        conversation = self.manager.start_conversation(self.test_phone, "Hi")
        
        # Manually set old timestamp
        old_time = datetime.now() - timedelta(hours=25)
        conversation.last_activity = old_time
        self.manager._save_conversation(conversation)
        
        # Try to add message - should start new conversation
        new_conversation = self.manager.add_message(self.test_phone, "New message", "inbound")
        
        assert new_conversation.conversation_id != conversation.conversation_id
        assert len(new_conversation.messages) == 1  # Only the new message
    
    def test_state_transitions(self):
        """Test conversation state transitions"""
        # Start with appointment request
        conversation = self.manager.start_conversation(
            self.test_phone, 
            "I need to schedule an appointment"
        )
        
        # Should transition to scheduling
        assert conversation.state == ConversationState.SCHEDULING
        
        # Add confirmation
        updated_conv = self.manager.add_message(
            self.test_phone,
            "Yes, that time works",
            "inbound"
        )
        
        # Should transition to confirming
        assert updated_conv.state == ConversationState.CONFIRMING
    
    def test_emergency_handling(self):
        """Test emergency message handling"""
        conversation = self.manager.start_conversation(
            self.test_phone,
            "EMERGENCY! My basement is flooding!"
        )
        
        # Should immediately require human intervention
        assert conversation.context["requires_human"] is True
        assert conversation.state == ConversationState.COMPLETE
    
    def test_message_type_classification(self):
        """Test message type classification"""
        test_cases = [
            ("Hello there", MessageType.GREETING),
            ("I need an appointment", MessageType.APPOINTMENT_REQUEST),
            ("How much will this cost?", MessageType.QUOTE_REQUEST),
            ("Yes, that sounds good", MessageType.CONFIRMATION),
            ("EMERGENCY! Help!", MessageType.EMERGENCY),
            ("What time are you open?", MessageType.QUESTION)
        ]
        
        for message, expected_type in test_cases:
            classified_type = self.manager._classify_message_type(message)
            assert classified_type == expected_type, f"Failed for: {message}"
    
    def test_context_extraction(self):
        """Test context extraction from messages"""
        conversation = self.manager.start_conversation(
            self.test_phone,
            "I need plumbing repair in the morning"
        )
        
        # Should extract service type and preferred time
        assert conversation.context.get("service_type") == "plumbing"
        assert conversation.context.get("preferred_time") == "morning"
    
    def test_conversation_summary_generation(self):
        """Test conversation summary generation"""
        # Create conversation with multiple messages
        self.manager.start_conversation(self.test_phone, "Hi, I need help")
        self.manager.add_message(self.test_phone, "My faucet is dripping", "inbound")
        self.manager.add_message(self.test_phone, "I can help with that!", "outbound")
        
        conversation = self.manager.get_active_conversation(self.test_phone)
        summary = self.manager._generate_conversation_summary(conversation)
        
        assert "Messages exchanged: 3" in summary
        assert "faucet is dripping" in summary
        assert "Customer:" in summary
        assert "Karen:" in summary
    
    def test_cleanup_expired_conversations(self):
        """Test cleanup of expired conversations"""
        # Create conversation
        self.manager.start_conversation(self.test_phone, "Hi")
        
        # Manually expire it
        conversation = self.manager.get_active_conversation(self.test_phone)
        old_time = datetime.now() - timedelta(hours=25)
        conversation.last_activity = old_time
        self.manager._save_conversation(conversation)
        
        # Run cleanup
        cleaned = self.manager.cleanup_expired_conversations()
        
        assert cleaned == 1
        assert self.manager.get_active_conversation(self.test_phone) is None
    
    def test_conversation_stats(self):
        """Test conversation statistics"""
        # Create multiple conversations
        self.manager.start_conversation("+15551111111", "Hi")
        self.manager.start_conversation("+15552222222", "Hello")
        
        stats = self.manager.get_conversation_stats()
        
        assert stats["active_conversations"] == 2
        assert stats["storage_type"] == "memory"
        assert "states" in stats

class TestSMSTemplateSystem:
    """Test SMS template system"""
    
    def setup_method(self):
        """Setup for each test"""
        self.template_system = SMSTemplateSystem()
    
    def test_template_loading(self):
        """Test template loading"""
        assert len(self.template_system.templates) > 0
        assert "welcome_new_customer" in self.template_system.templates
        assert "appointment_confirmation" in self.template_system.templates
    
    def test_template_filling(self):
        """Test filling templates with variables"""
        result = self.template_system.fill_template(
            "welcome_new_customer",
            {"customer_name": "John Smith"}
        )
        
        assert "John Smith" in result
        assert "757 Handy" in result
        assert "Karen" in result
    
    def test_template_filling_with_missing_variables(self):
        """Test template filling with missing variables"""
        # Should use fallback
        result = self.template_system.fill_template(
            "appointment_confirmation",
            {},  # No variables provided
            use_fallback=True
        )
        
        assert "confirmed" in result.lower()
    
    def test_quick_reply_classification(self):
        """Test quick reply classification"""
        test_cases = [
            ("Y", "yes"),
            ("yes", "yes"),
            ("👍", "yes"),
            ("N", "no"),
            ("cancel", "no"),
            ("reschedule", "reschedule"),
            ("URGENT", "emergency"),
            ("random message", None)
        ]
        
        for message, expected in test_cases:
            result = self.template_system.classify_quick_reply(message)
            assert result == expected, f"Failed for: {message}"
    
    def test_intent_based_template_selection(self):
        """Test selecting templates based on intent"""
        result = self.template_system.get_template_for_intent(
            "greeting",
            {"customer_name": "John"}
        )
        
        assert "John" in result
        assert any(word in result.lower() for word in ["hello", "hi", "welcome"])
    
    def test_template_validation(self):
        """Test template validation"""
        validation = self.template_system.validate_template(
            "appointment_confirmation",
            {
                "customer_name": "John",
                "service_type": "plumbing",
                "date": "March 15",
                "time": "2:00 PM",
                "address": "123 Main St"
            }
        )
        
        assert validation["valid"] is True
        assert len(validation["text"]) > 0
        assert validation["sms_parts"] >= 1
    
    def test_template_validation_missing_vars(self):
        """Test template validation with missing variables"""
        validation = self.template_system.validate_template(
            "appointment_confirmation",
            {"customer_name": "John"}  # Missing other required vars
        )
        
        # Should still be valid due to fallback
        assert len(validation["missing_variables"]) > 0
        assert validation["has_fallback"] is True
    
    def test_template_search(self):
        """Test template search functionality"""
        results = self.template_system.search_templates("appointment")
        
        assert len(results) > 0
        assert any("appointment" in result["name"] for result in results)
        
        # Results should be sorted by relevance
        assert results[0]["relevance_score"] >= results[-1]["relevance_score"]
    
    def test_template_categories(self):
        """Test template category functionality"""
        greeting_templates = self.template_system.get_templates_by_category("greeting")
        assert len(greeting_templates) > 0
        
        categories = self.template_system.list_categories()
        assert "greeting" in categories
        assert "appointment" in categories
    
    def test_template_stats(self):
        """Test template statistics"""
        stats = self.template_system.get_template_stats()
        
        assert stats["total_templates"] > 0
        assert "categories" in stats
        assert stats["average_length"] > 0
    
    def test_add_custom_template(self):
        """Test adding custom template"""
        success = self.template_system.add_template(
            "test_template",
            "general",
            "Hello {name}, this is a test template",
            ["name"],
            "Hello, this is a test template"
        )
        
        assert success is True
        assert "test_template" in self.template_system.templates
        
        # Test using the new template
        result = self.template_system.fill_template(
            "test_template",
            {"name": "World"}
        )
        assert "Hello World" in result

class TestIntegration:
    """Integration tests for conversation manager and templates"""
    
    def setup_method(self):
        """Setup for integration tests"""
        with patch('redis.Redis') as mock_redis:
            mock_redis.side_effect = Exception("Redis not available")
            self.manager = ConversationManager()
        
        self.template_system = SMSTemplateSystem()
        self.test_phone = "+17575551234"
    
    def test_full_conversation_flow(self):
        """Test complete conversation flow with templates"""
        # Start conversation
        conversation = self.manager.start_conversation(
            self.test_phone,
            "Hi, I need to schedule a plumbing appointment"
        )
        
        assert conversation.state == ConversationState.SCHEDULING
        
        # Get appropriate template response
        context = self.manager.get_context(self.test_phone)
        template_response = self.template_system.get_template_for_intent(
            "schedule_appointment",
            {
                "service_type": context["context"].get("service_type", "service"),
                "available_times": "Tomorrow 9AM, 2PM, or Thursday 10AM"
            }
        )
        
        # Add template response
        self.manager.add_message(self.test_phone, template_response, "outbound")
        
        # Customer confirms
        self.manager.add_message(self.test_phone, "Tomorrow at 2PM works great", "inbound")
        
        # Get confirmation template
        confirmation_response = self.template_system.get_template_for_intent(
            "confirm_yes",
            {
                "customer_name": "Valued Customer",
                "next_steps": "I'll send you confirmation details shortly"
            }
        )
        
        # Add confirmation
        final_conversation = self.manager.add_message(
            self.test_phone, 
            confirmation_response, 
            "outbound"
        )
        
        # Verify flow
        assert len(final_conversation.messages) == 4
        assert final_conversation.state == ConversationState.CONFIRMING
        assert "2PM" in final_conversation.messages[-2].content
    
    def test_emergency_flow_with_templates(self):
        """Test emergency handling with appropriate templates"""
        # Emergency message
        conversation = self.manager.start_conversation(
            self.test_phone,
            "EMERGENCY! My basement is flooding!"
        )
        
        # Should require human intervention
        assert conversation.context["requires_human"] is True
        
        # Get emergency template
        emergency_response = self.template_system.fill_template(
            "emergency_response",
            {
                "customer_name": "Valued Customer",
                "address": "your location", 
                "eta": "15-30 minutes"
            }
        )
        
        # Verify emergency template content
        assert "EMERGENCY" in emergency_response
        assert "dispatching" in emergency_response.lower()
        assert "15-30 minutes" in emergency_response
    
    def test_context_driven_template_selection(self):
        """Test selecting templates based on conversation context"""
        # Start conversation about quotes
        self.manager.start_conversation(
            self.test_phone,
            "How much would it cost to fix my kitchen faucet?"
        )
        
        context = self.manager.get_context(self.test_phone)
        
        # Get suggested templates
        suggestions = self.template_system.suggest_templates_for_context(context["context"])
        
        # Should suggest quote-related templates
        template_names = [s["name"] for s in suggestions]
        assert any("quote" in name for name in template_names)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])