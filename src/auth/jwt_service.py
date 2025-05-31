import jwt
from datetime import datetime, timedelta

class JWTService:
    def __init__(self, secret_key, algorithm='HS256'):
        self.secret_key = secret_key
        self.algorithm = algorithm

    def encode_auth_token(self, user_id):
        try:
            payload = {
                'exp': datetime.utcnow() + timedelta(days=1, seconds=5),
                'iat': datetime.utcnow(),
                'sub': user_id
            }
            return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        except Exception as e:
            return e

    def decode_auth_token(self, auth_token):
        try:
            payload = jwt.decode(auth_token, self.secret_key, algorithms=[self.algorithm])
            return payload['sub']
        except jwt.ExpiredSignatureError:
            return 'Signature expired. Please log in again.'
        except jwt.InvalidTokenError:
            return 'Invalid token. Please log in again.'