"""VigilRAG Backend — FastAPI entry-point."""
from __future__ import annotations

import logging
import jwt
from typing import Optional, List
from fastapi import FastAPI, Depends, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .config import settings
from .routers import health, knowledge, agent, auth
from .client import http_client

logger = logging.getLogger(__name__)

# ── Auth ──────────────────────────────────────────────────────────────────────
security = HTTPBearer(auto_error=False)

async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    # 1. Allow internal service-to-service calls via X-Internal-API-Key
    internal_key = request.headers.get("X-Internal-API-Key")
    expected_key = settings.internal_api_key.get_secret_value()
    
    logger.debug(f"Auth check - Path: {request.url.path}, Method: {request.method}")
    logger.debug(f"Internal key present: {bool(internal_key)}, Expected key length: {len(expected_key)}")
    
    import hmac
    if internal_key:
        if hmac.compare_digest(internal_key, expected_key):
            logger.info(f"Internal auth verified for {request.url.path}")
            return {"sub": "internal-agent", "internal": True}
        logger.warning(f"Internal auth failure: invalid key for {request.url.path}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid internal API key"
        )

    # 2. Otherwise expect a valid JWT
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.secret_key.get_secret_value(), algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

# ── Application ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="VigilRAG Knowledge & Agent API",
    description="Unified knowledge API with LLM-enabled Q&A and multi-agent orchestration.",
    version="1.0.0",
)

@app.on_event("startup")
async def startup_event():
    import hashlib
    # Security startup guards
    internal_key = settings.internal_api_key.get_secret_value()
    jwt_secret = settings.secret_key.get_secret_value()
    admin_pw = settings.admin_password.get_secret_value()

    # Hash checks to block compromised keys without committing their plaintext values
    internal_key_hash = hashlib.sha256(internal_key.encode()).hexdigest()
    jwt_secret_hash = hashlib.sha256(jwt_secret.encode()).hexdigest()
    admin_pw_hash = hashlib.sha256(admin_pw.encode()).hexdigest()

    if internal_key in ("", "change-me-in-production") or internal_key_hash == "dca9dfae9695e813dfed3443fe447d36059e8f9feb390b7385cf74e0c6a708df":
        raise RuntimeError("INTERNAL_API_KEY is not configured or uses insecure default — refusing to start")
    if jwt_secret in ("", "change-me-in-production") or jwt_secret_hash == "1451ef1d9c49c4a19115909437f65327db2446ec820d1572e69322f4122af763":
        raise RuntimeError("SECRET_KEY is not configured or uses insecure default — refusing to start")
    if admin_pw in ("", "change-me-in-production") or admin_pw_hash == "0b48ee68f9de7a403027775ab3bf217e864de4ef1fee96e3c4b18974cc3df470":
        raise RuntimeError("ADMIN_PASSWORD is not configured or uses insecure default — refusing to start")

    await http_client.start()

@app.on_event("shutdown")
async def shutdown_event():
    await http_client.stop()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # SECURITY: Do not log or return the request body as it may contain plaintext credentials
    logger.error(f"422 Validation Error on {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])

app.include_router(
    knowledge.router,
    prefix="/api/v1/knowledge",
    tags=["Knowledge"],
    dependencies=[Depends(get_current_user)],
)
app.include_router(
    agent.router,
    prefix="/api/v1/agent",
    tags=["Agent"],
    dependencies=[Depends(get_current_user)],
)



