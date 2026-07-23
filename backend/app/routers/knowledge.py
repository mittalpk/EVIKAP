"""
VigilRAG Unified Knowledge API Router (US-008).

Provides:
- POST /api/v1/knowledge/query endpoint powered by HybridRetrievalEngine over database chunks.
"""

import datetime
import logging
import uuid

from fastapi import APIRouter, Body, Depends
from fastapi.responses import JSONResponse

from backend.app.auth import get_current_user
from backend.app.models import AsyncSessionLocal
from backend.app.schemas import HybridRetrievalResponse, KnowledgeQueryRequest
from backend.app.services.hybrid_retrieval_engine import HybridRetrievalEngine


router = APIRouter()
logger = logging.getLogger(__name__)

retrieval_engine = HybridRetrievalEngine()


@router.post("/query", response_model=HybridRetrievalResponse)
async def query_knowledge(
    body: KnowledgeQueryRequest = Body(...),
    current_user: dict = Depends(get_current_user),
):
    start_time = datetime.datetime.now()
    trace_id = f"trc-{uuid.uuid4().hex[:12]}"

    # Extract validated requester identity from authenticated user payload
    requester_identity = current_user.get("sub", "user@example.com")

    # Execute Hybrid Search over SQLAlchemy database chunks
    async with AsyncSessionLocal() as session:
        evidence = await retrieval_engine.retrieve(
            session=session,
            query=body.query,
            requester_identity=requester_identity,
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
        try:
            async with AsyncSessionLocal() as session:
                from sqlalchemy import func, select
                from backend.app.models import Chunk
                cnt_res = await session.execute(select(func.count()).select_from(Chunk).where(Chunk.deleted_at.is_(None)))
                total_chunks = cnt_res.scalar() or 0
                if total_chunks == 0:
                    headers["X-VigilRAG-Warning"] = "corpus-empty"
                else:
                    headers["X-VigilRAG-Info"] = "all-results-filtered-by-permission"
        except Exception:
            headers["X-VigilRAG-Warning"] = "corpus-empty"

    return JSONResponse(content=response.model_dump(), headers=headers)


