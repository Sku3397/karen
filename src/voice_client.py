# VoiceClient: Handles GCP Speech-to-Text and Text-to-Speech
from google.cloud import speech, texttospeech
import os

class VoiceClient:
    def __init__(self, gcp_credentials_json):
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = gcp_credentials_json
        self.speech_client = speech.SpeechClient()
        self.tts_client = texttospeech.TextToSpeechClient()

    def transcribe(self, audio_file_path, language_code="en-US"):
        with open(audio_file_path, 'rb') as audio_file:
            content = audio_file.read()
        audio = speech.RecognitionAudio(content=content)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            language_code=language_code
        )
        response = self.speech_client.recognize(config=config, audio=audio)
        return ' '.join([result.alternatives[0].transcript for result in response.results])

    def synthesize(self, text, output_audio_file, language_code="en-US"):
        synthesis_input = texttospeech.SynthesisInput(text=text)
        voice = texttospeech.VoiceSelectionParams(
            language_code=language_code,
            ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.LINEAR16
        )
        response = self.tts_client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )
        with open(output_audio_file, 'wb') as out:
            out.write(response.audio_content)
        return output_audio_file
