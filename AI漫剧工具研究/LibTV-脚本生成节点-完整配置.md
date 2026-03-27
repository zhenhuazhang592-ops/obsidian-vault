# LibTV 脚本生成节点 - 完整配置

> 研究日期：2026-03-23
> 研究方法：浏览器 CDP 抓包 + API 捕获
> 状态：✅ 完整掌握

---

## 一、节点基本信息

| 属性 | 值 |
|------|-----|
| **节点类型** | `script` |
| **动作** | `script_generate` |
| **默认模型** | `aurora-3-prime`（多模态文本模型Pro） |
| **场景** | `script-generate` |
| **视图模式** | `table`（表格） |

---

## 二、完整节点配置

```typescript
{
  id: "dd699550-c746-4f89-beab-bca2347692e9",
  type: "script",
  data: {
    type: "script",
    name: "脚本生成器",
    rows: [],                      // 生成结果（初始为空数组）
    viewMode: "table",             // 表格视图
    action: "script_generate",    // 动作类型
    generatorType: "default",     // 生成器类型
    params: {
      model: "aurora-3-prime",    // 模型 ID
      scene: "script-generate",    // 场景类型
      prompt: "根据我上传的剧本生成一个完整的故事脚本",
      count: 1,
      textList: [{
        nodeId: "d2ad4b0b-2f9a-40b0-b559-1c5e4fbe5cf3",
        content: ["《我在盛唐写天下》\n\n**类型**：古风 / 穿越 / 爽文漫剧\n\n**时长建议**：60–90秒\n\n**基调**：热血 × 盛唐史诗感 × 爽点节奏\n\n【序幕】\n\n【现代 · 深夜办公室】\n\n键盘声急促。电脑屏幕蓝光刺眼。 沈昭昭（女，28岁），面色苍白，伏案加班。\n...\n"]
      }],
      imageList: [],
      videoList: [],
      audioList: []
    }
  },
  position: {x: 650, y: 126},
  sourcePosition: "right",
  targetPosition: "left"
}
```

---

## 三、配置参数详解

### 3.1 params 参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `model` | string | 是 | 模型 ID，如 `aurora-3-prime` |
| `scene` | string | 是 | 场景类型，如 `script-generate` |
| `prompt` | string | 否 | 自定义提示词，默认"根据我上传的剧本生成一个完整的故事脚本" |
| `count` | number | 否 | 生成数量，默认 1 |
| `textList` | array | 是 | 输入文本来源 |
| `imageList` | array | 否 | 输入图片来源 |
| `videoList` | array | 否 | 输入视频来源 |
| `audioList` | array | 否 | 输入音频来源 |

### 3.2 textList 结构

```typescript
textList: [{
  nodeId: string,      // 源节点 ID
  content: string[]    // 剧本文本内容（数组）
}]
```

### 3.3 输入来源对应关系

| 类型 | 来源节点类型 | 说明 |
|------|-------------|------|
| `textList` | `text` | 剧本节点，存放原始剧本 |
| `imageList` | `image` | 角色参考图、场景图 |
| `videoList` | `video` | 视频片段 |
| `audioList` | `audio` | 配音、BGM |

---

## 四、界面配置面板

从截图观测到的配置界面：

```
┌─────────────────────────────────────────┐
│ 脚本生成器                    [×]        │
├─────────────────────────────────────────┤
│                                         │
│ 模型配置                                 │
│ ┌─────────────────────────────────────┐ │
│ │ 多模态文本模型Pro              [▼]  │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ 来源数据                                 │
│ ┌─────────────────────────────────────┐ │
│ │ 沈昭昭                           [6] │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ ☑ 提示词优化                            │
│                                         │
│ [清空]                    [生成]        │
└─────────────────────────────────────────┘
```

### 4.1 配置项说明

| 配置项 | 说明 |
|--------|------|
| 模型配置 | 选择使用的 AI 模型（默认 aurora-3-prime） |
| 来源数据 | 从哪个节点获取输入（显示节点名称和内容长度） |
| 提示词优化 | 是否启用提示词自动优化 |
| 清空 | 清除生成结果 |
| 生成 | 提交生成任务 |

---

## 五、生成结果推测格式

### 5.1 rows 数组结构

```typescript
rows: [{
  id: string,              // 行 ID
  shotNumber: number,     // 镜头号
  shotType: string,       // 镜头类型：特写/中景/全景/远景
  description: string,   // 场景描述
  character: string,      // 角色
  dialogue: string,       // 台词
  action: string,        // 动作描述
  duration: number        // 持续时间（秒）
}]
```

### 5.2 推测的完整输出格式

```typescript
interface ScriptOutput {
  rows: Array<{
    id: string;
    shotNumber: number;
    shotType: "特写" | "中景" | "全景" | "远景" | "航拍" | "其他";
    description: string;      // 场景描述：如"金銮殿内，日，光线明亮"
    character: string;         // 角色名：沈昭昭、皇帝、大臣
    dialogue: string;          // 台词内容
    action: string;            // 角色动作
    duration: number;          // 镜头持续时间
  }>;
  totalDuration: number;      // 总时长（秒）
}
```

---

## 六、draftJson 存储格式

### 6.1 项目草稿结构

```typescript
interface ProjectDraft {
  nodes: CanvasNode[];    // 节点列表
  edges: CanvasEdge[];    // 连接列表
  savedAt: number;        // 保存时间戳
  version: number;        // 版本号
}
```

### 6.2 保存 API

```
POST /api/canvas/project/draft/update
```

**请求体：**
```json
{
  "projectUuid": "18d4a083e58e4252ab0daf596373018e",
  "draftJson": "{\"nodes\":[...],\"edges\":[...],\"savedAt\":1774256696852,\"version\":0}",
  "viewportX": "0",
  "viewportY": "100",
  "viewportZoom": "1"
}
```

---

## 七、Aurora 模型规格

### 7.1 模型信息

| 属性 | 值 |
|------|-----|
| **模型 ID** | `aurora-3-prime` |
| **模型名称** | 多模态文本模型Pro |
| **供应商** | Aurora |
| **类型** | Text（文本） |
| **checkpointId** | - |

### 7.2 模型属性

```typescript
{
  "prompt": {
    "description": "",
    "placeholder": "",
    "maxLength": 0
  },
  "modeType": {
    "description": "模态类型",
    "items": {
      "image2text": [0, 7],
      "video2text": [0, 1]
    }
  }
}
```

### 7.3 支持的模式

| 模式 | 说明 |
|------|------|
| `image2text` | 图像转文本（图片分析） |
| `video2text` | 视频转文本（视频分析） |

---

## 八、实现参考

### 8.1 节点组件结构

```typescript
// React Flow 自定义节点
const ScriptNode: React.FC<NodeProps> = ({ data, selected }) => {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className={`react-flow__node-script ${selected ? 'selected' : ''}`}>
      <div className="node-header" onClick={() => setExpanded(!expanded)}>
        <span>{data.name}</span>
        <span>{data.params.model}</span>
      </div>

      {expanded && (
        <div className="node-config-panel">
          {/* 模型选择 */}
          {/* 来源数据 */}
          {/* 提示词优化 */}
          {/* 生成按钮 */}
        </div>
      )}

      <div className="node-output">
        {data.rows?.length > 0 ? (
          <Table data={data.rows} />
        ) : (
          <span>等待生成...</span>
        )}
      </div>
    </div>
  );
};
```

### 8.2 生成任务提交

```typescript
async function submitScriptGeneration(nodeData: ScriptNodeData) {
  const response = await fetch('/api/task/submit', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      nodeId: nodeData.id,
      action: 'script_generate',
      params: {
        model: nodeData.params.model,
        scene: 'script-generate',
        prompt: nodeData.params.prompt,
        count: nodeData.params.count,
        textList: nodeData.params.textList.map(t => ({
          nodeId: t.nodeId,
          content: t.content
        }))
      }
    })
  });

  const { taskId } = await response.json();
  return taskId;
}
```

### 8.3 进度轮询

```typescript
async function pollScriptResult(taskId: string, onProgress: (p: number) => void) {
  while (true) {
    const response = await fetch('/api/task/generation/progress/batch', {
      method: 'POST',
      body: JSON.stringify({ taskIds: [taskId] })
    });

    const { data } = await response.json();
    const task = data[0];

    onProgress(task.progress);

    if (task.status === 'completed') {
      return task.result; // 包含 rows 数组
    }

    if (task.status === 'failed') {
      throw new Error(task.error.message);
    }

    await sleep(2000);
  }
}
```

---

## 九、与牛油果漫剧剧本 Agent 对比

| 维度 | 牛油果漫剧 | LibTV 脚本生成 |
|------|-----------|----------------|
| **输入** | 选题（JSON） | 剧本文本 |
| **模型** | AIScript | Aurora-3-Prime |
| **输出** | 结构化剧本 | 分镜表格 |
| **工作流** | 线性 | 节点式 |
| **交互** | API 调用 | 可视化拖拽 |

---

## 十、总结

LibTV 的脚本生成节点是一个**基于 Aurora 多模态模型**的智能脚本生成器，核心特点：

1. **输入灵活**：支持从其他节点（剧本、角色、场景）获取输入
2. **输出结构化**：以表格形式输出分镜，包含镜头号、类型、描述、角色、台词等
3. **可视化配置**：通过配置面板选择模型、设置提示词、管理输入来源
4. **实时保存**：通过 draftJson 自动保存节点状态

---

*文档版本：v1.0*
*最后更新：2026-03-23*
