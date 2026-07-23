"""
GitHub Source Connector & Embedding Ingestion Pipeline (US-006).

Handles:
- Fetching text repository files via GitHub API (with rate limit handling).
- Best-effort extraction of code import/include references (Graph-Ready).
- Splitting into chunks with configurable token overlap (default: 512 tokens, 50 overlap).
- Setting `parent_doc_id` to document ID and capturing `permissions_ref`.
- Generating chunk embedding vectors via configured embedding generator / mockable API.
- Idempotent upserting to Postgres/SQLAlchemy database (`Source`, `Chunk`).
- Updating `Source.last_indexed_at`.
"""

from dataclasses import dataclass, field
import hashlib
import json
import logging
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone

import httpx
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models import Chunk, Source

logger = logging.getLogger(__name__)


@dataclass
class IngestionSummary:
    source_id: str
    files_fetched: int = 0
    chunks_created: int = 0
    chunks_updated: int = 0
    chunks_skipped_unchanged: int = 0
    binary_files_skipped: int = 0
    errors_encountered: List[str] = field(default_factory=list)
    rate_limit_paused: bool = False
    status: str = "completed"


class GitHubIngestionConnector:
    """GitHub Source Connector & Embedding Ingestion Pipeline."""

    # Default file extensions to process
    DEFAULT_TEXT_EXTENSIONS = {
        ".py", ".md", ".json", ".yaml", ".yml", ".ts", ".tsx", ".js", ".jsx",
        ".go", ".java", ".cpp", ".c", ".h", ".sql", ".sh", ".html", ".css", ".txt"
    }

    def __init__(
        self,
        github_token: Optional[str] = None,
        chunk_size_tokens: int = 512,
        chunk_overlap_tokens: int = 50,
        timeout_seconds: float = 10.0,
    ):
        self.github_token = github_token
        self.chunk_size_tokens = chunk_size_tokens
        self.chunk_overlap_tokens = chunk_overlap_tokens
        self.timeout_seconds = timeout_seconds

    def parse_references(self, content: str, file_path: str) -> List[str]:
        """Extracts code import/include statements as references (Graph-Ready metadata)."""
        refs: List[str] = []
        ext = file_path.rsplit(".", 1)[-1].lower() if "." in file_path else ""

        if ext == "py":
            # Python import regex: import foo, from bar import baz
            matches = re.findall(r"^(?:from\s+([\w\.]+)\s+import|import\s+([\w\.]+))", content, re.MULTILINE)
            for m in matches:
                ref = m[0] or m[1]
                if ref and ref not in refs:
                    refs.append(ref)

        elif ext in ("ts", "tsx", "js", "jsx"):
            # JS/TS import regex: import x from 'y', require('z')
            matches = re.findall(r"(?:import\s+.*?\s+from\s+['\"](.*?)['\"]|require\(['\"](.*?)['\"]\))", content)
            for m in matches:
                ref = m[0] or m[1]
                if ref and ref not in refs:
                    refs.append(ref)

        elif ext == "go":
            # Go import regex: import "foo/bar"
            matches = re.findall(r"import\s+(?:\(\s*([\s\S]*?)\s*\)|[\"'](.*?)[\"'])", content)
            for m in matches:
                if m[0]:
                    sub_matches = re.findall(r"[\"'](.*?)[\"']", m[0])
                    for sm in sub_matches:
                        if sm and sm not in refs:
                            refs.append(sm)
                elif m[1] and m[1] not in refs:
                    refs.append(m[1])

        elif ext in ("md", "markdown"):
            # Markdown link regex: [title](link)
            matches = re.findall(r"\[.*?\]\((.*?)\)", content)
            for m in matches:
                if m and not m.startswith("http") and m not in refs:
                    refs.append(m)

        return refs[:10]  # Cap at top 10 references

    def chunk_content(self, content: str, max_tokens: int = 512, overlap_tokens: int = 50) -> List[str]:
        """Splits file content into overlapping token-budget chunks."""
        from backend.app.services.ingestion_utils import chunk_text
        tokens_max = max_tokens or self.chunk_size_tokens
        tokens_overlap = overlap_tokens or self.chunk_overlap_tokens
        return chunk_text(content, max_tokens=tokens_max, overlap_tokens=tokens_overlap)


    def generate_dummy_embedding(self, text: str) -> List[float]:
        """Generates 768-dim embedding vector via unified EmbeddingProvider."""
        from backend.app.services.ingestion_utils import generate_embedding_vector
        return generate_embedding_vector(text)


    async def fetch_repository_files(
        self,
        endpoint_url: str,
        path_filter: Optional[str] = None,
    ) -> Tuple[List[Dict[str, str]], Optional[str]]:
        """Fetches file metadata and raw contents from GitHub REST API."""
        headers = {
            "User-Agent": "VigilRAG-GitHub-Ingestor/1.0",
            "Accept": "application/vnd.github.v3+json",
        }
        if self.github_token:
            headers["Authorization"] = f"Bearer {self.github_token}"

        # Normalize endpoint to tree API if repo API passed
        tree_url = endpoint_url
        if "/repos/" in endpoint_url and "/git/trees" not in endpoint_url:
            parts = endpoint_url.rstrip("/").split("/repos/")
            repo_path = parts[1]
            tree_url = f"https://api.github.com/repos/{repo_path}/git/trees/main?recursive=1"

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.get(tree_url, headers=headers)

                if response.status_code == 403 and "rate limit" in response.text.lower():
                    return [], "GitHub API rate limit exceeded."
                elif response.status_code != 200:
                    return [], f"GitHub API error HTTP {response.status_code}: {response.text[:200]}"

                data = response.json()
                tree = data.get("tree", [])

                fetched_files: List[Dict[str, str]] = []
                for item in tree:
                    if item.get("type") != "blob":
                        continue

                    path = item.get("path", "")
                    # Filter binary files
                    ext = "." + path.rsplit(".", 1)[-1].lower() if "." in path else ""
                    if ext not in self.DEFAULT_TEXT_EXTENSIONS:
                        continue

                    if path_filter and not path.startswith(path_filter):
                        continue

                    fetched_files.append({"path": path, "sha": item.get("sha", ""), "url": item.get("url", "")})

                return fetched_files, None

        except httpx.TimeoutException:
            return [], f"Connection to GitHub API timed out after {self.timeout_seconds}s."
        except Exception as exc:
            return [], f"GitHub API request error: {str(exc)}"

    async def fetch_raw_file_content(self, raw_url: str) -> Optional[str]:
        """Fetches file text content."""
        headers = {"User-Agent": "VigilRAG-GitHub-Ingestor/1.0"}
        if self.github_token:
            headers["Authorization"] = f"Bearer {self.github_token}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                resp = await client.get(raw_url, headers=headers)
                if resp.status_code == 200:
                    return resp.text
                return None
        except Exception:
            return None

    async def run_ingestion(
        self,
        session: AsyncSession,
        source: Source,
        mock_files: Optional[List[Dict[str, str]]] = None,
    ) -> IngestionSummary:
        """Executes full GitHub ingestion pipeline for a given Source entity."""
        summary = IngestionSummary(source_id=source.id)

        # 1. Fetch file list
        if mock_files is not None:
            files = mock_files
            err = None
        else:
            files, err = await self.fetch_repository_files(source.endpoint_url)

        if err:
            summary.errors_encountered.append(err)
            if "rate limit" in err.lower():
                summary.rate_limit_paused = True
                summary.status = "rate_limited"
            else:
                summary.status = "failed"
            return summary

        summary.files_fetched = len(files)
        permissions_ref = f"github:{source.name}:read"
        active_chunk_ids: set[str] = set()

        # 2. Process files
        for f in files:
            file_path = f.get("path", "")
            raw_content = f.get("content")

            if raw_content is None and f.get("url"):
                raw_content = await self.fetch_raw_file_content(f["url"])

            if not raw_content:
                summary.binary_files_skipped += 1
                continue

            doc_id = f"doc-gh-{hashlib.md5(file_path.encode('utf-8')).hexdigest()[:12]}"
            references = self.parse_references(raw_content, file_path)
            content_chunks = self.chunk_content(raw_content)

            for idx, chunk_text in enumerate(content_chunks):
                checksum = hashlib.sha256(chunk_text.encode("utf-8")).hexdigest()
                chunk_id = f"chk-{doc_id}-{idx}"
                active_chunk_ids.add(chunk_id)

                # Check if chunk exists in DB with unchanged checksum
                existing_res = await session.execute(
                    select(Chunk).where(Chunk.id == chunk_id)
                )
                existing_chunk = existing_res.scalar_one_or_none()

                if existing_chunk and existing_chunk.checksum == checksum:
                    existing_chunk.deleted_at = None
                    summary.chunks_skipped_unchanged += 1
                    continue

                vector_embedding = self.generate_dummy_embedding(chunk_text)

                if existing_chunk:
                    # Update existing chunk
                    existing_chunk.content = chunk_text
                    existing_chunk.checksum = checksum
                    existing_chunk.references_json = json.dumps(references)
                    existing_chunk.embedding_vector_str = json.dumps(vector_embedding)
                    existing_chunk.permissions_ref = permissions_ref
                    existing_chunk.deleted_at = None
                    existing_chunk.last_indexed_at = datetime.now(timezone.utc)
                    summary.chunks_updated += 1
                else:
                    # Create new Chunk
                    new_chunk = Chunk(
                        id=chunk_id,
                        source_id=source.id,
                        document_id=doc_id,
                        parent_doc_id=file_path,  # Graph-Ready parent doc path
                        content=chunk_text,
                        permissions_ref=permissions_ref,
                        checksum=checksum,
                        references_json=json.dumps(references),
                        embedding_vector_str=json.dumps(vector_embedding),
                    )
                    session.add(new_chunk)
                    summary.chunks_created += 1

        # 3. Mark deleted/stale chunks
        all_source_chunks_res = await session.execute(
            select(Chunk).where(Chunk.source_id == source.id, Chunk.deleted_at.is_(None))
        )
        for chk in all_source_chunks_res.scalars().all():
            if chk.id not in active_chunk_ids:
                chk.deleted_at = datetime.now(timezone.utc)

        # 4. Update Source.updated_at
        source.updated_at = datetime.now(timezone.utc)
        await session.commit()


        return summary
