# prompts.chat 全局研究报告

> 来源：/Users/huage/Downloads/prompts.chat-main/
> 项目规模：143k+ GitHub stars，91054条提示词，CC0许可

---

## 一、项目定位

**prompts.chat**（前身：Awesome ChatGPT Prompts）是全球最大开源AI提示词库。

### 核心身份
- **发起时间**：2022年12月（首个提示词库）
- **定位**：收集+整理+分享AI提示词，兼容ChatGPT/Claude/Gemini/Llama/Mistral等
- **影响力**：Forbes报道、哈佛/哥伦比亚大学引用、40+学术引用、GitHub Staff Pick

### 生态矩阵
```
prompts.chat/
├── Web平台（https://prompts.chat）— 提示词浏览+提交+投票
├── prompts.csv — 离线数据集（Hugging Face）
├── PROMPTS.md — GitHub纯文本版
├── MCP Server — AI工具集成
├── Claude Plugin — Claude Code插件
├── Self-hosting — 私有化部署
└── Promi（儿童AI教育）
```

---

## 二、技术架构

### 2.1 技术栈
- **框架**：Next.js（App Router）
- **数据库**：Prisma ORM + PostgreSQL
- **认证**：GitHub/Google/Apple/Azure AD
- **分析**：Google Analytics事件追踪
- **监控**：Sentry错误监控
- **容器**：Docker一键部署

### 2.2 数据库模型（核心实体）

```prisma
// 提示词
Prompt {
  id, title, act, prompt, description,
  forDevs: Boolean,        // 是否仅开发者
  type: String,            // 类型
  contributorId,
  categoryId,
  isPrivate, isUnlisted,
  deletedAt,
  // 质量字段
  voteCount, contributorCount
}

// 投票
Vote { promptId, userId, vote }

// 贡献者
Contributor { userId, promptId }

// 分类
Category { id, name, slug }

// 连接关系
Connection { fromPromptId, toPromptId, label }

// 用户示例
UserExample { promptId, mediaUrl, userId }
```

### 2.3 质量检查系统（AI驱动）

**文件**：`src/lib/ai/quality-check.ts`

```typescript
// 基础检查（无需AI）
- 最短字符数：50
- 最短词数：10

// AI质量检查（需要OPENAI_API_KEY）
- confidence < 0.85 → 不下架（避免误杀）
- JSON解析失败 → 默认通过（避免误杀）
- API调用失败 → 默认通过（避免误杀）
```

**DelistReason枚举**：
- `TOO_SHORT` — 内容过短
- `NOT_ENGLISH` — 非英语
- `LOW_QUALITY` — 质量低
- `NOT_LLM_INSTRUCTION` — 非LLM指令
- `MANUAL` — 人工下架

### 2.4 事件追踪体系（analytics.ts）

```typescript
// 认证事件
analyticsAuth.login / loginFailed / register / logout / oauthStart

// 提示词事件
analyticsPrompt.view / copy / fork / submit / vote / search

// 贡献者事件
analyticsContributor.follow / unfollow

// 分类事件
analyticsCategory.browse / filter
```

### 2.5 配置文件（prompts.config.ts）

```typescript
export default defineConfig({
  branding: { name, logo, appStoreUrl, chromeExtensionUrl },
  theme: { radius, variant, density, colors },
  auth: { providers: ["github", "google", "apple"], allowRegistration: false },
  i18n: { locales: ["en","tr","es","zh","ja","ar","pt","fr","it","de","nl","ko","ru","he","el","az","fa"], defaultLocale: "en" },
  features: {
    privatePrompts: true,
    changeRequests: true,    // 版本控制
    categories: true,
    tags: true,
    aiSearch: true,          // AI语义搜索
    aiGeneration: true,
    mcp: true,               // MCP协议支持
    comments: true,
  },
  homepage: { achievements: true, sponsors: [...] }
})
```

---

## 三、提示词格式

### 3.1 CSV格式（prompts.csv）
```
act,prompt,for_devs,type,contributor
```

示例：
```csv
Ethereum Developer,"Imagine you are an experienced Ethereum developer...",false,BLOCKCHAIN,John Doe
Linux Terminal,"I want you to act as a linux terminal...",false,CODE,Jane Smith
```

### 3.2 提示词结构规范
```markdown
## 提示词名称（act）

[角色定义]
I want you to act as...

[约束条件]
You will...

[变量]
Variables:
- {variable1}

[输出格式]
Structure:
1. First section

[质量标准]
Quality Criteria:
- must be...
- should be...

[禁止项]
You will not...
```

---

## 四、Claude插件系统

### 4.1 Skill查找（skill-lookup）

**触发条件**：
- `/plugin marketplace add f/prompts.chat`
- `/plugin install prompts.chat@prompts.chat`

**MCP工具**：
```json
search_skills({ query, limit, category, tag })
get_skill({ id })
```

### 4.2 Prompt查找（prompt-lookup）

Claude Code中直接搜索提示词。

---

## 五、漫舟借鉴价值

### 5.1 可直接借鉴的工程实践

| prompts.chat实践 | 漫舟现状 | 借鉴方案 |
|-----------------|---------|---------|
| AI质量检查（confidence 0.85） | 手动审核 | 引入AI评分阈值 |
| Change Requests版本控制 | 无 | 漫舟CDP需版本记录 |
| analytics事件追踪 | 部分（效果追踪已有） | 补充submit/vote事件 |
| 多语言18种 | 仅中英文 | 当前不需要 |
| MCP Server | 无 | P2可考虑 |

### 5.2 漫舟适配建议

**质量检查阈值**（参考prompts.chat）：
```json
{
  "min_chars": 50,
  "min_words": 10,
  "ai_confidence_threshold": 0.85
}
```

**提示词结构模板**：
```markdown
## 【【】】角色ID
[角色定义] 你是...
[约束条件] 你需要...
[输出格式] 按以下格式输出...
[质量标准] 必须满足...
[禁止项] 禁止出现...
```
