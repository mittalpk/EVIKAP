#!/usr/bin/env python3
"""
CLI evaluation script for US-009 Retrieval Quality Golden Dataset.
Executes ingestion on sample corpus, seeds evaluation cases, runs retrieval evaluation,
and prints quality report.
"""

import asyncio
import json
import os
import sys
import yaml

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.app.models import Base, Source
from backend.app.services.github_connector import GitHubIngestionConnector
from backend.app.services.retrieval_evaluator import run_retrieval_evaluation, seed_golden_dataset
from backend.app.services.wiki_connector import WikiIngestionConnector


async def main():
    print("=== VigilRAG US-009 Retrieval Quality Evaluation ===")
    
    # 1. Setup in-memory DB engine
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        # Seed Source entities
        gh_src = Source(
            id="src-eval-gh",
            name="core-backend",
            source_type="github_repo",
            endpoint_url="https://api.github.com/repos/org/core-backend",
            secret_reference="sec-gh",
            owner_email="dev@example.com",
            sensitivity_level="internal-general",
            sensitivity_signed_off=True,
        )
        wiki_src = Source(
            id="src-eval-wiki",
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

        # Ingest sample corpus files into DB
        gh_connector = GitHubIngestionConnector()
        await gh_connector.run_ingestion(
            session,
            gh_src,
            mock_files=[
                {"path": "backend/app/main.py", "content": "import jwt\nINTERNAL_API_KEY = os.getenv('INTERNAL_API_KEY')\nSECRET_KEY = os.getenv('SECRET_KEY')\nADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')"},
                {"path": "backend/app/models.py", "content": "class Source(Base):\nclass Chunk(Base):\nparent_doc_id = Column()\nreferences_json = Column()\nclass EvaluationCase(Base):\npermission_cache"},
                {"path": "backend/app/services/github_connector.py", "content": "class GitHubIngestionConnector:\ndef parse_references(): regex patterns for python, js, go\ndef run_ingestion(): rate limit status = rate_limited"},
            ]
        )

        wiki_connector = WikiIngestionConnector()
        await wiki_connector.run_ingestion(
            session,
            wiki_src,
            mock_pages=[
                {"page_id": "p1", "title": "Wiki Utils", "html_body": "<html><body><script>var x=1;</script><p>BeautifulSoup4 html.parser strips script, style, nav.</p></body></html>", "parent_doc_id": "wiki-root"},
                {"page_id": "p2", "title": "Confluence Fallback", "html_body": "<p>The connector falls back to loading local Markdown files from disk when no token provided.</p>", "parent_doc_id": "wiki-p1"},
            ]
        )

        # Load golden dataset YAML
        yaml_path = os.path.join(os.path.dirname(__file__), "../backend/tests/evaluation/golden_dataset_v1.yaml")
        if not os.path.exists(yaml_path):
            yaml_path = "backend/tests/evaluation/golden_dataset_v1.yaml"

        with open(yaml_path, "r", encoding="utf-8") as f:
            dataset_data = yaml.safe_load(f)

        cases_list = dataset_data.get("cases", [])
        seeded_count = await seed_golden_dataset(session, cases_list)
        print(f"✓ Seeded {seeded_count} EvaluationCase records into database.")

        # Run retrieval evaluation
        report = await run_retrieval_evaluation(session)

        print("\n--- Retrieval Quality Evaluation Report ---")
        print(f"Total Golden Cases Evaluated: {report.total_cases}")
        print(f"Successful Retrievals (Top-5): {report.successful_retrievals}")
        print(f"Top-5 Recall Accuracy: {report.top_5_recall_pct}%")
        print(f"Breakdown by Source Type: {report.cases_by_source_type}")
        print("------------------------------------------")

        if report.top_5_recall_pct >= 80.0:
            print("✓ SUCCESS: Retrieval accuracy meets or exceeds target threshold (≥80.0%).")
        else:
            print(f"✖ WARNING: Retrieval accuracy ({report.top_5_recall_pct}%) is below 80% threshold.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
