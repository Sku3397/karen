# Google Secret Manager Integration
from google.cloud import secretmanager
import os

PROJECT_ID = os.environ.get("GCP_PROJECT_ID")

client = secretmanager.SecretManagerServiceClient()

def access_secret(secret_id: str, version_id: str = "latest") -> str:
    name = f"projects/{PROJECT_ID}/secrets/{secret_id}/versions/{version_id}"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode('UTF-8')
