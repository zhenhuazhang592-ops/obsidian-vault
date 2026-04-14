# Dify Writer MCP Server - FastAPI main application
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path

import psutil
import uvicorn
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from app.core.config import CACHE_DIR, LOG_FILE, MCP_SERVER_KEY, SESSIONS_DIR
from app.core.session import SessionState
from app.core.utils import safe_json_parse
from app.tools.base import get_registry

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Dify Writer MCP Server", version="1.0.0")

# CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Auth Middleware ───────────────────────────────────────────────

async def verify_mcp_key(x_mcp_key: str = Header(None)) -> str:
    """Verify X-MCP-Key header."""
    if x_mcp_key != MCP_SERVER_KEY:
        raise HTTPException(status_code=401, detail="Invalid MCP key")
    return x_mcp_key


# ─── Startup ───────────────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("Dify Writer MCP Server started")


# ─── Health Endpoints ─────────────────────────────────────────────

@app.get("/health")
async def health():
    """
    Lightweight health check (no auth).
    Dify workflow polls this before starting.
    """
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/health/detailed")
async def health_detailed(x_mcp_key: str = Header(None)):
    """Detailed health with process stats. Requires auth."""
    await verify_mcp_key(x_mcp_key)
    process = psutil.Process()
    return {
        "status": "ok",
        "pid": process.pid,
        "cpu_percent": process.cpu_percent(interval=0.1),
        "memory_mb": process.memory_info().rss / (1024 * 1024),
        "uptime_seconds": time.time() - process.create_time(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ─── Metrics ───────────────────────────────────────────────────────

@app.get("/metrics")
async def metrics():
    """
    Observability metrics (no auth).
    Returns: requests_total, latency_p50/p95/p99, tool_success_rate, active_sessions, errors_total.
    """
    metrics_file = CACHE_DIR / "metrics.json"
    if metrics_file.exists():
        try:
            with open(metrics_file) as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            pass

    # Default metrics
    return {
        "requests_total": 0,
        "latency_p50_ms": 0,
        "latency_p95_ms": 0,
        "latency_p99_ms": 0,
        "tool_success_rate": {},
        "active_sessions": 0,
        "errors_total": 0,
    }


def _record_request(tool: str, latency_ms: float, success: bool, error_type: str | None = None):
    """Record request to metrics file."""
    metrics_file = CACHE_DIR / "metrics.json"
    try:
        if metrics_file.exists():
            with open(metrics_file) as f:
                m = json.load(f)
        else:
            m = {
                "requests_total": 0,
                "latencies": [],
                "tool_success_rate": {},
                "errors_total": 0,
            }
    except (OSError, json.JSONDecodeError):
        m = {"requests_total": 0, "latencies": [], "tool_success_rate": {}, "errors_total": 0}

    m["requests_total"] = m.get("requests_total", 0) + 1
    m["latencies"] = m.get("latencies", []) + [latency_ms]
    m["latencies"] = m["latencies"][-1000:]  # Keep last 1000
    if len(m["latencies"]) >= 10:
        sorted_latencies = sorted(m["latencies"])
        n = len(sorted_latencies)
        m["latency_p50_ms"] = sorted_latencies[int(n * 0.5)]
        m["latency_p95_ms"] = sorted_latencies[int(n * 0.95)]
        m["latency_p99_ms"] = sorted_latencies[int(n * 0.99)]

    tool_rate = m["tool_success_rate"].get(tool, {"success": 0, "total": 0})
    tool_rate["total"] = tool_rate.get("total", 0) + 1
    if success:
        tool_rate["success"] = tool_rate.get("success", 0) + 1
    m["tool_success_rate"][tool] = tool_rate

    if not success:
        m["errors_total"] = m.get("errors_total", 0) + 1

    with open(metrics_file, "w") as f:
        json.dump(m, f)


# ─── Session Endpoints ─────────────────────────────────────────────

@app.post("/sessions")
async def create_session(
    body: dict,
    x_mcp_key: str = Header(None),
):
    """Create new session state."""
    await verify_mcp_key(x_mcp_key)
    topic = body.get("topic", "")
    platform = body.get("platform", "wechat")
    session = SessionState.create(topic=topic, platform=platform)
    session.write_checkpoint()
    return {"session_id": session.session_id, "state": session.state}


@app.get("/sessions/{session_id}")
async def get_session(
    session_id: str,
    x_mcp_key: str = Header(None),
):
    """Get session state."""
    await verify_mcp_key(x_mcp_key)
    session = SessionState.load(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"session_id": session_id, "state": session.state}


@app.post("/sessions/{session_id}/checkpoint")
async def write_session_checkpoint(
    session_id: str,
    updates: dict,
    x_mcp_key: str = Header(None),
):
    """Write session checkpoint with updates."""
    await verify_mcp_key(x_mcp_key)
    session = SessionState.load(session_id)
    if not session:
        session = SessionState(session_id)
    session.update(**updates)
    try:
        session.write_checkpoint()
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    return {"session_id": session_id, "state": session.state}


# ─── Tool Endpoints ─────────────────────────────────────────────────

@app.post("/tools")
async def call_tool(
    body: dict,
    x_mcp_key: str = Header(None),
):
    """
    Synchronous tool invocation.
    POST /tools with {"tool": "name", "params": {...}}
    """
    await verify_mcp_key(x_mcp_key)
    start = time.time()

    tool_name = body.get("tool", "")
    params = body.get("params", {})
    session_id = body.get("session_id")

    registry = get_registry()
    if not registry.has(tool_name):
        raise HTTPException(status_code=404, detail=f"Tool not found: {tool_name}")

    tool = registry.get(tool_name)
    try:
        result = await tool.execute(**params)
        latency_ms = (time.time() - start) * 1000
        _record_request(tool_name, latency_ms, success=True)
        logger.info(
            json.dumps(
                {
                    "session_id": session_id,
                    "tool": tool_name,
                    "latency_ms": round(latency_ms, 2),
                    "success": True,
                }
            )
        )
        return {"result": result, "tool": tool_name}
    except Exception as e:
        latency_ms = (time.time() - start) * 1000
        _record_request(tool_name, latency_ms, success=False, error_type=type(e).__name__)
        logger.error(f"Tool {tool_name} failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/tools")
async def list_tools(x_mcp_key: str = Header(None)):
    """List all available tools."""
    await verify_mcp_key(x_mcp_key)
    registry = get_registry()
    return {"tools": registry.list_tools()}


# ─── SSE Streaming Endpoint ────────────────────────────────────────

@app.get("/tools/{tool}/stream")
async def stream_tool(
    tool: str,
    session_id: str = "",
    topic: str = "",
    queries: str = "",
    platform: str = "wechat",
    request: Request = None,
    x_mcp_key: str = Header(None),
):
    """
    SSE streaming for long-running tools (e.g., deep_research).
    GET /tools/deep_research/stream?topic=...&queries=...,&queries=...
    """
    await verify_mcp_key(x_mcp_key)

    registry = get_registry()
    if not registry.has(tool):
        raise HTTPException(status_code=404, detail=f"Tool not found: {tool}")

    async def event_generator():
        query_list = queries.split(",") if queries else [topic]

        def sse_event(event_type: str, data: dict) -> bytes:
            line = f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
            return line.encode("utf-8")

        # Send initial progress
        yield sse_event("progress", {
            "stage": tool,
            "status": "starting",
            "queries": query_list,
        })

        # Execute tool
        try:
            tool_instance = registry.get(tool)
            result = await tool_instance.execute(
                topic=topic,
                queries=query_list,
                platform=platform,
                session_id=session_id,
            )

            # Send completion
            yield sse_event("done", {
                "stage": tool,
                "result": result,
            })

        except Exception as e:
            yield sse_event("error", {
                "stage": tool,
                "error": str(e),
            })

        # Check for client disconnect
        if request:
            try:
                async for _ in request.stream():
                    pass
            except Exception:
                pass

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ─── Root ──────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "name": "Dify Writer MCP Server",
        "version": "1.0.0",
        "endpoints": [
            "GET /health",
            "GET /metrics",
            "POST /sessions",
            "GET /sessions/{session_id}",
            "POST /sessions/{session_id}/checkpoint",
            "POST /tools",
            "GET /tools",
            "GET /tools/{tool}/stream",
        ],
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
