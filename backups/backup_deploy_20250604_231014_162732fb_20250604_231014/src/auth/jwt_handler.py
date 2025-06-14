import jwt

def generate_token(payload, secret, algorithm='HS256'):
    return jwt.encode(payload, secret, algorithm=algorithm)

def decode_token(token, secret, algorithms=['HS256']):
    return jwt.decode(token, secret, algorithms=algorithms)