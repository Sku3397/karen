# Google Cloud KMS Integration Stub
from google.cloud import kms
import os

PROJECT_ID = os.environ.get("GCP_PROJECT_ID")
LOCATION_ID = os.environ.get("KMS_LOCATION", "global")
KEY_RING_ID = os.environ.get("KMS_KEY_RING_ID")
CRYPTO_KEY_ID = os.environ.get("KMS_CRYPTO_KEY_ID")

client = kms.KeyManagementServiceClient()

# Example: Encrypt a plaintext using Cloud KMS.
def encrypt_symmetric(plaintext: str) -> bytes:
    key_name = client.crypto_key_path(PROJECT_ID, LOCATION_ID, KEY_RING_ID, CRYPTO_KEY_ID)
    response = client.encrypt(request={"name": key_name, "plaintext": plaintext.encode()})
    return response.ciphertext

# Example: Decrypt ciphertext using Cloud KMS.
def decrypt_symmetric(ciphertext: bytes) -> str:
    key_name = client.crypto_key_path(PROJECT_ID, LOCATION_ID, KEY_RING_ID, CRYPTO_KEY_ID)
    response = client.decrypt(request={"name": key_name, "ciphertext": ciphertext})
    return response.plaintext.decode()
