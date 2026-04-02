# LibTV Canvas 研究突破（2026-03-25）

> 突破方式：通过 Chrome DevTools Protocol 拦截 Network 请求 + XHR 直接调用 API
> 核心发现：成功获取 tool_spec/list 完整工具规格（86KB），暴露所有可用模型和参数

---

## 一、Canvas 项目截图

- **文件**：`LibTV/canvas-project-libtv-skills.png`
- **项目名**：LibTV Skills（未命名）
- **节点**：4个，全部100%完成

```
故事脚本生成 ──→ 角色三视图 ──┬→ 首帧图生视频
                             └→ 音频生视频
```

---

## 二、已获取的真实数据

### 2.1 tool_spec/list API（86KB，62个工具，可落地）

成功通过 XHR 劫持获取完整工具规格。完整工具清单已保存至 `tool_spec.json`。

**工具分类汇总**：

**视频生成模型**：
| modelKey | modelName | 厂商 | 关键参数 |
|----------|-----------|------|---------|
| `kling-video-o1` | 可灵O1 | Kling | ratio(16:9/1:1/9:16), duration(5s/10s), quality(low/high), modeType |
| `kling-video-o3` | 可灵 3.0 | Kling | duration(5-15s滑块), enableSound(on/off), smartStoryboard开关 |
| `kling-v3-omni` | 可灵 3.0 Omni | Kling | 多模态支持 |
| `seedance-2.0` | 生视频2.0 | 自研 | 待确认参数 |
| `wan-2.1` | Wan 2.1 | 自研 | 待确认参数 |

**图片生成模型**：
| modelKey | modelName | 关键参数 |
|----------|-----------|---------|
| `nebula-ultra` | 全能图片模型V2 | quality(1K/2K/4K), ratio(9:16/16:9/1:1等多档), cameraControl, magic, focus |
| `multiple-angles` | 多角度 | qwen厂商，多角度生成 |

**图像增强**：
| modelKey | modelName | 关键参数 |
|----------|-----------|---------|
| `topaz-image-upscaler` | Topazlabs放大 | scale(2/4/6), style(Standard/Low Res/CGI/High Fidelity) |
| `topaz-video-upscaler` | Topazlabs视频放大 | scale(2/4/6), frame_rate(30/60/90fps) |
| `kling-video-enhance-o1` | 可灵O1增强 | resolution(1080p/2K/4K), frameRate(30/60/90), slowMotion |

**文本模型**：
| modelKey | modelName | 关键参数 |
|----------|-----------|---------|
| `aurora-3-prime` | 多模态文本模型Pro | prompt, modeType(Image2text/Video2text) |

### 2.2 模型参数详情（从 metadata JSON 提取）

#### 可灵 O1 (kling-video-o1) 完整参数
```json
{
  "modelKey": "kling-video-o1",
  "modelName": "可灵O1",
  "modelVendor": "Kling",
  "properties": {
    "count": [1],
    "template": { "displayName": "特效", "maxCount": 1 },
    "magic": true,
    "mention": true,
    "prompt": { "maxLength": 2000 },
    "ratio": { "displayName": "比例", "default": "16:9", "enum": ["16:9","1:1","9:16"] },
    "ratio_auto": { "default": "auto" },
    "duration": { "displayName": "时长", "enum": [5, 10], "default": 5 },
    "resolution": { "displayName": "清晰度", "default": "auto" },
    "quality": { "displayName": "生成品质", "enum": ["low","high"], "default": "low" },
    "modeType": {
      "description": "模态类型",
      "items": {
        "mixed2video": [1, 7],
        "frames2video": [1, 2],
        "videoEdit2video": [1, 5],
        "audio2video": [0, 0],
        "singleImage2video": [1, 1]
      },
      "mixed2videoConfig": { "videoMax": 1, "imageMaxWithVideo": 4 },
      "videoEdit2videoConfig": { "videoMax": 1, "imageMaxWithVideo": 4 }
    }
  },
  "config": {
    "settings": {
      "text2video": ["ratio", "quality", "duration"],
      "frames2video": ["quality", "resolution", "duration"],
      "singleImage2video": ["quality", "resolution", "duration"],
      "videoEdit2video": ["quality", "resolution", "duration"],
      "mixed2video": ["ratio", "resolution", "duration"]
    }
  },
  "rules": [
    { "require": ["prompt", "media"], "mode": "any" },
    { "require": ["prompt"], "forModeTypes": ["text2video"] }
  ]
}
```

#### 可灵 3.0 (kling-video-o3) 完整参数
```json
{
  "modelKey": "kling-video-o3",
  "modelName": "可灵 3.0",
  "modelVendor": "Kling",
  "properties": {
    "duration": { "min": 5, "max": 15, "step": 1, "default": 5 },
    "enableSound": { "displayName": "生成音频", "default": "on", "enum": ["on","off"] },
    "smartStoryboard": { "displayName": "智能分镜", "component": "switch", "default": false }
  }
}
```

#### 全能图片模型V2 (nebula-ultra) 完整参数
```json
{
  "modelKey": "nebula-ultra",
  "modelName": "全能图片模型V2",
  "modelVendor": "nebula",
  "properties": {
    "cameraControl": true,
    "magic": true,
    "focus": true,
    "mention": true,
    "count": [1, 2, 4],
    "prompt": { "maxLength": 0 },
    "quality": { "displayName": "分辨率", "enum": ["1K","2K","4K"], "default": "2K" },
    "ratio": {
      "displayName": "比例",
      "enum": ["auto","1:1","9:16","16:9","3:4","4:3","3:2","2:3","4:5","5:4","21:9"],
      "default": "16:9"
    },
    "searchable": { "displayName": "联网搜索", "default": 1 },
    "modeType": { "items": { "Image2image": [0, 7] } }
  }
}
```

---

## 三、Canvas 项目架构（从截图推断）

### 3.1 节点类型
| 节点 | 功能 | 输入 | 输出 |
|------|------|------|------|
| 故事脚本生成 | 生成剧本 | 小说文本? | 剧本JSON |
| 角色三视图 | 生成角色定妆照 | 角色描述 | 3张参考图 |
| 首帧图生视频 | 从图片生成视频 | 参考图+Prompt | 视频 |
| 音频生视频 | 从音频生成视频 | 音频+Prompt | 视频 |

### 3.2 工作流连接关系
```
故事脚本生成 → 角色三视图 → 首帧图生视频
                            → 音频生视频
```

---

## 四、仍无法获取的数据（认证问题）

以下 API 返回 `user not authorized`（JWT token 无效）：
- `GET /api/canvas/project/detail?uuid=xxx` — 项目完整数据（workflow JSON + nodes）
- `POST /api/canvas/project/draft/update` — 草稿更新
- `POST /api/task/generation/progress/batch` — 任务进度

**原因**：Canvas 专属 API 需要额外认证层（可能是 session cookie 或专用 canvas_token）

**已成功获取**：
- `GET /api/tool_spec/list` — 86KB，完整工具规格 ✅
- `GET /api/agent/whitelist/verify` — 白名单验证 ✅

---

## 五、结论

| 数据类型 | 可落地？ | 数据量 |
|---------|---------|--------|
| 模型工具规格（tool_spec） | ✅ | 86KB |
| 项目节点截图（Canvas界面） | ✅ | 截图已保存 |
| 项目workflow JSON（详细配置） | ❌ | 需canvas专属认证 |
| StarVideo 2.0短剧工作台数据 | ❌ | 需实际进入/tv |

---

## 六、后续研究建议

1. **获取Canvas项目数据**：需要研究 Canvas 的认证机制（可能是 `canvas_token` 或额外 cookie）
2. **StarVideo 2.0 工作台**：`/tv` URL 在无 profile 的浏览器中显示 404，需使用有登录态的 Chrome profile
3. **LibTV Skills 工作流**：可尝试在 Canvas 界面创建新项目，观察 API 调用

---

## 七、API 端点汇总

| API | 方法 | 认证 | 状态 |
|-----|------|------|------|
| `/api/tool_spec/list` | GET | JWT Bearer | ✅ 成功 |
| `/api/agent/whitelist/verify` | GET | JWT Bearer | ✅ 成功 |
| `/api/canvas/project/detail` | GET | JWT Bearer | ❌ 未授权 |
| `/api/canvas/project/list` | GET | JWT Bearer | ❌ Not Found |
| `/api/canvas/project/draft/update` | POST | JWT Bearer | ❌ 未授权 |
| `/api/task/generation/progress/batch` | POST | JWT Bearer | ❌ 未授权 |
| `/api/tv/msg/msgCounter` | GET | JWT Bearer | 待测试 |
