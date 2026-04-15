# Dify Writer MCP Server

> Hybrid architecture: Dify Chatflow (orchestration/HITL) + Python MCP Server (local tools)

## Architecture

```
Dify Chatflow (9 nodes)
├── HITL 策略确认 ──────→ MCP Server /webhooks/dify/hitl
├── HITL 大纲确认
├── HITL 最终预览
└── 质量 Loop（85分阈值）

Python MCP Server (port 8080)
├── 10 tools (deep_research, check_quality, format_html...)
├── DifyClient (httpx + retry + metrics)
└── SessionManager (checkpoint persistence)
```

## Quick Start

```bash
cd AI工具箱/dify-writer
pip install -r requirements.txt
cp .env.example .env
# 填写 .env 中的 DIFY_API_KEY 等

uvicorn app.main:app --reload --port 8080
```

## Environment Variables

```bash
# 必填
DIFY_API_KEY=app-xxx                    # Dify API Key
DIFY_CHATFLOW_ID=xxx                    # Chatflow App ID

# HITL Webhook（必填）
DIFY_WEBHOOK_BEARER_TOKEN=xxx            # Bearer Token（openssl rand -hex 32）
DIFY_WEBHOOK_URL=https://xxx.ngrok.io/webhooks/dify/hitl

# 可选
TAVILY_API_KEY=tvly-xxx                # 深度研究
JIMENG_API_KEY=xxx                      # 即梦图像
MCP_SERVER_KEY=xxx                      # MCP Server 认证
```

## Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health` | No | Health check |
| GET | `/metrics` | No | Dify metrics (requests_total, hitl_triggered...) |
| POST | `/sessions` | Yes | Create session → Dify Chatflow |
| GET | `/sessions/{id}` | Yes | Get session state |
| POST | `/sessions/{id}/checkpoint` | Yes | Write checkpoint |
| POST | `/sessions/{id}/hitl/approve` | Yes | Approve HITL |
| POST | `/sessions/{id}/hitl/reject` | Yes | Reject HITL |
| GET | `/sessions/{id}/status` | Yes | Pipeline status |
| POST | `/webhooks/dify/hitl` | Bearer | Dify HITL callback (auto-registers) |
| POST | `/tools` | Yes | Call tool |
| GET | `/tools` | Yes | List tools |
| GET | `/tools/{tool}/stream` | Yes | SSE stream |

## DifyClient (`dify_api/client.py`)

```python
from dify_api.client import DifyClient, DifyConfig

config = DifyConfig(api_key="app-xxx")
client = DifyClient(config)

# 创建会话
result = await client.create_chatflow_session(
    chatflow_id="xxx",
    user_id="user_001",
    query="写一篇关于AI的文章",
    inputs={"platform": "wechat"},
)

# HITL 恢复
await client.resume_from_hitl(
    task_id="task_xxx",
    action="approve",
    data={"feedback": "ok"},
)

# 查询消息历史
messages = await client.get_conversation_messages(
    conversation_id="conv_xxx",
    user_id="user_001",
)
```

Features: 429 exponential backoff, structured logging, in-process metrics.

## HITL Confirm Cards

| hitl_type | 确认内容 |
|-----------|---------|
| `strategy` | 创作策略（主题/平台/风格/框架）|
| `outline` | 文章大纲（标题/章节）|
| `final_preview` | 终稿预览（质量分/字数/图像）|

## Session State (`~/.cache/dify-writer/sessions/`)

```json
{
  "session_id": "sess_xxx",
  "conversation_id": "conv_xxx",
  "status": "waiting_hitl",
  "hitl_type": "strategy",
  "current_node": "hitl_strategy"
}
```

## Testing

```bash
# 全部测试（128 tests）
pytest tests/ -v

# 分类运行
pytest tests/test_dify_client.py -v        # DifyClient 核心
pytest tests/test_dify_client_retry.py -v # httpx 重试逻辑
pytest tests/test_dify_client_metrics.py -v # metrics
pytest tests/test_integration_dify.py -v   # Mock Dify Server 集成
pytest tests/test_e2e_hitl.py -v          # E2E HITL 流程
pytest tests/test_webhook_auth.py -v      # Bearer Token 认证
```

## Tools

| Tool | Description |
|------|-------------|
| `deep_research` | 并发 Tavily 搜索 |
| `extract_author_style` | 从 Vault 提取风格 |
| `check_quality` | 质量评分（0-100）|
| `format_html` | 微信 HTML 输出 |
| `adapt_to_xhs` | XHS 适配（stub）|
| `generate_cover` | 封面图像（stub）|
| `generate_inline_images` | 内嵌图像（stub）|
| `monitor_obsidian_topics` | 话题监控（stub）|
| `record_performance` | 性能记录（stub）|
| `health` | 进程健康检查 |

## Dify Chatflow (`dify-chatflow.yaml`)

9-node pipeline with 3 HITL confirm points:

```
意图解析 → 深度研究 → 大纲生成 → HITL(策略)
    ↓ approved
大纲确认 → HITL(大纲)
    ↓ approved
写作Agent → 质量审查 → HITL(终稿)
    ↓ score>=85
封面生成 → HTML排版 → 完成
    ↓ score<85
    (loop back to 写作Agent, max 3 iterations)
```
