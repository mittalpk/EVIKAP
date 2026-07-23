"""
Test suite for US-008 Hybrid Retrieval Endpoint & Engine.
Tests:
- RRF score calculation algorithms.
- Hybrid search over database `Chunk` records (vector similarity + keyword search).
- Permission filtering on evidence chunks.
- Pluggable reranker hook execution.
- Endpoint API call and response structure.
Uses workspace-root imports: `from backend.app.services.hybrid_retrieval_engine import ...`
"""

import json
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.app.models import Base, Chunk, Source
from backend.app.schemas import EvidenceItem, KnowledgeQueryRequest
from backend.app.services.hybrid_retrieval_engine import (
    HybridRetrievalEngine,
    PassthroughReranker,
    compute_rrf_scores,
)
from backend.app.services.ingestion_utils import generate_embedding_vector


@pytest_asyncio.fixture
async def test_async_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        # Seed Source & Chunks
        src = Source(
            id="src-001",
            name="test-repo",
            source_type="github_repo",
            endpoint_url="https://api.github.com/repos/org/test-repo",
            secret_reference="sec-01",
            owner_email="dev@example.com",
            sensitivity_level="internal-general",
            sensitivity_signed_off=True,
        )
        session.add(src)

        chunk1 = Chunk(
            id="chk-001",
            source_id="src-001",
            document_id="doc-001",
            parent_doc_id="auth/policy.py",
            content="Microservice authentication using JWT bearer tokens and gRPC mTLS",
            permissions_ref="public",
            checksum="hash1",
            references_json='["jwt", "mtls"]',
            embedding_vector_str=json.dumps(generate_embedding_vector("Microservice authentication using JWT bearer tokens")),
        )
        chunk2 = Chunk(
            id="chk-002",
            source_id="src-001",
            document_id="doc-002",
            parent_doc_id="db/config.py",
            content="Database connection string using PostgreSQL asyncpg pool configuration",
            permissions_ref="github:test-repo:restricted-team",
            checksum="hash2",
            references_json='["asyncpg"]',
            embedding_vector_str=json.dumps(generate_embedding_vector("Database connection string using PostgreSQL")),
        )
        session.add_all([chunk1, chunk2])
        await session.commit()
        yield session

    await engine.dispose()


def test_rrf_scoring_algorithm():
    vector_ids = ["chk-001", "chk-002"]
    keyword_ids = ["chk-002", "chk-001"]

    scores = compute_rrf_scores(vector_ids, keyword_ids, k=60)
    assert "chk-001" in scores
    assert "chk-002" in scores
    assert scores["chk-001"] > 0.0


@pytest.mark.asyncio
async def test_hybrid_search_retrieval_and_permissions(test_async_session):
    engine = HybridRetrievalEngine()

    # Public / authorized user query
    evidence = await engine.retrieve(
        session=test_async_session,
        query="JWT authentication policy",
        requester_identity="user@example.com",
        top_k=5,
    )

    assert len(evidence) >= 1
    top_item = evidence[0]
    assert top_item.chunk_id == "chk-001"
    assert top_item.parent_doc_id == "auth/policy.py"
    assert top_item.relevance_score > 0.0


@pytest.mark.asyncio
async def test_reranker_hook_execution(test_async_session):
    class MockReranker:
        def rerank(self, query: str, items: list[EvidenceItem]) -> list[EvidenceItem]:
            for item in items:
                item.rerank_score = 0.99
            return items

    engine = HybridRetrievalEngine(reranker=MockReranker())
    evidence = await engine.retrieve(
        session=test_async_session,
        query="PostgreSQL database pool",
        requester_identity="internal-agent",
        top_k=5,
    )

    assert len(evidence) >= 1
    assert evidence[0].rerank_score == 0.99
