# Authentication & Security Framework

## OAuth 2.0 via Google Identity
- Initiates login via `/login/google`.
- Handles callback and exchanges code for tokens.
- Validates Google ID token, issues internal JWT.

## JWT Token Handling
- Issues JWT with user claims after Google login.
- Validates JWT on protected endpoints.
- JWT secret managed via Secret Manager.

## RBAC (Role-Based Access Control)
- Roles: admin, user, guest.
- Permissions mapped per role.
- Use `require_permission` dependency for endpoint protection.

## Google Cloud KMS & Secret Manager
- KMS: stub for symmetric encryption/decryption.
- Secret Manager: securely fetches secrets (e.g., JWT secret, OAuth credentials).

## TLS 1.3 Configuration
- Run Uvicorn with `--ssl-version=TLSv1_3` and managed certs (see env vars).
- Ensure all external communication uses HTTPS.

## Environment Variables Needed
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`
- `JWT_SECRET_KEY` (ideally loaded via Secret Manager)
- `GCP_PROJECT_ID`, `KMS_LOCATION`, `KMS_KEY_RING_ID`, `KMS_CRYPTO_KEY_ID`
- `SSL_KEYFILE`, `SSL_CERTFILE`
