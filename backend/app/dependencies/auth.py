"""
Authentication dependency for FastAPI routes.

This module provides a reusable dependency that:
1. Extracts the JWT token from the Authorization header
2. Verifies its signature using our Supabase JWT secret
3. Returns the authenticated user's ID and email
4. Automatically raises a 401 error if the token is missing/invalid

Usage in any route:
    @app.get("/protected-endpoint")
    async def my_route(current_user: dict = Depends(get_current_user)):
        user_id = current_user["user_id"]
        ...
"""

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.config import SUPABASE_JWT_SECRET

# HTTPBearer automatically extracts the token from the
# "Authorization: Bearer <token>" header for us.
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    Dependency that validates the JWT token and returns user info.

    Raises:
        HTTPException 401 if token is missing, invalid, or expired.
    """
    token = credentials.credentials

    try:
        # Decode and verify the token's signature using our secret.
        # audience="authenticated" is required because Supabase
        # issues tokens with this specific audience claim.
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated",
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired. Please log in again.",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
        )

    # 'sub' (subject) claim contains the user's unique ID in Supabase
    user_id = payload.get("sub")
    email = payload.get("email")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing user information.",
        )

    return {"user_id": user_id, "email": email}