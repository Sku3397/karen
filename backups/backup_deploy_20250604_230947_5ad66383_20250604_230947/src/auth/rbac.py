# Simple RBAC Implementation
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from src.auth.jwt_handler import verify_jwt_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

ROLES_PERMISSIONS = {
    "admin": ["create_task", "assign_task", "view_user", "manage_users"],
    "user": ["create_task", "view_task", "update_profile"],
    "guest": ["view_task"]
}

def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = verify_jwt_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return payload

def require_permission(permission: str):
    def decorator(user=Depends(get_current_user)):
        role = user.get("role", "guest")
        if permission not in ROLES_PERMISSIONS.get(role, []):
            raise HTTPException(403, f"Permission '{permission}' required.")
        return user
    return decorator
