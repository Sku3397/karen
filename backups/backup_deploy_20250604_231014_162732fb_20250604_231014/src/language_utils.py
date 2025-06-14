# Multi-language response generator using Google Translate
from google.cloud import translate_v2 as translate

def generate_multilang_response(text, target_lang):
    client = translate.Client()
    result = client.translate(text, target_language=target_lang)
    return result['translatedText']
