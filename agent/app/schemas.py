"""
Pydantic Schemas for VigilRAG Agent Service (US-011).
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class AgentQueryRequest(BaseModel):
    query: str = Field(..., description="Natural language question to submit")
    requester_identity: Optional[str] = Field(None, description="Authenticated user identity / email")
    top_k: int = Field(default=5, ge=1, le=20, description="Top-K evidence items to retrieve")


class Citation(BaseModel):
    chunk_id: str = Field(..., description="Unique ID of the retrieved chunk")
    source_url: str = Field(..., description="Canonical URL of the source document")
    source_type: str = Field(default="unknown", description="Source connector type (github_repo, confluence_wiki)")
    content_excerpt: str = Field(..., description="Truncated text excerpt of the evidence chunk")


class AgentQueryResponse(BaseModel):
    answer: str = Field(..., description="Synthesised answer text from LLM")
    citations: List[Citation] = Field(default_factory=list, description="Evidence citations mapping to answer claims")
    trace_id: str = Field(..., description="Unique trace ID for telemetry and debugging")
    guardrail_flags: List[str] = Field(default_factory=list, description="Flags produced by guardrails validation")
    execution_time_ms: int = Field(..., description="End-to-end execution latency in milliseconds")
