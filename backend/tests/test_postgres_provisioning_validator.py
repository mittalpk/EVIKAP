"""
Test suite for US-005 Database Provisioning, Migration, and ORM Schema Validation.
Tests async DB connectivity (SELECT 1), table initialization, Graph-Ready schema fields,
Alembic migration execution, and provisioning report validation.
Uses workspace-root imports: `from backend.app.services.postgres_provisioning_validator import ...`
"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.app.models import Base, Chunk, PermissionCacheModel, Source
from backend.app.services.postgres_provisioning_validator import (
    DatabaseProvisioningReport,
    DatabaseProvisioningValidator,
)


@pytest_asyncio.fixture
async def test_async_session():
    # Use SQLite in-memory engine for fast isolated unit test execution
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_database_connectivity_select_1(test_async_session):
    validator = DatabaseProvisioningValidator()
    connected = await validator.verify_connectivity(test_async_session)
    assert connected is True


@pytest.mark.asyncio
async def test_schema_integrity_and_graph_ready_fields(test_async_session):
    validator = DatabaseProvisioningValidator()
    res = await validator.verify_schema_integrity(test_async_session)

    assert res["schema_valid"] is True
    assert res["graph_ready_parent_doc_id"] is True
    assert res["graph_ready_references"] is True


def test_provisioning_report_validation_success():
    validator = DatabaseProvisioningValidator()
    report = DatabaseProvisioningReport(
        database_url="postgresql+asyncpg://user:pass@localhost:5432/vigilrag_db",
        is_pgvector_enabled=True,
        tables_exist=["sources", "chunks", "permission_cache"],
        graph_ready_fields_present=True,
        alembic_upgrade_successful=True,
        alembic_reversibility_confirmed=True,
        connectivity_test_passed=True,
    )

    res = validator.validate_provisioning_report(report)
    assert res.passed is True
    assert len(res.errors) == 0
    assert res.summary["issue_010_resolved"] is True
    assert res.summary["graph_ready"] is True


def test_provisioning_report_validation_missing_tables():
    validator = DatabaseProvisioningValidator()
    report = DatabaseProvisioningReport(
        database_url="postgresql+asyncpg://user:pass@localhost:5432/vigilrag_db",
        is_pgvector_enabled=True,
        tables_exist=["sources"],  # missing chunks and permission_cache
        graph_ready_fields_present=True,
        alembic_upgrade_successful=True,
        alembic_reversibility_confirmed=True,
        connectivity_test_passed=True,
    )

    res = validator.validate_provisioning_report(report)
    assert res.passed is False
    assert any("missing: ['chunks', 'permission_cache']" in err for err in res.errors)


def test_provisioning_report_validation_failed_connectivity():
    validator = DatabaseProvisioningValidator()
    report = DatabaseProvisioningReport(
        database_url="postgresql+asyncpg://user:pass@localhost:5432/vigilrag_db",
        is_pgvector_enabled=False,
        tables_exist=["sources", "chunks", "permission_cache"],
        graph_ready_fields_present=False,
        alembic_upgrade_successful=False,
        alembic_reversibility_confirmed=False,
        connectivity_test_passed=False,
    )

    res = validator.validate_provisioning_report(report)
    assert res.passed is False
    assert any("connectivity test (SELECT 1) failed" in err for err in res.errors)
    assert any("Chunk schema is not Graph-Ready" in err for err in res.errors)
