# LibTV 小说转剧本 - 完整配置

> 研究日期：2026-03-23
> 研究方法：浏览器 CDP 抓包 + 界面观测 + Playwright自动化
> 状态：✅ 完全掌握（真实API已捕获）

---

## 一、节点基本信息

| 属性 | 值 |
|------|-----|
| **页面路径** | `/canvas/script-tools/novel-to-script`（需通过 Canvas 内部 router 访问，直接 URL 访问返回 404） |
| **功能名称** | 小说转剧本 |
| **所属分类** | 剧本工具 → Canvas 工作流节点 |
| **输入** | 小说文档（TXT/DOCX）或直接粘贴文本 |
| **输出** | 分集剧本（故事梗概、分集大纲、角色设定） |
| **底层模型** | Aurora-3-Prime |
| **实际API** | `POST /api/task/generation/create`（与文本生成器共用） |

---

## 二、完整配置界面

从截图观测到的配置界面：

```
┌─────────────────────────────────────────────────────────────┐
│  小说转剧本                                      [返回首页]  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  小说文档                                                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                                                     │   │
│  │    拖拽小说文档到此处，或点击上传                    │   │
│  │    支持 TXT, DOCX 格式                               │   │
│  │    最多上传 5 个文件                                 │   │
│  │    单次处理 10 万字以内                              │   │
│  │                                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  剧集类型                                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 分集剧本（单集 60-90 秒）                       [▼] │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  剧本风格                                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 都市言情                                        [▼] │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  集数                                                      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 5                                              [▼]  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│                               [清空]    [生成剧本]          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 三、真实 API 捕获

### 3.1 任务创建 API

**Endpoint**: `POST https://api.liblib.tv/api/task/generation/create`

**请求体**（真实捕获）：

```json
{
  "params": {
    "prompt": "根据我上传的小说，转化成完整的剧本\n",
    "model": "aurora-3-prime",
    "count": 1,
    "textList": [
      "“办公室里，谭斌收拾东西准备离开。关机前她习惯性地查看次日的备忘录。早上八点和客户有个交流会，比公司正常的上班时间提前一个小时，这意味着她明早五点半就要起床。\n\nMPL员工价值观的第一条，就是客户优先...\n（小说全文）..."
    ],
    "imageList": [],
    "videoList": [],
    "audioList": [],
    "infiniteSwitch": 0
  },
  "metadata": {
    "node_id": "21af8431-1694-4d7c-a58f-5b7268be0feb",
    "project_id": "babb3d569e65492ca19d8d8fa1036124"
  },
  "provider": "aurora",
  "model": "aurora-3-prime",
  "taskType": "text",
  "requestId": "714785ec-46ab-4380-89f6-c059078638c2"
}
```

**关键发现**：
- `prompt` = "根据我上传的小说，转化成完整的剧本\n" - 系统自动生成的提示词
- `textList` = 小说文本内容（不是文件上传，是文本提取）
- `model` = "aurora-3-prime" - 与 AI 剧本生成器相同模型
- `metadata.node_id` = 画布节点 ID
- `metadata.project_id` = 项目 ID

### 3.2 任务进度轮询 API

**Endpoint**: `POST https://api.liblib.tv/api/task/generation/progress`

**请求体**：

```json
{
  "taskIds": ["20260323202303411590901"]
}
```

**响应体**（推测）：

```json
{
  "tasks": [
    {
      "taskId": "20260323202303411590901",
      "status": "completed",
      "result": {
        "content": "生成的剧本内容..."
      }
    }
  ]
}
```

### 3.3 结果保存 API

**Endpoint**: `POST https://api.liblib.tv/api/canvas/nodes/batch`

**请求体**（真实捕获）：

```json
{
  "projectUuid": "babb3d569e65492ca19d8d8fa1036124",
  "nodes": {
    "update": [
      {
        "nodeKey": "21af8431-1694-4d7c-a58f-5b7268be0feb",
        "projectUuid": "babb3d569e65492ca19d8d8fa1036124",
        "type": 1,
        "name": "剧本",
        "position": {
          "positionX": "330",
          "positionY": "104"
        },
        "measured": {
          "width": "350",
          "height": "350"
        },
        "parentKey": "",
        "data": "{\"type\":\"text\",\"name\":\"剧本\",\"content\":[\"生成的剧本内容...\"]}"
      }
    ]
  }
}
```

---

## 四、工作流程

```
┌──────────────────────────────────────────────────────────────────┐
│                        完整工作流                                  │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  1. [用户上传] 小说 TXT/DOCX 文件                                   │
│              ↓                                                    │
│  2. [文本提取] 前端解析文件内容为纯文本                              │
│              ↓                                                    │
│  3. [API调用] POST /api/task/generation/create                   │
│              │  model: aurora-3-prime                            │
│              │  textList: [小说文本]                              │
│              │  prompt: "根据我上传的小说，转化成完整的剧本"         │
│              ↓                                                    │
│  4. [任务创建] 返回 taskId: 20260323202303411590901               │
│              ↓                                                    │
│  5. [轮询进度] POST /api/task/generation/progress                 │
│              │  taskIds: ["20260323202303411590901"]              │
│              ↓                                                    │
│  6. [完成] status: completed                                      │
│              ↓                                                    │
│  7. [保存结果] POST /api/canvas/nodes/batch                       │
│              │  更新画布节点 data 字段                             │
│              ↓                                                    │
│  8. [显示] 剧本内容展示在画布节点中                                 │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

---

## 五、关键发现

### 5.1 "小说转剧本"不是独立工具

**重大发现**：小说转剧本底层调用的API和"AI剧本生成器"完全一样！

| 对比 | 小说转剧本 | AI剧本生成器 |
|------|-----------|--------------|
| **底层API** | `/api/task/generation/create` | `/api/task/generation/create` |
| **模型** | Aurora-3-Prime | Aurora-3-Prime |
| **输入** | 小说文件 → 文本提取 → textList | 直接输入 textList |
| **Prompt** | "根据我上传的小说，转化成完整的剧本" | 用户自定义 |

**区别仅在于**：
1. 小说转剧本有文件上传和解析流程
2. 系统自动生成固定的 prompt

### 5.2 文件处理方式

- **不是** multipart/form-data 文件上传
- **是** 前端解析文件为纯文本，存入 `textList` 数组
- 支持 TXT、DOCX 格式
- 单次限制 10 万字

### 5.3 画布节点数据流

```
小说文件 → 文本提取 → API调用 → taskId → 轮询进度 → 完成 → 保存到画布节点
                                          ↓
                                   node.data.content = ["生成的剧本"]
```

---

## 六、剧本风格选项

| 风格 | 说明 |
|------|------|
| 都市言情 | 现代都市爱情故事 |
| 穿越重生 | 穿越到过去或重获新生 |
| 玄幻奇幻 | 魔法、异世界题材 |
| 悬疑惊悚 | 推理、恐怖题材 |
| 古装历史 | 历史题材 |
| 青春校园 | 校园青春故事 |

---

## 七、生成输出示例

生成的剧本内容包含：

1. **剧本格式**：
   - 场次、时间、地点、人物
   - 场景描述 [场景描述]
   - 动作描写 [动作]
   - 特写镜头 [特写]
   - 台词（角色 + 旁白V.O）
   - 括号内动作提示

2. **内容结构**：
   - 将小说叙事转化为视听语言
   - 保持故事核心情节
   - 添加场景转换提示
   - 角色对白口语化

---

## 八、与 AI 剧本生成器对比

| 维度 | 小说转剧本 | AI剧本生成器 |
|------|-----------|--------------|
| **输入** | 小说文档（TXT/DOCX） | 主题/描述（文本） |
| **处理方式** | 解析+转换 | AI生成 |
| **底层API** | `/api/task/generation/create` | `/api/task/generation/create` |
| **模型** | Aurora-3-Prime | Aurora-3-Prime |
| **Prompt** | 系统自动生成 | 用户自定义 |
| **输出** | 分集剧本 | 分集剧本 |
| **适用场景** | 已有小说版权 | 从零创作 |
| **字数限制** | 10万字/次 | 无限制 |

---

## 九、Canvas 工作流定位

LibTV 剧本工具完整生态：

```
┌──────────────────────────────────────────────────────────────────┐
│                     LibTV Canvas 剧本工具                         │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  [小说文档] → [小说转剧本] → [AI剧本生成器] → [分镜生成器] → ...  │
│       │              │              │              │              │
│    原始小说      结构化剧本      优化剧本        分镜表格          │
│   (TXT/DOCX)    (梗概+大纲)   (台词+动作)     (镜头+景别)        │
│                                                                  │
│  所在位置：                                                       │
│  - 小说转剧本：Canvas 画布节点（TV工具箱展开）                     │
│  - AI剧本生成器：Canvas 画布节点                                  │
│  - 分镜生成器：Canvas 画布节点                                    │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 十、CDP 抓包完整记录

### 抓包会话信息

- **Tab URL**: `https://www.liblib.tv/canvas?projectId=babb3d569e65492ca19d8d8fa1036124`
- **抓包工具**: CDP (Chrome DevTools Protocol)
- **监控端点**: `ws://localhost:9222/devtools/page/FA72BCCBD27A6BE2ECF0337BEEC4B7B3`

### 完整请求序列

```
[REQ-1]  POST  https://api.liblib.tv/api/task/generation/create
         Body: {"params":{"prompt":"根据我上传的小说，转化成完整的剧本\n",
                   "model":"aurora-3-prime","count":1,
                   "textList":["小说全文..."],"imageList":[],...},
               "metadata":{"node_id":"21af8431-1694-4d7c-a58f-5b7268be0feb",
                          "project_id":"babb3d569e65492ca19d8d8fa1036124"},
               "provider":"aurora","model":"aurora-3-prime","taskType":"text",
               "requestId":"714785ec-46ab-4380-89f6-c059078638c2"}

[REQ-2]  POST  https://api2.liblib.art/api/www/log/acceptor/f
         Body: Analytics/ABTest log

[REQ-3]  GET   https://api2.liblib.art/api/www/member/account?isApp=false

[REQ-4]  GET   https://api2.liblib.art/api/www/commerce/activity/benefit?productTypes=3

[REQ-5]  GET   https://api2.liblib.art/api/www/commerce/activity/rateLimitBenefit

[REQ-6-17] POST https://api.liblib.tv/api/task/generation/progress
         Body: {"taskIds":["20260323202303411590901"]}
         重复轮询直到任务完成

[REQ-18] POST  https://api.liblib.tv/api/canvas/nodes/batch
         Body: {"projectUuid":"babb3d569e65492ca19d8d8fa1036124",
                "nodes":{"update":[{
                  "nodeKey":"21af8431-1694-4d7c-a58f-5b7268be0feb",
                  "name":"剧本",
                  "data":"{\"type\":\"text\",\"name\":\"剧本\",\"content\":[\"生成的剧本...\"]}"
                }]}}
```

---

*文档版本：v2.0*
*最后更新：2026-03-23*
*研究方法：CDP 真实API抓包*
