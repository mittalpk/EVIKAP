"""
VigilRAG Extensible Multi-Agent System Tools.
These tools now call the internal Knowledge API to provide data-driven 
search results from the simulated source systems.
"""
from langchain_core.tools import tool
import httpx
import os
import json
import logging
from .client import http_client

# Setup logging
logger = logging.getLogger(__name__)

# Internal API URL for tool communication
BACKEND_URL = os.environ.get("BACKEND_URL", "http://backend:8000")
logger.info(f"Agent configured with BACKEND_URL: {BACKEND_URL}")

async def _search_unified_api(query: str, system: str) -> str:
    """Internal helper to call the Knowledge API router."""
    from .config import settings
    client = http_client.get_client()
    try:
        api_key = settings.internal_api_key.get_secret_value()
        logger.debug(f"Calling {BACKEND_URL}/api/v1/knowledge/query for system={system}, api_key length={len(api_key)}")
        
        response = await client.post(
            f"{BACKEND_URL}/api/v1/knowledge/query",
            json={"query": query, "target_systems": [system]},
            headers={"X-Internal-API-Key": api_key},
            timeout=30.0
        )
        
        logger.debug(f"Knowledge API response: status={response.status_code}")
        if response.status_code == 200:
            return response.text
        
        logger.error(f"Knowledge API returned {response.status_code}: {response.text[:100]}")
        return json.dumps({"error": f"API returned {response.status_code}", "facts": [], "metadata": []})
    except Exception as e:
        logger.error(f"Error calling Knowledge API: {e}")
        return json.dumps({"error": str(e), "facts": [], "metadata": []})

@tool
async def search_confluence(query: str) -> str:
    """Search Confluence for internal business documentation and product specs."""
    return await _search_unified_api(query, "confluence")

@tool
async def query_code_repositories(search_term: str) -> str:
    """Search Git repositories across the organization to find code implementations."""
    return await _search_unified_api(search_term, "code_repos")

@tool
async def search_sql_databases(natural_language_question: str) -> str:
    """Convert natural language to SQL and query metadata/production databases."""
    return await _search_unified_api(natural_language_question, "databases")

# The diverse set of tools available to the LangGraph agents
REGISTERED_TOOLS = [
    search_confluence,
    query_code_repositories,
    search_sql_databases,
]
