# TranscriptionService: Handles audio transcription using Google Speech-to-Text
from google.cloud import speech_v1p1beta1 as speech

class TranscriptionService:
    def __init__(self, gcloud_creds):
        self.client = speech.SpeechClient(credentials=gcloud_creds)

    def transcribe(self, audio_url, lang_code='en-US'):
        audio = speech.RecognitionAudio(uri=audio_url)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            language_code=lang_code
        )
        response = self.client.recognize(config=config, audio=audio)
        transcript = " ".join([result.alternatives[0].transcript for result in response.results])
        return transcript
