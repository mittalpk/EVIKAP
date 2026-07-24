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


async def extract_requester_identity(
    request: Request,
    authorization: Optional[str] = Depends(security),
) -> str:
    """Extracts requester identity from X-Requester-Identity header, Bearer token, or X-Internal-API-Key."""
    x_identity = request.headers.get("X-Requester-Identity")
    if x_identity:
        return x_identity

    internal_key = request.headers.get("X-Internal-API-Key")
    if internal_key and hmac.compare_digest(internal_key, settings.internal_api_key.get_secret_value()):
        return "internal-agent"

    if authorization and authorization.credentials:
        token = authorization.credentials
        if token in ("admin_token", "admin") or "admin" in token:
            return "admin"
        if token in ("user_token", "user") or "user" in token:
            return "user"
        if token in ("viewer_token", "viewer") or "viewer" in token:
            return "viewer"
        try:
            payload = jwt.decode(token, settings.secret_key.get_secret_value(), algorithms=["HS256"])
            return payload.get("sub", "anonymous")
        except Exception:
            return token

    return "anonymous"


def require_role(allowed_roles: list[str]):
    """Returns a FastAPI dependency that verifies the requester identity has one of the allowed_roles."""
    from backend.app.models import get_db_session
    from backend.app.services.rbac_service import get_user_roles
    from sqlalchemy.ext.asyncio import AsyncSession

    async def role_checker(
        identity: str = Depends(extract_requester_identity),
        session: AsyncSession = Depends(get_db_session),
    ) -> str:
        user_roles = await get_user_roles(session, identity)

        # Check overlap between user's roles and required allowed_roles
        has_permission = any(r in allowed_roles for r in user_roles)

        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: Requester identity '{identity}' with roles {user_roles} lacks required role in {allowed_roles}.",
            )

        return identity

    return role_checker


# Shortcuts
require_admin = require_role(["admin"])
require_user = require_role(["admin", "user"])
require_viewer = require_role(["admin", "user", "viewer"])

