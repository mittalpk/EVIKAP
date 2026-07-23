"""
VigilRAG Unified Knowledge API Router
Consolidates GitHub and Azure Blob Storage truth sources.
Supports Smart Hybrid Search (GitHub Code + Azure Wiki).
"""
import os
import uuid
import datetime
import httpx
import base64
import logging
import urllib.parse
import re
import asyncio
from functools import lru_cache
from fastapi import APIRouter, Body, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from typing import Any, List, Optional
from azure.storage.blob.aio import BlobServiceClient

from ..client import http_client
from ..config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

# --- Configuration ---

MOCK_DATA_DIR = os.environ.get("MOCK_DATA_PATH", "/app/mock_data")
GITHUB_PAT = os.environ.get("GITHUB_PAT") or os.environ.get("github-pat")
GITHUB_REPO = "mittalpk/repos"

# Azure Config
AZURE_STORAGE_CONNECTION_STRING = os.environ.get("AZURE_STORAGE_CONNECTION_STRING") or os.environ.get("azure-storage-connection-string")
if AZURE_STORAGE_CONNECTION_STRING:
    AZURE_STORAGE_CONNECTION_STRING = AZURE_STORAGE_CONNECTION_STRING.strip('"').strip("'")

AZURE_WIKI_CONTAINER = os.environ.get("AZURE_WIKI_CONTAINER") or os.environ.get("azure-wiki-container") or "vigilrag-wiki"
if AZURE_WIKI_CONTAINER:
    AZURE_WIKI_CONTAINER = AZURE_WIKI_CONTAINER.strip('"').strip("'")

# --- Subsystems ---

class GitHubSearchSubsystem:
    @staticmethod
    def extract_keywords(query: str) -> List[str]:
        stop_words = {"what", "is", "the", "in", "for", "with", "a", "an", "of", "to", "our", "how"}
        words = re.findall(r'\w+', query.lower())
        return [w for w in words if w not in stop_words and len(w) > 2]

    @staticmethod
    async def search_code(query: str) -> List[dict]:
        if not GITHUB_PAT:
            return []
        
        headers = {"Authorization": f"token {GITHUB_PAT}", "Accept": "application/vnd.github.v3+json", "User-Agent": "VigilRAG-System"}
        client = http_client.get_client()
        try:
            # 1. Search API
            encoded_query = urllib.parse.quote(f"{query} repo:{GITHUB_REPO}")
            url = f"https://api.github.com/search/code?q={encoded_query}"
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                items = resp.json().get("items", [])
                if items: return [{"path": i["path"], "url": i["html_url"], "sha": i["sha"]} for i in items[:3]]
            
            # 2. Fallback Tree Scan
            keywords = GitHubSearchSubsystem.extract_keywords(query)
            tree_url = f"https://api.github.com/repos/{GITHUB_REPO}/git/trees/main?recursive=1"
            tree_resp = await client.get(tree_url, headers=headers)
            matches = []
            if tree_resp.status_code == 200:
                tree_data = tree_resp.json().get("tree", [])
                for item in tree_data:
                    if item["type"] == "blob" and any(kw in item["path"].lower() for kw in keywords):
                        matches.append({"path": item["path"], "url": f"https://github.com/{GITHUB_REPO}/blob/main/{item['path']}", "sha": item["sha"]})
            return matches[:3]
        except Exception as e:
            logger.error(f"GitHub Error: {e}")
            return []

    @staticmethod
    async def get_file_content(path: str) -> str:
        if not GITHUB_PAT: return ""
        headers = {"Authorization": f"token {GITHUB_PAT}", "User-Agent": "VigilRAG-System"}
        client = http_client.get_client()
        try:
            resp = await client.get(f"https://api.github.com/repos/{GITHUB_REPO}/contents/{path}", headers=headers)
            if resp.status_code == 200:
                c = resp.json().get("content", "")
                return base64.b64decode(c).decode("utf-8") if c else ""
            return ""
        except Exception: return ""

class AzureWikiSubsystem:
    """
    Sifts through Azure Blob Storage for Wiki documentation.
    Falls back to local mock data if connection string is missing.
    """
    @staticmethod
    async def search_wiki(query: str) -> List[dict]:
        query_terms = query.lower().split()
        results = []

        # 1. Cloud Search (Azure Blobs)
        if AZURE_STORAGE_CONNECTION_STRING:
            try:
                blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
                async with blob_service_client:
                    container_client = blob_service_client.get_container_client(AZURE_WIKI_CONTAINER)
                    
                    async def process_blob(blob):
                        if blob.name.endswith(".md"):
                            blob_client = container_client.get_blob_client(blob.name)
                            stream = await blob_client.download_blob()
                            data = await stream.readall()
                            content = data.decode("utf-8")
                            if any(term in content.lower() for term in query_terms):
                                return {
                                    "content": content,
                                    "id": f"AZ-{blob.name}",
                                    "url": f"https://{blob_service_client.account_name}.blob.core.windows.net/{AZURE_WIKI_CONTAINER}/{blob.name}",
                                    "source": "Azure Blob Storage (Wiki)"
                                }
                        return None

                    tasks = []
                    async for blob in container_client.list_blobs():
                        tasks.append(process_blob(blob))
                    
                    if tasks:
                        blob_results = await asyncio.gather(*tasks)
                        results.extend([r for r in blob_results if r])
                
                if results: return results
            except Exception as e:
                logger.error(f"Azure Storage Error: {str(e)}")

        # 2. Local Fallback (Simulation Mode) - Gated by DEMO_MODE
        if settings.demo_mode:
            wiki_dir = os.path.join(MOCK_DATA_DIR, "wiki")
            if os.path.exists(wiki_dir):
                for filename in os.listdir(wiki_dir):
                    if filename.endswith(".md"):
                        with open(os.path.join(wiki_dir, filename), "r") as f:
                            content = f.read()
                            if any(term in content.lower() for term in query_terms):
                                results.append({
                                    "content": content,
                                    "id": f"CONF-{filename}",
                                    "url": f"https://vigilrag.wiki/{filename}",
                                    "source": "Confluence (Simulated)"
                                })
        return results

class DatabaseSubsystem:
    @staticmethod
    async def query_schemas(query: str) -> List[dict]:
        """Searches for SQL schemas and data models in the repositories."""
        headers = {"Authorization": f"token {GITHUB_PAT}", "User-Agent": "VigilRAG-System"} if GITHUB_PAT else {}
        results = []
        client = http_client.get_client()
        try:
            # 1. Search GitHub for .sql files
            if GITHUB_PAT:
                tree_url = f"https://api.github.com/repos/{GITHUB_REPO}/git/trees/main?recursive=1"
                tree_resp = await client.get(tree_url, headers=headers)
                if tree_resp.status_code == 200:
                    tree_data = tree_resp.json().get("tree", [])
                    for item in tree_data:
                        ext = item["path"].split(".")[-1].lower()
                        if ext in ["sql", "prisma", "db"] or "schema" in item["path"].lower():
                            results.append({
                                "path": item["path"],
                                "url": f"https://github.com/{GITHUB_REPO}/blob/main/{item['path']}",
                                "id": f"DB-{item['path'].split('/')[-1]}"
                            })
            return results[:3]
        except Exception: return results[:3]

class UnifiedSearchEngine:
    @staticmethod
    async def search(query: str, systems: List[str]) -> tuple[List[Any], List[Any]]:
        facts, metadata = [], []

        # 1. Search Wiki (Azure + Local Fallback)
        if "confluence" in systems:
            wiki_results = await AzureWikiSubsystem.search_wiki(query)
            for res in wiki_results:
                facts.append({"fact": f"Documentation: {res['content'][:150]}...", "confidence": 0.95, "derived_from_stable_ids": [res["id"]]})
                metadata.append({"source_system": res["source"], "stable_id": res["id"], "timestamp": datetime.datetime.now().isoformat(), "url": res["url"]})

        if "code_repos" in systems:
            gh_results = await GitHubSearchSubsystem.search_code(query)
            tasks = [GitHubSearchSubsystem.get_file_content(res["path"]) for res in gh_results]
            contents = await asyncio.gather(*tasks)
            
            for res, content in zip(gh_results, contents):
                filename = res["path"].split("/")[-1]
                safe_content = content[:200].replace('\n', ' ')
                facts.append({"fact": f"GitHub Source ({res['path']}): {safe_content}...", "confidence": 0.98, "derived_from_stable_ids": [filename]})
                metadata.append({"source_system": "GitHub (Live API)", "stable_id": filename, "timestamp": datetime.datetime.now().isoformat(), "url": res["url"]})

        if "databases" in systems:
            db_results = await DatabaseSubsystem.query_schemas(query)
            
            async def get_db_content(res):
                if "content" in res:
                    return res["content"]
                return await GitHubSearchSubsystem.get_file_content(res["path"])

            tasks = [get_db_content(res) for res in db_results]
            contents = await asyncio.gather(*tasks)

            for res, content in zip(db_results, contents):
                safe_content = content[:200].replace('\n', ' ')
                facts.append({"fact": f"SQL Schema ({res['path']}): {safe_content}...", "confidence": 0.99, "derived_from_stable_ids": [res["id"]]})
                metadata.append({"source_system": "Database Metadata (Live)", "stable_id": res["id"], "timestamp": datetime.datetime.now().isoformat(), "url": res["url"]})

        return facts, metadata

# --- Schemas ---

class KnowledgeQuery(BaseModel):
    query: str = Field(...)
    target_systems: Optional[List[str]] = Field(default=None)

class KnowledgeAnswerJSON(BaseModel):
    answer_synthesis: str
    facts: List[Any]
    metadata: List[Any]
    execution_time_ms: int

# --- API & Hybrid Retrieval Endpoint (US-008) ---

from backend.app.models import AsyncSessionLocal
from backend.app.schemas import EvidenceItem, HybridRetrievalResponse, KnowledgeQueryRequest
from backend.app.services.hybrid_retrieval_engine import HybridRetrievalEngine

retrieval_engine = HybridRetrievalEngine()


@router.post("/query", response_model=HybridRetrievalResponse)
async def query_knowledge(
    body: KnowledgeQueryRequest = Body(...),
):
    start_time = datetime.datetime.now()
    trace_id = f"trc-{uuid.uuid4().hex[:12]}"

    # Execute Hybrid Search over SQLAlchemy database chunks
    async with AsyncSessionLocal() as session:
        evidence = await retrieval_engine.retrieve(
            session=session,
            query=body.query,
            requester_identity=body.requester_identity or "user@example.com",
            top_k=body.top_k,
        )

    exec_time_ms = (datetime.datetime.now() - start_time).microseconds // 1000

    response = HybridRetrievalResponse(
        evidence=evidence,
        trace_id=trace_id,
        execution_time_ms=exec_time_ms,
        query=body.query,
        total_retrieved=len(evidence),
    )

    headers = {}
    if len(evidence) == 0:
        headers["X-VigilRAG-Warning"] = "corpus-empty-or-filtered"

    return JSONResponse(content=response.model_dump(), headers=headers)

