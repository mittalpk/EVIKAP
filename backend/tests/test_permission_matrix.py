"""
Permission Matrix Test Suite for US-015 (FR-006, NFR-002, NFR-010).

Automated test suite verifying zero over-exposure across 22 scenarios in permission_matrix.yaml.
Covers GitHub and Confluence Wiki source types.
"""

from pathlib import Path
import pytest
import pytest_asyncio
import yaml
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.app.models import Base, Chunk
from backend.app.services.permission_evaluator import PermissionEvaluator

FIXTURES_PATH = Path(__file__).parent / "fixtures" / "permission_matrix.yaml"


def load_matrix_scenarios():
    with open(FIXTURES_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("scenarios", [])


SCENARIOS = load_matrix_scenarios()


@pytest_asyncio.fixture
async def matrix_async_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s["id"])
async def test_permission_matrix_scenario(matrix_async_session, scenario):
    evaluator = PermissionEvaluator()

    chunk_id = f"chk-{scenario['id']}"
    source_id = f"src-{scenario['source_type']}"

    chunk = Chunk(
        id=chunk_id,
        source_id=source_id,
        document_id=f"doc-{scenario['id']}",
        content=f"Content for {scenario['id']}: {scenario['description']}",
        checksum="abcd1234checksum",
        permissions_ref=scenario["permissions_ref"],
    )


    requester_identity = scenario["requester_identity"]
    expected_result = scenario["expected_result"]  # "included" or "excluded"

    is_accessible = await evaluator.evaluate_chunk_access(
        session=matrix_async_session,
        chunk=chunk,
        requester_identity=requester_identity,
    )

    if expected_result == "included":
        assert is_accessible is True, (
            f"Scenario [{scenario['id']}] failed: expected INCLUDED for identity '{requester_identity}' "
            f"on permissions_ref '{scenario['permissions_ref']}', but got EXCLUDED."
        )
    else:
        assert is_accessible is False, (
            f"Scenario [{scenario['id']}] failed: expected EXCLUDED for identity '{requester_identity}' "
            f"on permissions_ref '{scenario['permissions_ref']}', but got INCLUDED (OVER-EXPOSURE VIOLATION!)."
        )


def test_permission_matrix_scenario_count():
    assert len(SCENARIOS) >= 20, f"Expected at least 20 scenarios, found {len(SCENARIOS)}."

    gh_scenarios = [s for s in SCENARIOS if s.get("source_type") == "github_repo"]
    wiki_scenarios = [s for s in SCENARIOS if s.get("source_type") == "confluence_wiki"]

    assert len(gh_scenarios) >= 10, f"Expected at least 10 GitHub scenarios, found {len(gh_scenarios)}."
    assert len(wiki_scenarios) >= 10, f"Expected at least 10 Wiki scenarios, found {len(wiki_scenarios)}."
