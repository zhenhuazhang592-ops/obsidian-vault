# Dify Writer MCP Server

> Hybrid architecture: Dify Chatflow (user interaction/HITL) + Python MCP Server (local Mac resident)

## Architecture

- **MCP Server**: FastAPI + SSE streaming on port 8080
- **Dify**: Chatflow orchestrator for 9-node pipeline + HITL
- **Session state**: `~/.cache/dify-writer/sessions/{session_id}/checkpoint.json`
- **Observability**: `GET /metrics`, structured JSON logs

## Quick Start

```bash
cd AI工具箱/dify-writer
pip install -r requirements.txt
export MCP_SERVER_KEY=your-key
export TAVILY_API_KEY=your-key
uvicorn app.main:app --reload --port 8080
```

## Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health` | No | Lightweight health check |
| GET | `/metrics` | No | Observability metrics |
| POST | `/sessions` | Yes | Create session |
| GET | `/sessions/{id}` | Yes | Get session |
| POST | `/sessions/{id}/checkpoint` | Yes | Write checkpoint |
| POST | `/tools` | Yes | Call tool |
| GET | `/tools` | Yes | List tools |
| GET | `/tools/{tool}/stream` | Yes | SSE stream |

## Tools

| Tool | Description |
|------|-------------|
| `deep_research` | Concurrent Tavily search |
| `extract_author_style` | StyleProfile from vault |
| `check_quality` | Quality scoring (0-100) |
| `format_html` | WeChat HTML output |
| `adapt_to_xhs` | XHS adaptation (stub) |
| `generate_cover` | Cover image (stub) |
| `generate_inline_images` | Inline images (stub) |
| `monitor_obsidian_topics` | Topic scanner (stub) |
| `record_performance` | Metrics recorder (stub) |
| `health` | Process health |

## Testing

```bash
pytest tests/ -v
```
