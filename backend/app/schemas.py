"""
Hybrid Retrieval & Evidence Types (US-008).

Defines Pydantic models and schemas for hybrid retrieval query requests and responses:
- KnowledgeQueryRequest
- EvidenceItem
- HybridRetrievalResponse
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class KnowledgeQueryRequest(BaseModel):
    query: str = Field(..., description="Natural language search query")
    requester_identity: Optional[str] = Field("user@example.com", description="Identity of requester for permission filtering")
    top_k: int = Field(5, ge=1, le=20, description="Number of top evidence items to return")
    target_systems: Optional[List[str]] = Field(None, description="Optional system filter (e.g. ['confluence', 'code_repos'])")


class EvidenceItem(BaseModel):
    chunk_id: str
    content: str
    source_url: str
    relevance_score: float
    source_id: str
    parent_doc_id: Optional[str] = None
    references: List[str] = Field(default_factory=list)
    rerank_score: Optional[float] = None
    permissions_ref: str = "public"


class HybridRetrievalResponse(BaseModel):
    evidence: List[EvidenceItem]
    trace_id: str
    execution_time_ms: int
    query: str
    total_retrieved: int
