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

@router.post("/login")
async def login(
    body: LoginRequest = Body(...),
    session: AsyncSession = Depends(get_db_session),
):
    if body.username != settings.admin_username or body.password != settings.admin_password.get_secret_value():
        logger.warning(f"Login failed for username='{body.username}'")
        raise HTTPException(status_code=401, detail="Invalid credentials")

    roles = await get_user_roles(session, body.username)
    token = jwt.encode({
        "sub": body.username,
        "role": roles[0] if roles else "admin",
        "roles": roles,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }, settings.secret_key.get_secret_value(), algorithm="HS256")
    return {"token": token, "roles": roles}


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



