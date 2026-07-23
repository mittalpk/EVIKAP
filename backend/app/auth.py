"""
Authentication & JWT / API key dependencies (US-008, US-010).

Provides:
- get_current_user FastAPI dependency for internal API key & JWT verification.
"""

import datetime
import hmac
import logging
import jwt
from typing import Optional, Dict, Any

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.app.config import settings

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Dict[str, Any]:
    # 1. Allow internal service-to-service calls via X-Internal-API-Key
    internal_key = request.headers.get("X-Internal-API-Key")
    expected_key = settings.internal_api_key.get_secret_value()

    if internal_key:
        if hmac.compare_digest(internal_key, expected_key):
            return {"sub": "internal-agent", "internal": True}
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid internal API key"
        )

    # 2. Otherwise expect a valid JWT
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.secret_key.get_secret_value(), algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
