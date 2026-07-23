"""
Unit and Integration Tests for Agent Query API Router (US-011).
Tests:
- POST /api/v1/query success flow with citation assembly.
- 401 Unauthorized on missing/empty requester_identity.
- 401 Unauthorized on invalid X-Internal-API-Key header.
- Handling empty evidence response from backend Knowledge API.
- 503 Service Unavailable handling on backend error or timeout.
"""

import os
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from fastapi.testclient import TestClient

# Set up test environment variables
os.environ["INTERNAL_API_KEY"] = "secure-test-internal-api-key-9999"
os.environ["GEMINI_API_KEY"] = "fake-gemini-key"

from agent.app.main import app

client = TestClient(app)
TEST_KEY = "secure-test-internal-api-key-9999"


def test_query_endpoint_success():
    """POST /api/v1/query should call Knowledge API, assemble citations, and return 200 OK."""
    mock_kb_response = MagicMock()
    mock_kb_response.status_code = 200
    mock_kb_response.json.return_value = {
        "evidence": [
            {
                "chunk_id": "chk-101",
                "document_id": "doc-github-01",
                "source_url": "https://github.com/org/repo/blob/main/auth.py",
                "source_type": "github_repo",
                "content": "def verify_token(): return True",
            },
            {
                "chunk_id": "chk-102",
                "document_id": "doc-wiki-01",
                "source_url": "https://wiki.org/pages/security",
                "source_type": "confluence_wiki",
                "content": "All requests must provide X-Internal-API-Key.",
            },
        ],
        "total_retrieved": 2,
        "trace_id": "trc-kb-001",
    }

    mock_async_client = AsyncMock()
    mock_async_client.post.return_value = mock_kb_response

    with patch("agent.app.client.http_client.get_client", return_value=mock_async_client):
        response = client.post(
            "/api/v1/query",
            headers={"X-Internal-API-Key": TEST_KEY},
            json={
                "query": "How is authentication handled in backend?",
                "requester_identity": "alice@example.com",
                "top_k": 5,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert len(data["citations"]) == 2
        assert data["citations"][0]["chunk_id"] == "chk-101"
        assert data["citations"][0]["source_url"] == "https://github.com/org/repo/blob/main/auth.py"
        assert data["citations"][0]["source_type"] == "github_repo"
        assert "verify_token" in data["citations"][0]["content_excerpt"]
        assert data["trace_id"].startswith("trc-")
        assert isinstance(data["execution_time_ms"], int)


def test_query_endpoint_missing_identity_401():
    """POST /api/v1/query should return 401 if requester_identity is missing or blank."""
    response = client.post(
        "/api/v1/query",
        headers={"X-Internal-API-Key": TEST_KEY},
        json={
            "query": "How is authentication handled?",
            "requester_identity": "",
            "top_k": 5,
        },
    )

    assert response.status_code == 401
    assert "requester_identity is required" in response.json()["detail"]


def test_query_endpoint_invalid_internal_key_401():
    """POST /api/v1/query should return 401 if X-Internal-API-Key is invalid."""
    response = client.post(
        "/api/v1/query",
        headers={"X-Internal-API-Key": "invalid-wrong-key"},
        json={
            "query": "How is authentication handled?",
            "requester_identity": "alice@example.com",
            "top_k": 5,
        },
    )

    assert response.status_code == 401
    assert "Invalid internal API key" in response.json()["detail"]


def test_query_endpoint_empty_evidence():
    """POST /api/v1/query should handle empty evidence list gracefully."""
    mock_kb_response = MagicMock()
    mock_kb_response.status_code = 200
    mock_kb_response.json.return_value = {
        "evidence": [],
        "total_retrieved": 0,
    }

    mock_async_client = AsyncMock()
    mock_async_client.post.return_value = mock_kb_response

    with patch("agent.app.client.http_client.get_client", return_value=mock_async_client):
        response = client.post(
            "/api/v1/query",
            headers={"X-Internal-API-Key": TEST_KEY},
            json={
                "query": "Unrelated non-existent question",
                "requester_identity": "alice@example.com",
                "top_k": 5,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "no relevant results" in data["answer"].lower()
        assert len(data["citations"]) == 0


def test_query_endpoint_backend_503_error():
    """POST /api/v1/query should return 503 if backend Knowledge API connection fails."""
    mock_async_client = AsyncMock()
    mock_async_client.post.side_effect = Exception("Connection refused")

    with patch("agent.app.client.http_client.get_client", return_value=mock_async_client):
        response = client.post(
            "/api/v1/query",
            headers={"X-Internal-API-Key": TEST_KEY},
            json={
                "query": "How is authentication handled?",
                "requester_identity": "alice@example.com",
                "top_k": 5,
            },
        )

        assert response.status_code == 503
        assert "unavailable" in response.json()["detail"].lower()
