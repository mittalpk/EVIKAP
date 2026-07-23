"""
Test suite for US-007 Wiki Source Connector & Embedding Ingestion Pipeline.
Tests:
- Shared ingestion utilities (HTML stripping, chunking, checksum).
- Parsing wiki cross-page link references.
- Confluence REST API ingestion & local Markdown fallback ingestion.
- Database persistence of `Chunk` records with Graph-Ready metadata.
Uses workspace-root imports: `from backend.app.services.wiki_connector import ...`
"""

import json
import os
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from unittest.mock import MagicMock, patch

from backend.app.models import Base, Chunk, Source
from backend.app.services.ingestion_utils import chunk_text, compute_checksum, strip_html_to_text
from backend.app.services.wiki_connector import WikiIngestionConnector, WikiIngestionSummary


@pytest_asyncio.fixture
async def test_async_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        # Seed Source record for Wiki
        src = Source(
            id="src-wiki-001",
            name="Engineering Architecture Wiki",
            source_type="confluence_wiki",
            endpoint_url="https://wiki.example.com/rest/api/content",
            secret_reference="kv-wiki-token",
            owner_email="archboard@example.com",
            sensitivity_level="internal-general",
            sensitivity_signed_off=True,
        )
        session.add(src)
        await session.commit()
        yield session

    await engine.dispose()


def test_html_stripping_utility():
    html = """
    <html>
        <head><style>body { color: red; }</style></head>
        <body>
            <nav>Navigation links</nav>
            <h1>Microservice Auth Policy</h1>
            <p>All inter-service calls must use <strong>gRPC mTLS</strong>.</p>
        </body>
    </html>
    """
    clean_text = strip_html_to_text(html)
    assert "Navigation links" not in clean_text
    assert "Microservice Auth Policy" in clean_text
    assert "gRPC mTLS" in clean_text


def test_wiki_cross_page_reference_parsing():
    connector = WikiIngestionConnector()
    text = """
    Please review [Frontend Security Baseline](wiki:ENG/Frontend-Security) and 
    [Database Rollback Runbook](/display/ENG/DB-Rollback-Runbook).
    Also see [architecture.md](architecture.md).
    """
    refs = connector.parse_cross_page_references(text)
    assert "ENG/Frontend-Security" in refs or "architecture.md" in refs


@pytest.mark.asyncio
async def test_successful_wiki_confluence_ingestion(test_async_session):
    connector = WikiIngestionConnector(wiki_token="valid_token")

    src_res = await test_async_session.get(Source, "src-wiki-001")
    assert src_res is not None

    mock_pages = [
        {
            "page_id": "1001",
            "title": "Microservice Auth Policy",
            "html_body": "<h2>Auth Policy</h2><p>Use JWT Bearer tokens.</p> Check [Security Baseline](security-baseline.md).",
            "parent_doc_id": "wiki-page-space-ENG",
        },
        {
            "page_id": "1002",
            "title": "Empty Attachment Page",
            "html_body": "  ",  # empty page
            "parent_doc_id": "wiki-page-1001",
        },
    ]

    summary = await connector.run_ingestion(test_async_session, src_res, mock_pages=mock_pages)

    assert summary.pages_fetched == 2
    assert summary.chunks_created == 1
    assert summary.empty_pages_skipped == 1
    assert summary.mode == "mock_test"

    # Verify Chunk stored in DB
    res = await test_async_session.execute(Base.metadata.tables["chunks"].select())
    rows = res.fetchall()
    assert len(rows) == 1

    chunk_row = rows[0]
    assert chunk_row.parent_doc_id == "wiki-page-space-ENG"
    assert "group-eng-staff" in chunk_row.permissions_ref



@pytest.mark.asyncio
async def test_wiki_local_markdown_fallback(test_async_session, tmp_path):
    # Create temporary local markdown folder
    wiki_dir = tmp_path / "demo_wiki"
    wiki_dir.mkdir()
    md_file = wiki_dir / "guide.md"
    md_file.write_text("# KeyVault Guide\nRequest access via IT portal [Portal Link](wiki:IT/Portal).", encoding="utf-8")

    connector = WikiIngestionConnector(wiki_token=None)  # No token triggers fallback
    src_res = await test_async_session.get(Source, "src-wiki-001")

    summary = await connector.run_ingestion(
        test_async_session,
        src_res,
        local_markdown_folder=str(wiki_dir),
    )

    assert summary.mode == "local_markdown_fallback"
    assert summary.pages_fetched == 1
    assert summary.chunks_created == 1

    # Verify Chunk stored
    res = await test_async_session.execute(Base.metadata.tables["chunks"].select())
    rows = res.fetchall()
    assert len(rows) == 1
    assert "KeyVault Guide" in rows[0].content
