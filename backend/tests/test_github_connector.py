"""
Test suite for US-006 GitHub Source Connector & Embedding Ingestion Pipeline.
Tests:
- Parsing import/include code references (Graph-Ready metadata).
- Content chunking with overlap.
- End-to-end ingestion pipeline execution with database persistence.
- Handling GitHub API rate limits.
- Skipping non-text/binary files.
Uses workspace-root imports: `from backend.app.services.github_connector import ...`
"""

import json
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from unittest.mock import AsyncMock, MagicMock, patch

from backend.app.models import Base, Chunk, Source
from backend.app.services.github_connector import GitHubIngestionConnector, IngestionSummary


@pytest_asyncio.fixture
async def test_async_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        # Seed Source record
        src = Source(
            id="src-github-001",
            name="core-platform",
            source_type="github_repo",
            endpoint_url="https://api.github.com/repos/org/core-platform",
            secret_reference="kv-token",
            owner_email="lead@example.com",
            sensitivity_level="internal-sensitive",
            sensitivity_signed_off=True,
        )
        session.add(src)
        await session.commit()
        yield session

    await engine.dispose()


def test_code_reference_parsing():
    connector = GitHubIngestionConnector()

    py_code = """
import os
from sys import path
import backend.app.models
from backend.app.services.github_connector import GitHubIngestionConnector
"""
    refs_py = connector.parse_references(py_code, "backend/app/main.py")
    assert "os" in refs_py
    assert "backend.app.models" in refs_py

    js_code = """
import React from 'react';
import { useState } from "react";
const utils = require('./utils');
"""
    refs_js = connector.parse_references(js_code, "frontend/src/App.tsx")
    assert "react" in refs_js
    assert "./utils" in refs_js


def test_chunking_with_overlap():
    connector = GitHubIngestionConnector()
    text = "Line 1\nLine 2\nLine 3\nLine 4\nLine 5\nLine 6\nLine 7\nLine 8\nLine 9\nLine 10"

    chunks = connector.chunk_content(text, max_chars=30, overlap_chars=10)
    assert len(chunks) > 1
    assert all(len(c) <= 30 for c in chunks)


@pytest.mark.asyncio
async def test_successful_github_ingestion(test_async_session):
    connector = GitHubIngestionConnector()

    src_res = await test_async_session.get(Source, "src-github-001")
    assert src_res is not None

    mock_files = [
        {
            "path": "backend/app/main.py",
            "content": "import os\nfrom backend.app.models import Source\n\ndef main():\n    print('Hello VigilRAG')",
        },
        {
            "path": "docs/architecture.md",
            "content": "# Architecture\nSee [data architecture](data.md) for details.",
        },
        {
            "path": "binary_image.png",
            "content": None,  # binary file
        },
    ]

    summary = await connector.run_ingestion(test_async_session, src_res, mock_files=mock_files)

    assert summary.files_fetched == 3
    assert summary.chunks_created == 2
    assert summary.binary_files_skipped == 1
    assert len(summary.errors_encountered) == 0

    # Query DB to verify Chunk persistence
    res = await test_async_session.execute(Base.metadata.tables["chunks"].select())
    rows = res.fetchall()
    assert len(rows) == 2

    # Check Graph-Ready parent_doc_id and references
    chunk_row = [r for r in rows if "main.py" in r.parent_doc_id][0]
    assert chunk_row.parent_doc_id == "backend/app/main.py"
    assert "backend.app.models" in chunk_row.references_json
    assert chunk_row.permissions_ref == "github:core-platform:read"


@pytest.mark.asyncio
async def test_github_api_rate_limit_handling(test_async_session):
    connector = GitHubIngestionConnector()
    src_res = await test_async_session.get(Source, "src-github-001")

    mock_resp = MagicMock()
    mock_resp.status_code = 403
    mock_resp.text = "API rate limit exceeded for user."

    with patch("httpx.AsyncClient.get", return_value=mock_resp):
        summary = await connector.run_ingestion(test_async_session, src_res)

        assert summary.status == "rate_limited"
        assert summary.rate_limit_paused is True
        assert any("rate limit exceeded" in err.lower() for err in summary.errors_encountered)
