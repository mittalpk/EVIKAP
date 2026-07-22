"""
VigilRAG Agent Service — LangGraph StateGraph Workflow.
Provides a multi-agent graph: Planner → Executor → Evaluator → Responder.
"""
from __future__ import annotations

import os
import operator
import logging
import time
import asyncio
from typing import TypedDict, Annotated, Any

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

from .tools import REGISTERED_TOOLS

logger = logging.getLogger(__name__)

# ── Tunable Timeouts ──────────────────────────────────────────────────────────
LLM_TIMEOUT_S   = int(os.environ.get("LLM_TIMEOUT_S",   "60"))   # per LLM call
TOOL_TIMEOUT_S  = int(os.environ.get("TOOL_TIMEOUT_S",  "30"))   # per tool call


# ── State Schema ──────────────────────────────────────────────────────────────

class AgentState(TypedDict):
    task: str
    messages: Annotated[list[BaseMessage], add_messages]
    plan: list[dict[str, Any]]
    results: Annotated[list[dict[str, Any]], operator.add]
    iteration: int
    max_iterations: int
    final_answer: str


# ── Build Graph ───────────────────────────────────────────────────────────────

def build_graph() -> Any:
    """
    Compile the LangGraph multi-agent graph.
    Optimized for Speed:
    - Planner: Gemini 2.5 Flash (Low latency)
    - Executor: Parallelized tool calls (asyncio.gather)
    - Responder: Gemini 2.5 Pro (High quality)
    """
    from .config import settings
    google_api_key = settings.gemini_api_key.get_secret_value()
    
    # Fast model for planning and mapping
    llm_flash = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0,
        google_api_key=google_api_key,
    )
    
    # High-quality model for final synthesis
    llm_pro = ChatGoogleGenerativeAI(
        model="gemini-2.5-pro",
        temperature=0,
        google_api_key=google_api_key,
    )
    
    planner_llm = llm_flash.bind_tools(REGISTERED_TOOLS)

    # ── Node Implementations ──────────────────────────────────────────────────

    async def node_plan(state: AgentState) -> dict:
        start_time = time.time()
        logger.info("Generating execution plan (Flash)...")
        system = SystemMessage(content=(
            "You are an expert VigilRAG AI engineer. Break the user's task into a concrete, "
            "ordered plan of tool calls using the tools available to you. "
            "Call all relevant tools needed to answer the user's task."
        ))
        try:
            resp = await asyncio.wait_for(
                planner_llm.ainvoke([system] + state["messages"]),
                timeout=LLM_TIMEOUT_S
            )
        except asyncio.TimeoutError:
            logger.warning(f"Plan LLM call timed out after {LLM_TIMEOUT_S}s — using fallback plan.")
            return {
                "plan": [{"tool": "search_confluence", "input": {"query": state["task"]}}],
                "results": [{"step": "plan", "count": 1, "note": "timeout_fallback"}],
            }

        # Primary path: LLM responded with structured tool_calls (expected when bind_tools is used)
        plan = []
        if hasattr(resp, "tool_calls") and resp.tool_calls:
            for tc in resp.tool_calls:
                tool_name = tc.get("name", "")
                if tool_name.startswith("default_api:"):
                    tool_name = tool_name.split(":", 1)[1]
                plan.append({"tool": tool_name, "input": tc.get("args", {})})
            logger.info(f"Plan from tool_calls: {len(plan)} step(s)")

        # Fallback path: LLM responded with plain text JSON
        if not plan:
            import json, re
            text_content = ""
            if isinstance(resp.content, str):
                text_content = resp.content
            elif isinstance(resp.content, list):
                text_content = "".join([c.get("text", "") for c in resp.content if isinstance(c, dict) and "text" in c])
            match = re.search(r"\[\s*\{.*\}\s*\]", text_content, re.DOTALL)
            raw = match.group(0) if match else re.sub(r"```json|```", "", text_content).strip()
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    plan = parsed
            except Exception as e:
                logger.warning(f"Plan JSON parse failed ({e})")

        if not plan:
            logger.warning("Empty plan — using fallback.")
            plan = [{"tool": "search_confluence", "input": {"query": state["task"]}}]

        duration = time.time() - start_time
        logger.info(f"Plan generated in {duration:.2f}s: {len(plan)} step(s)")
        return {"plan": plan, "results": [{"step": "plan", "count": len(plan)}]}

    async def node_execute(state: AgentState) -> dict:
        """Parallel Execution of all planned steps."""
        start_time = time.time()
        steps = state["plan"]
        if not steps:
            return {"iteration": state["iteration"] + 1}

        logger.info(f"Executing {len(steps)} steps in parallel...")

        async def run_step(step):
            tool_name = step.get("tool", "")
            if tool_name.startswith("default_api:"):
                tool_name = tool_name.split(":", 1)[1]

            tool_input = step.get("input", {})
            tool = next((t for t in REGISTERED_TOOLS if t.name == tool_name), None)
            if not tool:
                return {"step": "execute", "tool": tool_name, "error": f"Unknown tool"}

            try:
                output = await asyncio.wait_for(tool.arun(tool_input), timeout=TOOL_TIMEOUT_S)
                return {"step": "execute", "tool": tool_name, "output": str(output)[:500]}
            except asyncio.TimeoutError:
                return {"step": "execute", "tool": tool_name, "error": "timeout"}
            except Exception as e:
                return {"step": "execute", "tool": tool_name, "error": str(e)}

        # Run all tools matching the plan concurrently
        results = await asyncio.gather(*[run_step(s) for s in steps])
        
        duration = time.time() - start_time
        logger.info(f"Parallel execution finished in {duration:.2f}s")
        return {
            "iteration": len(steps),
            "results": results,
        }

    async def node_evaluate(state: AgentState) -> dict:
        return {}

    def should_continue(state: AgentState) -> str:
        # After parallel execution, we jump to response synthesis
        return "respond"

    async def node_respond(state: AgentState) -> dict:
        logger.info("Composing final response (Pro)...")
        summary = "\n".join(
            f"- {r.get('tool')}: {r.get('output', r.get('error', 'ok'))}"
            for r in state["results"]
            if r.get("step") == "execute"
        )
        system = SystemMessage(content=(
            f"You are summarizing the outcome of an AI agent task.\n"
            f"Execution log:\n{summary}\n"
            f"Write a concise professional summary for the user. Focus on facts found."
        ))
        resp = await llm_pro.ainvoke([system] + state["messages"])

        text_content = ""
        if isinstance(resp.content, str):
            text_content = resp.content
        elif isinstance(resp.content, list):
            text_content = "".join([c.get("text", "") for c in resp.content if isinstance(c, dict) and "text" in c])
            if not text_content: text_content = str(resp.content)
            
        return {"final_answer": text_content}

    # ── Wire Graph ────────────────────────────────────────────────────────────
    workflow = StateGraph(AgentState)

    workflow.add_node("plan", node_plan)
    workflow.add_node("execute", node_execute)
    workflow.add_node("evaluate", node_evaluate)
    workflow.add_node("respond", node_respond)

    workflow.set_entry_point("plan")
    workflow.add_edge("plan", "execute")
    workflow.add_edge("execute", "evaluate")
    workflow.add_conditional_edges("evaluate", should_continue, {"execute": "execute", "respond": "respond"})
    workflow.add_edge("respond", END)

    return workflow.compile()


# ── Singleton Graph ───────────────────────────────────────────────────────────
graph = build_graph()
