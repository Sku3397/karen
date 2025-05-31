from google.cloud import speech
from typing import Optional
import io

class VoiceTranscriptionHandler:
    def __init__(self, language_code: str = 'en-US'):
        self.client = speech.SpeechClient()
        self.language_code = language_code

    def transcribe_audio(self, audio_bytes: bytes) -> Optional[str]:
        audio = speech.RecognitionAudio(content=audio_bytes)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code=self.language_code,
        )
        try:
            response = self.client.recognize(config=config, audio=audio)
            for result in response.results:
                return result.alternatives[0].transcript
            return None
        except Exception as e:
            print(f"VoiceTranscriptionHandler: Failed to transcribe audio - {e}")
            return None
