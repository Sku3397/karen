# OAuth 2.0 with Google Identity
import os
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from google.oauth2 import id_token
from google.auth.transport import requests as grequests

router = APIRouter()
GOOGLE_CLIENT_ID = os.environ["GOOGLE_CLIENT_ID"]
GOOGLE_CLIENT_SECRET = os.environ["GOOGLE_CLIENT_SECRET"]
GOOGLE_REDIRECT_URI = os.environ["GOOGLE_REDIRECT_URI"]

GOOGLE_AUTH_URL = (
    "https://accounts.google.com/o/oauth2/v2/auth"
    "?response_type=code"
    f"&client_id={GOOGLE_CLIENT_ID}"
    f"&redirect_uri={GOOGLE_REDIRECT_URI}"
    "&scope=openid%20email%20profile"
)

@router.get("/login/google")
def login_google():
    return RedirectResponse(GOOGLE_AUTH_URL)

@router.get("/auth/google/callback")
def google_callback(request: Request):
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(400, "Missing code from Google OAuth.")
    # Exchange code for tokens
    import requests
    token_resp = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code"
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    token_data = token_resp.json()
    if "id_token" not in token_data:
        raise HTTPException(401, "Failed to authenticate with Google.")
    # Verify ID token
    try:
        idinfo = id_token.verify_oauth2_token(
            token_data["id_token"], grequests.Request(), GOOGLE_CLIENT_ID
        )
    except Exception as e:
        raise HTTPException(401, f"Invalid ID token: {str(e)}")
    # Here, create user in DB if not exists, then issue our own JWT
    from src.auth.jwt_handler import create_jwt_token
    user_jwt = create_jwt_token(idinfo)
    return {"access_token": user_jwt}
