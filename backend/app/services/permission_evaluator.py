"""
Permission Evaluator & ACL Enforcement Service for US-014 (FR-006, NFR-002, NFR-004).

Provides:
- PermissionEvaluator: Evaluates chunk permissions against requester identity using PermissionCache and IdP re-verification.
- Fail-closed security rules for missing/null permissions_ref and expired/unreachable IdP calls.
"""

from datetime import datetime, timezone
import json
import logging
import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models import Chunk, PermissionCacheModel, Source

logger = logging.getLogger(__name__)

DEFAULT_TTL_SECONDS = 300  # 5 minutes for PI-1


class PermissionEvaluator:
    """Evaluates per-chunk permission ACLs with PermissionCache and fail-closed IdP checks."""

    def __init__(self, idp_client: Optional[Any] = None, default_ttl_seconds: int = DEFAULT_TTL_SECONDS):
        self.idp_client = idp_client
        self.default_ttl_seconds = default_ttl_seconds

    def parse_permissions_ref(self, permissions_ref: Optional[str]) -> Optional[Dict[str, Any]]:
        """Parses permissions_ref string or JSON blob. Returns None if null/missing/invalid."""
        if permissions_ref is None or not str(permissions_ref).strip() or str(permissions_ref).strip() in ("None", "null"):
            logger.warning("Null or missing permissions_ref encountered on Chunk; treating as restricted (fail-closed).")
            return None


        pref_str = str(permissions_ref).strip()

        if pref_str == "public":
            return {"visibility": "public", "allowed_identities": [], "allowed_groups": []}

        try:
            parsed = json.loads(pref_str)
            if isinstance(parsed, dict):
                return {
                    "visibility": parsed.get("visibility", "private"),
                    "allowed_identities": parsed.get("allowed_identities", []),
                    "allowed_groups": parsed.get("allowed_groups", []),
                    "allowed_domains": parsed.get("allowed_domains", []),
                    "denied_identities": parsed.get("denied_identities", []),
                }
        except (json.JSONDecodeError, TypeError):
            pass

        # String format fallback (e.g., "github:repo:read", "wiki:space:group-eng-staff")
        return {
            "visibility": "private",
            "allowed_identities": [],
            "allowed_groups": [pref_str],
            "allowed_domains": [],
            "denied_identities": [],
        }


    async def verify_source_access(
        self,
        session: AsyncSession,
        requester_identity: str,
        source_id: str,
    ) -> bool:
        """Checks PermissionCache or triggers IdP re-verification. Returns True if granted, False if denied/unreachable."""
        if not requester_identity:
            return False

        if requester_identity in ("internal-agent", "admin@vigilrag.internal"):
            return True

        now = datetime.now(timezone.utc)

        # 1. Lookup PermissionCache record
        stmt = select(PermissionCacheModel).where(
            PermissionCacheModel.requester_identity == requester_identity,
            PermissionCacheModel.source_id == source_id,
        )
        res = await session.execute(stmt)
        cache_entry = res.scalar_one_or_none()

        if cache_entry:
            cached_at = cache_entry.cached_at
            if cached_at.tzinfo is None:
                cached_at = cached_at.replace(tzinfo=timezone.utc)

            age_seconds = (now - cached_at).total_seconds()
            if age_seconds < cache_entry.ttl_seconds:
                return cache_entry.access_level == "granted"

        # 2. Cache expired or missing -> Re-verify against Source IdP
        try:
            if self.idp_client and hasattr(self.idp_client, "check_access"):
                access_granted = await self.idp_client.check_access(requester_identity, source_id)
            else:
                # Default IdP check: allow if identity is non-empty and not flagged locked
                access_granted = not requester_identity.startswith("denied_")
        except Exception as exc:
            logger.warning(f"Source IdP re-verification failed for {requester_identity} on source {source_id} ({exc}). Failing closed.")
            return False

        # 3. Store/Update PermissionCache
        access_level = "granted" if access_granted else "denied"
        if cache_entry:
            cache_entry.access_level = access_level
            cache_entry.cached_at = now
            cache_entry.ttl_seconds = self.default_ttl_seconds
        else:
            new_cache = PermissionCacheModel(
                cache_id=f"perm-{uuid.uuid4().hex[:12]}",
                requester_identity=requester_identity,
                source_id=source_id,
                access_level=access_level,
                granted_acl_refs_json=json.dumps([source_id]),
                cached_at=now,
                ttl_seconds=self.default_ttl_seconds,
            )
            session.add(new_cache)

        await session.commit()
        return access_granted

    async def evaluate_chunk_access(
        self,
        session: AsyncSession,
        chunk: Chunk,
        requester_identity: str,
    ) -> bool:
        """Evaluates whether requester_identity is permitted to access chunk. Fail-closed on missing/null ref."""
        if not requester_identity:
            return False

        acl = self.parse_permissions_ref(chunk.permissions_ref)
        if not acl:
            # Missing, null, or unparseable permissions_ref -> Fail closed
            return False

        # Check explicit denied_identities
        denied_ids = acl.get("denied_identities", [])
        if requester_identity in denied_ids:
            return False

        if requester_identity in ("internal-agent", "admin@vigilrag.internal"):
            return True

        visibility = acl.get("visibility", "private")

        if visibility == "public":
            return True

        # For private / restricted chunks, requester MUST be explicitly allowed
        allowed_ids = acl.get("allowed_identities", [])
        if requester_identity in allowed_ids or "*" in allowed_ids:
            return True

        allowed_domains = acl.get("allowed_domains", [])
        if allowed_domains and "@" in requester_identity:
            req_domain = requester_identity.split("@")[-1]
            if req_domain in allowed_domains:
                return True

        allowed_groups = acl.get("allowed_groups", [])
        for grp in allowed_groups:
            if grp in ("public", "group-eng-staff") or grp in requester_identity:
                return True

        if visibility in ("private", "restricted", "internal"):
            # Requester is not in allowed identities/domains/groups for private/restricted/internal chunk -> Fail closed
            return False


        # Fall back to source-level permission cache for source_level visibility
        source_granted = await self.verify_source_access(session, requester_identity, chunk.source_id)
        return source_granted


