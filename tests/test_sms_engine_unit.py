"""
Unit tests for HandymanSMSEngine
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from src.handyman_sms_engine import HandymanSMSEngine


class TestHandymanSMSEngine:
    """Unit tests for HandymanSMSEngine class"""

    @pytest.fixture
    def mock_llm_client(self):
        """Create mock LLM client"""
        mock_client = AsyncMock()
        mock_client.generate_text.return_value = "Thanks for your message! Call 757-354-4577 for assistance."
        return mock_client

    @pytest.fixture
    def sms_engine(self, mock_llm_client):
        """Create SMS engine with mock LLM"""
        return HandymanSMSEngine(
            business_name="Beach Handyman",
            service_area="Virginia Beach area",
            phone="757-354-4577",
            llm_client=mock_llm_client
        )

    @pytest.fixture
    def sms_engine_no_llm(self):
        """Create SMS engine without LLM for fallback testing"""
        return HandymanSMSEngine(
            business_name="Beach Handyman",
            service_area="Virginia Beach area",
            phone="757-354-4577",
            llm_client=None
        )

    def test_initialization(self, sms_engine):
        """Test SMS engine initialization"""
        assert sms_engine.business_name == "Beach Handyman"
        assert sms_engine.service_area == "Virginia Beach area"
        assert sms_engine.phone == "757-354-4577"
        assert sms_engine.sms_char_limit == 160
        assert sms_engine.sms_multipart_limit == 1600

    def test_sms_quick_responses_mapping(self, sms_engine):
        """Test SMS quick response mappings"""
        assert 'yes' in sms_engine.sms_quick_responses
        assert 'no' in sms_engine.sms_quick_responses
        assert 'stop' in sms_engine.sms_quick_responses
        assert 'help' in sms_engine.sms_quick_responses

    def test_sms_abbreviations_mapping(self, sms_engine):
        """Test SMS abbreviations mapping"""
        assert 'asap' in sms_engine.sms_abbreviations
        assert sms_engine.sms_abbreviations['asap'] == 'as soon as possible'
        assert 'appt' in sms_engine.sms_abbreviations
        assert sms_engine.sms_abbreviations['appt'] == 'appointment'


class TestSMSClassification:
    """Test SMS message classification"""

    @pytest.fixture
    def sms_engine(self):
        """Create SMS engine for classification testing"""
        return HandymanSMSEngine()

    def test_emergency_classification(self, sms_engine):
        """Test emergency message classification"""
        emergency_messages = [
            "EMERGENCY! Pipe burst flooding house!",
            "URGENT: Gas leak in kitchen",
            "Help! Electrical fire in basement",
            "Emergency plumbing needed NOW"
        ]
        
        for msg in emergency_messages:
            classification = sms_engine.classify_sms_type("+15551234567", msg)
            assert classification['is_emergency'] is True, f"Failed to classify as emergency: {msg}"

    def test_quote_request_classification(self, sms_engine):
        """Test quote request classification"""
        quote_messages = [
            "Can I get a quote for plumbing repair?",
            "How much to fix my sink?",
            "Quote needed for bathroom renovation",
            "What's the cost for electrical work?"
        ]
        
        for msg in quote_messages:
            classification = sms_engine.classify_sms_type("+15551234567", msg)
            assert classification['is_quote_request'] is True, f"Failed to classify as quote: {msg}"

    def test_appointment_request_classification(self, sms_engine):
        """Test appointment request classification"""
        appointment_messages = [
            "Can you come tomorrow at 2 PM?",
            "Schedule me for next week",
            "Book an appointment for Monday",
            "Available this afternoon?"
        ]
        
        for msg in appointment_messages:
            classification = sms_engine.classify_sms_type("+15551234567", msg)
            assert classification['is_appointment_request'] is True, f"Failed to classify as appointment: {msg}"

    def test_quick_response_classification(self, sms_engine):
        """Test quick response classification"""
        quick_responses = {
            "yes": "appointment confirmed",
            "no": "appointment cancelled", 
            "stop": "unsubscribe",
            "help": "service information"
        }
        
        for msg, expected_type in quick_responses.items():
            classification = sms_engine.classify_sms_type("+15551234567", msg)
            assert classification['is_quick_response'] is True
            assert classification['quick_response_type'] == expected_type

    def test_short_message_classification(self, sms_engine):
        """Test short message classification"""
        short_msg = "ok"
        long_msg = "This is a longer message that contains more than fifty characters for testing purposes"
        
        short_classification = sms_engine.classify_sms_type("+15551234567", short_msg)
        long_classification = sms_engine.classify_sms_type("+15551234567", long_msg)
        
        assert short_classification['is_short_message'] is True
        assert long_classification['is_short_message'] is False

    def test_local_phone_number_detection(self, sms_engine):
        """Test local phone number detection"""
        local_number = "+17575551234"
        non_local_number = "+12125551234"
        
        local_classification = sms_engine.classify_sms_type(local_number, "test message")
        non_local_classification = sms_engine.classify_sms_type(non_local_number, "test message")
        
        assert local_classification['is_local'] is True
        assert non_local_classification['is_local'] is False

    def test_multipart_requirement_detection(self, sms_engine):
        """Test multipart SMS requirement detection"""
        short_msg = "Short message"
        long_msg = "A" * 200  # Longer than single SMS limit
        
        short_classification = sms_engine.classify_sms_type("+15551234567", short_msg)
        long_classification = sms_engine.classify_sms_type("+15551234567", long_msg)
        
        assert short_classification['requires_multipart'] is False
        assert long_classification['requires_multipart'] is True


class TestSMSAbbreviationExpansion:
    """Test SMS abbreviation expansion"""

    @pytest.fixture
    def sms_engine(self):
        return HandymanSMSEngine()

    def test_basic_abbreviation_expansion(self, sms_engine):
        """Test basic abbreviation expansion"""
        test_cases = [
            ("Need help asap", "Need help as soon as possible"),
            ("Can you come tmrw?", "Can you come tomorrow?"),
            ("Book an appt pls", "Book an appointment please"),
            ("Are you avail this wknd?", "Are you available this weekend?")
        ]
        
        for original, expected in test_cases:
            expanded = sms_engine.expand_sms_abbreviations(original)
            assert expanded == expected

    def test_case_insensitive_expansion(self, sms_engine):
        """Test case-insensitive abbreviation expansion"""
        test_cases = [
            ("ASAP help needed", "as soon as possible help needed"),
            ("Appt for Monday", "appointment for Monday"),
            ("Pls call back", "please call back")
        ]
        
        for original, expected in test_cases:
            expanded = sms_engine.expand_sms_abbreviations(original)
            assert expanded == expected

    def test_word_boundary_expansion(self, sms_engine):
        """Test that abbreviations only expand on word boundaries"""
        # Should not expand "asap" within "asaparagus" (hypothetical)
        text = "The asaparagus needs help asap"
        expanded = sms_engine.expand_sms_abbreviations(text)
        assert "asaparagus" in expanded  # Should remain unchanged
        assert "as soon as possible" in expanded  # asap should be expanded

    def test_no_abbreviations(self, sms_engine):
        """Test text with no abbreviations remains unchanged"""
        original = "This is a normal message with no abbreviations."
        expanded = sms_engine.expand_sms_abbreviations(original)
        assert expanded == original


class TestSMSPromptGeneration:
    """Test SMS prompt generation"""

    @pytest.fixture
    def sms_engine(self):
        return HandymanSMSEngine()

    def test_basic_prompt_generation(self, sms_engine):
        """Test basic SMS prompt generation"""
        classification = {
            'is_emergency': False,
            'is_quote_request': True,
            'is_quick_response': False,
            'is_short_message': False
        }
        
        prompt = sms_engine.generate_sms_prompt(
            "+15551234567", 
            "How much for plumbing?", 
            classification
        )
        
        assert "Karen" in prompt
        assert "Beach Handyman" in prompt
        assert "SMS RESPONSE GUIDELINES" in prompt
        assert "under 160 characters" in prompt
        assert "+15551234567" in prompt
        assert "How much for plumbing?" in prompt

    def test_emergency_prompt_generation(self, sms_engine):
        """Test emergency SMS prompt generation"""
        classification = {
            'is_emergency': True,
            'is_quote_request': False,
            'is_quick_response': False,
            'is_short_message': False
        }
        
        prompt = sms_engine.generate_sms_prompt(
            "+15551234567",
            "Emergency pipe burst!",
            classification
        )
        
        assert "SMS EMERGENCY PROTOCOL" in prompt
        assert "Call us NOW" in prompt
        assert "757-354-4577" in prompt

    def test_quick_response_prompt_generation(self, sms_engine):
        """Test quick response prompt generation"""
        classification = {
            'is_emergency': False,
            'is_quote_request': False,
            'is_quick_response': True,
            'quick_response_type': 'appointment confirmed',
            'is_short_message': True
        }
        
        prompt = sms_engine.generate_sms_prompt(
            "+15551234567",
            "yes",
            classification
        )
        
        assert "QUICK RESPONSE: Appointment Confirmation" in prompt
        assert "SHORT MESSAGE RESPONSE" in prompt

    def test_abbreviation_expansion_in_prompt(self, sms_engine):
        """Test that abbreviations are expanded in prompt"""
        classification = {'is_emergency': False, 'is_quote_request': False, 'is_quick_response': False, 'is_short_message': False}
        
        prompt = sms_engine.generate_sms_prompt(
            "+15551234567",
            "Need help asap pls",
            classification
        )
        
        assert "as soon as possible" in prompt
        assert "please" in prompt
        assert "Need help asap pls" in prompt  # Original should also be included


class TestSMSResponseGeneration:
    """Test SMS response generation"""

    @pytest.fixture
    def mock_llm_client(self):
        mock_client = AsyncMock()
        mock_client.generate_text.return_value = "Thank you for your message! For immediate assistance, please call 757-354-4577."
        return mock_client

    @pytest.fixture
    def sms_engine(self, mock_llm_client):
        return HandymanSMSEngine(llm_client=mock_llm_client)

    @pytest.mark.asyncio
    async def test_basic_response_generation(self, sms_engine):
        """Test basic SMS response generation"""
        response, classification = await sms_engine.generate_sms_response_async(
            "+15551234567",
            "Need plumbing help"
        )
        
        assert isinstance(response, str)
        assert len(response) > 0
        assert isinstance(classification, dict)
        assert "757-354-4577" in response

    @pytest.mark.asyncio
    async def test_quick_response_bypass_llm(self, sms_engine):
        """Test that quick responses bypass LLM"""
        response, classification = await sms_engine.generate_sms_response_async(
            "+15551234567",
            "yes"
        )
        
        assert "Appointment confirmed" in response
        assert classification['is_quick_response'] is True
        # LLM should not have been called for quick response
        sms_engine.llm_client.generate_text.assert_not_called()

    @pytest.mark.asyncio
    async def test_response_length_limit(self, sms_engine):
        """Test that responses are limited to SMS constraints"""
        # Mock LLM to return very long response
        sms_engine.llm_client.generate_text.return_value = "Very long response " * 100
        
        response, classification = await sms_engine.generate_sms_response_async(
            "+15551234567",
            "Need help"
        )
        
        # Should be truncated
        assert len(response) <= 1600  # Multipart limit

    @pytest.mark.asyncio
    async def test_fallback_when_llm_fails(self, sms_engine):
        """Test fallback response when LLM fails"""
        sms_engine.llm_client.generate_text.side_effect = Exception("LLM error")
        
        response, classification = await sms_engine.generate_sms_response_async(
            "+15551234567",
            "Need quote for plumbing"
        )
        
        assert isinstance(response, str)
        assert len(response) > 0
        assert "757-354-4577" in response

    @pytest.mark.asyncio
    async def test_no_llm_client_fallback(self, mock_llm_client):
        """Test fallback when no LLM client is provided"""
        engine = HandymanSMSEngine(llm_client=None)
        
        response, classification = await engine.generate_sms_response_async(
            "+15551234567",
            "Emergency plumbing needed!"
        )
        
        assert isinstance(response, str)
        assert len(response) > 0
        assert "757-354-4577" in response


class TestSMSResponseTruncation:
    """Test SMS response truncation"""

    @pytest.fixture
    def sms_engine(self):
        return HandymanSMSEngine()

    def test_short_response_unchanged(self, sms_engine):
        """Test that short responses are unchanged"""
        short_response = "Thanks! Call 757-354-4577"
        truncated = sms_engine._truncate_sms_response(short_response)
        assert truncated == short_response

    def test_long_response_truncation(self, sms_engine):
        """Test truncation of long responses"""
        long_response = "This is a very long response " * 20
        truncated = sms_engine._truncate_sms_response(long_response)
        
        assert len(truncated) <= 160
        assert "757-354-4577" in truncated  # Phone should be preserved

    def test_sentence_boundary_truncation(self, sms_engine):
        """Test truncation at sentence boundaries"""
        response = "First sentence. Second sentence. Third sentence. Fourth sentence."
        truncated = sms_engine._truncate_sms_response(response)
        
        # Should end at a sentence boundary
        assert truncated.endswith('.') or truncated.endswith('!') or truncated.endswith('?') or truncated.endswith('Call 757-354-4577')

    def test_email_signature_removal(self, sms_engine):
        """Test removal of email-style signatures"""
        response_with_signature = "Thanks for your message!\n\nBest regards,\nKaren\nBeach Handyman"
        truncated = sms_engine._truncate_sms_response(response_with_signature)
        
        assert "Best regards" not in truncated
        assert "Beach Handyman" not in truncated or "757-354-4577" in truncated

    def test_phone_preservation(self, sms_engine):
        """Test that phone number is preserved during truncation"""
        long_response = "Very long message " * 50  # Much longer than limit
        truncated = sms_engine._truncate_sms_response(long_response, preserve_phone=True)
        
        assert "757-354-4577" in truncated

    def test_no_phone_preservation(self, sms_engine):
        """Test truncation without phone preservation"""
        long_response = "Very long message " * 50
        truncated = sms_engine._truncate_sms_response(long_response, preserve_phone=False)
        
        assert truncated.endswith("...")


class TestMultipartSMS:
    """Test multipart SMS handling"""

    @pytest.fixture
    def sms_engine(self):
        return HandymanSMSEngine()

    def test_should_send_multipart_detection(self, sms_engine):
        """Test detection of multipart SMS need"""
        short_msg = "Short message"
        long_msg = "A" * 200
        
        assert sms_engine.should_send_multipart_sms(short_msg) is False
        assert sms_engine.should_send_multipart_sms(long_msg) is True

    def test_single_part_message(self, sms_engine):
        """Test that short messages return single part"""
        short_msg = "Thanks for your message!"
        parts = sms_engine.split_sms_response(short_msg)
        
        assert len(parts) == 1
        assert parts[0] == short_msg

    def test_multipart_message_splitting(self, sms_engine):
        """Test splitting of long messages"""
        long_msg = "This is a test message. " * 20  # Multiple sentences
        parts = sms_engine.split_sms_response(long_msg)
        
        assert len(parts) > 1
        for i, part in enumerate(parts):
            assert len(part) <= 160
            assert f"({i+1}/{len(parts)})" in part

    def test_multipart_sentence_boundaries(self, sms_engine):
        """Test that multipart splitting respects sentence boundaries"""
        msg = "First sentence. Second sentence. Third sentence. Fourth sentence. Fifth sentence."
        parts = sms_engine.split_sms_response(msg)
        
        # Parts should generally end with sentence endings
        for part in parts[:-1]:  # All but last part
            clean_part = part.split('(')[0].strip()  # Remove part numbering
            if clean_part:
                assert clean_part.endswith('.') or clean_part.endswith('!') or clean_part.endswith('?')

    def test_max_parts_limit(self, sms_engine):
        """Test maximum parts limit"""
        very_long_msg = "Very long message. " * 100
        parts = sms_engine.split_sms_response(very_long_msg, max_parts=3)
        
        assert len(parts) <= 3


class TestFallbackResponses:
    """Test fallback response generation"""

    @pytest.fixture
    def sms_engine(self):
        return HandymanSMSEngine()

    def test_emergency_fallback(self, sms_engine):
        """Test emergency fallback response"""
        classification = {'is_emergency': True}
        fallback = sms_engine._generate_sms_fallback_response(
            "+15551234567", "Emergency!", classification
        )
        
        assert "URGENT" in fallback or "757-354-4577" in fallback
        assert "NOW" in fallback

    def test_quote_request_fallback(self, sms_engine):
        """Test quote request fallback response"""
        classification = {'is_quote_request': True, 'is_emergency': False}
        fallback = sms_engine._generate_sms_fallback_response(
            "+15551234567", "How much?", classification
        )
        
        assert "quote" in fallback.lower()
        assert "757-354-4577" in fallback

    def test_appointment_request_fallback(self, sms_engine):
        """Test appointment request fallback response"""
        classification = {'is_appointment_request': True, 'is_quote_request': False, 'is_emergency': False}
        fallback = sms_engine._generate_sms_fallback_response(
            "+15551234567", "Can you come Monday?", classification
        )
        
        assert "schedule" in fallback.lower() or "757-354-4577" in fallback

    def test_services_mentioned_fallback(self, sms_engine):
        """Test fallback when services are mentioned"""
        classification = {
            'services_mentioned': ['plumbing'],
            'is_emergency': False,
            'is_quote_request': False,
            'is_appointment_request': False
        }
        fallback = sms_engine._generate_sms_fallback_response(
            "+15551234567", "Need plumbing help", classification
        )
        
        assert "plumbing" in fallback
        assert "757-354-4577" in fallback

    def test_generic_fallback(self, sms_engine):
        """Test generic fallback response"""
        classification = {
            'is_emergency': False,
            'is_quote_request': False,
            'is_appointment_request': False,
            'services_mentioned': []
        }
        fallback = sms_engine._generate_sms_fallback_response(
            "+15551234567", "Random message", classification
        )
        
        assert "Beach Handyman" in fallback
        assert "757-354-4577" in fallback


class TestAppointmentConfirmation:
    """Test appointment confirmation formatting"""

    @pytest.fixture
    def sms_engine(self):
        return HandymanSMSEngine()

    def test_appointment_confirmation_format(self, sms_engine):
        """Test appointment confirmation SMS formatting"""
        appointment_details = {
            'date': 'Monday, July 15',
            'time': '2:00 PM',
            'service': 'Plumbing repair'
        }
        
        confirmation = sms_engine.format_appointment_confirmation_sms(appointment_details)
        
        assert "Appt confirmed" in confirmation
        assert "Monday, July 15" in confirmation
        assert "2:00 PM" in confirmation
        assert "Plumbing repair" in confirmation
        assert "757-354-4577" in confirmation
        assert len(confirmation) <= 160

    def test_appointment_confirmation_truncation(self, sms_engine):
        """Test that long appointment confirmations are truncated"""
        appointment_details = {
            'date': 'Monday, July 15th, 2024',
            'time': '2:00 PM Eastern Standard Time',
            'service': 'Complete bathroom renovation including plumbing, electrical, and tile work'
        }
        
        confirmation = sms_engine.format_appointment_confirmation_sms(appointment_details)
        
        assert len(confirmation) <= 160
        assert "757-354-4577" in confirmation


if __name__ == '__main__':
    pytest.main([__file__, '-v'])