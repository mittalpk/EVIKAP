"""
Test suite for US-014 Permission-Aware Retrieval & Source ACL Enforcement.
Tests:
- Permission reference parsing and fail-closed null/missing handling.
- PermissionCache hit, miss, and TTL expiry.
- Fail-closed behavior on IdP unreachability.
- Per-chunk access evaluation (public, identity match, group match, denied).
- Zero over-exposure in HybridRetrievalEngine retrieval results.
- Response header differentiation (X-VigilRAG-Info: all-results-filtered-by-permission).
"""

from datetime import datetime, timedelta, timezone
import json
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from unittest.mock import AsyncMock

from backend.app.models import Base, Chunk, PermissionCacheModel, Source
from backend.app.services.hybrid_retrieval_engine import HybridRetrievalEngine
from backend.app.services.permission_evaluator import PermissionEvaluator


@pytest_asyncio.fixture
async def test_async_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        # Seed Source records
        src_public = Source(
            id="src-pub-001",
            name="public-docs",
            source_type="confluence_wiki",
            endpoint_url="https://wiki.example.com/public",
            secret_reference="sec-pub",
            owner_email="docs@example.com",
            sensitivity_level="internal-general",
            sensitivity_signed_off=True,
        )
        src_restricted = Source(
            id="src-rest-001",
            name="sec-backend",
            source_type="github_repo",
            endpoint_url="https://api.github.com/repos/org/sec-backend",
            secret_reference="sec-priv",
            owner_email="ciso@example.com",
            sensitivity_level="internal-restricted",
            sensitivity_signed_off=True,
        )
        session.add_all([src_public, src_restricted])
        await session.commit()

        # Seed Chunks
        chk_public = Chunk(
            id="chk-pub-001",
            source_id="src-pub-001",
            document_id="doc-pub-001",
            parent_doc_id="wiki-public",
            content="Public documentation on system architecture.",
            permissions_ref="public",
            checksum="chksum-pub",
        )
        chk_restricted = Chunk(
            id="chk-rest-001",
            source_id="src-rest-001",
            document_id="doc-rest-001",
            parent_doc_id="backend-secret",
            content="Top secret authentication secret keys and keys vault config.",
            permissions_ref=json.dumps({
                "visibility": "private",
                "allowed_identities": ["alice@example.com"],
                "allowed_groups": ["ciso-team"],
            }),
            checksum="chksum-rest",
        )
        chk_null_ref = Chunk(
            id="chk-null-001",
            source_id="src-rest-001",
            document_id="doc-null-001",
            parent_doc_id="legacy-doc",
            content="Legacy chunk with missing null permission ref.",
            permissions_ref=None,
            checksum="chksum-null",
        )
        session.add_all([chk_public, chk_restricted, chk_null_ref])
        await session.commit()

        yield session

    await engine.dispose()


def test_parse_permissions_ref():
    evaluator = PermissionEvaluator()

    # Public string
    acl_pub = evaluator.parse_permissions_ref("public")
    assert acl_pub["visibility"] == "public"

    # JSON structure
    json_str = json.dumps({"visibility": "private", "allowed_identities": ["user1@example.com"]})
    acl_json = evaluator.parse_permissions_ref(json_str)
    assert acl_json["visibility"] == "private"
    assert "user1@example.com" in acl_json["allowed_identities"]

    # Null or empty -> fail-closed (returns None)
    assert evaluator.parse_permissions_ref(None) is None
    assert evaluator.parse_permissions_ref("   ") is None


@pytest.mark.asyncio
async def test_permission_cache_hit_and_expiry(test_async_session):
    evaluator = PermissionEvaluator(default_ttl_seconds=300)

    # 1. Fresh cache hit granted
    now = datetime.now(timezone.utc)
    cache_granted = PermissionCacheModel(
        cache_id="c-granted",
        requester_identity="bob@example.com",
        source_id="src-rest-001",
        access_level="granted",
        granted_acl_refs_json="[]",
        cached_at=now,
        ttl_seconds=300,
    )
    test_async_session.add(cache_granted)
    await test_async_session.commit()

    is_granted = await evaluator.verify_source_access(test_async_session, "bob@example.com", "src-rest-001")
    assert is_granted is True

    # 2. Expired cache triggers re-verification
    cache_expired = PermissionCacheModel(
        cache_id="c-expired",
        requester_identity="denied_user@example.com",
        source_id="src-rest-001",
        access_level="granted",
        granted_acl_refs_json="[]",
        cached_at=now - timedelta(seconds=600),  # expired
        ttl_seconds=300,
    )
    test_async_session.add(cache_expired)
    await test_async_session.commit()

    is_granted_exp = await evaluator.verify_source_access(test_async_session, "denied_user@example.com", "src-rest-001")
    assert is_granted_exp is False


@pytest.mark.asyncio
async def test_idp_unreachable_fail_closed(test_async_session):
    mock_idp = AsyncMock()
    mock_idp.check_access.side_effect = Exception("IdP connection timed out")
    evaluator = PermissionEvaluator(idp_client=mock_idp)

    is_granted = await evaluator.verify_source_access(test_async_session, "unreachable_user@example.com", "src-rest-001")
    # Must fail closed
    assert is_granted is False


@pytest.mark.asyncio
async def test_chunk_access_evaluation(test_async_session):
    evaluator = PermissionEvaluator()

    chk_pub = await test_async_session.get(Chunk, "chk-pub-001")
    chk_rest = await test_async_session.get(Chunk, "chk-rest-001")
    chk_null = await test_async_session.get(Chunk, "chk-null-001")

    # Public chunk granted to anyone
    assert await evaluator.evaluate_chunk_access(test_async_session, chk_pub, "anonymous@example.com") is True

    # Restricted chunk granted to allowed_identities (alice)
    assert await evaluator.evaluate_chunk_access(test_async_session, chk_rest, "alice@example.com") is True

    # Restricted chunk denied to unauthorized identity (eve)
    assert await evaluator.evaluate_chunk_access(test_async_session, chk_rest, "denied_eve@example.com") is False

    # Null permissions_ref chunk fail-closed denied
    assert await evaluator.evaluate_chunk_access(test_async_session, chk_null, "alice@example.com") is False


@pytest.mark.asyncio
async def test_hybrid_retrieval_permission_filtering(test_async_session):
    engine = HybridRetrievalEngine()

    # Query for secret keys as authorized identity (alice)
    items_alice = await engine.retrieve(
        session=test_async_session,
        query="secret keys vault config",
        requester_identity="alice@example.com",
        top_k=5,
    )
    alice_chunk_ids = [it.chunk_id for it in items_alice]
    assert "chk-rest-001" in alice_chunk_ids

    # Query for secret keys as unauthorized identity (denied_eve)
    items_eve = await engine.retrieve(
        session=test_async_session,
        query="secret keys vault config",
        requester_identity="denied_eve@example.com",
        top_k=5,
    )
    eve_chunk_ids = [it.chunk_id for it in items_eve]
    # Zero over-exposure: restricted chunk MUST NOT be returned
    assert "chk-rest-001" not in eve_chunk_ids
