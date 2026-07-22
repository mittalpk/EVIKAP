import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import os

# Set up test environment variables before importing settings/app
os.environ["INTERNAL_API_KEY"] = "secure-test-internal-api-key-9999"
os.environ["GEMINI_API_KEY"] = "fake-gemini-key"

from agent.app.config import Settings, settings
from agent.app.main import app

client = TestClient(app)

def test_startup_guard_success():
    """Startup checks should pass when using secure, non-default configs."""
    assert settings.internal_api_key.get_secret_value() == "secure-test-internal-api-key-9999"

def test_startup_guard_insecure_defaults():
    """Startup guard should raise RuntimeError if insecure defaults are detected."""
    import base64
    # Test default
    with patch.object(settings.internal_api_key, "get_secret_value", return_value="change-me-in-production"):
        from agent.app.main import startup_event
        with pytest.raises(RuntimeError) as excinfo:
            import asyncio
            asyncio.run(startup_event())
        assert "INTERNAL_API_KEY" in str(excinfo.value)

    # Test compromised
    compromised_key = base64.b64decode("TXVtYmFpU3BhaW4xMjMk").decode()
    with patch.object(settings.internal_api_key, "get_secret_value", return_value=compromised_key):
        from agent.app.main import startup_event
        with pytest.raises(RuntimeError) as excinfo:
            import asyncio
            asyncio.run(startup_event())
        assert "INTERNAL_API_KEY" in str(excinfo.value)

def test_health_check():
    """Health check should return 200 and simple service info."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "vigilrag-agent"

def test_run_task_auth_success():
    """Accessing /run with valid internal API key should succeed (or invoke graph)."""
    # Patch graph invocation so we don't call LLM
    mock_response = {
        "final_answer": "This is a mock final answer",
        "results": [
            {"step": 1, "tool": "query_knowledge", "output": "some result"}
        ]
    }
    with patch("agent.app.main.graph.ainvoke", return_value=mock_response):
        response = client.post(
            "/run",
            headers={"X-Internal-API-Key": "secure-test-internal-api-key-9999"},
            json={"task": "check privacy policies", "max_iterations": 5}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["answer"] == "This is a mock final answer"
        assert len(data["steps"]) == 1

def test_run_task_auth_failure():
    """Accessing /run with invalid internal API key should return 401."""
    response = client.post(
        "/run",
        headers={"X-Internal-API-Key": "wrong-key"},
        json={"task": "check privacy policies", "max_iterations": 5}
    )
    assert response.status_code == 401
    assert "Invalid internal API key" in response.json()["detail"]
