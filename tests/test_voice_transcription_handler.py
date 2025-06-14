"""
Comprehensive unit tests for Voice Transcription Handler
"""
import pytest
import asyncio
import os
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from datetime import datetime
import json
import tempfile
from dataclasses import asdict

# Import both versions of the transcription handler
from src.voice_transcription_handler import (
    VoiceTranscriptionHandler as AdvancedHandler,
    VoicemailData, Priority, MessageType
)
from src.communication_agent.voice_transcription_handler import (
    VoiceTranscriptionHandler as SimpleHandler
)


class TestSimpleVoiceTranscriptionHandler:
    """Test the simple voice transcription handler"""

    @pytest.fixture
    def mock_speech_client(self):
        """Create mock Google Speech client"""
        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_alternative = MagicMock()
        mock_alternative.transcript = "Hello, this is a test transcription"
        mock_result.alternatives = [mock_alternative]
        mock_response = MagicMock()
        mock_response.results = [mock_result]
        mock_client.recognize.return_value = mock_response
        return mock_client

    @pytest.fixture
    def simple_handler(self, mock_speech_client):
        """Create simple handler with mocked client"""
        with patch('src.communication_agent.voice_transcription_handler.speech.SpeechClient', return_value=mock_speech_client):
            handler = SimpleHandler()
            handler.client = mock_speech_client
            return handler

    def test_simple_initialization_with_credentials(self):
        """Test simple handler initialization with credentials"""
        with patch('os.path.exists', return_value=True):
            with patch('src.communication_agent.voice_transcription_handler.service_account.Credentials.from_service_account_file') as mock_creds:
                with patch('src.communication_agent.voice_transcription_handler.speech.SpeechClient') as mock_client_class:
                    handler = SimpleHandler()
                    
                    mock_creds.assert_called_once()
                    mock_client_class.assert_called_once()
                    assert handler.language_code == 'en-US'

    def test_simple_initialization_without_credentials(self):
        """Test simple handler initialization without credentials"""
        with patch('os.getenv', return_value=None):
            with patch('src.communication_agent.voice_transcription_handler.speech.SpeechClient') as mock_client_class:
                handler = SimpleHandler(language_code='es-ES')
                
                mock_client_class.assert_called_once()
                assert handler.language_code == 'es-ES'

    def test_simple_transcribe_audio_success(self, simple_handler):
        """Test successful audio transcription"""
        audio_bytes = b"fake audio data"
        
        result = simple_handler.transcribe_audio(audio_bytes)
        
        assert result == "Hello, this is a test transcription"
        simple_handler.client.recognize.assert_called_once()

    def test_simple_transcribe_audio_no_results(self, simple_handler):
        """Test transcription with no results"""
        simple_handler.client.recognize.return_value.results = []
        audio_bytes = b"fake audio data"
        
        result = simple_handler.transcribe_audio(audio_bytes)
        
        assert result is None

    def test_simple_transcribe_audio_exception(self, simple_handler):
        """Test transcription with exception"""
        simple_handler.client.recognize.side_effect = Exception("API Error")
        audio_bytes = b"fake audio data"
        
        result = simple_handler.transcribe_audio(audio_bytes)
        
        assert result is None

    def test_simple_transcribe_audio_config(self, simple_handler):
        """Test that transcription uses correct config"""
        audio_bytes = b"fake audio data"
        
        simple_handler.transcribe_audio(audio_bytes)
        
        call_args = simple_handler.client.recognize.call_args
        config = call_args[1]['config']
        audio = call_args[1]['audio']
        
        assert config.language_code == 'en-US'
        assert config.sample_rate_hertz == 16000
        assert audio.content == audio_bytes


class TestAdvancedVoiceTranscriptionHandler:
    """Test the advanced voice transcription handler"""

    @pytest.fixture
    def mock_google_client(self):
        """Create mock Google Speech client"""
        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_alternative = MagicMock()
        mock_alternative.transcript = "This is an emergency! Gas leak in kitchen."
        mock_alternative.confidence = 0.95
        mock_result.alternatives = [mock_alternative]
        mock_response = MagicMock()
        mock_response.results = [mock_result]
        mock_client.recognize.return_value = mock_response
        return mock_client

    @pytest.fixture
    def mock_openai_client(self):
        """Create mock OpenAI client"""
        mock_client = MagicMock()
        mock_transcript = MagicMock()
        mock_transcript.text = "OpenAI transcription result"
        mock_client.Audio.transcribe.return_value = mock_transcript
        return mock_client

    @pytest.fixture
    def advanced_handler(self, mock_google_client, mock_openai_client):
        """Create advanced handler with mocked clients"""
        with patch('src.voice_transcription_handler.speech.SpeechClient', return_value=mock_google_client):
            with patch('src.voice_transcription_handler.openai', mock_openai_client):
                with patch('src.voice_transcription_handler.EmailClient'):
                    with patch('src.voice_transcription_handler.SMSClient'):
                        handler = AdvancedHandler()
                        handler.google_speech_client = mock_google_client
                        handler.openai_client = mock_openai_client
                        return handler

    def test_advanced_initialization(self):
        """Test advanced handler initialization"""
        with patch('os.getenv') as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: {
                'GOOGLE_APPLICATION_CREDENTIALS': '/path/to/creds.json',
                'OPENAI_API_KEY': 'test_key',
                'ADMIN_EMAIL_ADDRESS': 'admin@test.com'
            }.get(key, default)
            
            with patch('src.voice_transcription_handler.speech.SpeechClient'):
                with patch('src.voice_transcription_handler.EmailClient'):
                    with patch('src.voice_transcription_handler.SMSClient'):
                        handler = AdvancedHandler()
                        
                        assert handler.emergency_keywords['immediate']
                        assert handler.service_keywords['plumbing']
                        assert handler.sentiment_keywords['positive']

    @pytest.mark.asyncio
    async def test_transcribe_with_google_success(self, advanced_handler):
        """Test successful Google transcription"""
        with patch.object(advanced_handler, '_download_audio', return_value=b"audio data"):
            result = await advanced_handler._transcribe_with_google("http://test.com/audio.mp3")
            
            assert result['text'] == "This is an emergency! Gas leak in kitchen."
            assert result['confidence'] == 0.95
            assert result['engine'] == 'google'

    @pytest.mark.asyncio
    async def test_transcribe_with_google_failure(self, advanced_handler):
        """Test Google transcription failure"""
        advanced_handler.google_speech_client.recognize.side_effect = Exception("API Error")
        
        with patch.object(advanced_handler, '_download_audio', return_value=b"audio data"):
            result = await advanced_handler._transcribe_with_google("http://test.com/audio.mp3")
            
            assert result['text'] == ''
            assert result['confidence'] == 0.0
            assert result['engine'] == 'google_failed'

    @pytest.mark.asyncio
    async def test_transcribe_with_whisper_success(self, advanced_handler):
        """Test successful Whisper transcription"""
        with patch.object(advanced_handler, '_download_audio_to_file', return_value='/tmp/test.wav'):
            with patch('builtins.open', create=True):
                with patch('os.unlink'):
                    result = await advanced_handler._transcribe_with_whisper("http://test.com/audio.mp3")
                    
                    assert result['text'] == "OpenAI transcription result"
                    assert result['confidence'] == 0.85
                    assert result['engine'] == 'whisper'

    @pytest.mark.asyncio
    async def test_transcribe_with_sr_success(self, advanced_handler):
        """Test successful speech_recognition transcription"""
        with patch.object(advanced_handler, '_download_audio_to_file', return_value='/tmp/test.wav'):
            with patch('src.voice_transcription_handler.sr.Recognizer') as mock_recognizer_class:
                mock_recognizer = MagicMock()
                mock_recognizer.recognize_google.return_value = "SR transcription result"
                mock_recognizer_class.return_value = mock_recognizer
                
                with patch('src.voice_transcription_handler.sr.AudioFile'):
                    with patch('os.unlink'):
                        result = await advanced_handler._transcribe_with_sr("http://test.com/audio.mp3")
                        
                        assert result['text'] == "SR transcription result"
                        assert result['confidence'] == 0.7
                        assert result['engine'] == 'speech_recognition'

    @pytest.mark.asyncio
    async def test_transcribe_audio_engine_fallback(self, advanced_handler):
        """Test transcription engine fallback"""
        # Mock Google to return low confidence
        with patch.object(advanced_handler, '_transcribe_with_google', return_value={'text': 'low quality', 'confidence': 0.3}):
            with patch.object(advanced_handler, '_transcribe_with_whisper', return_value={'text': 'high quality', 'confidence': 0.9}):
                result = await advanced_handler._transcribe_audio("http://test.com/audio.mp3")
                
                assert result['text'] == 'high quality'
                assert result['confidence'] == 0.9

    @pytest.mark.asyncio
    async def test_download_audio_success(self, advanced_handler):
        """Test successful audio download"""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read = AsyncMock(return_value=b"audio content")
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = MagicMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
            mock_session.get.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_session_class.return_value = mock_session
            
            result = await advanced_handler._download_audio("http://test.com/audio.mp3")
            
            assert result == b"audio content"

    @pytest.mark.asyncio
    async def test_download_audio_failure(self, advanced_handler):
        """Test audio download failure"""
        mock_response = MagicMock()
        mock_response.status = 404
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = MagicMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
            mock_session.get.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_session_class.return_value = mock_session
            
            with pytest.raises(Exception, match="Failed to download audio: 404"):
                await advanced_handler._download_audio("http://test.com/audio.mp3")


class TestVoicemailDataStructure:
    """Test VoicemailData dataclass"""

    def test_voicemail_data_initialization(self):
        """Test VoicemailData initialization"""
        voicemail = VoicemailData(
            call_sid="CA123456789",
            caller_id="+15551234567",
            recording_url="http://test.com/audio.mp3",
            duration=45,
            timestamp=datetime.now()
        )
        
        assert voicemail.call_sid == "CA123456789"
        assert voicemail.caller_id == "+15551234567"
        assert voicemail.priority == Priority.NORMAL
        assert voicemail.message_type == MessageType.GENERAL_VOICEMAIL
        assert voicemail.keywords == []
        assert voicemail.entities == {}

    def test_voicemail_data_post_init(self):
        """Test VoicemailData __post_init__ method"""
        voicemail = VoicemailData(
            call_sid="CA123456789",
            caller_id="+15551234567",
            recording_url="http://test.com/audio.mp3",
            duration=45,
            timestamp=datetime.now(),
            keywords=None,
            entities=None,
            action_items=None,
            customer_info=None
        )
        
        # Should initialize None values to empty containers
        assert isinstance(voicemail.keywords, list)
        assert isinstance(voicemail.entities, dict)
        assert isinstance(voicemail.action_items, list)
        assert isinstance(voicemail.customer_info, dict)


class TestVoicemailAnalysis:
    """Test voicemail content analysis"""

    @pytest.fixture
    def handler(self):
        with patch('src.voice_transcription_handler.EmailClient'):
            with patch('src.voice_transcription_handler.SMSClient'):
                return AdvancedHandler()

    @pytest.mark.asyncio
    async def test_analyze_transcription_keywords(self, handler):
        """Test keyword extraction from transcription"""
        voicemail = VoicemailData(
            call_sid="CA123456789",
            caller_id="+15551234567",
            recording_url="http://test.com/audio.mp3",
            duration=45,
            timestamp=datetime.now(),
            transcription="I need a plumber to fix my toilet and sink"
        )
        
        await handler._analyze_transcription(voicemail)
        
        assert any('plumbing:plumber' in keyword for keyword in voicemail.keywords)
        assert any('plumbing:toilet' in keyword for keyword in voicemail.keywords)
        assert any('plumbing:sink' in keyword for keyword in voicemail.keywords)

    @pytest.mark.asyncio
    async def test_analyze_transcription_entities(self, handler):
        """Test entity extraction from transcription"""
        voicemail = VoicemailData(
            call_sid="CA123456789",
            caller_id="+15551234567",
            recording_url="http://test.com/audio.mp3",
            duration=45,
            timestamp=datetime.now(),
            transcription="Call me back at 757-555-1234 or email john@example.com. I'm available at 2:00 PM."
        )
        
        await handler._analyze_transcription(voicemail)
        
        assert '757-555-1234' in voicemail.entities.get('phone_numbers', [])
        assert 'john@example.com' in voicemail.entities.get('emails', [])
        assert '2:00 PM' in voicemail.entities.get('times', [])

    @pytest.mark.asyncio
    async def test_analyze_transcription_sentiment(self, handler):
        """Test sentiment analysis"""
        test_cases = [
            ("I'm very frustrated with the service", "negative"),
            ("Thank you for the excellent work", "positive"),
            ("This is an urgent emergency", "urgent")
        ]
        
        for transcription, expected_sentiment in test_cases:
            voicemail = VoicemailData(
                call_sid="CA123456789",
                caller_id="+15551234567",
                recording_url="http://test.com/audio.mp3",
                duration=45,
                timestamp=datetime.now(),
                transcription=transcription
            )
            
            await handler._analyze_transcription(voicemail)
            
            assert voicemail.sentiment == expected_sentiment

    def test_determine_priority_emergency(self, handler):
        """Test emergency priority determination"""
        voicemail = VoicemailData(
            call_sid="CA123456789",
            caller_id="+15551234567",
            recording_url="http://test.com/audio.mp3",
            duration=45,
            timestamp=datetime.now(),
            transcription="Emergency! Gas leak right now, urgent help needed immediately!"
        )
        
        handler._determine_priority(voicemail)
        
        assert voicemail.priority == Priority.EMERGENCY
        assert voicemail.message_type == MessageType.EMERGENCY_VOICEMAIL

    def test_determine_priority_high(self, handler):
        """Test high priority determination"""
        voicemail = VoicemailData(
            call_sid="CA123456789",
            caller_id="+15551234567",
            recording_url="http://test.com/audio.mp3",
            duration=45,
            timestamp=datetime.now(),
            transcription="Urgent plumbing issue today, frustrated customer"
        )
        
        handler._determine_priority(voicemail)
        
        assert voicemail.priority == Priority.HIGH

    def test_determine_priority_normal(self, handler):
        """Test normal priority determination"""
        voicemail = VoicemailData(
            call_sid="CA123456789",
            caller_id="+15551234567",
            recording_url="http://test.com/audio.mp3",
            duration=45,
            timestamp=datetime.now(),
            transcription="I need a quote for kitchen renovation when you have time"
        )
        
        handler._determine_priority(voicemail)
        
        assert voicemail.priority == Priority.NORMAL

    def test_extract_customer_info(self, handler):
        """Test customer information extraction"""
        voicemail = VoicemailData(
            call_sid="CA123456789",
            caller_id="+15551234567",
            recording_url="http://test.com/audio.mp3",
            duration=45,
            timestamp=datetime.now(),
            transcription="Hi, my name is John Smith. Please call me back at 757-555-1234.",
            entities={'phone_numbers': ['757-555-1234']}
        )
        
        handler._extract_customer_info(voicemail)
        
        assert voicemail.customer_info['name'] == 'John Smith'
        assert voicemail.customer_info['callback_number'] == '757-555-1234'

    def test_generate_action_items_emergency(self, handler):
        """Test action item generation for emergency"""
        voicemail = VoicemailData(
            call_sid="CA123456789",
            caller_id="+15551234567",
            recording_url="http://test.com/audio.mp3",
            duration=45,
            timestamp=datetime.now(),
            transcription="Emergency gas leak!",
            priority=Priority.EMERGENCY
        )
        
        handler._generate_action_items(voicemail)
        
        assert any("EMERGENCY" in item for item in voicemail.action_items)
        assert any("immediately" in item for item in voicemail.action_items)

    def test_generate_action_items_quote_request(self, handler):
        """Test action item generation for quote request"""
        voicemail = VoicemailData(
            call_sid="CA123456789",
            caller_id="+15551234567",
            recording_url="http://test.com/audio.mp3",
            duration=45,
            timestamp=datetime.now(),
            transcription="I need a quote for bathroom renovation"
        )
        
        handler._generate_action_items(voicemail)
        
        assert any("estimate" in item for item in voicemail.action_items)
        assert voicemail.message_type == MessageType.QUOTE_REQUEST


class TestVoicemailNotifications:
    """Test voicemail notification system"""

    @pytest.fixture
    def handler_with_mocks(self):
        """Create handler with mocked notification clients"""
        with patch('src.voice_transcription_handler.EmailClient') as mock_email:
            with patch('src.voice_transcription_handler.SMSClient') as mock_sms:
                handler = AdvancedHandler()
                handler.email_client = Mock()
                handler.email_client.send_email = AsyncMock()
                handler.sms_client = Mock()
                handler.sms_client.send_sms = AsyncMock()
                return handler

    @pytest.mark.asyncio
    async def test_send_emergency_notifications(self, handler_with_mocks):
        """Test emergency notification sending"""
        voicemail = VoicemailData(
            call_sid="CA123456789",
            caller_id="+15551234567",
            recording_url="http://test.com/audio.mp3",
            duration=45,
            timestamp=datetime.now(),
            transcription="Emergency gas leak!",
            priority=Priority.EMERGENCY,
            action_items=["Call back immediately"]
        )
        
        await handler_with_mocks._send_emergency_notifications(voicemail)
        
        # Verify SMS was sent
        handler_with_mocks.sms_client.send_sms.assert_called_once()
        sms_call = handler_with_mocks.sms_client.send_sms.call_args
        assert "EMERGENCY" in sms_call[1]['message']
        
        # Verify email was sent
        handler_with_mocks.email_client.send_email.assert_called()

    @pytest.mark.asyncio
    async def test_send_high_priority_notifications(self, handler_with_mocks):
        """Test high priority notification sending"""
        voicemail = VoicemailData(
            call_sid="CA123456789",
            caller_id="+15551234567",
            recording_url="http://test.com/audio.mp3",
            duration=45,
            timestamp=datetime.now(),
            transcription="Urgent plumbing issue",
            priority=Priority.HIGH,
            message_type=MessageType.GENERAL_VOICEMAIL
        )
        
        await handler_with_mocks._send_high_priority_notifications(voicemail)
        
        # Verify SMS was sent
        handler_with_mocks.sms_client.send_sms.assert_called_once()
        sms_call = handler_with_mocks.sms_client.send_sms.call_args
        assert "HIGH PRIORITY" in sms_call[1]['message']

    @pytest.mark.asyncio
    async def test_send_normal_notifications(self, handler_with_mocks):
        """Test normal priority notification sending"""
        voicemail = VoicemailData(
            call_sid="CA123456789",
            caller_id="+15551234567",
            recording_url="http://test.com/audio.mp3",
            duration=45,
            timestamp=datetime.now(),
            transcription="Regular message",
            priority=Priority.NORMAL
        )
        
        await handler_with_mocks._send_normal_notifications(voicemail)
        
        # Should only send email for normal priority
        handler_with_mocks.sms_client.send_sms.assert_not_called()
        handler_with_mocks.email_client.send_email.assert_called_once()

    def test_generate_email_content(self, handler_with_mocks):
        """Test email content generation"""
        voicemail = VoicemailData(
            call_sid="CA123456789",
            caller_id="+15551234567",
            recording_url="http://test.com/audio.mp3",
            duration=45,
            timestamp=datetime.now(),
            transcription="Test transcription",
            priority=Priority.HIGH,
            message_type=MessageType.QUOTE_REQUEST,
            keywords=["plumbing:sink"],
            action_items=["Call back within 1 hour"],
            customer_info={"name": "John Smith"}
        )
        
        html_content = handler_with_mocks._generate_email_content(voicemail)
        
        assert "HIGH" in html_content
        assert "Test transcription" in html_content
        assert "John Smith" in html_content
        assert "Call back within 1 hour" in html_content
        assert "plumbing:sink" in html_content


class TestVoicemailProcessingIntegration:
    """Test complete voicemail processing workflow"""

    @pytest.fixture
    def handler_with_all_mocks(self):
        """Create handler with all external dependencies mocked"""
        with patch('src.voice_transcription_handler.EmailClient'):
            with patch('src.voice_transcription_handler.SMSClient'):
                handler = AdvancedHandler()
                
                # Mock transcription
                handler._transcribe_audio = AsyncMock(return_value={
                    'text': 'Emergency! Gas leak in kitchen, call 757-555-1234',
                    'confidence': 0.95,
                    'engine': 'google'
                })
                
                # Mock notifications
                handler._send_notifications = AsyncMock()
                handler._log_voicemail = AsyncMock()
                handler._extract_caller_id = Mock(return_value="+15551234567")
                
                return handler

    @pytest.mark.asyncio
    async def test_process_voicemail_complete_workflow(self, handler_with_all_mocks):
        """Test complete voicemail processing workflow"""
        result = await handler_with_all_mocks.process_voicemail(
            call_sid="CA123456789",
            recording_url="http://test.com/audio.mp3",
            duration=45,
            message_type="general"
        )
        
        # Verify voicemail was processed
        assert result.call_sid == "CA123456789"
        assert result.transcription == 'Emergency! Gas leak in kitchen, call 757-555-1234'
        assert result.confidence == 0.95
        assert result.priority == Priority.EMERGENCY  # Should be determined from content
        
        # Verify all processing steps were called
        handler_with_all_mocks._transcribe_audio.assert_called_once()
        handler_with_all_mocks._send_notifications.assert_called_once()
        handler_with_all_mocks._log_voicemail.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_voicemail_error_handling(self, handler_with_all_mocks):
        """Test error handling in voicemail processing"""
        handler_with_all_mocks._transcribe_audio.side_effect = Exception("Transcription failed")
        handler_with_all_mocks._send_error_notification = AsyncMock()
        
        with pytest.raises(Exception, match="Transcription failed"):
            await handler_with_all_mocks.process_voicemail(
                call_sid="CA123456789",
                recording_url="http://test.com/audio.mp3",
                duration=45
            )
        
        # Verify error notification was sent
        handler_with_all_mocks._send_error_notification.assert_called_once()


class TestVoicemailLogging:
    """Test voicemail logging and analytics"""

    @pytest.fixture
    def handler(self):
        with patch('src.voice_transcription_handler.EmailClient'):
            with patch('src.voice_transcription_handler.SMSClient'):
                return AdvancedHandler()

    @pytest.mark.asyncio
    async def test_log_voicemail(self, handler):
        """Test voicemail logging"""
        voicemail = VoicemailData(
            call_sid="CA123456789",
            caller_id="+15551234567",
            recording_url="http://test.com/audio.mp3",
            duration=45,
            timestamp=datetime.now(),
            transcription="Test message",
            priority=Priority.HIGH,
            message_type=MessageType.QUOTE_REQUEST
        )
        
        with patch('builtins.open', create=True) as mock_open:
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file
            
            await handler._log_voicemail(voicemail)
            
            # Verify file was opened and written to
            mock_open.assert_called_once()
            mock_file.write.assert_called_once()
            
            # Verify JSON structure
            written_data = mock_file.write.call_args[0][0]
            log_entry = json.loads(written_data.rstrip('\n'))
            assert log_entry['call_sid'] == "CA123456789"
            assert log_entry['priority'] == 'high'

    def test_get_voicemail_analytics(self, handler):
        """Test voicemail analytics retrieval"""
        analytics = handler.get_voicemail_analytics(days=30)
        
        # Should return analytics structure
        assert 'total_voicemails' in analytics
        assert 'by_priority' in analytics
        assert 'by_type' in analytics
        assert 'average_duration' in analytics


if __name__ == '__main__':
    pytest.main([__file__, '-v'])