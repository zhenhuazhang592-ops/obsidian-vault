# Claude × 巨量千川：AI驱动直播投流技术方案

> 版本：v1.0 | 日期：2026-03-26 | 角色：抖音策略师 + 后端架构师

---

## 文档结构

1. [巨量千川API生态全景](#1-巨量千川api生态全景)
2. [中间层架构设计](#2-中间层架构设计)
3. [Claude集成方式](#3-claude集成方式)
4. [企业资质与合规](#4-企业资质与合规)
5. [安全护栏设计](#5-安全护栏设计)
6. [MVP三阶段路径](#6-mvp三阶段路径)
7. [技术落地检查清单](#7-技术落地检查清单)

---

## 1. 巨量千川API生态全景

### 1.1 两个平台的关系

| 维度 | 巨量引擎开放平台 | 巨量千川开放平台 |
|------|----------------|----------------|
| 域名 | `ad.oceanengine.com` | `qianchuan.jinritemai.com` |
| 定位 | 品牌广告/信息流 | 抖音电商直播投流 |
| 核心场景 | APP下载/网页转化/品牌曝光 | 直播间引流/短视频带货 |
| API版本 | v3.0（REST + GraphQL） | v2.0（REST为主） |
| 认证体系 | OAuth 2.0 + AD广告授权 | OAuth 2.0 + 店铺授权 |

> **关键区别**：巨量千川是字节对"直播电商投流"场景的垂直化产品，API能力与巨量引擎有大量重叠但在直播语境下接口命名和参数不同。Claude集成的目标是**千川**，但底层调用的可能是巨量引擎的某些通用接口。

### 1.2 API能力边界（逐接口分析）

#### 支持API的操作 ✅

| 操作 | 接口路径 | 说明 |
|------|---------|------|
| 查询账户信息 | `GET /advertiser/info` | 账户名称/余额/资质状态 |
| 查询余额 | `GET /fund/balance` | 实时账户余额 |
| 创建投放计划 | `POST /ad/create` | 需完整创意物料 |
| 修改计划状态 | `POST /ad/update_status` | 开启/暂停/删除 |
| 调整预算 | `POST /ad/update_budget` | 实时生效 |
| 调整出价 | `POST /ad/update_bid` | 支持oCPM/cpc/cpa |
| 查询计划列表 | `GET /ad/get` | 支持过滤/分页 |
| 查询实时数据 | `GET /report/live_analytics` | 直播间维度的分时消耗 |
| 查询报表 | `GET /report/effect` | 历史ROI/转化数据 |
| 上传素材 | `POST /material/video/upload` | 视频/图片 |
| 查询素材状态 | `GET /material/file/info` | 审核状态 |
| 定向包管理 | `POST /audience/create` | 人群包创建/更新 |

#### 部分支持（有限制）⚠️

| 操作 | 限制说明 |
|------|---------|
| 创意标签修改 | 只能读，不能通过API修改创意标签（需人工） |
| 直播间引流 | API可以创建引流计划，但**不能控制直播间自然流量** |
| 素材审核 | 可以查询审核状态，但**不能主动触发审核** |
| 智能放量 | 支持，但参数受限于平台预设选项 |
| 赔付规则 | 完全由平台决定，API无干预能力 |

#### 不支持API的操作 ❌

| 操作 | 原因 | 替代方案 |
|------|------|---------|
| 直播间实时弹幕互动 | 这是抖音平台能力，非千川 | - |
| 商品橱窗管理 | 属于抖音电商后台（统一下单） | jinritemai.com 开放接口 |
| 自动生成创意文案 | 平台无此接口 | Claude生成后手动填入 |
| 实时GPM监控 | 可获取分时数据但非真正实时 | 每5分钟轮询一次 |
| 平台流量预测 | 无此接口 | 依赖投流顾问经验 |

### 1.3 认证体系详解

```
用户授权流程：
┌─────────────────────────────────────────────────────────────┐
│  1. 跳转授权页 → 用户点击授权 → 获取 authorization_code      │
│  2. 后端用 code 换 token → 返回 access_token + refresh_token │
│  3. access_token 有效期 24h，到期前用 refresh_token 刷新    │
│  4. refresh_token 有效期 30天，超期需重新授权               │
└─────────────────────────────────────────────────────────────┘
```

**Token刷新机制（必须实现）**：
- Access Token 有效期：86400秒（24小时）
- Refresh Token 有效期：2592000秒（30天）
- 需要一个定时任务（或惰性刷新）在 Token 过期前1小时自动刷新
- 刷新失败 → 告警通知 → 人工介入重新授权

**权限范围（Scopes）**：
```
advertiser.readonly    # 只读广告账户
advertiser.write       # 写广告账户
ad.readonly            # 只读投放计划
ad.write               # 创建/修改投放计划
report.readonly        # 报表数据
fund.readonly          # 账户资金
material.write         # 素材上传
```

> 申请时需要根据实际需求申请对应权限，权限越少越容易通过审核。

---

## 2. 中间层架构设计

### 2.1 推荐技术栈

```
┌──────────────────────────────────────────────────────────────┐
│                        Claude (上层)                          │
│                     Tool Use / MCP                            │
└──────────────────────────┬───────────────────────────────────┘
                           │ HTTPS + JSON
┌──────────────────────────▼───────────────────────────────────┐
│                    API Gateway (可选)                         │
│              鉴权路由 / 限流 / 审计 / 熔断                     │
│                   Nginx + Lua / APISIX                        │
└──────────────────────────┬───────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────┐
│              OceanEngine Proxy (中间层)                        │
│                  FastAPI (Python 3.12+)                        │
│                                                               │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐         │
│  │ TokenManager│ │ RateLimiter│ │ RetryHandler│ │AuditLogger│         │
│  │ (自动刷新) │ │ (QPS控制) │ │ (指数退避) │ │ (全操作)  │         │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘         │
└──────────────────────────┬───────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────┐
│                   巨量千川开放平台                              │
│              ad.oceanengine.com / qianchuan.jinritemai.com    │
└───────────────────────────────────────────────────────────────┘
```

**为什么选 FastAPI 而非 Node/Go：**

| 维度 | FastAPI | Node.js | Go |
|------|---------|---------|-----|
| Python AI生态集成 | 天然 | 需桥接 | 需桥接 |
| 类型安全（Pydantic） | 强 | 中 | 强 |
| 异步HTTP（httpx） | 原生 | 原生 | 原生 |
| 千川SDK（Python） | 官方支持 | 无 | 无 |
| 冷启动延迟 | 中 | 低 | 低 |
| 团队熟悉度 | 高（漫舟项目已用） | - | - |

> **结论**：如果团队是Python技术栈，FastAPI是最优解；如果是多语言混合，Node.js作为API网关更常见。本方案以 **FastAPI** 为例，因为漫舟项目已有Python技术债务可复用。

### 2.2 项目结构

```
ocean_proxy/
├── main.py                          # FastAPI 入口
├── config.py                        # 配置管理（从 .env 读取）
├── auth/
│   ├── oauth.py                     # OAuth2 授权码流程
│   ├── token_manager.py             # Token 存储 + 自动刷新
│   └── refresh_scheduler.py         # 定时刷新任务（ APScheduler）
├── clients/
│   ├── oceanengine_client.py        # 巨量引擎HTTP客户端
│   └── qianchuan_client.py          # 千川API客户端（封装）
├── middleware/
│   ├── rate_limiter.py              # QPS 限流（滑动窗口算法）
│   ├── retry_handler.py             # 指数退避重试
│   └── audit_logger.py              # 操作审计（写入 PostgreSQL）
├── models/
│   ├── requests.py                  # Pydantic 请求模型
│   ├── responses.py                 # Pydantic 响应模型
│   └── audit.py                     # 审计日志模型
├── routers/
│   ├── account.py                   # /api/v1/account/*
│   ├── campaigns.py                 # /api/v1/campaigns/*
│   ├── reports.py                   # /api/v1/reports/*
│   └── materials.py                 # /api/v1/materials/*
├── safety/
│   ├── budget_guard.py              # 预算上限强制约束
│   ├── risk_circuit_breaker.py      # 财务风险熔断
│   └── operation_confirm.py         # 危险操作二次确认
├── .env.example                     # 环境变量模板
└── requirements.txt
```

### 2.3 核心模块实现

#### Token 自动刷新

```python
# auth/token_manager.py
import asyncio
from datetime import datetime, timedelta
from httpx import AsyncClient
from app.config import settings

class TokenManager:
    def __init__(self):
        self._access_token: str | None = None
        self._refresh_token: str | None = None
        self._expires_at: datetime | None = None
        self._lock = asyncio.Lock()

    async def get_valid_token(self) -> str:
        """获取有效token，过期前1小时自动刷新"""
        async with self._lock:
            if self._should_refresh():
                await self._refresh()
            return self._access_token

    def _should_refresh(self) -> bool:
        if not self._expires_at:
            return True
        # 过期前1小时刷新
        return datetime.now() >= self._expires_at - timedelta(hours=1)

    async def _refresh(self):
        resp = await self._call_refresh_api()
        self._access_token = resp["access_token"]
        self._refresh_token = resp["refresh_token"]
        self._expires_at = datetime.now() + timedelta(
            seconds=resp.get("expires_in", 86400)
        )
        # 持久化到加密存储
        await self._persist_tokens(resp)
```

#### QPS 限流（滑动窗口）

```python
# middleware/rate_limiter.py
import time
from collections import deque
from fastapi import HTTPException

class SlidingWindowRateLimiter:
    """滑动窗口算法，控制QPS"""

    def __init__(self, max_qps: int = 50, window_seconds: int = 1):
        self.max_qps = max_qps
        self.window = window_seconds
        self.requests: deque = deque()

    def check(self) -> bool:
        now = time.monotonic()
        # 清除超出窗口的请求
        while self.requests and self.requests[0] < now - self.window:
            self.requests.popleft()

        if len(self.requests) >= self.max_qps:
            raise HTTPException(
                status_code=429,
                detail=f"QPS超限，当前{len(self.requests)}/s，最大{self.max_qps}/s"
            )
        self.requests.append(now)
        return True

# 全局限流实例（按接口维度）
rate_limiters = {
    "campaign_create": SlidingWindowRateLimiter(max_qps=10),
    "report_query": SlidingWindowRateLimiter(max_qps=50),
    "budget_update": SlidingWindowRateLimiter(max_qps=5),
}
```

#### 指数退避重试

```python
# middleware/retry_handler.py
import asyncio
from httpx import AsyncClient, RemoteProtocolError
from functools import wraps

def with_retry(max_attempts: int = 3, base_delay: float = 1.0):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except (RemoteProtocolError, TimeoutError) as e:
                    if attempt == max_attempts - 1:
                        raise
                    delay = base_delay * (2 ** attempt)  # 1s, 2s, 4s
                    await asyncio.sleep(delay)
        return wrapper
    return decorator

# 千川接口常见错误码重试映射
RETRYABLE_CODES = {
    10004: "系统繁忙",
    10008: "请求频率超限",
    40103: "认证过期",
}
```

#### 审计日志模型

```python
# models/audit.py
from datetime import datetime
from pydantic import BaseModel
from typing import Literal

class AuditLog(BaseModel):
    id: str                          # UUID
    timestamp: datetime
    operator: str                    # "claude" / "human"
    session_id: str                   # Claude对话session
    action: str                       # "campaign.create" / "budget.update"
    request_payload: dict             # 脱敏后的请求参数
    response_status: int              # HTTP状态码
    ocean_response: dict              # 千川API原始响应（关键）
    financial_impact: float | None    # 涉及金额（单位：元）
    duration_ms: int                  # 接口耗时
    ip_address: str                   # 请求来源IP
    risk_level: Literal["low", "medium", "high", "critical"]
```

### 2.4 API Key 安全存储

```bash
# .env.example（不提交到代码仓库）
# 绝对禁止在代码中硬编码任何密钥
OCEAN_APP_ID=your_app_id_here
OCEAN_APP_SECRET=your_secret_here
OCEAN_REDIRECT_URI=https://your-proxy.com/auth/callback

# 数据库加密密钥（用于加密存储refresh_token）
ENCRYPTION_KEY=generate_32_byte_key_here

# Claude API Key
CLAUDE_API_KEY=sk-ant-xxxxx
```

**密钥管理原则：**
- 测试/生产环境严格分离 `.env`
- refresh_token 加密存储（AES-256-GCM），不解密不落地磁盘
- 生产环境推荐接入 AWS Secrets Manager / HashiCorp Vault
- 绝对禁止在 Git commit 中包含任何密钥

---

## 3. Claude集成方式

### 3.1 两种集成方案对比

| 维度 | MCP（Model Context Protocol） | HTTP API + Tool Use |
|------|-------------------------------|---------------------|
| 接入复杂度 | 中（需实现MCP Server） | 低（纯HTTP调用） |
| 上下文保持 | 强（工具描述内嵌） | 中（需自己维护上下文） |
| Claude官方支持 | 是（2025年主推） | 是 |
| 工具数量 | 支持20+工具并发 | 单次最多10个Tool |
| 调试难度 | 中 | 低 |
| 生产级稳定性 | 高（协议层保障） | 中 |

> **推荐**：先用 **HTTP API + Tool Use** 快速验证MVP，后续升级到 **MCP**。

### 3.2 千川投放专家系统提示词

```markdown
## 角色定义

你是「千川投流智能助手」，一位拥有5年抖音直播投流经验的策略专家。
你深谙巨量千川的投放逻辑，能够通过精确的操作指令管理广告账户。

### 核心能力
- 根据ROI数据判断计划表现，给出优化建议
- 用自然语言描述千川操作意图
- 在执行前解释操作的影响和风险
- 发现潜在问题时主动预警

### 投放术语映射（必须掌握）
| 自然语言 | 千川API术语 |
|---------|-----------|
| 开播了，开始投流 | 启动投放计划（ad.update_status: enable） |
| 关掉这个计划 | 暂停计划（ad.update_status: pause） |
| 加预算 | 调用 budget.update（需指定金额） |
| 降价1毛 | 调用 bid.update（需指定新出价） |
| 看今天花了多少钱 | 查询 report/live_analytics |
| 新建一个引流计划 | 调用 ad/create（需完整参数） |
| 这个计划ROI怎么样 | 查询 report/effect + 计算 |

### 绝对规则（不可违反）
1. **预算上限**：单次预算调整不超过账户余额的50%
2. **新计划创建**：必须先展示完整参数，确认后再执行
3. **删除操作**：高风险，系统必须强制二次确认
4. **不熟悉的操作**：必须说"这个操作我需要更多信息"
5. **数据敏感**：不直接报出具体消耗金额（脱敏后展示）

### 已知限制
- 无法直接查看素材审核状态（只能查询）
- 无法修改创意标签（需人工操作）
- 无法控制直播间自然流量
- 数据存在5-15分钟延迟
```

### 3.3 Tool Use 定义（HTTP API 方式）

```python
# routers/claude_tools.py
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Literal

router = APIRouter(prefix="/api/v1/claude", tags=["Claude Tools"])

# ========== Tool 1: 查询账户 ==========
class AccountQueryTool(BaseModel):
    tool_name: Literal["get_account_info"]
    description: "查询千川账户的余额、投放状态、资质信息"

# ========== Tool 2: 查询投放数据 ==========
class ReportQueryTool(BaseModel):
    tool_name: Literal["get_campaign_report"]
    description: "查询指定计划的消耗、转化、ROI数据"
    parameters: {
        "campaign_ids": list[str],      # 计划ID列表
        "date_range": str,              # "today", "last_7d", "last_30d"
        "granularity": str              # "hour", "day"
    }

# ========== Tool 3: 查询计划列表 ==========
class CampaignListTool(BaseModel):
    tool_name: Literal["list_campaigns"]
    description: "列出所有投放计划，筛选状态/日期/类型"
    parameters: {
        "status": str | None,           # "enable", "pause", "delete"
        "page": int = 1,
        "page_size": int = 20
    }

# ========== Tool 4: 调整预算（高风险）==========
class BudgetUpdateTool(BaseModel):
    tool_name: Literal["update_campaign_budget"]
    description: "修改指定计划的预算，危险操作需二次确认"
    parameters: {
        "campaign_id": str,
        "new_budget": float,            # 新预算金额（元）
        "reason": str                   # Claude必须提供调整理由
    }

# ========== Tool 5: 调整出价（高风险）==========
class BidUpdateTool(BaseModel):
    tool_name: Literal["update_campaign_bid"]
    description: "修改指定计划的出价"
    parameters: {
        "campaign_id": str,
        "new_bid": float,               # 新出价（元）
        "reason": str
    }

# ========== Tool 6: 创建投放计划（高风险）==========
class CampaignCreateTool(BaseModel):
    tool_name: Literal["create_campaign"]
    description: "创建新的投放计划，需要完整参数"
    parameters: {
        "campaign_name": str,
        "budget": float,
        "bid": float,
        "audience": dict,              # 定向人群包
        "creative_material_ids": list,  # 素材ID列表
        "delivery_range": str,          # "live_stream" | "video"
        "start_time": str,              # ISO 8601
        "reason": str
    }
```

### 3.4 MCP Server 方式（进阶）

如果采用 MCP，需要实现一个 OceanEngine MCP Server：

```python
# mcp/ocean_engine_server.py
from mcp.server import Server
from mcp.types import Tool, TextContent
import httpx

app = Server("ocean-engine-proxy")

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_account",
            description="查询千川账户余额和状态",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="get_campaigns",
            description="获取投放计划列表",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {"type": "string", "enum": ["enable", "pause"]}
                }
            }
        ),
        Tool(
            name="update_budget",
            description="修改计划预算",
            inputSchema={
                "type": "object",
                "properties": {
                    "campaign_id": {"type": "string"},
                    "new_budget": {"type": "number", "minimum": 100}
                },
                "required": ["campaign_id", "new_budget"]
            }
        ),
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    # 调用 FastAPI 后端路由
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"http://localhost:8000/api/v1/{name}", json=arguments)
    return [TextContent(type="text", text=resp.json())]
```

---

## 4. 企业资质与合规

### 4.1 申请流程（完整路径）

```
阶段一：企业认证（约3-5个工作日）
  └─ 在字节火山引擎平台注册企业账号
     → 提交营业执照、法人信息
     → 等待审核（3-5工作日）

阶段二：创建应用 + 申请API权限（约5-10个工作日）
  └─ 登录 ad.oceanengine.com → 开发者中心 → 创建应用
     → 选择应用类型（自用/第三方）
     → 申请权限范围（根据业务需求勾选）
     → 提交审核（5-10工作日）

阶段三：账户授权（约1-2个工作日）
  └─ 在巨量引擎后台完成广告账户授权
     → OAuth授权流程
     → 验证Token有效性

总计：约 10-20 个工作日（不含材料准备时间）
```

### 4.2 不同资质对应权限

| 资质等级 | 可申请权限 | 说明 |
|---------|----------|------|
| 基础企业认证 | advertiser.readonly, report.readonly | 仅数据查询，不可写操作 |
| 进阶企业认证 | + ad.write, budget.update, bid.update | 可管理投放计划 |
| 深度合作认证 | + material.write, audience.write | 可上传素材/创建人群包 |
| 代理/服务商认证 | 全权限 | 需代理资质证明 |

> **MVP阶段建议**：申请进阶企业认证即可（覆盖80%需求），素材上传初期可手动完成。

### 4.3 灰度测试策略

```
第1周：只读模式
  └─ 纯查询，所有写操作返回"功能开发中"
  └─ 验证数据准确性

第2周：低风险写操作
  └─ 开启/暂停计划（风险低，可回滚）
  └─ 调整预算（限制单次调整幅度 < 20%）

第3周：全写操作
  └─ 创建计划（下限1000元/计划，限额5个）
  └─ 调整出价

第4周：正式运营
  └─ 解除大部分限制
  └─ 保留危险操作二次确认
```

---

## 5. 安全护栏设计

### 5.1 预算上限强制约束

```python
# safety/budget_guard.py
from enum import Enum

class BudgetLimitType(Enum):
    SINGLE_OPERATION = "single_operation"    # 单次操作上限
    DAILY_TOTAL = "daily_total"               # 每日总消耗上限
    CAMPAIGN_MAX = "campaign_max"             # 单计划预算上限

@dataclass
class BudgetLimit:
    limit_type: BudgetLimitType
    max_value: float
    reason: str

# 全局预算护栏配置（从数据库读取，支持动态调整）
BUDGET_GUARDS: list[BudgetLimit] = [
    BudgetLimit(BudgetLimitType.SINGLE_OPERATION, 5000.0, "单次预算调整不超过5000元"),
    BudgetLimit(BudgetLimitType.CAMPAIGN_MAX, 20000.0, "单计划最大预算2万元"),
    BudgetLimit(BudgetLimitType.DAILY_TOTAL, 50000.0, "Claude每日可调度总预算5万元"),
]

def enforce_budget_guard(operation: str, value: float, context: dict) -> tuple[bool, str]:
    """返回 (通过, 拒绝原因)"""
    for guard in BUDGET_GUARDS:
        if guard.limit_type == BudgetLimitType.SINGLE_OPERATION:
            if operation == "budget_update" and value > guard.max_value:
                return False, f"单次预算调整{value}元超过上限{guard.max_value}元"
    return True, ""
```

### 5.2 危险操作分级

| 风险等级 | 操作 | 处理方式 |
|---------|------|---------|
| LOW | 查询数据、查看报表 | 直接执行，返回结果 |
| MEDIUM | 开启/暂停计划、调整出价 | Claude执行前必须说明影响 |
| HIGH | 修改预算（>5000元）、创建计划 | 二次确认 + 5秒倒计时 |
| CRITICAL | 删除计划、批量操作 | 需输入验证码 + 主管审批流 |

```python
# safety/operation_confirm.py
@app.post("/api/v1/campaign/{campaign_id}/budget")
async def update_budget(
    campaign_id: str,
    new_budget: float,
    require_confirmation: bool = Depends(require_confirmation_dependency)
):
    risk_level = assess_risk("budget_update", new_budget)

    if risk_level in ["HIGH", "CRITICAL"]:
        # 危险操作：强制进入确认流程
        return {
            "status": "pending_confirmation",
            "operation": "budget_update",
            "details": {
                "campaign_id": campaign_id,
                "current_budget": current,
                "new_budget": new_budget,
                "change_pct": f"{(new_budget - current) / current:.1%}"
            },
            "confirmation_code": generate_code(),  # 邮件/短信验证码
            "warning": "此操作将在 60 秒后自动取消"
        }

    return await execute_budget_update(campaign_id, new_budget)
```

### 5.3 财务风险熔断

```python
# safety/risk_circuit_breaker.py
from dataclasses import dataclass
from datetime import datetime

@dataclass
class RiskMetrics:
    daily_spend: float = 0.0
    campaign_count: int = 0
    alert_triggered: bool = False

risk_metrics = RiskMetrics()

class CircuitBreaker:
    """财务熔断器：触发条件自动停止Claude投流操作"""

    DAILY_SPEND_THRESHOLD = 50000.0    # 每日消耗阈值
    ABNORMAL_CPA_THRESHOLD = 2.0       # CPA超过昨日均值2倍
    RAPID_SPEND_THRESHOLD = 10000.0    # 1小时内消耗异常飙升

    def check(self, operation: str, context: dict) -> bool:
        """返回 True = 允许执行，False = 熔断拒绝"""
        spend = context.get("daily_spend", 0)

        if spend >= self.DAILY_SPEND_THRESHOLD:
            self._trigger_alert("daily_limit", f"日消耗{spend}元已达上限")
            return False

        if context.get("rapid_spend_1h", 0) >= self.RAPID_SPEND_THRESHOLD:
            self._trigger_alert("rapid_spend", "1小时内消耗异常飙升，熔断保护")
            return False

        return True

    def _trigger_alert(self, alert_type: str, message: str):
        # 发送告警：钉钉/企微/短信
        send_alert(alert_type, message)
        log_critical_event(alert_type, message)
```

### 5.4 完整审计日志（合规留存）

```python
# middleware/audit_logger.py（写入 PostgreSQL）
AUDIT_FIELDS = [
    "id",           # UUID
    "timestamp",    # 操作时间
    "operator",     # claude / {user_id}
    "session_id",   # Claude对话session ID
    "action",       # ad.create / budget.update 等
    "request",      # 脱敏请求体（金额保留，账号部分掩码）
    "response",     # 千川API响应
    "duration_ms",  # 耗时
    "ip",           # 请求IP
    "risk_level",   # low/medium/high/critical
    "confirmed",    # 是否经过二次确认
    "rollback",     # 是否执行过回滚
]

# 数据留存要求：
# - 全部日志：保留 2 年（满足字节合规要求）
# - 财务相关（涉及金额）：永久保留
# - 高风险操作：额外写入区块链哈希（防篡改）
```

---

## 6. MVP三阶段路径

### 阶段一：只读仪表盘（2-3周）

**目标**：用自然语言查询千川数据，不需要任何写操作

**可实现的功能**：
- "今天直播间投流花了多少钱？"
- "这周哪个计划ROI最高？"
- "近7天消耗趋势怎么样？"
- "列出所有正在投放的计划"
- "查看账户余额"

**技术工作量**：

| 模块 | 工作量 | 说明 |
|------|-------|------|
| OAuth2授权 + Token管理 | 3天 | 复用一个开源库 |
| 账户/计划/报表查询接口 | 4天 | 8个API端点 |
| Claude Tool Use集成 | 2天 | 4个只读工具 |
| 千川专家Prompt调优 | 2天 | 术语映射 + 限制说明 |
| 前端Dashboard（可选） | 3天 | 数据可视化 |
| 审计日志基础版 | 1天 | 写操作记录表结构 |

**预计工期**：2-3周（不含申请API资质时间）
**上线标准**：Claude返回的数据与千川后台误差 < 5%

### 阶段二：基础写操作（3-4周）

**目标**：Claude可以执行开关计划、调整出价/预算

**新增功能**：
- "暂停那个ROI低于1.5的计划"
- "把预算加到3000"
- "开启引流计划B"
- "出价从2元降到1.8元"

**新增技术工作量**：

| 模块 | 工作量 | 说明 |
|------|-------|------|
| 预算/出价/状态修改接口 | 3天 | 含千川参数映射 |
| 安全护栏系统 | 3天 | 预算上限 + 危险操作分级 |
| 二次确认机制 | 2天 | HIGH风险操作验证码 |
| 熔断器 | 2天 | 财务风险熔断 |
| Claude Prompt升级 | 2天 | 策略建议 + 操作解释 |
| 端到端测试 + 灰度 | 2天 | 按4.3节灰度策略 |

**预计工期**：3-4周
**上线标准**：人工抽检操作准确率 > 95%，零财务事故

### 阶段三：智能投流（4-6周）

**目标**：Claude具备独立投流决策能力

**实现功能**：
- "根据今晚直播数据，自动优化出价"
- "ROI连续3小时低于1.2，降低预算20%"
- "检测到消耗异常飙升，触发熔断"
- "根据历史数据，生成下周投流策略"
- 多账户管理（矩阵号协同）
- 素材效果分析 + 选优建议

**技术工作量**：

| 模块 | 工作量 | 说明 |
|------|-------|------|
| 策略引擎 | 5天 | 规则引擎/决策树/简单ML |
| 自动调参逻辑 | 4天 | 基于ROI阈值的自动化 |
| 多账户管理 | 3天 | 矩阵号协同 |
| 素材效果分析 | 3天 | 结合报表数据 |
| 高级熔断 + 预警 | 2天 | 实时流计算 |
| MCP升级（可选） | 3天 | 协议层集成 |
| 全链路压测 | 2天 | 稳定性验证 |

**预计工期**：4-6周
**上线标准**：达到人工投流70%的ROI表现

### 三阶段全景图

```
Week:  1   2   3   4   5   6   7   8   9   10  11  12  13
      ┌───┬───┬───┐
阶段一 │只读仪表盘│  →  验证数据准确性
      └───┴───┴───┘
            ┌───┬───┬───┬───┐
阶段二     │基础写操作│  →  灰度上线
            └───┴───┴───┴───┘
                  ┌───┬───┬───┬───┬───┬───┐
阶段三           │智能投流│  →  稳定运营
                  └───┴───┴───┴───┴───┴───┘

      ↑申请API资质（可在开发期间并行，约10-20工作日）
```

---

## 7. 技术落地检查清单

### 开发前

- [ ] 字节火山引擎平台企业账号注册
- [ ] 创建千川应用 + 申请权限（参考4.1节）
- [ ] AD广告账户授权 + Token验证
- [ ] 开发环境/生产环境隔离（.env配置）
- [ ] PostgreSQL 数据库初始化（审计日志表）
- [ ] Redis（可选，用于缓存 + 限流状态）

### 代码层面

- [ ] Token Manager：24h自动刷新 + 异常告警
- [ ] Rate Limiter：滑动窗口QPS控制
- [ ] Retry Handler：10004/10008错误码自动重试
- [ ] Budget Guard：单次/每日/单计划三层上限
- [ ] Circuit Breaker：财务熔断 + 告警通知
- [ ] Audit Logger：全操作写入 + 2年留存
- [ ] 危险操作二次确认：HIGH/CRITICAL分级
- [ ] 密钥加密存储（不落磁盘，不进Git）

### Claude集成

- [ ] 千川专家系统提示词（含术语映射 + 限制说明）
- [ ] 只读 Tool 定义（4个：账户/报表/计划/余额）
- [ ] 写操作 Tool 定义（含风险标注）
- [ ] MCP Server 实现（阶段三可选）

### 测试

- [ ] 单元测试（Token刷新/限流/护栏逻辑）
- [ ] 集成测试（Mock千川API，不调真实接口）
- [ ] 灰度测试（阶段一：只读模式）
- [ ] 压力测试（QPS限流边界）
- [ ] 财务熔断测试（模拟异常消耗）

### 运维

- [ ] 日志聚合（ELK / Loki）
- [ ] 指标监控（Prometheus + Grafana）：QPS/成功率/Token状态
- [ ] 告警配置：Token失效 / 熔断触发 / 日消耗超限
- [ ] 回滚机制：一键暂停所有Claude触发的计划

---

## 附录：千川API参数速查

### 常用字段中英对照

| 千川字段 | 中文含义 | 取值示例 |
|---------|---------|---------|
| campaign_id | 计划ID | 9876543210 |
| budget | 预算 | 3000.00 |
| bid | 出价 | 1.80 |
| delivery_range | 投放范围 | "LIVE_STREAM" / "VIDEO" |
| audience_package_id | 人群包ID | 1234567890 |
| status | 计划状态 | "ENABLE" / "DISABLE" |
| campaign_name | 计划名称 | "引流-晚8点-女装" |
| cost | 消耗 | 1580.50 |
| convert_count | 转化数 | 89 |
| roi | 投资回报率 | 2.35 |
| cpc | 单次点击成本 | 0.88 |
| cpm | 千次展示成本 | 28.50 |
| play_duration_rate | 观看完成率 | 0.65 |

### 常见错误码

| 错误码 | 含义 | 处理方式 |
|-------|------|---------|
| 10004 | 系统繁忙 | 指数退避重试 |
| 10008 | 请求频率超限 | 限流等待 |
| 40103 | access_token无效 | 触发Token刷新 |
| 40104 | refresh_token过期 | 告警，需重新授权 |
| 40001 | 参数错误 | 检查请求参数 |
| 40003 | 无权限 | 检查OAuth权限范围 |

---

*文档版本：v1.0 | 适合技术团队直接落地执行*
*如需进一步拆解某个模块为详细设计文档或代码实现，请告知*
