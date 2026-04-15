# Dify Setup Guide

> 华哥专属 — Dify Chatflow 接入 MCP Server 完整指南

## 前提

- Python 3.10+
- Dify 云服务账号 或 本地部署 Dify >= 1.0.0
- ngrok（用于本地开发时公网 Webhook）

---

## 第一步：导入 Chatflow

### 1.1 登录 Dify Console

登录 [cloud.dify.ai](https://cloud.dify.ai)（或本地部署的 Dify）。

### 1.2 创建 App

1. 点击 **Create New App**
2. 选择 **Import from YAML**
3. 上传 `dify-chatflow.yaml`（位于 `AI工具箱/dify-writer/dify-chatflow.yaml`）

### 1.3 配置模型

每个 LLM 节点需要选择模型供应商：

| 节点 | 模型 | 说明 |
|------|------|------|
| 意图解析 | claude-sonnet-4-6 | 或等效 Claude 模型 |
| 写作Agent | claude-sonnet-4-6 | 主要生成模型 |
| 质量审查 | claude-haiku-4-5 | 成本优化用 Haiku |

在 Dify Console 中为每个 LLM 节点配置：
- **Model**: 选择你的模型供应商（Anthropic / OpenAI 等）
- **Credentials**:填入 API Key

### 1.4 配置 HTTP Request 节点

`deep_research` 节点调用 Tavily API，需要配置：

```
URL: https://api.tavily.com/search
Method: POST
Headers:
  Content-Type: application/json
Body:
  {"api_key": "{{TAVILY_API_KEY}}", "query": "{{query}}", "search_depth": "advanced"}
```

在 Dify Console 的 **Environment Variables** 中添加 `TAVILY_API_KEY`。

### 1.5 记录 Chatflow ID

创建完成后，从 App 详情页复制 **App ID**（格式：`xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`）。

这就是你的 `DIFY_CHATFLOW_ID`。

---

## 第二步：配置 MCP Server 环境变量

复制 `.env.example` 为 `.env`：

```bash
cd AI工具箱/dify-writer
cp .env.example .env
```

编辑 `.env`：

```bash
# Dify API（必填）
DIFY_API_KEY=app-xxxxxxxxxxxxxxxxxxxxxxxxxxxx
DIFY_BASE_URL=https://api.dify.ai/v1
DIFY_CHATFLOW_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

# HITL Webhook（必填）
# 生成一个随机字符串作为 Bearer Token
DIFY_WEBHOOK_BEARER_TOKEN=your-secure-random-token-here
# ngrok 转发后的公网 URL
DIFY_WEBHOOK_URL=https://xxxxxxxx.ngrok.io/webhooks/dify/hitl

# MCP Server
MCP_SERVER_KEY=your-mcp-server-key-here

# Tavily（用于深度研究）
TAVILY_API_KEY=tvly-xxxxxxxxxxxxxxxxxxxxxxxx
```

### 生成 Bearer Token

```bash
# macOS
openssl rand -hex 32

# Linux
head -c 32 /dev/urandom | xxd -p
```

---

## 第三步：配置 HITL Webhook

Dify 的 HITL（Human-in-the-Loop）节点通过 Webhook 回调通知外部系统。

### 3.1 在 Dify Chatflow 中添加 Webhook 节点

在 Dify Editor 中，为每个 HITL 节点配置 **Webhook**：

1. 点击 HITL 节点
2. 选择 **Webhook** 类型
3. 填写 Webhook URL：
   ```
   https://your-server.com/webhooks/dify/hitl
   ```
4. Method: `POST`
5. Authentication: `Bearer Token`
6. Token: 填写你生成的 `DIFY_WEBHOOK_BEARER_TOKEN`

### 3.2 ngrok 转发（本地开发）

```bash
# 安装 ngrok（macOS）
brew install ngrok

# 或下载 https://ngrok.com/download

# 启动转发
ngrok http 8080

# 复制 Forwarding 地址（如 https://xxxxxxxx.ngrok.io）
# 填入 DIFY_WEBHOOK_URL
```

> **注意**：ngrok 免费版每次重启后 URL 会变，需要更新 `DIFY_WEBHOOK_URL`。

---

## 第四步：启动 MCP Server

```bash
cd AI工具箱/dify-writer

# 安装依赖
pip install -r requirements.txt

# 启动服务器
uvicorn app.main:app --reload --port 8080
```

验证健康状态：

```bash
curl http://localhost:8080/health
# {"status":"ok","version":"0.1.0"}
```

---

## 第五步：端到端测试

### 5.1 Mock 模式（不需要真实 Dify 账号）

```bash
python3 -m pytest tests/ -v
# 预期：128 tests passed
```

### 5.2 真实 Dify 验证

```bash
# 确保 .env 中 DIFY_API_KEY 已填入真实值
# 确保 MCP Server 已启动（uvicorn）
# 确保 ngrok 已转发

# 创建会话
curl -X POST http://localhost:8080/sessions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-mcp-server-key-here" \
  -d '{"topic": "AI写作趋势", "platform": "wechat", "style_profile": "专业严谨"}'
```

预期流程：

1. Dify Chatflow 启动 → LLM 开始写作
2. 遇到 HITL 节点（策略确认）→ Dify 回调 `POST /webhooks/dify/hitl`
3. MCP Server 返回确认卡片
4. 用户批准 → `POST /sessions/{id}/hitl/approve`
5. Chatflow 继续 → 下一阶段...

### 5.3 HITL 手动测试

```bash
# 模拟 Dify HITL 回调
curl -X POST http://localhost:8080/webhooks/dify/hitl \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-dify-webhook-bearer-token" \
  -d '{
    "hitl_type": "strategy",
    "session_id": "sess_001",
    "user_response": "开始创作",
    "action": "approve",
    "context": {
      "topic": "AI写作趋势",
      "platform": "wechat"
    }
  }'
```

---

## 第六步：验证 Chatflow 编排

### 查看节点结构

Dify Console → 你的 App → Editor，应看到 9 个节点：

```
意图解析 (LLM)
    ↓
深度研究 (HTTP Request)
    ↓
大纲生成 (LLM)
    ↓
HITL_1_策略确认 (Human)
    ↓
大纲确认 (LLM)
    ↓
HITL_2_大纲确认 (Human)
    ↓
写作Agent (Agent)
    ↓
质量审查 (LLM)
    ↓
终稿生成 (LLM)
    ↓
HITL_3_最终预览 (Human)
    ↓
HTML排版 (Template)
    ↓
封面生成 (Image Generation)
    ↓
内嵌图像 (Image Generation)
    ↓
完成
```

---

## 环境变量速查

| 变量 | 说明 | 获取方式 |
|------|------|---------|
| `DIFY_API_KEY` | Dify API 密钥 | Dify Console → Settings → API Keys |
| `DIFY_CHATFLOW_ID` | Chatflow App ID | Dify Console → App → 复制 App ID |
| `DIFY_WEBHOOK_BEARER_TOKEN` | Webhook 认证 Token | `openssl rand -hex 32` |
| `DIFY_WEBHOOK_URL` | Webhook 公网地址 | ngrok Forwarding URL + `/webhooks/dify/hitl` |
| `TAVILY_API_KEY` | Tavily 搜索 API | [tavily.com](https://tavily.com) |
| `MCP_SERVER_KEY` | MCP Server 认证 | 自定义随机字符串 |
| `JIMENG_API_KEY` | 即梦图像 API | 字节跳动即梦平台 |

---

## 故障排查

### `401 Unauthorized`

- 检查 `DIFY_API_KEY` 是否正确
- 检查 `DIFY_BASE_URL` 是否为 `https://api.dify.ai/v1`（注意是 `/v1`）

### Webhook 未触发

- 确认 `DIFY_WEBHOOK_URL` 是公网可访问的 ngrok 地址
- 确认 Bearer Token 与 `DIFY_WEBHOOK_BEARER_TOKEN` 一致
- 查看 Dify Console → App → 运行日志

### HITL 一直等待

- 确认 MCP Server 正在运行
- 确认 Webhook 回调正常（检查 MCP Server 日志）
- 手动触发：`POST /sessions/{id}/hitl/approve`

### 测试失败

```bash
# 查看详细错误
python3 -m pytest tests/ -v --tb=long

# 只运行特定测试
python3 -m pytest tests/test_dify_client.py -v
```
