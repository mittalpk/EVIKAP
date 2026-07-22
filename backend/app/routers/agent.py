"""Agent router — proxies task execution to the ca-vigilrag-agent service."""
import os
import logging
import httpx
from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Any
from ..config import settings
from ..client import http_client

router = APIRouter()
logger = logging.getLogger(__name__)

# Production Internal ACA URL (Internal Ingress)
# Try environment variable first, then fall back to internal DNS, then external
AGENT_SERVICE_URL = os.environ.get(
    "AGENT_SERVICE_URL",
    None
) or os.environ.get(
    "AGENT_FQDN",
    None
) or "http://ca-vigilrag-agent:8000"

logger.info(f"Agent service configured at: {AGENT_SERVICE_URL}")


class AgentTaskRequest(BaseModel):
    task: str
    max_iterations: int = 10
    context: dict[str, Any] = {}


class AgentTaskResponse(BaseModel):
    task: str
    answer: Optional[str] = None
    steps: List[str] = Field(default_factory=list)


@router.post("/run", response_model=AgentTaskResponse)
async def run_agent_task(body: AgentTaskRequest = Body(...)):
    """Proxy the task to the LangGraph agent service and return its result."""
    try:
        logger.info(f"Running agent task: {body.task[:100]}... via {AGENT_SERVICE_URL}/run")
        
        client = http_client.get_client()
        
        # Retrieve the internal API key from settings
        internal_key = settings.internal_api_key.get_secret_value()
        logger.debug(f"Using internal API key: {internal_key[:3]}...")
        
        try:
            resp = await client.post(
                f"{AGENT_SERVICE_URL}/run",
                json={
                    "task": body.task, 
                    "max_iterations": body.max_iterations, 
                    "context": body.context
                },
                headers={"X-Internal-API-Key": internal_key},
                timeout=240.0
            )
            resp.raise_for_status()
        except httpx.ConnectError as e:
            logger.error(f"Cannot connect to agent service at {AGENT_SERVICE_URL}: {e}")
            raise HTTPException(
                status_code=503, 
                detail=f"Agent service unreachable at {AGENT_SERVICE_URL}. Check network and service status."
            )
        except httpx.TimeoutException as e:
            logger.error(f"Timeout connecting to agent service: {e}")
            raise HTTPException(status_code=504, detail="Agent service request timed out (240s)")
        except httpx.HTTPStatusError as e:
            logger.error(f"Agent service returned {e.response.status_code}: {e.response.text}")
            raise HTTPException(
                status_code=502, 
                detail=f"Agent service error ({e.response.status_code}): {e.response.text[:200]}"
            )
        
        data = resp.json()
        return AgentTaskResponse(
            task=data.get("task", body.task),
            answer=data.get("answer") or data.get("final_answer") or "Agent completed with no output.",
            steps=data.get("steps", [])
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in agent task: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
