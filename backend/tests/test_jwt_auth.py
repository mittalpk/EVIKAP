"""
Test suite for US-017 JWT Authentication & Multi-User Token Flow (NFR-002, FR-006, FR-008).
Tests:
- Token generation with claims (sub, role, roles, iat, exp).
- Password hashing (PBKDF2-HMAC-SHA256) and verification.
- token_endpoint (success, wrong credentials 401, disabled account 403).
- Expired token 401 and tampered token 401 enforcement.
- Admin-guarded register_user_endpoint.
"""

import datetime
import pytest
import pytest_asyncio
import jwt
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.app.config import settings
from backend.app.models import Base, User
from backend.app.auth import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from backend.app.routers.auth import (
    LoginRequest,
    RoleAssignRequest,
    UserRegisterRequest,
    register_user_endpoint,
    token_endpoint,
)
from backend.app.services.rbac_service import seed_bootstrap_roles_and_admin


@pytest_asyncio.fixture
async def jwt_test_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


def test_hash_and_verify_password():
    raw_pass = "SecurePass123!"
    hashed = hash_password(raw_pass)

    assert hashed.startswith("pbkdf2_sha256$")
    assert verify_password(raw_pass, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


def test_create_and_decode_access_token():
    token = create_access_token(identity="alice@example.com", role="user", roles=["user"])
    assert isinstance(token, str)

    payload = jwt.decode(token, settings.secret_key.get_secret_value(), algorithms=["HS256"])
    assert payload["sub"] == "alice@example.com"
    assert payload["role"] == "user"
    assert "iat" in payload
    assert "exp" in payload


@pytest.mark.asyncio
async def test_token_endpoint_success(jwt_test_session):
    await seed_bootstrap_roles_and_admin(jwt_test_session)

    # Create active user in DB
    user = User(
        id="usr-test-alice",
        username="alice",
        hashed_password=hash_password("AliceSecret123"),
        is_active=True,
    )
    jwt_test_session.add(user)
    await jwt_test_session.commit()

    resp = await token_endpoint(
        body=LoginRequest(username="alice", password="AliceSecret123"),
        session=jwt_test_session,
    )
    assert "access_token" in resp
    assert resp["token_type"] == "bearer"
    assert resp["expires_in"] == 28800


@pytest.mark.asyncio
async def test_token_endpoint_wrong_password_401(jwt_test_session):
    await seed_bootstrap_roles_and_admin(jwt_test_session)

    user = User(
        id="usr-test-bob",
        username="bob",
        hashed_password=hash_password("BobPass123"),
        is_active=True,
    )
    jwt_test_session.add(user)
    await jwt_test_session.commit()

    with pytest.raises(HTTPException) as exc:
        await token_endpoint(
            body=LoginRequest(username="bob", password="WrongBobPassword"),
            session=jwt_test_session,
        )
    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid credentials"


@pytest.mark.asyncio
async def test_token_endpoint_disabled_account_403(jwt_test_session):
    await seed_bootstrap_roles_and_admin(jwt_test_session)

    disabled_user = User(
        id="usr-disabled-1",
        username="disabled_user",
        hashed_password=hash_password("Pass123!"),
        is_active=False,
    )
    jwt_test_session.add(disabled_user)
    await jwt_test_session.commit()

    with pytest.raises(HTTPException) as exc:
        await token_endpoint(
            body=LoginRequest(username="disabled_user", password="Pass123!"),
            session=jwt_test_session,
        )
    assert exc.value.status_code == 403
    assert exc.value.detail == "Account disabled"


@pytest.mark.asyncio
async def test_expired_token_returns_401():
    expired_token = create_access_token("expired_user", expires_delta_seconds=-10)

    class DummyCredentials:
        credentials = expired_token

    class DummyRequest:
        headers = {}

    with pytest.raises(HTTPException) as exc:
        await get_current_user(request=DummyRequest(), credentials=DummyCredentials())
    assert exc.value.status_code == 401
    assert exc.value.detail == "Token expired"


@pytest.mark.asyncio
async def test_tampered_token_returns_401():
    tampered_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalidpayload.invalidsignature"

    class DummyCredentials:
        credentials = tampered_token

    class DummyRequest:
        headers = {}

    with pytest.raises(HTTPException) as exc:
        await get_current_user(request=DummyRequest(), credentials=DummyCredentials())
    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid token"


@pytest.mark.asyncio
async def test_register_user_endpoint(jwt_test_session):
    await seed_bootstrap_roles_and_admin(jwt_test_session)

    resp = await register_user_endpoint(
        body=UserRegisterRequest(username="new_user_1", password="NewUserPass123!", role_id="user"),
        admin_identity="admin",
        session=jwt_test_session,
    )
    assert resp["status"] == "success"
    assert resp["username"] == "new_user_1"
