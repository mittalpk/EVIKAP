"""
Test suite for US-016 RBAC Foundation (NFR-002, FR-006, FR-008).
Tests:
- Database roles and user_roles models.
- Bootstrap roles and admin seeding logic.
- get_user_roles and assign_user_role functions.
- require_role FastAPI dependency enforcement (admin, user, viewer permissions).
- POST /api/v1/auth/roles/assign endpoint authorization.
"""

import pytest
import pytest_asyncio
from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.app.main import app
from backend.app.models import Base, Role, User, UserRole
from backend.app.auth import require_admin, require_role, require_user

from backend.app.services.rbac_service import (
    RoleEnum,
    assign_user_role,
    get_user_roles,
    seed_bootstrap_roles_and_admin,
)


@pytest_asyncio.fixture
async def rbac_test_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_seed_bootstrap_roles_and_admin(rbac_test_session):
    await seed_bootstrap_roles_and_admin(rbac_test_session)

    # Verify 3 roles created
    roles_res = await rbac_test_session.execute(select(Role))
    roles = roles_res.scalars().all()
    assert len(roles) >= 3
    role_names = [r.name for r in roles]
    assert "admin" in role_names
    assert "user" in role_names
    assert "viewer" in role_names

    # Verify admin user created
    user_res = await rbac_test_session.execute(select(User).where(User.username == "admin"))
    admin = user_res.scalar_one_or_none()
    assert admin is not None

    # Verify admin UserRole assigned
    ur_res = await rbac_test_session.execute(select(UserRole).where(UserRole.user_id == admin.id))
    urs = ur_res.scalars().all()
    assert len(urs) == 1
    assert urs[0].role_id == "admin"


@pytest.mark.asyncio
async def test_get_user_roles_fallback(rbac_test_session):
    await seed_bootstrap_roles_and_admin(rbac_test_session)

    # Admin returns admin roles
    admin_roles = await get_user_roles(rbac_test_session, "admin")
    assert "admin" in admin_roles

    # Unknown user returns viewer fallback (minimum privilege)
    unknown_roles = await get_user_roles(rbac_test_session, "unknown_user_123")
    assert unknown_roles == ["viewer"]


@pytest.mark.asyncio
async def test_assign_user_role(rbac_test_session):
    await seed_bootstrap_roles_and_admin(rbac_test_session)

    # Assign user role to dev1
    success = await assign_user_role(
        session=rbac_test_session,
        target_username="dev1",
        role_id="user",
        assigned_by="admin",
    )
    assert success is True

    # Check dev1 roles
    dev_roles = await get_user_roles(rbac_test_session, "dev1")
    assert "user" in dev_roles

    # Test invalid role name
    with pytest.raises(ValueError):
        await assign_user_role(rbac_test_session, "dev1", "invalid_role", "admin")


@pytest.mark.asyncio
async def test_require_role_dependency_enforcement(rbac_test_session):
    await seed_bootstrap_roles_and_admin(rbac_test_session)

    admin_checker = require_role(["admin"])

    # Admin identity -> PASS
    res = await admin_checker(identity="admin", session=rbac_test_session)
    assert res == "admin"

    # Viewer identity -> 403 Forbidden
    with pytest.raises(HTTPException) as exc_info:
        await admin_checker(identity="viewer", session=rbac_test_session)
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_roles_assign_endpoint_rbac():
    from backend.app.models import init_db
    await init_db()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        # 1. Admin identity -> 200 OK
        resp = await client.post(
            "/api/v1/auth/roles/assign",
            json={"target_username": "bob", "role_id": "user"},
            headers={"X-Requester-Identity": "admin"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

        # 2. Viewer identity -> 403 Forbidden
        resp_forbidden = await client.post(
            "/api/v1/auth/roles/assign",
            json={"target_username": "charlie", "role_id": "admin"},
            headers={"X-Requester-Identity": "viewer_user"},
        )
        assert resp_forbidden.status_code == 403

