from fastapi import APIRouter, HTTPException, Body, Depends
from pydantic import BaseModel
import jwt
import datetime
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from ..config import settings
from ..models import get_db_session
from ..auth import require_admin, require_user

from ..services.rbac_service import assign_user_role, get_user_roles

router = APIRouter()

class LoginRequest(BaseModel):
    username: str
    password: str

class RoleAssignRequest(BaseModel):
    target_username: str
    role_id: str

import logging
logger = logging.getLogger(__name__)

from sqlalchemy import select
from ..models import User
from ..auth import create_access_token, verify_password, hash_password, JWT_TTL_SECONDS

class UserRegisterRequest(BaseModel):
    username: str
    password: str
    role_id: Optional[str] = "user"


@router.post("/login")
@router.post("/token")
async def token_endpoint(
    body: LoginRequest = Body(...),
    session: AsyncSession = Depends(get_db_session),
):
    """Multi-user JWT authentication endpoint (US-017)."""
    username = body.username.strip().lower()

    # 1. Lookup DB User
    db_user = None
    try:
        stmt = select(User).where(User.username == username)
        res = await session.execute(stmt)
        db_user = res.scalar_one_or_none()
    except Exception as exc:
        logger.debug(f"DB User lookup skipped/failed: {exc}")

    authenticated = False

    if db_user:
        if not db_user.is_active:
            logger.warning(f"Login attempt for disabled account '{username}'")
            raise HTTPException(status_code=403, detail="Account disabled")
        authenticated = verify_password(body.password, db_user.hashed_password)
    else:
        # Fallback check for config admin credentials
        if body.username == settings.admin_username and body.password == settings.admin_password.get_secret_value():
            authenticated = True


    if not authenticated:
        logger.warning(f"Authentication failed for username='{body.username}'")
        raise HTTPException(status_code=401, detail="Invalid credentials")

    roles = await get_user_roles(session, username)
    primary_role = roles[0] if roles else "user"

    access_token = create_access_token(
        identity=username,
        role=primary_role,
        roles=roles,
        expires_delta_seconds=JWT_TTL_SECONDS,
    )

    return {
        "access_token": access_token,
        "token": access_token,
        "token_type": "bearer",
        "expires_in": JWT_TTL_SECONDS,
        "role": primary_role,
        "roles": roles,
    }


@router.post("/register")
async def register_user_endpoint(
    body: UserRegisterRequest = Body(...),
    admin_identity: str = Depends(require_admin),
    session: AsyncSession = Depends(get_db_session),
):
    """Admin-only endpoint to register a new user account (US-017)."""
    username = body.username.strip().lower()

    stmt = select(User).where(User.username == username)
    res = await session.execute(stmt)
    if res.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username already exists")

    import uuid
    new_user = User(
        id=f"usr-{uuid.uuid4().hex[:10]}",
        username=username,
        hashed_password=hash_password(body.password),
        is_active=True,
    )
    session.add(new_user)
    await session.commit()

    if body.role_id:
        await assign_user_role(session, username, body.role_id, assigned_by=admin_identity)

    return {"status": "success", "username": username, "role_id": body.role_id}



@router.post("/roles/assign")
async def assign_role_endpoint(
    body: RoleAssignRequest = Body(...),
    admin_identity: str = Depends(require_admin),
    session: AsyncSession = Depends(get_db_session),
):
    """Admin-only endpoint to assign roles to users (US-016)."""
    try:
        success = await assign_user_role(
            session=session,
            target_username=body.target_username,
            role_id=body.role_id,
            assigned_by=admin_identity,
        )
        return {
            "status": "success",
            "target_username": body.target_username,
            "role_id": body.role_id,
            "assigned_by": admin_identity,
        }
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))



