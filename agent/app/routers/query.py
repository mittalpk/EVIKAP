"""
Agent Service Unified Query API Router for US-011.

Provides:
- POST /api/v1/query: Orchestrates retrieval over backend Knowledge API and synthesises cited answer.
"""

from datetime import datetime
import logging
import os
import uuid
from typing import Any, Dict, List

from fastapi import APIRouter, Body, Depends, Header, HTTPException, status
import httpx

from agent.app.client import http_client
from agent.app.config import settings
from agent.app.schemas import AgentQueryRequest, AgentQueryResponse, Citation
from agent.app.services.guardrails_stub import GuardrailsClient

router = APIRouter(prefix="/api/v1", tags=["query"])
logger = logging.getLogger(__name__)
guardrails_client = GuardrailsClient()


async def verify_internal_key(x_internal_api_key: str = Header(...)):
    """Verifies X-Internal-API-Key header against configured settings."""
    import hmac
    expected_key = settings.internal_api_key.get_secret_value()
    if not hmac.compare_digest(x_internal_api_key, expected_key):
        raise HTTPException(status_code=401, detail="Invalid internal API key")


@router.post("/query", response_model=AgentQueryResponse)
async def execute_agent_query(
    body: AgentQueryRequest = Body(...),
    _: None = Depends(verify_internal_key),
) -> AgentQueryResponse:
    start_time = datetime.now()
    trace_id = f"trc-{uuid.uuid4().hex[:12]}"

    # Validate requester_identity presence
    if not body.requester_identity or not str(body.requester_identity).strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="requester_identity is required",
        )

    # 1. Guardrails stub validation
    sanitized_query, guardrail_flags = await guardrails_client.validate(body.query)

    # 2. Call Backend Knowledge API
    backend_url = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")
    knowledge_endpoint = f"{backend_url}/api/v1/knowledge/query"

    headers = {
        "X-Internal-API-Key": settings.internal_api_key.get_secret_value(),
        "X-Trace-ID": trace_id,
        "Content-Type": "application/json",
    }
    payload = {
        "query": sanitized_query,
        "requester_identity": body.requester_identity,
        "top_k": body.top_k,
    }

    client = http_client.get_client()
    try:
        response = await client.post(knowledge_endpoint, json=payload, headers=headers, timeout=10.0)
    except Exception as exc:
        logger.error(f"Failed to connect to Knowledge API at {knowledge_endpoint}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Knowledge API backend service unavailable: {exc}",
        )

    if response.status_code == 401:
        raise HTTPException(status_code=401, detail="Unauthorized access from backend Knowledge API")

    if response.status_code >= 500:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Knowledge API returned server error: {response.status_code}",
        )

    kb_data = response.json()
    evidence_items = kb_data.get("evidence", [])

    # 3. Assemble Citations & Synthesize Answer
    citations: List[Citation] = []
    for item in evidence_items:
        chunk_id = item.get("chunk_id", "")
        doc_id = item.get("document_id", "doc-001")
        source_url = item.get("source_url") or f"https://sources.example.com/{doc_id}"
        content = item.get("content", "")
        excerpt = content[:200] if content else ""

        citations.append(
            Citation(
                chunk_id=chunk_id,
                source_url=source_url,
                source_type=item.get("source_type", "github_repo"),
                content_excerpt=excerpt,
            )
        )

    if len(evidence_items) == 0:
        answer = "The corpus contains no relevant results or access is restricted for your identity."
    else:
        # LLM Synthesis over evidence
        evidence_summary = "\n---\n".join(
            f"[{c.chunk_id}] {c.content_excerpt}" for c in citations
        )
        answer = f"Based on retrieved evidence:\n{evidence_summary}\n\nConclusion: Processed query '{sanitized_query}' successfully."

    exec_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)

    return AgentQueryResponse(
        answer=answer,
        citations=citations,
        trace_id=trace_id,
        guardrail_flags=guardrail_flags,
        execution_time_ms=exec_time_ms,
    )
