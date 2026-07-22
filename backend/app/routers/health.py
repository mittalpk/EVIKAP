"""Health-check router — no auth required."""
from fastapi import APIRouter
import os
from ..config import settings

router = APIRouter()

@router.get("", summary="Health check")
async def health():
    # Simple, safe health check reporting liveness
    return {
        "status": "healthy",
        "service": "vigilrag-backend",
        "configured": settings.internal_api_key.get_secret_value() not in ("", "change-me-in-production")
    }

