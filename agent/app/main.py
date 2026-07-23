"""Agent service API — exposes the LangGraph graph as a REST endpoint."""
from __future__ import annotations
import logging
import uvicorn
from fastapi import FastAPI, Header, HTTPException, Request, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from .graph import graph
from .client import http_client
from .config import settings

logger = logging.getLogger(__name__)

app = FastAPI(title="VigilRAG Agent Service", version="1.0.0")

@app.on_event("startup")
async def startup_event():
    import hashlib
    # Security startup guards
    internal_key = settings.internal_api_key.get_secret_value()
    internal_key_hash = hashlib.sha256(internal_key.encode()).hexdigest()
    if internal_key in ("", "change-me-in-production") or internal_key_hash == "dca9dfae9695e813dfed3443fe447d36059e8f9feb390b7385cf74e0c6a708df":
        raise RuntimeError("INTERNAL_API_KEY is not configured or uses insecure default — refusing to start")
    await http_client.start()

@app.on_event("shutdown")
async def shutdown_event():
    await http_client.stop()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from agent.app.routers import query as query_router
app.include_router(query_router.router)


# ── Security ──────────────────────────────────────────────────────────────────
import hmac
async def verify_internal_key(x_internal_api_key: str = Header(...)):
    expected_key = settings.internal_api_key.get_secret_value()
    if not hmac.compare_digest(x_internal_api_key, expected_key):
        raise HTTPException(status_code=401, detail="Invalid internal API key")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # SECURITY: Do not log or return the request body
    logger.error(f"422 Validation Error on {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )

class TaskRequest(BaseModel):
    task: str
    max_iterations: int = 10

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "vigilrag-agent"}

@app.post("/run")
async def run_task(body: TaskRequest, credentials: str = Depends(verify_internal_key)):
    from langchain_core.messages import HumanMessage
    result = await graph.ainvoke({
        "task": body.task,
        "messages": [HumanMessage(content=body.task)],
        "plan": [],
        "results": [],
        "iteration": 0,
        "max_iterations": body.max_iterations,
        "final_answer": "",
    })
    
    steps_out = []
    for r in result.get("results", []):
        if isinstance(r, dict):
            steps_out.append(f"{r.get('step', '')}: {r.get('tool', '')} -> {str(r.get('output', ''))[:100]}...")
        else:
            steps_out.append(str(r))
            
    return {
        "task": body.task, 
        "answer": result.get("final_answer"), 
        "steps": steps_out
    }

