"""
Database Provisioning & Migration Validator Module (US-005).

Provides validation helpers for verifying Postgres/pgvector provisioning,
Alembic migration status, Graph-Ready schema compliance (parent_doc_id, references),
and async database connectivity.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import logging
from sqlalchemy import inspect, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models import Chunk, PermissionCacheModel, Source, init_db

logger = logging.getLogger(__name__)


@dataclass
class DatabaseProvisioningReport:
    database_url: str
    is_pgvector_enabled: bool
    tables_exist: List[str] = field(default_factory=list)
    graph_ready_fields_present: bool = True
    alembic_upgrade_successful: bool = True
    alembic_reversibility_confirmed: bool = True
    connectivity_test_passed: bool = True


@dataclass
class ProvisioningValidationResult:
    passed: bool
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    summary: Optional[Dict] = None


class DatabaseProvisioningValidator:
    """Validates US-005 database provisioning, migration status, and schema compliance."""

    REQUIRED_TABLES = {"sources", "chunks", "permission_cache"}

    async def verify_connectivity(self, session: AsyncSession) -> bool:
        """Executes a basic async SELECT 1 query to confirm DB connectivity."""
        try:
            result = await session.execute(text("SELECT 1"))
            val = result.scalar()
            return val == 1
        except Exception as exc:
            logger.error(f"Database connectivity test failed: {exc}")
            return False

    async def verify_schema_integrity(self, session: AsyncSession) -> Dict[str, bool]:
        """Verifies that Source, Chunk, and PermissionCache entities exist and chunk schema is Graph-Ready."""
        # Test insert and query on SQLite/Postgres to verify schema functionality
        try:
            src = Source(
                id="test-src-001",
                name="Test Repo",
                source_type="github_repo",
                endpoint_url="https://api.github.com/repos/test/repo",
                secret_reference="kv-test",
                owner_email="owner@example.com",
                sensitivity_level="internal-general",
                sensitivity_signed_off=True,
            )
            session.add(src)
            await session.flush()

            chk = Chunk(
                id="test-chk-001",
                source_id="test-src-001",
                document_id="doc-001",
                parent_doc_id="doc-parent-001",  # Graph-Ready check
                content="Test chunk content",
                permissions_ref="public",
                checksum="abc123hash",
                references_json='["ref-001", "ref-002"]',  # Graph-Ready references
                embedding_vector_str="[0.1, 0.2, 0.3]",
            )
            session.add(chk)
            await session.flush()

            # Query back
            res = await session.execute(select(Chunk).where(Chunk.id == "test-chk-001"))
            retrieved = res.scalar_one_or_none()

            has_parent = retrieved is not None and retrieved.parent_doc_id == "doc-parent-001"
            has_refs = retrieved is not None and "ref-001" in retrieved.references_json

            # Clean up
            await session.rollback()

            return {
                "schema_valid": retrieved is not None,
                "graph_ready_parent_doc_id": has_parent,
                "graph_ready_references": has_refs,
            }
        except Exception as exc:
            logger.error(f"Schema integrity check failed: {exc}")
            await session.rollback()
            return {
                "schema_valid": False,
                "graph_ready_parent_doc_id": False,
                "graph_ready_references": False,
            }

    def validate_provisioning_report(self, report: DatabaseProvisioningReport) -> ProvisioningValidationResult:
        warnings: List[str] = []
        errors: List[str] = []

        if not report.connectivity_test_passed:
            errors.append("Database connectivity test (SELECT 1) failed.")

        missing_tables = set(self.REQUIRED_TABLES) - set(report.tables_exist)
        if missing_tables:
            errors.append(f"Required database tables missing: {sorted(list(missing_tables))}")

        if not report.graph_ready_fields_present:
            errors.append("Chunk schema is not Graph-Ready: parent_doc_id or references[] missing.")

        if not report.alembic_upgrade_successful:
            errors.append("Alembic upgrade head failed during execution.")

        if not report.alembic_reversibility_confirmed:
            warnings.append("Alembic downgrade base + upgrade head reversibility test not executed on live target.")

        is_passed = len(errors) == 0

        summary = {
            "database_url_masked": report.database_url.split("@")[-1] if "@" in report.database_url else "local-in-memory",
            "tables_count": len(report.tables_exist),
            "pgvector_enabled": report.is_pgvector_enabled,
            "graph_ready": report.graph_ready_fields_present,
            "issue_010_resolved": is_passed,
        }

        return ProvisioningValidationResult(
            passed=is_passed,
            warnings=warnings,
            errors=errors,
            summary=summary,
        )
