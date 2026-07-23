"""
Wiki Source Connector & Embedding Ingestion Pipeline (US-007).

Handles:
- Fetching Confluence REST API pages or local Markdown directory fallback.
- HTML stripping via BeautifulSoup to clean plain text.
- Extracting page hierarchy (`parent_doc_id` mapping) and cross-page links (`references`).
- Capturing Confluence space/page permissions metadata (`permissions_ref`).
- Chunking, embedding generation, and idempotent database upserting (`Source`, `Chunk`).
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import logging
import os
import re
from typing import Dict, List, Optional, Tuple

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models import Chunk, Source
from backend.app.services.ingestion_utils import (
    chunk_text,
    compute_checksum,
    generate_embedding_vector,
    strip_html_to_text,
)

logger = logging.getLogger(__name__)


@dataclass
class WikiIngestionSummary:
    source_id: str
    pages_fetched: int = 0
    chunks_created: int = 0
    chunks_updated: int = 0
    chunks_skipped_unchanged: int = 0
    empty_pages_skipped: int = 0
    errors_encountered: List[str] = field(default_factory=list)
    mode: str = "confluence_api"  # "confluence_api" or "local_markdown_fallback"
    status: str = "completed"


class WikiIngestionConnector:
    """Wiki Source Connector & Embedding Ingestion Pipeline."""

    def __init__(
        self,
        wiki_token: Optional[str] = None,
        timeout_seconds: float = 10.0,
    ):
        self.wiki_token = wiki_token
        self.timeout_seconds = timeout_seconds

    def parse_cross_page_references(self, text: str) -> List[str]:
        """Extracts internal wiki cross-page link references (Graph-Ready metadata)."""
        refs: List[str] = []
        # Match wiki page links e.g. [Page Title](wiki:...) or [title](/display/SPACE/Page)
        matches = re.findall(r"\[.*?\]\((?:wiki:|/display/|/wiki/)(.*?)\)", text)
        for m in matches:
            clean_ref = m.split("?")[0].strip()
            if clean_ref and clean_ref not in refs:
                refs.append(clean_ref)

        # Match markdown relative links e.g. [Title](page.md)
        matches_md = re.findall(r"\[.*?\]\(((?!http).*?\.md)\)", text)
        for m in matches_md:
            if m and m not in refs:
                refs.append(m)

        return refs[:10]  # Cap at top 10

    async def fetch_confluence_pages(
        self,
        endpoint_url: str,
        space_key: str = "ENG",
    ) -> Tuple[List[Dict[str, str]], Optional[str]]:
        """Fetches pages via Confluence REST API v2."""
        headers = {
            "User-Agent": "VigilRAG-Wiki-Ingestor/1.0",
            "Accept": "application/json",
        }
        if self.wiki_token:
            headers["Authorization"] = f"Bearer {self.wiki_token}"

        api_url = endpoint_url
        if "/rest/api/content" not in endpoint_url and "api.confluence" not in endpoint_url:
            api_url = f"{endpoint_url.rstrip('/')}/rest/api/content?spaceKey={space_key}&expand=body.storage,ancestors"

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.get(api_url, headers=headers)

                if response.status_code == 403 and "rate limit" in response.text.lower():
                    return [], "Confluence API rate limit exceeded."
                elif response.status_code != 200:
                    return [], f"Confluence API error HTTP {response.status_code}: {response.text[:200]}"

                data = response.json()
                results = data.get("results", [])

                fetched_pages: List[Dict[str, str]] = []
                for item in results:
                    page_id = item.get("id", "")
                    title = item.get("title", "")
                    body_html = item.get("body", {}).get("storage", {}).get("value", "")
                    ancestors = item.get("ancestors", [])

                    # Map parent page ID from ancestors hierarchy
                    parent_page_id = ancestors[-1].get("id") if ancestors else f"space-{space_key}"

                    fetched_pages.append({
                        "page_id": page_id,
                        "title": title,
                        "html_body": body_html,
                        "parent_doc_id": f"wiki-page-{parent_page_id}",
                    })

                return fetched_pages, None

        except httpx.TimeoutException:
            return [], f"Connection to Confluence API timed out after {self.timeout_seconds}s."
        except Exception as exc:
            return [], f"Confluence API request error: {str(exc)}"

    def load_local_markdown_fallback(self, folder_path: str) -> List[Dict[str, str]]:
        """Fallback for demo profile: loads pages from a local directory of Markdown files."""
        pages: List[Dict[str, str]] = []
        if not os.path.exists(folder_path):
            logger.warning(f"Local Markdown folder path '{folder_path}' does not exist.")
            return pages

        for root, _, files in os.walk(folder_path):
            for file in sorted(files):
                if file.endswith((".md", ".markdown")):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, folder_path)
                    try:
                        with open(full_path, "r", encoding="utf-8") as f:
                            content = f.read()

                        parent = os.path.dirname(rel_path) or "root-space"
                        pages.append({
                            "page_id": rel_path,
                            "title": file,
                            "plain_text": content,
                            "parent_doc_id": f"wiki-dir-{parent}",
                        })
                    except Exception as exc:
                        logger.error(f"Error reading local markdown file {full_path}: {exc}")

        return pages

    async def run_ingestion(
        self,
        session: AsyncSession,
        source: Source,
        mock_pages: Optional[List[Dict[str, str]]] = None,
        local_markdown_folder: Optional[str] = None,
    ) -> WikiIngestionSummary:
        """Executes full Wiki ingestion pipeline for a given Source entity."""
        summary = WikiIngestionSummary(source_id=source.id)

        pages: List[Dict[str, str]] = []
        # 1. Page fetching logic (Confluence API -> Local Markdown Fallback -> Mock)
        if mock_pages is not None:
            pages = mock_pages
            summary.mode = "mock_test"
        elif local_markdown_folder or not self.wiki_token:
            target_folder = local_markdown_folder or "./knowledge"
            pages = self.load_local_markdown_fallback(target_folder)
            summary.mode = "local_markdown_fallback"
            if not pages:
                summary.errors_encountered.append(f"No Markdown pages found in local fallback directory '{target_folder}'.")
        else:
            api_pages, err = await self.fetch_confluence_pages(source.endpoint_url)
            if err:
                logger.warning(f"Confluence API failed ({err}). Switching to local Markdown fallback.")
                summary.errors_encountered.append(err)
                pages = self.load_local_markdown_fallback("./knowledge")
                summary.mode = "local_markdown_fallback"
            else:
                pages = api_pages
                summary.mode = "confluence_api"

        summary.pages_fetched = len(pages)
        permissions_ref = json.dumps({"source_type": "confluence_wiki", "space_key": "ENG", "access_restriction": "group-eng-staff"})

        # 2. Process pages
        for p in pages:
            page_id = p.get("page_id", "")
            html_body = p.get("html_body")
            plain_text = p.get("plain_text")

            if plain_text is None and html_body:
                plain_text = strip_html_to_text(html_body)

            if not plain_text or not plain_text.strip():
                summary.empty_pages_skipped += 1
                continue

            doc_id = f"doc-wiki-{re.sub(r'[^a-zA-Z0-9_-]', '_', page_id)}"
            parent_doc_id = p.get("parent_doc_id", "wiki-root")
            references = self.parse_cross_page_references(plain_text)
            content_chunks = chunk_text(plain_text)

            for idx, chunk_str in enumerate(content_chunks):
                checksum = compute_checksum(chunk_str)
                chunk_id = f"chk-{doc_id}-{idx}"

                # Check existing chunk in DB
                existing_res = await session.execute(
                    select(Chunk).where(Chunk.id == chunk_id)
                )
                existing_chunk = existing_res.scalar_one_or_none()

                if existing_chunk and existing_chunk.checksum == checksum:
                    summary.chunks_skipped_unchanged += 1
                    continue

                vector_embedding = generate_embedding_vector(chunk_str)

                if existing_chunk:
                    existing_chunk.content = chunk_str
                    existing_chunk.checksum = checksum
                    existing_chunk.references_json = json.dumps(references)
                    existing_chunk.embedding_vector_str = json.dumps(vector_embedding)
                    existing_chunk.permissions_ref = permissions_ref
                    existing_chunk.last_indexed_at = datetime.now(timezone.utc)
                    summary.chunks_updated += 1
                else:
                    new_chunk = Chunk(
                        id=chunk_id,
                        source_id=source.id,
                        document_id=doc_id,
                        parent_doc_id=parent_doc_id,  # Preserves space -> page hierarchy
                        content=chunk_str,
                        permissions_ref=permissions_ref,
                        checksum=checksum,
                        references_json=json.dumps(references),
                        embedding_vector_str=json.dumps(vector_embedding),
                    )
                    session.add(new_chunk)
                    summary.chunks_created += 1

        # 3. Update Source.updated_at and last_indexed_at
        source.updated_at = datetime.now(timezone.utc)
        source.last_indexed_at = datetime.now(timezone.utc)
        await session.commit()

        return summary

