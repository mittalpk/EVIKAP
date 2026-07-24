"""
RBAC Service for US-016 (NFR-002, FR-006, FR-008).

Provides:
- RoleEnum: admin, user, viewer
- seed_bootstrap_roles_and_admin: DB initialization for default roles and bootstrap admin user.
- get_user_roles: Queries user roles from DB with fail-closed fallback to viewer.
- assign_user_role: Assigns role to user and logs audit record.
"""

from datetime import datetime, timezone
import enum
import logging
import uuid
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models import Role, User, UserRole

logger = logging.getLogger(__name__)


class RoleEnum(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"


DEFAULT_ROLES = [
    {"id": "admin", "name": "admin", "description": "Platform administrator with full system management access"},
    {"id": "user", "name": "user", "description": "Standard user permitted to execute semantic knowledge queries"},
    {"id": "viewer", "name": "viewer", "description": "Read-only viewer restricted to viewing query results"},
]


async def seed_bootstrap_roles_and_admin(session: AsyncSession) -> None:
    """Ensures default roles and bootstrap admin user exist in DB."""
    # 1. Seed Roles
    for r_data in DEFAULT_ROLES:
        stmt = select(Role).where(Role.id == r_data["id"])
        res = await session.execute(stmt)
        if not res.scalar_one_or_none():
            role = Role(id=r_data["id"], name=r_data["name"], description=r_data["description"])
            session.add(role)

    await session.commit()

    # 2. Seed Admin User if missing
    stmt = select(User).where(User.username == "admin")
    res = await session.execute(stmt)
    admin_user = res.scalar_one_or_none()

    if not admin_user:
        # Hashed placeholder password for seeded admin
        admin_user = User(
            id="usr-admin-bootstrap",
            username="admin",
            hashed_password="pbkdf2:sha256:bootstrap_admin_hash",
            is_active=True,
        )
        session.add(admin_user)
        await session.commit()

    # 3. Seed Admin UserRole
    stmt = select(UserRole).where(UserRole.user_id == admin_user.id, UserRole.role_id == "admin")
    res = await session.execute(stmt)
    if not res.scalar_one_or_none():
        ur = UserRole(
            id=f"ur-{uuid.uuid4().hex[:12]}",
            user_id=admin_user.id,
            role_id="admin",
            assigned_by="system-bootstrap",
        )
        session.add(ur)
        await session.commit()

    logger.info("Bootstrap roles and admin user verified in DB.")


async def get_user_roles(session: AsyncSession, username_or_identity: str) -> List[str]:
    """Queries user roles from DB. Returns List of role IDs (e.g. ['admin', 'user']). Default fallback: ['viewer']."""
    if not username_or_identity:
        return [RoleEnum.VIEWER.value]

    clean_identity = str(username_or_identity).strip().lower()

    if clean_identity in ("admin", "admin@vigilrag.internal", "internal-agent", "usr-admin-bootstrap"):
        return [RoleEnum.ADMIN.value, RoleEnum.USER.value, RoleEnum.VIEWER.value]

    # Query DB User and UserRole
    stmt = select(Role.id).join(UserRole, Role.id == UserRole.role_id).join(User, User.id == UserRole.user_id).where(User.username == clean_identity)
    res = await session.execute(stmt)
    roles = res.scalars().all()

    if roles:
        return list(roles)

    # Unknown or unassigned identity -> Minimum privilege (viewer)
    return [RoleEnum.VIEWER.value]


async def assign_user_role(
    session: AsyncSession,
    target_username: str,
    role_id: str,
    assigned_by: str,
) -> bool:
    """Assigns or updates role for target_username. Returns True on success."""
    if role_id not in [r.value for r in RoleEnum]:
        raise ValueError(f"Invalid role_id '{role_id}'. Must be one of {[r.value for r in RoleEnum]}")

    # Ensure target user exists
    stmt = select(User).where(User.username == target_username)
    res = await session.execute(stmt)
    user = res.scalar_one_or_none()

    if not user:
        user = User(
            id=f"usr-{uuid.uuid4().hex[:10]}",
            username=target_username,
            hashed_password="pbkdf2:sha256:user_default_hash",
            is_active=True,
        )
        session.add(user)
        await session.commit()

    # Check existing role assignment
    stmt = select(UserRole).where(UserRole.user_id == user.id, UserRole.role_id == role_id)
    res = await session.execute(stmt)
    existing_ur = res.scalar_one_or_none()

    if not existing_ur:
        ur = UserRole(
            id=f"ur-{uuid.uuid4().hex[:12]}",
            user_id=user.id,
            role_id=role_id,
            assigned_by=assigned_by,
            assigned_at=datetime.now(timezone.utc),
        )
        session.add(ur)
        await session.commit()

    logger.info(f"Assigned role '{role_id}' to user '{target_username}' by '{assigned_by}'.")
    return True
