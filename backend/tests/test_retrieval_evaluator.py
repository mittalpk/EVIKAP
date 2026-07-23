"""
Test suite for US-009 Retrieval Quality Golden Dataset & Evaluation.
Tests:
- Seeding EvaluationCase records into SQLite/Postgres DB from YAML dataset.
- Running evaluation engine and computing top-5 recall metrics.
- Verifying recall accuracy threshold (>= 80%).
Uses workspace-root imports: `from backend.app.services.retrieval_evaluator import ...`
"""

import os
import pytest
import pytest_asyncio
import yaml
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.app.models import Base, EvaluationCase, Source
from backend.app.services.github_connector import GitHubIngestionConnector
from backend.app.services.retrieval_evaluator import run_retrieval_evaluation, seed_golden_dataset
from backend.app.services.wiki_connector import WikiIngestionConnector


@pytest_asyncio.fixture
async def test_async_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        # Seed Source & Ingest Sample Corpus
        gh_src = Source(
            id="src-eval-gh-test",
            name="core-backend",
            source_type="github_repo",
            endpoint_url="https://api.github.com/repos/org/core-backend",
            secret_reference="sec-gh",
            owner_email="dev@example.com",
            sensitivity_level="internal-general",
            sensitivity_signed_off=True,
        )
        wiki_src = Source(
            id="src-eval-wiki-test",
            name="eng-wiki",
            source_type="confluence_wiki",
            endpoint_url="https://wiki.example.com/rest/api/content",
            secret_reference="sec-wiki",
            owner_email="wiki@example.com",
            sensitivity_level="internal-general",
            sensitivity_signed_off=True,
        )
        session.add_all([gh_src, wiki_src])
        await session.commit()

        gh_connector = GitHubIngestionConnector()
        await gh_connector.run_ingestion(
            session,
            gh_src,
            mock_files=[
                {"path": "backend/app/main.py", "content": "import jwt\nINTERNAL_API_KEY = os.getenv('INTERNAL_API_KEY')\nSECRET_KEY = os.getenv('SECRET_KEY')\nADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')"},
                {"path": "backend/app/models.py", "content": "class Source(Base):\nclass Chunk(Base):\nparent_doc_id = Column()\nreferences_json = Column()\nclass EvaluationCase(Base):\npermission_cache"},
            ]
        )

        wiki_connector = WikiIngestionConnector()
        await wiki_connector.run_ingestion(
            session,
            wiki_src,
            mock_pages=[
                {"page_id": "p1", "title": "Wiki Utils", "html_body": "<p>BeautifulSoup4 html.parser strips script, style, nav.</p>", "parent_doc_id": "wiki-root"},
            ]
        )

        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_seed_golden_dataset(test_async_session):
    yaml_path = os.path.join(
        os.path.dirname(__file__),
        "evaluation/golden_dataset_v1.yaml"
    )
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    cases = data.get("cases", [])
    assert len(cases) >= 20

    inserted = await seed_golden_dataset(test_async_session, cases)
    assert inserted >= 20

    # Query back to verify DB insertion
    res = await test_async_session.execute(Base.metadata.tables["evaluation_cases"].select())
    rows = res.fetchall()
    assert len(rows) >= 20


@pytest.mark.asyncio
async def test_retrieval_quality_evaluation_recall(test_async_session):
    yaml_path = os.path.join(
        os.path.dirname(__file__),
        "evaluation/golden_dataset_v1.yaml"
    )
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)


    await seed_golden_dataset(test_async_session, data.get("cases", []))

    report = await run_retrieval_evaluation(test_async_session)

    assert report.total_cases >= 20
    assert report.top_5_recall_pct >= 80.0
    assert "github_repo" in report.cases_by_source_type
