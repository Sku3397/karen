from google.cloud import speech
from typing import Optional
import io
import os
from google.oauth2 import service_account

class VoiceTranscriptionHandler:
    def __init__(self, language_code: str = 'en-US'):
        # Use the same service account credentials as configured for Firebase
        credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if credentials_path and os.path.exists(credentials_path):
            credentials = service_account.Credentials.from_service_account_file(credentials_path)
            self.client = speech.SpeechClient(credentials=credentials)
        else:
            # Fallback to default (this will still fail if ADC not set up, but we log it)
            print("Warning: GOOGLE_APPLICATION_CREDENTIALS not found, using default credentials for Speech API")
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
