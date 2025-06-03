import sys
print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")
print(f"sys.path: {sys.path}")
try:
    from google.cloud import speech
    print("Successfully imported google.cloud.speech")
    print(f"Speech client: {speech.SpeechClient}")
except ImportError as e:
    print(f"Failed to import google.cloud.speech: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")

# Also check firebase_admin as it was an issue before
try:
    import firebase_admin
    print("Successfully imported firebase_admin")
except ImportError as e:
    print(f"Failed to import firebase_admin: {e}") 