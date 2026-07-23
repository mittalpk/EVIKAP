"""
Hybrid Retrieval Engine & Reranker Interface (US-008).

Provides:
- PassthroughReranker (Pluggable reranking interface hook; default in PI-1, active in PI-2).
- Reciprocal Rank Fusion (RRF) merge algorithm combining vector similarity & keyword BM25/FTS search.
- HybridRetrievalEngine executing DB queries against SQLAlchemy models with permission filtering.
"""

from typing import Dict, List, Optional, Protocol
import json
import logging
import math
import re
from sqlalchemy import select, text

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models import Chunk, Source
from backend.app.schemas import EvidenceItem
from backend.app.services.ingestion_utils import generate_embedding_vector

logger = logging.getLogger(__name__)


class RerankerInterface(Protocol):
    def rerank(self, query: str, items: List[EvidenceItem]) -> List[EvidenceItem]:
        ...


class PassthroughReranker:
    """Default PI-1 reranker hook that leaves ranks intact (passthrough)."""

    def rerank(self, query: str, items: List[EvidenceItem]) -> List[EvidenceItem]:
        return items


def compute_rrf_scores(
    vector_ranked_ids: List[str],
    keyword_ranked_ids: List[str],
    k: int = 60,
) -> Dict[str, float]:
    """Reciprocal Rank Fusion (RRF) algorithm: score(d) = 1/(k + r_vector) + 1/(k + r_keyword)."""
    scores: Dict[str, float] = {}

    for rank, chunk_id in enumerate(vector_ranked_ids, start=1):
        scores[chunk_id] = scores.get(chunk_id, 0.0) + (1.0 / (k + rank))

    for rank, chunk_id in enumerate(keyword_ranked_ids, start=1):
        scores[chunk_id] = scores.get(chunk_id, 0.0) + (1.0 / (k + rank))

    return scores


from backend.app.services.permission_evaluator import PermissionEvaluator


class HybridRetrievalEngine:
    """Executes hybrid vector + keyword search with RRF merge and permission filtering."""

    def __init__(
        self,
        reranker: Optional[RerankerInterface] = None,
        permission_evaluator: Optional[PermissionEvaluator] = None,
    ):
        self.reranker = reranker or PassthroughReranker()
        self.permission_evaluator = permission_evaluator or PermissionEvaluator()

    async def retrieve(
        self,
        session: AsyncSession,
        query: str,
        requester_identity: str,
        top_k: int = 5,
    ) -> List[EvidenceItem]:
        # Require non-empty requester_identity
        if not requester_identity:
            return []

        """Performs hybrid vector + keyword search and RRF merge."""
        # 1. Generate query embedding
        query_vector = generate_embedding_vector(query)

        # 2. Extract query keywords for DB candidate pre-filtering
        query_terms = [w.lower() for w in re.findall(r"\w+", query) if len(w) > 2][:10]

        # 3. Fetch candidate Chunks from DB with SQL candidate bounds (top_k * 10)
        try:
            from sqlalchemy import and_, or_
            active_filter = Chunk.deleted_at.is_(None)
            if query_terms:
                conditions = [Chunk.content.ilike(f"%{term}%") for term in query_terms[:5]]
                stmt = select(Chunk).where(and_(active_filter, or_(*conditions))).limit(top_k * 10)
                res = await session.execute(stmt)
                chunks: List[Chunk] = list(res.scalars().all())
            else:
                chunks = []

            # Fallback if keyword filter returns insufficient candidates
            if len(chunks) < top_k * 2:
                stmt_fallback = select(Chunk).where(active_filter).limit(top_k * 10)
                res_fb = await session.execute(stmt_fallback)
                chunks = list(res_fb.scalars().all())
        except Exception as exc:
            logger.warning(f"DB query error (uninitialized DB or table missing): {exc}")
            return []


        if not chunks:
            return []

        # 4. Vector Similarity Search (Cosine similarity over candidate set)
        def cosine_similarity(v1: List[float], v2: List[float]) -> float:
            if not v1 or not v2 or len(v1) != len(v2):
                return 0.0
            dot = sum(a * b for a, b in zip(v1, v2))
            norm1 = math.sqrt(sum(a * a for a in v1))
            norm2 = math.sqrt(sum(b * b for b in v2))
            if norm1 == 0.0 or norm2 == 0.0:
                return 0.0
            return dot / (norm1 * norm2)

        vector_scores: List[tuple[Chunk, float]] = []
        for chk in chunks:
            if chk.embedding_vector_str:
                try:
                    vec = json.loads(chk.embedding_vector_str)
                    sim = cosine_similarity(query_vector, vec)
                    vector_scores.append((chk, sim))
                except Exception:
                    vector_scores.append((chk, 0.0))
            else:
                vector_scores.append((chk, 0.0))

        vector_scores.sort(key=lambda x: x[1], reverse=True)
        vector_ranked_ids = [c[0].id for c in vector_scores]

        # 5. Keyword / Full-Text Search Overlap Scoring
        query_terms_set = set(query_terms)

        def keyword_score(content: str) -> float:
            if not content or not query_terms_set:
                return 0.0
            words = set(re.findall(r"\w+", content.lower()))
            matches = query_terms_set.intersection(words)
            return len(matches) / float(len(query_terms_set))

        keyword_scores: List[tuple[Chunk, float]] = []
        for chk in chunks:
            score = keyword_score(chk.content)
            keyword_scores.append((chk, score))

        keyword_scores.sort(key=lambda x: x[1], reverse=True)
        keyword_ranked_ids = [c[0].id for c in keyword_scores]


        # 5. Reciprocal Rank Fusion (RRF) Merge
        rrf_scores = compute_rrf_scores(vector_ranked_ids, keyword_ranked_ids, k=60)

        # 6. Map to EvidenceItems & Apply Permission Filter
        chunk_map = {chk.id: chk for chk in chunks}
        sorted_rrf_ids = sorted(rrf_scores.keys(), key=lambda cid: rrf_scores[cid], reverse=True)

        evidence_items: List[EvidenceItem] = []
        for cid in sorted_rrf_ids:
            chk = chunk_map[cid]

            allowed = await self.permission_evaluator.evaluate_chunk_access(
                session=session,
                chunk=chk,
                requester_identity=requester_identity,
            )
            if not allowed:
                logger.info(f"Permission denied for requester '{requester_identity}' on chunk '{chk.id}' (source: '{chk.source_id}')")
                continue


            try:
                refs = json.loads(chk.references_json) if chk.references_json else []
            except Exception:
                refs = []

            item = EvidenceItem(
                chunk_id=chk.id,
                content=chk.content,
                source_url=f"https://vigilrag.internal/sources/{chk.source_id}/chunks/{chk.id}",
                relevance_score=round(rrf_scores[cid], 4),
                source_id=chk.source_id,
                parent_doc_id=chk.parent_doc_id,
                references=refs,
                permissions_ref=chk.permissions_ref,
            )
            evidence_items.append(item)

        # 7. Apply Reranking hook
        reranked_items = self.reranker.rerank(query, evidence_items)

        return reranked_items[:top_k]
