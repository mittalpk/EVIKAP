"""
Source Connectivity Validator & Pilot BU Verification Module.

Handles validation of source system access, checking least-privilege token connectivity,
sensitivity classification sign-off status, and edge-case handling (SSO/SAML, permissions, timeouts).
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional
import httpx
import logging

logger = logging.getLogger(__name__)


class SourceType(str, Enum):
    GITHUB_REPO = "github_repo"
    CONFLUENCE_WIKI = "confluence_wiki"


class SensitivityLevel(str, Enum):
    INTERNAL_GENERAL = "internal-general"
    INTERNAL_SENSITIVE = "internal-sensitive"
    RESTRICTED = "restricted"


class ValidationStatus(str, Enum):
    SUCCESS = "success"
    UNAUTHORIZED = "unauthorized"
    FORBIDDEN = "forbidden"
    NON_STANDARD_AUTH_SAML = "non_standard_auth_saml"
    TIMEOUT = "timeout"
    CONNECTION_ERROR = "connection_error"
    MISSING_SPONSOR = "missing_sponsor"
    MISSING_SENSITIVITY_SIGNOFF = "missing_sensitivity_signoff"


@dataclass
class SourceSystemConfig:
    source_id: str
    source_type: SourceType
    name: str
    endpoint_url: str
    api_token: str
    owner_email: str
    sensitivity_level: SensitivityLevel
    sensitivity_signed_off: bool = False


@dataclass
class PilotBUCharter:
    business_unit_name: str
    sponsor_name: str
    sponsor_email: str
    sponsor_signed_off: bool
    target_sources: List[SourceSystemConfig] = field(default_factory=list)


@dataclass
class ValidationResult:
    source_id: str
    status: ValidationStatus
    message: str
    details: Optional[Dict] = None


class SourceConnectivityValidator:
    """Validates connectivity and access scope for pilot business unit source systems."""

    def __init__(self, timeout_seconds: float = 5.0):
        self.timeout_seconds = timeout_seconds

    async def validate_pilot_charter(self, charter: PilotBUCharter) -> Dict[str, List[ValidationResult]]:
        """Validate the full pilot charter including sponsor sign-off and all source connections."""
        results: List[ValidationResult] = []

        if not charter.sponsor_signed_off:
            results.append(
                ValidationResult(
                    source_id="charter",
                    status=ValidationStatus.MISSING_SPONSOR,
                    message=f"Pilot charter for '{charter.business_unit_name}' lacks formal sponsor sign-off from {charter.sponsor_name}.",
                )
            )

        for source in charter.target_sources:
            if not source.sensitivity_signed_off:
                results.append(
                    ValidationResult(
                        source_id=source.source_id,
                        status=ValidationStatus.MISSING_SENSITIVITY_SIGNOFF,
                        message=f"Source system '{source.name}' has not received data sensitivity classification sign-off from {source.owner_email}.",
                    )
                )

            # Perform live connection verification
            connection_res = await self.verify_source_connection(source)
            results.append(connection_res)

        return {"results": results}

    async def verify_source_connection(self, source: SourceSystemConfig) -> ValidationResult:
        """Verifies API connection to a specific source system."""
        headers = {
            "User-Agent": "VigilRAG-Source-Validator/1.0",
            "Accept": "application/json",
        }

        if source.source_type == SourceType.GITHUB_REPO:
            headers["Authorization"] = f"Bearer {source.api_token}"
        elif source.source_type == SourceType.CONFLUENCE_WIKI:
            headers["Authorization"] = f"Bearer {source.api_token}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds, follow_redirects=True) as client:
                response = await client.get(source.endpoint_url, headers=headers)

                # Edge case check: HTML / SAML Single Sign-On Redirect Detection
                content_type = response.headers.get("content-type", "").lower()
                if "text/html" in content_type or "saml" in str(response.url).lower() or "<html" in response.text.lower()[:200]:
                    return ValidationResult(
                        source_id=source.source_id,
                        status=ValidationStatus.NON_STANDARD_AUTH_SAML,
                        message=f"Source '{source.name}' returned SAML/SSO HTML page instead of REST API response. Non-standard auth required.",
                        details={"url": str(response.url), "status_code": response.status_code},
                    )

                if response.status_code == 200:
                    return ValidationResult(
                        source_id=source.source_id,
                        status=ValidationStatus.SUCCESS,
                        message=f"Successfully connected to source '{source.name}'.",
                        details={"status_code": 200},
                    )
                elif response.status_code == 401:
                    return ValidationResult(
                        source_id=source.source_id,
                        status=ValidationStatus.UNAUTHORIZED,
                        message=f"Authentication failed for source '{source.name}'. Token invalid or expired.",
                        details={"status_code": 401},
                    )
                elif response.status_code == 403:
                    return ValidationResult(
                        source_id=source.source_id,
                        status=ValidationStatus.FORBIDDEN,
                        message=f"Access forbidden for source '{source.name}'. Token lacks necessary read scopes.",
                        details={"status_code": 403},
                    )
                else:
                    return ValidationResult(
                        source_id=source.source_id,
                        status=ValidationStatus.CONNECTION_ERROR,
                        message=f"Source '{source.name}' returned HTTP status code {response.status_code}.",
                        details={"status_code": response.status_code},
                    )

        except httpx.TimeoutException:
            return ValidationResult(
                source_id=source.source_id,
                status=ValidationStatus.TIMEOUT,
                message=f"Connection to source '{source.name}' timed out after {self.timeout_seconds}s.",
            )
        except httpx.RequestError as exc:
            return ValidationResult(
                source_id=source.source_id,
                status=ValidationStatus.CONNECTION_ERROR,
                message=f"Failed to connect to source '{source.name}': {str(exc)}",
            )
