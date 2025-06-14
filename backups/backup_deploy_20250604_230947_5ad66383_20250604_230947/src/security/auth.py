from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from src.schemas.user import User

# For demonstration purposes only
SECRET_KEY = "secretkey"
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

# Dummy user for demonstration
DEMO_USER = {
    "email": "demo@ai.com",
    "profile": {},
    "preferences": {},
    "permissions": ["user"]
}

def get_current_user(token: str = Depends(oauth2_scheme)):
    # For demonstration, accept any token and return DEMO_USER
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return User(**DEMO_USER)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
