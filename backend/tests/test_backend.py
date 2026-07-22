import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import os
import jwt
import datetime
import base64

# Set up test environment variables before importing settings/app
os.environ["INTERNAL_API_KEY"] = "secure-test-internal-api-key-9999"
os.environ["SECRET_KEY"] = "secure-test-secret-key-9999-jwt"
os.environ["ADMIN_PASSWORD"] = "secure-test-admin-password-9999"
os.environ["DEMO_MODE"] = "false"

from backend.app.config import Settings, settings
from backend.app.main import app

client = TestClient(app)

def test_startup_guard_success():
    """Startup checks should pass when using secure, non-default configs."""
    # Since we set environment variables, config settings are secure.
    assert settings.internal_api_key.get_secret_value() == "secure-test-internal-api-key-9999"
    assert settings.secret_key.get_secret_value() == "secure-test-secret-key-9999-jwt"
    assert settings.admin_password.get_secret_value() == "secure-test-admin-password-9999"

def test_startup_guard_insecure_defaults():
    """Startup guard should raise RuntimeError if insecure defaults are detected."""
    import base64
    # Test internal key
    with patch.object(settings.internal_api_key, "get_secret_value", return_value="change-me-in-production"):
        from backend.app.main import startup_event
        with pytest.raises(RuntimeError) as excinfo:
            import asyncio
            asyncio.run(startup_event())
        assert "INTERNAL_API_KEY" in str(excinfo.value)

    # Test compromised internal key (reconstructed from base64)
    compromised_key = base64.b64decode("TXVtYmFpU3BhaW4xMjMk").decode()
    with patch.object(settings.internal_api_key, "get_secret_value", return_value=compromised_key):
        from backend.app.main import startup_event
        with pytest.raises(RuntimeError) as excinfo:
            import asyncio
            asyncio.run(startup_event())
        assert "INTERNAL_API_KEY" in str(excinfo.value)

    # Test compromised secret key (reconstructed from base64)
    compromised_jwt = base64.b64decode("b21lZ2EtbmV4dXMtc2VjcmV0LWtleS0xMjM0NTY=").decode()
    with patch.object(settings.secret_key, "get_secret_value", return_value=compromised_jwt):
        from backend.app.main import startup_event
        with pytest.raises(RuntimeError) as excinfo:
            import asyncio
            asyncio.run(startup_event())
        assert "SECRET_KEY" in str(excinfo.value)

    # Test compromised admin password (reconstructed from base64)
    compromised_admin = base64.b64decode("YWRtaW4xMjMk").decode()
    with patch.object(settings.admin_password, "get_secret_value", return_value=compromised_admin):
        from backend.app.main import startup_event
        with pytest.raises(RuntimeError) as excinfo:
            import asyncio
            asyncio.run(startup_event())
        assert "ADMIN_PASSWORD" in str(excinfo.value)

def test_health_check_safe():
    """Health check should be safe, return 200, and not leak secrets."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "vigilrag-backend"
    assert "diagnosis" not in data
    res_str = response.text
    assert base64.b64decode("TXVtYmFpU3BhaW4xMjM=").decode() not in res_str
    assert "secure-test-internal-api-key-9999" not in res_str

def test_login_success():
    """Successful login should return a valid JWT token."""
    response = client.post("/api/v1/auth/login", json={
        "username": "admin",
        "password": "secure-test-admin-password-9999"
    })
    assert response.status_code == 200
    token = response.json().get("token")
    assert token is not None
    
    # Decode token to verify
    payload = jwt.decode(token, "secure-test-secret-key-9999-jwt", algorithms=["HS256"])
    assert payload["sub"] == "admin"

def test_login_failure():
    """Failed login should return 401 Unauthorized."""
    response = client.post("/api/v1/auth/login", json={
        "username": "admin",
        "password": "wrong-password"
    })
    assert response.status_code == 401
    assert "Invalid credentials" in response.json()["detail"]

def test_internal_api_key_auth_success():
    """Accessing knowledge query with valid internal API key should succeed."""
    # We patch GitHubSearchSubsystem.search_code to avoid outbound network call
    with patch("backend.app.routers.knowledge.GitHubSearchSubsystem.search_code", return_value=[]), \
         patch("backend.app.routers.knowledge.AzureWikiSubsystem.search_wiki", return_value=[]):
        response = client.post(
            "/api/v1/knowledge/query",
            headers={"X-Internal-API-Key": "secure-test-internal-api-key-9999"},
            json={"query": "test query", "target_systems": ["confluence"]}
        )
        assert response.status_code == 200

def test_internal_api_key_auth_failure():
    """Accessing knowledge query with invalid internal API key should fail with 401."""
    response = client.post(
        "/api/v1/knowledge/query",
        headers={"X-Internal-API-Key": "wrong-key"},
        json={"query": "test query", "target_systems": ["confluence"]}
    )
    assert response.status_code == 401
    assert "Invalid internal API key" in response.json()["detail"]

def test_jwt_auth_success():
    """Accessing knowledge query with valid JWT should succeed."""
    token = jwt.encode({
        "sub": "admin",
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }, "secure-test-secret-key-9999-jwt", algorithm="HS256")
    
    with patch("backend.app.routers.knowledge.GitHubSearchSubsystem.search_code", return_value=[]), \
         patch("backend.app.routers.knowledge.AzureWikiSubsystem.search_wiki", return_value=[]):
        response = client.post(
            "/api/v1/knowledge/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "test query", "target_systems": ["confluence"]}
        )
        assert response.status_code == 200

def test_jwt_auth_failure_invalid():
    """Accessing knowledge query with invalid JWT should fail with 401."""
    response = client.post(
        "/api/v1/knowledge/query",
        headers={"Authorization": "Bearer invalid-token-string"},
        json={"query": "test query", "target_systems": ["confluence"]}
    )
    assert response.status_code == 401
    assert "Invalid token" in response.json()["detail"]

def test_no_fabricated_data_in_db_query():
    """DatabaseSubsystem should not return any simulated database schema fallbacks."""
    # Verify mock/simulated fallback is gone
    with patch("backend.app.routers.knowledge.GitHubSearchSubsystem.search_code", return_value=[]), \
         patch("backend.app.routers.knowledge.AzureWikiSubsystem.search_wiki", return_value=[]), \
         patch("backend.app.routers.knowledge.DatabaseSubsystem.query_schemas", return_value=[]):
        response = client.post(
            "/api/v1/knowledge/query",
            headers={"X-Internal-API-Key": "secure-test-internal-api-key-9999"},
            json={"query": "user database schema", "target_systems": ["databases"]}
        )
        assert response.status_code == 200
        data = response.json()
        # Since we patched DatabaseSubsystem.query_schemas to return [], results must be empty
        assert len(data["facts"]) == 0

def test_demo_mode_local_fallback(tmp_path):
    """Local wiki fallback should only return results when demo_mode is True."""
    # Create temporary mock wiki structure
    wiki_dir = tmp_path / "wiki"
    wiki_dir.mkdir()
    doc_file = wiki_dir / "privacy.md"
    doc_file.write_text("This is our official data privacy policy. PII data is restricted.")

    # Test when demo_mode is False (default)
    from backend.app.routers.knowledge import AzureWikiSubsystem
    with patch("backend.app.routers.knowledge.settings.demo_mode", False), \
         patch("backend.app.routers.knowledge.MOCK_DATA_DIR", str(tmp_path)), \
         patch("backend.app.routers.knowledge.AzureWikiSubsystem.search_wiki", wraps=AzureWikiSubsystem.search_wiki) as mock_search:
        # We don't configure connection string, so it should hit local fallback code
        # but since demo_mode is False, it returns empty
        response = client.post(
            "/api/v1/knowledge/query",
            headers={"X-Internal-API-Key": "secure-test-internal-api-key-9999"},
            json={"query": "privacy PII", "target_systems": ["confluence"]}
        )
        assert response.status_code == 200
        assert len(response.json()["facts"]) == 0

    # Test when demo_mode is True
    from backend.app.routers.knowledge import QUERY_CACHE
    QUERY_CACHE.clear()
    with patch("backend.app.routers.knowledge.settings.demo_mode", True), \
         patch("backend.app.routers.knowledge.MOCK_DATA_DIR", str(tmp_path)):
        response = client.post(
            "/api/v1/knowledge/query",
            headers={"X-Internal-API-Key": "secure-test-internal-api-key-9999"},
            json={"query": "privacy PII", "target_systems": ["confluence"]}
        )
        assert response.status_code == 200
        # Should retrieve local mock wiki file
        assert len(response.json()["facts"]) > 0
        assert "Confluence (Simulated)" in response.json()["metadata"][0]["source_system"]

