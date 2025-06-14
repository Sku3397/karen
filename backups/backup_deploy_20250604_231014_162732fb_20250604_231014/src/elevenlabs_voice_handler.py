#!/usr/bin/env python3
"""
ElevenLabs Voice Integration for 757 Handy Premium Voice System
High-quality, emotional AI voices for professional phone experience

Author: Phone Engineer Agent
"""

import os
import json
import logging
import asyncio
import aiohttp
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)

class VoiceModel(Enum):
    """ElevenLabs voice models"""
    MULTILINGUAL_V2 = "eleven_multilingual_v2"
    MONOLINGUAL_V1 = "eleven_monolingual_v1"
    ENGLISH_V1 = "eleven_english_v1"
    TURBO_V2 = "eleven_turbo_v2"  # Fastest, good for real-time

class EmotionStyle(Enum):
    """Emotional styles for different call contexts"""
    PROFESSIONAL = "professional"
    WARM = "warm"
    EMPATHETIC = "empathetic"
    URGENT = "urgent"
    REASSURING = "reassuring"
    FRIENDLY = "friendly"

@dataclass
class VoiceSettings:
    """ElevenLabs voice configuration"""
    stability: float = 0.75  # 0-1, higher = more stable/consistent
    similarity_boost: float = 0.75  # 0-1, higher = closer to original voice
    style: float = 0.5  # 0-1, style exaggeration
    use_speaker_boost: bool = True  # Enhance clarity
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "stability": self.stability,
            "similarity_boost": self.similarity_boost,
            "style": self.style,
            "use_speaker_boost": self.use_speaker_boost
        }

@dataclass
class VoiceProfile:
    """Complete voice profile for different contexts"""
    voice_id: str
    name: str
    description: str
    model: VoiceModel
    settings: VoiceSettings
    best_for: List[str]
    emotion_range: List[EmotionStyle]

class ElevenLabsVoiceHandler:
    """
    Premium voice generation using ElevenLabs API
    
    Features:
    - Multiple voice personalities for different contexts
    - Emotional voice modulation based on call type
    - Real-time voice synthesis for dynamic content
    - Voice caching for frequently used phrases
    - Cost optimization with smart caching
    - Quality monitoring and fallback options
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('ELEVENLABS_API_KEY')
        if not self.api_key:
            raise ValueError("ElevenLabs API key required")
        
        self.base_url = "https://api.elevenlabs.io/v1"
        self.session = None
        
        # Voice cache directory
        self.cache_dir = Path("voice_cache")
        self.cache_dir.mkdir(exist_ok=True)
        
        # Premium voice profiles for 757 Handy
        self.voice_profiles = {
            'karen_professional': VoiceProfile(
                voice_id="21m00Tcm4TlvDq8ikWAM",  # Rachel - Professional female
                name="Karen Professional",
                description="Primary business voice - warm but professional",
                model=VoiceModel.MULTILINGUAL_V2,
                settings=VoiceSettings(
                    stability=0.8,
                    similarity_boost=0.75,
                    style=0.3,
                    use_speaker_boost=True
                ),
                best_for=["main_menu", "general_info", "appointments"],
                emotion_range=[EmotionStyle.PROFESSIONAL, EmotionStyle.WARM, EmotionStyle.FRIENDLY]
            ),
            'karen_empathetic': VoiceProfile(
                voice_id="EXAVITQu4vr4xnSDxMaL",  # Bella - Empathetic female
                name="Karen Empathetic",
                description="For customer service and emotional situations",
                model=VoiceModel.MULTILINGUAL_V2,
                settings=VoiceSettings(
                    stability=0.7,
                    similarity_boost=0.8,
                    style=0.6,
                    use_speaker_boost=True
                ),
                best_for=["complaints", "voicemail_instructions", "apologies"],
                emotion_range=[EmotionStyle.EMPATHETIC, EmotionStyle.REASSURING, EmotionStyle.WARM]
            ),
            'karen_urgent': VoiceProfile(
                voice_id="pNInz6obpgDQGcFmaJgB",  # Adam - Clear male for emergencies
                name="Emergency Response",
                description="For emergency situations requiring immediate attention",
                model=VoiceModel.TURBO_V2,  # Fast for emergencies
                settings=VoiceSettings(
                    stability=0.9,
                    similarity_boost=0.7,
                    style=0.2,
                    use_speaker_boost=True
                ),
                best_for=["emergency_routing", "urgent_instructions"],
                emotion_range=[EmotionStyle.URGENT, EmotionStyle.PROFESSIONAL]
            ),
            'karen_friendly': VoiceProfile(
                voice_id="ThT5KcBeYPX3keUQqHPh",  # Dorothy - Friendly and approachable
                name="Karen Friendly",
                description="For casual interactions and thank you messages",
                model=VoiceModel.MULTILINGUAL_V2,
                settings=VoiceSettings(
                    stability=0.75,
                    similarity_boost=0.8,
                    style=0.7,
                    use_speaker_boost=True
                ),
                best_for=["thank_you", "casual_chat", "follow_up"],
                emotion_range=[EmotionStyle.FRIENDLY, EmotionStyle.WARM]
            )
        }
        
        # Context-based voice selection rules
        self.voice_selection_rules = {
            'emergency': 'karen_urgent',
            'complaint': 'karen_empathetic',
            'voicemail': 'karen_empathetic',
            'greeting': 'karen_professional',
            'menu': 'karen_professional',
            'thank_you': 'karen_friendly',
            'hours_info': 'karen_professional',
            'appointment': 'karen_professional',
            'quote': 'karen_professional',
            'after_hours': 'karen_empathetic',
            'queue': 'karen_empathetic'
        }
        
        # Frequently used phrases for caching
        self.common_phrases = {
            'company_greeting': "Thank you for calling 757 Handy, Hampton Roads' premier home improvement experts.",
            'menu_intro': "To help you quickly, please choose from the following options:",
            'transferring': "Please hold while I connect you with the right person to help you.",
            'emergency_response': "This is our emergency service line. Please stay on the line while I connect you immediately.",
            'voicemail_intro': "Please leave a detailed message and we'll return your call.",
            'thank_you_closing': "Thank you for calling 757 Handy. Have a wonderful day!"
        }
        
        # Cost tracking
        self.usage_stats = {
            'characters_processed': 0,
            'api_calls': 0,
            'cache_hits': 0,
            'total_cost_estimate': 0.0
        }
        
        logger.info("ElevenLabsVoiceHandler initialized with premium voice profiles")
    
    async def initialize_session(self):
        """Initialize aiohttp session for API calls"""
        if not self.session:
            headers = {
                "xi-api-key": self.api_key,
                "Content-Type": "application/json"
            }
            self.session = aiohttp.ClientSession(headers=headers)
    
    async def close_session(self):
        """Clean up aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def generate_voice_for_context(self, text: str, context: str, 
                                       emotion: EmotionStyle = None) -> str:
        """
        Generate voice audio for specific context with appropriate voice and emotion
        
        Returns: URL to generated audio file
        """
        try:
            # Select appropriate voice profile
            voice_profile_name = self.voice_selection_rules.get(context, 'karen_professional')
            voice_profile = self.voice_profiles[voice_profile_name]
            
            # Check cache first
            cache_key = self._generate_cache_key(text, voice_profile_name, emotion)
            cached_path = await self._get_from_cache(cache_key)
            
            if cached_path:
                self.usage_stats['cache_hits'] += 1
                logger.debug(f"Voice cache hit for context: {context}")
                return cached_path
            
            # Generate new audio
            audio_url = await self._generate_audio(text, voice_profile, emotion)
            
            # Cache the result
            if audio_url:
                await self._save_to_cache(cache_key, audio_url)
            
            self.usage_stats['api_calls'] += 1
            self.usage_stats['characters_processed'] += len(text)
            self.usage_stats['total_cost_estimate'] += len(text) * 0.0001  # Rough estimate
            
            return audio_url
            
        except Exception as e:
            logger.error(f"Failed to generate voice for context {context}: {e}")
            return None
    
    async def _generate_audio(self, text: str, voice_profile: VoiceProfile, 
                            emotion: EmotionStyle = None) -> Optional[str]:
        """Generate audio using ElevenLabs API"""
        try:
            await self.initialize_session()
            
            # Adjust voice settings based on emotion
            settings = self._adjust_settings_for_emotion(voice_profile.settings, emotion)
            
            # Prepare request
            url = f"{self.base_url}/text-to-speech/{voice_profile.voice_id}"
            
            payload = {
                "text": text,
                "model_id": voice_profile.model.value,
                "voice_settings": settings.to_dict()
            }
            
            # Add optimization parameters
            params = {
                "optimize_streaming_latency": "3",  # Balance quality vs speed
                "output_format": "mp3_44100_128"    # Good quality, reasonable size
            }
            
            async with self.session.post(url, json=payload, params=params) as response:
                if response.status == 200:
                    # Save audio to temporary file
                    audio_data = await response.read()
                    
                    # Create temporary file with proper extension
                    temp_file = tempfile.NamedTemporaryFile(
                        delete=False, 
                        suffix='.mp3',
                        dir=self.cache_dir
                    )
                    
                    temp_file.write(audio_data)
                    temp_file.close()
                    
                    logger.debug(f"Generated audio: {len(audio_data)} bytes for voice {voice_profile.name}")
                    return temp_file.name
                else:
                    error_text = await response.text()
                    logger.error(f"ElevenLabs API error {response.status}: {error_text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error generating audio: {e}")
            return None
    
    def _adjust_settings_for_emotion(self, base_settings: VoiceSettings, 
                                   emotion: EmotionStyle) -> VoiceSettings:
        """Adjust voice settings based on desired emotion"""
        if not emotion:
            return base_settings
        
        # Create copy of base settings
        adjusted = VoiceSettings(
            stability=base_settings.stability,
            similarity_boost=base_settings.similarity_boost,
            style=base_settings.style,
            use_speaker_boost=base_settings.use_speaker_boost
        )
        
        # Emotional adjustments
        if emotion == EmotionStyle.URGENT:
            adjusted.stability = min(1.0, base_settings.stability + 0.1)  # More stable for clarity
            adjusted.style = max(0.0, base_settings.style - 0.2)  # Less stylistic variation
            
        elif emotion == EmotionStyle.EMPATHETIC:
            adjusted.similarity_boost = min(1.0, base_settings.similarity_boost + 0.1)
            adjusted.style = min(1.0, base_settings.style + 0.2)  # More expressive
            
        elif emotion == EmotionStyle.WARM:
            adjusted.style = min(1.0, base_settings.style + 0.15)
            adjusted.similarity_boost = min(1.0, base_settings.similarity_boost + 0.05)
            
        elif emotion == EmotionStyle.PROFESSIONAL:
            adjusted.stability = min(1.0, base_settings.stability + 0.05)
            adjusted.style = max(0.1, base_settings.style - 0.1)
            
        elif emotion == EmotionStyle.REASSURING:
            adjusted.stability = min(1.0, base_settings.stability + 0.1)
            adjusted.style = min(1.0, base_settings.style + 0.1)
        
        return adjusted
    
    def _generate_cache_key(self, text: str, voice_profile: str, 
                          emotion: EmotionStyle = None) -> str:
        """Generate cache key for text/voice/emotion combination"""
        emotion_str = emotion.value if emotion else "neutral"
        combined = f"{text}|{voice_profile}|{emotion_str}"
        return hashlib.md5(combined.encode()).hexdigest()
    
    async def _get_from_cache(self, cache_key: str) -> Optional[str]:
        """Check if audio is cached"""
        cache_file = self.cache_dir / f"{cache_key}.mp3"
        if cache_file.exists():
            # Check if cache is still fresh (24 hours)
            if datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime) < timedelta(hours=24):
                return str(cache_file)
        return None
    
    async def _save_to_cache(self, cache_key: str, audio_path: str):
        """Save audio to cache"""
        try:
            cache_file = self.cache_dir / f"{cache_key}.mp3"
            
            # Copy temp file to cache
            import shutil
            shutil.copy2(audio_path, cache_file)
            
            logger.debug(f"Cached audio: {cache_key}")
            
        except Exception as e:
            logger.error(f"Failed to cache audio: {e}")
    
    async def pre_generate_common_phrases(self):
        """Pre-generate and cache commonly used phrases"""
        logger.info("Pre-generating common phrases for cache")
        
        tasks = []
        for phrase_name, text in self.common_phrases.items():
            # Determine context from phrase name
            if 'emergency' in phrase_name:
                context = 'emergency'
            elif 'greeting' in phrase_name:
                context = 'greeting'
            elif 'menu' in phrase_name:
                context = 'menu'
            elif 'thank' in phrase_name:
                context = 'thank_you'
            else:
                context = 'general'
            
            task = self.generate_voice_for_context(text, context)
            tasks.append(task)
        
        # Generate all phrases concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        successful = sum(1 for r in results if isinstance(r, str))
        logger.info(f"Pre-generated {successful}/{len(tasks)} common phrases")
    
    async def generate_dynamic_message(self, template: str, variables: Dict[str, str], 
                                     context: str) -> str:
        """Generate voice for dynamic messages with variable substitution"""
        try:
            # Substitute variables in template
            message = template
            for var_name, var_value in variables.items():
                placeholder = f"{{{var_name}}}"
                message = message.replace(placeholder, var_value)
            
            return await self.generate_voice_for_context(message, context)
            
        except Exception as e:
            logger.error(f"Failed to generate dynamic message: {e}")
            return None
    
    async def get_voice_for_menu_option(self, option_text: str, option_number: str) -> str:
        """Generate voice for specific menu option with proper formatting"""
        try:
            # Format menu option with proper pacing
            formatted_text = f"For {option_text}, press {option_number}."
            
            return await self.generate_voice_for_context(formatted_text, 'menu')
            
        except Exception as e:
            logger.error(f"Failed to generate menu option voice: {e}")
            return None
    
    async def get_personalized_greeting(self, customer_name: str = None, 
                                      time_of_day: str = None) -> str:
        """Generate personalized greeting based on customer and time"""
        try:
            # Build personalized greeting
            if time_of_day:
                time_greeting = f"Good {time_of_day}"
            else:
                time_greeting = "Hello"
            
            if customer_name:
                greeting = f"{time_greeting}, {customer_name}! Thank you for calling 757 Handy."
            else:
                greeting = f"{time_greeting}! Thank you for calling 757 Handy, Hampton Roads' premier home improvement experts."
            
            return await self.generate_voice_for_context(greeting, 'greeting', EmotionStyle.WARM)
            
        except Exception as e:
            logger.error(f"Failed to generate personalized greeting: {e}")
            return None
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics for monitoring and cost control"""
        return {
            **self.usage_stats,
            'cache_hit_rate': (
                self.usage_stats['cache_hits'] / 
                max(1, self.usage_stats['cache_hits'] + self.usage_stats['api_calls'])
            ),
            'estimated_monthly_cost': self.usage_stats['total_cost_estimate'] * 30,
            'voices_available': len(self.voice_profiles),
            'cache_size_mb': self._get_cache_size_mb()
        }
    
    def _get_cache_size_mb(self) -> float:
        """Calculate cache directory size in MB"""
        try:
            total_size = sum(
                f.stat().st_size for f in self.cache_dir.rglob('*') if f.is_file()
            )
            return total_size / (1024 * 1024)
        except:
            return 0.0
    
    async def cleanup_old_cache(self, days_old: int = 7):
        """Clean up old cached audio files"""
        try:
            cutoff_time = datetime.now() - timedelta(days=days_old)
            removed_count = 0
            
            for cache_file in self.cache_dir.glob('*.mp3'):
                if datetime.fromtimestamp(cache_file.stat().st_mtime) < cutoff_time:
                    cache_file.unlink()
                    removed_count += 1
            
            logger.info(f"Cleaned up {removed_count} old cache files")
            
        except Exception as e:
            logger.error(f"Failed to cleanup cache: {e}")
    
    async def validate_voice_quality(self, audio_path: str) -> Dict[str, Any]:
        """Basic audio quality validation"""
        try:
            import wave
            import os
            
            # Get file size
            file_size = os.path.getsize(audio_path)
            
            # Basic quality metrics
            quality_metrics = {
                'file_size_kb': file_size / 1024,
                'exists': os.path.exists(audio_path),
                'is_valid': file_size > 1000,  # At least 1KB
                'estimated_duration': file_size / 16000,  # Rough estimate
            }
            
            return quality_metrics
            
        except Exception as e:
            logger.error(f"Failed to validate audio quality: {e}")
            return {'is_valid': False, 'error': str(e)}

# Integration functions for existing voice webhook handler
async def get_elevenlabs_audio_url(text: str, context: str = 'general', 
                                 emotion: str = None) -> Optional[str]:
    """
    Convenience function to get ElevenLabs audio URL
    To be called from TwiML generation in voice_webhook_handler.py
    """
    try:
        voice_handler = ElevenLabsVoiceHandler()
        
        emotion_enum = None
        if emotion:
            try:
                emotion_enum = EmotionStyle(emotion)
            except ValueError:
                logger.warning(f"Invalid emotion style: {emotion}")
        
        audio_path = await voice_handler.generate_voice_for_context(text, context, emotion_enum)
        await voice_handler.close_session()
        
        if audio_path:
            # Convert local path to accessible URL
            # In production, this would upload to CDN/S3 and return public URL
            # For now, return a local server URL
            filename = os.path.basename(audio_path)
            return f"https://your-domain.com/voice-assets/{filename}"
        
        return None
        
    except Exception as e:
        logger.error(f"Failed to get ElevenLabs audio: {e}")
        return None

def enhance_twiml_with_elevenlabs(voice_response, text: str, context: str = 'general'):
    """
    Enhance TwiML VoiceResponse with ElevenLabs audio
    Falls back to standard TTS if ElevenLabs fails
    """
    try:
        # Try to get ElevenLabs audio URL
        import asyncio
        
        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        audio_url = loop.run_until_complete(
            get_elevenlabs_audio_url(text, context)
        )
        loop.close()
        
        if audio_url:
            # Use ElevenLabs audio
            voice_response.play(audio_url)
            logger.info(f"Using ElevenLabs audio for context: {context}")
        else:
            # Fallback to standard TTS
            voice_response.say(text, voice='Polly.Joanna', language='en-US')
            logger.warning(f"Fallback to standard TTS for context: {context}")
            
    except Exception as e:
        logger.error(f"Error enhancing TwiML with ElevenLabs: {e}")
        # Always fallback to standard TTS
        voice_response.say(text, voice='Polly.Joanna', language='en-US')

if __name__ == "__main__":
    # Test the ElevenLabs integration
    async def test_elevenlabs():
        # Initialize with test API key
        handler = ElevenLabsVoiceHandler()
        
        # Test different contexts and emotions
        test_cases = [
            ("Thank you for calling 757 Handy. How can I help you today?", "greeting", EmotionStyle.WARM),
            ("This is an emergency. Please stay on the line.", "emergency", EmotionStyle.URGENT),
            ("I understand your frustration. Let me help you with that.", "complaint", EmotionStyle.EMPATHETIC),
            ("For appointment scheduling, press 1.", "menu", EmotionStyle.PROFESSIONAL)
        ]
        
        for text, context, emotion in test_cases:
            print(f"\nTesting: {context} - {emotion.value}")
            audio_path = await handler.generate_voice_for_context(text, context, emotion)
            if audio_path:
                print(f"Generated: {audio_path}")
                
                # Validate quality
                quality = await handler.validate_voice_quality(audio_path)
                print(f"Quality: {quality}")
            else:
                print("Failed to generate audio")
        
        # Show usage stats
        stats = handler.get_usage_stats()
        print(f"\nUsage Stats: {json.dumps(stats, indent=2)}")
        
        await handler.close_session()
    
    # Run test
    asyncio.run(test_elevenlabs())