"""
Authentication dependency for FastAPI routes.

This module verifies Supabase-issued JWT tokens using ES256
(asymmetric signing) via Supabase's public JWKS endpoint,
rather than a shared secret. This matches Supabase's current
default security model for new projects.
"""

import jwt
from jwt import PyJWKClient
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.config import SUPABASE_URL

security = HTTPBearer()

# Supabase publishes its public signing keys at this well-known URL.
# PyJWKClient automatically fetches and caches these keys, and
# refreshes them if a token references a key it doesn't have yet.
JWKS_URL = f"{SUPABASE_URL}/auth/v1/.well-known/jwks.json"
jwks_client = PyJWKClient(JWKS_URL)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    Dependency that validates the JWT token (ES256) and returns
    user info extracted from its payload.
    """
    token = credentials.credentials

    try:
        # Look up the specific public key that matches this token's
        # 'kid' (key ID), then use it to verify the signature.
        signing_key = jwks_client.get_signing_key_from_jwt(token)

        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["ES256"],
            audience="authenticated",
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired. Please log in again.",
        )
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {str(e)}",
        )

    user_id = payload.get("sub")
    email = payload.get("email")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing user information.",
        )

    return {"user_id": user_id, "email": email}