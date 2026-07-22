"""
Test suite for US-001 Source Connectivity Validator and Pilot BU Charter validation.
Covers happy path, missing sponsor, missing sensitivity sign-off, and edge cases (SAML redirect, 401/403 errors, timeout).
Uses unittest.mock for HTTP mocking without external dependencies.
"""

from unittest.mock import AsyncMock, MagicMock, patch
import httpx
import pytest

from backend.app.services.source_connectivity_validator import (
    PilotBUCharter,
    SensitivityLevel,
    SourceConnectivityValidator,
    SourceSystemConfig,
    SourceType,
    ValidationStatus,
)


@pytest.fixture
def sample_charter():
    return PilotBUCharter(
        business_unit_name="Digital Services & Engineering",
        sponsor_name="Jane Doe",
        sponsor_email="jane.doe@example.com",
        sponsor_signed_off=True,
        target_sources=[
            SourceSystemConfig(
                source_id="src-github-001",
                source_type=SourceType.GITHUB_REPO,
                name="Core Platform Repository",
                endpoint_url="https://api.github.com/repos/org/core-platform",
                api_token="ghp_testtoken123",
                owner_email="lead@example.com",
                sensitivity_level=SensitivityLevel.INTERNAL_SENSITIVE,
                sensitivity_signed_off=True,
            ),
            SourceSystemConfig(
                source_id="src-wiki-001",
                source_type=SourceType.CONFLUENCE_WIKI,
                name="Engineering Architecture Wiki",
                endpoint_url="https://wiki.example.com/rest/api/content/123",
                api_token="wiki_testtoken456",
                owner_email="wikiowner@example.com",
                sensitivity_level=SensitivityLevel.INTERNAL_GENERAL,
                sensitivity_signed_off=True,
            ),
        ],
    )


@pytest.mark.asyncio
async def test_successful_pilot_charter_validation(sample_charter):
    validator = SourceConnectivityValidator()

    mock_resp_github = MagicMock()
    mock_resp_github.status_code = 200
    mock_resp_github.headers = {"content-type": "application/json"}
    mock_resp_github.url = "https://api.github.com/repos/org/core-platform"
    mock_resp_github.text = '{"id": 101}'

    mock_resp_wiki = MagicMock()
    mock_resp_wiki.status_code = 200
    mock_resp_wiki.headers = {"content-type": "application/json"}
    mock_resp_wiki.url = "https://wiki.example.com/rest/api/content/123"
    mock_resp_wiki.text = '{"id": "123"}'

    with patch("httpx.AsyncClient.get", side_effect=[mock_resp_github, mock_resp_wiki]):
        res = await validator.validate_pilot_charter(sample_charter)
        results = res["results"]

        assert len(results) == 2
        assert all(r.status == ValidationStatus.SUCCESS for r in results)


@pytest.mark.asyncio
async def test_edge_case_missing_sponsor_signoff(sample_charter):
    sample_charter.sponsor_signed_off = False
    validator = SourceConnectivityValidator()

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {"content-type": "application/json"}
    mock_resp.url = "http://test.local"
    mock_resp.text = "{}"

    with patch("httpx.AsyncClient.get", return_value=mock_resp):
        res = await validator.validate_pilot_charter(sample_charter)
        results = res["results"]

        sponsor_res = [r for r in results if r.status == ValidationStatus.MISSING_SPONSOR]
        assert len(sponsor_res) == 1
        assert "lacks formal sponsor sign-off" in sponsor_res[0].message


@pytest.mark.asyncio
async def test_edge_case_missing_sensitivity_signoff(sample_charter):
    sample_charter.target_sources[0].sensitivity_signed_off = False
    validator = SourceConnectivityValidator()

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {"content-type": "application/json"}
    mock_resp.url = "http://test.local"
    mock_resp.text = "{}"

    with patch("httpx.AsyncClient.get", return_value=mock_resp):
        res = await validator.validate_pilot_charter(sample_charter)
        results = res["results"]

        sensitivity_res = [r for r in results if r.status == ValidationStatus.MISSING_SENSITIVITY_SIGNOFF]
        assert len(sensitivity_res) == 1
        assert sensitivity_res[0].source_id == "src-github-001"


@pytest.mark.asyncio
async def test_edge_case_unauthorized_token_401(sample_charter):
    validator = SourceConnectivityValidator()

    mock_resp = MagicMock()
    mock_resp.status_code = 401
    mock_resp.headers = {"content-type": "application/json"}
    mock_resp.url = "https://api.github.com/repos/org/core-platform"
    mock_resp.text = '{"message": "Bad credentials"}'

    with patch("httpx.AsyncClient.get", return_value=mock_resp):
        res = await validator.verify_source_connection(sample_charter.target_sources[0])
        assert res.status == ValidationStatus.UNAUTHORIZED
        assert "Token invalid or expired" in res.message


@pytest.mark.asyncio
async def test_edge_case_forbidden_scopes_403(sample_charter):
    validator = SourceConnectivityValidator()

    mock_resp = MagicMock()
    mock_resp.status_code = 403
    mock_resp.headers = {"content-type": "application/json"}
    mock_resp.url = "https://api.github.com/repos/org/core-platform"
    mock_resp.text = '{"message": "Resource not accessible"}'

    with patch("httpx.AsyncClient.get", return_value=mock_resp):
        res = await validator.verify_source_connection(sample_charter.target_sources[0])
        assert res.status == ValidationStatus.FORBIDDEN
        assert "Token lacks necessary read scopes" in res.message


@pytest.mark.asyncio
async def test_edge_case_saml_sso_html_redirect(sample_charter):
    validator = SourceConnectivityValidator()

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {"content-type": "text/html"}
    mock_resp.url = "https://sso.example.com/saml"
    mock_resp.text = "<html><body>SAML Redirect</body></html>"

    with patch("httpx.AsyncClient.get", return_value=mock_resp):
        res = await validator.verify_source_connection(sample_charter.target_sources[1])
        assert res.status == ValidationStatus.NON_STANDARD_AUTH_SAML
        assert "SAML/SSO HTML page instead of REST API response" in res.message


@pytest.mark.asyncio
async def test_edge_case_connection_timeout(sample_charter):
    validator = SourceConnectivityValidator(timeout_seconds=0.1)

    with patch("httpx.AsyncClient.get", side_effect=httpx.TimeoutException("Read timed out")):
        res = await validator.verify_source_connection(sample_charter.target_sources[0])
        assert res.status == ValidationStatus.TIMEOUT
        assert "timed out after 0.1s" in res.message
