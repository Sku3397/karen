# Role-based Authorization Middleware
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from src.auth.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

ROLES = ["admin", "agent", "client"]


def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    if 'role' not in payload or payload['role'] not in ROLES:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid role")
    return payload

def require_role(required_roles: list):
    def role_checker(user = Depends(get_current_user)):
        if user['role'] not in required_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return user
    return role_checker
