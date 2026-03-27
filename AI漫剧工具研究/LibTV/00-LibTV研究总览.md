# LibTV 研究总览

> 研究时间线：2026-03-24（首次）→ 2026-03-25（API突破 + StarVideo 2.0工作流完整解析）
> 研究深度：展示层 + tool_spec API（86KB） + StarVideo 2.0 10个节点完整配置

---

## 一、研究文件清单

| 文件 | 内容 | 可落地 |
|------|-------|--------|
| `LibTV/starvideo2/LibTV-StarVideo2-深度研究报告.md` | StarVideo 2.0 展示层分析（5步流程/5大工具/架构图） | ❌ 展示层 |
| `LibTV/starvideo2/01-startevideo2-hero.png` | StarVideo 2.0 首屏截图 | ⚠️ 参考 |
| `LibTV/starvideo2/02-five-steps-flow.png` | 5步制作流程截图 | ⚠️ 参考 |
| `LibTV/starvideo2/03-five-tools-detail.png` | 5大工具详解截图 | ⚠️ 参考 |
| `LibTV/starvideo2/04-system-architecture.png` | 系统架构图（上） | ⚠️ 参考 |
| `LibTV/starvideo2/05-detailed-arch.png` | 系统架构图（中） | ⚠️ 参考 |
| `LibTV/starvideo2/06-full-arch-complete.png` | 完整系统架构 | ⚠️ 参考 |
| `LibTV/starvideo2/07-model-layer-arch.png` | 模型层架构 | ⚠️ 参考 |
| `LibTV/canvas-project-libtv-skills.png` | LibTV Canvas 项目截图（4节点100%完成） | ⚠️ 参考 |
| `LibTV/LibTV-Canvas-API突破研究.md` | tool_spec API 完整数据 + 模型参数 | ✅ 86KB 可落地 |
| `LibTV-Canvas-深度研究报告.md` | 早期Canvas研究（框架级） | ❌ 旧版 |

---

## 二、StarVideo 2.0 已知信息

### 2.1 产品定位
- **slogan**：一键将小说转换为专业级短剧
- **入口**：`https://www.liblib.tv/tv`（需登录）
- **注意**：无profile浏览器访问返回404

### 2.2 5步制作流程
```
小说内容 → 剧本 → 分镜脚本 → 角色管理 → AI视频生成 → 后期剪辑（成片）
```

### 2.3 5大高效工具
| 工具 | 功能 |
|------|------|
| 剧本大师 | StarVideo 2.0 底模，文本→剧本 |
| 分镜大师 | 智能理解镜头语言 |
| 角色大师 | 统一风格和细节（形象+声音） |
| AI角色视频 | 多角色一致性算法 |
| 自动剪辑 | AI剪辑+配乐+音效 |

### 2.4 四层架构
```
应用层（5工具）→ 模型层（5专用模型）→ 工具层（6工具）→ 存储层（云+本）
```

### 2.5 待研究（需你的Chrome profile）
- 每个环节的具体输入/输出界面
- 内部数据结构（Schema）
- Prompt 配置详情
- API 接口

---

## 三、LibTV Canvas 已知信息

### 3.1 项目截图
- **文件**：`LibTV/canvas-project-libtv-skills.png`
- **项目**：LibTV Skills（未命名）
- **节点**：4个，全部100%完成
- **工作流**：
  ```
  故事脚本生成 ──→ 角色三视图 ──┬→ 首帧图生视频
                                └→ 音频生视频
  ```

### 3.2 成功获取的 API 数据

**tool_spec/list（86KB）** ✅

完整工具规格清单（部分）：

**视频模型**：
| modelKey | modelName | 厂商 | 关键参数 |
|----------|-----------|------|---------|
| `kling-video-o1` | 可灵O1 | Kling | ratio(16:9/1:1/9:16), duration(5s/10s), quality(low/high) |
| `kling-video-o3` | 可灵 3.0 | Kling | duration(5-15s), enableSound, smartStoryboard |
| `kling-v3-omni` | 可灵 3.0 Omni | Kling | 多模态 |
| `seedance-2.0` | 生视频2.0 | 自研 | 待确认 |
| `wan-2.1` | Wan 2.1 | 自研 | 待确认 |

**图片模型**：
| modelKey | modelName | 关键参数 |
|----------|-----------|---------|
| `nebula-ultra` | 全能图片模型V2 | ratio(11种), quality(1K/2K/4K), cameraControl, magic, focus, searchable |
| `multiple-angles` | 多角度 | 多角度生成 |

**增强模型**：
| modelKey | modelName | 关键参数 |
|----------|-----------|---------|
| `topaz-image-upscaler` | Topazlabs放大 | scale(2/4/6), style(5种) |
| `topaz-video-upscaler` | Topazlabs视频放大 | scale(2/4/6), frame_rate |
| `kling-video-enhance-o1` | 可灵O1增强 | resolution, frameRate, slowMotion |

**文本模型**：
| modelKey | modelName | 关键参数 |
|----------|-----------|---------|
| `aurora-3-prime` | 多模态文本模型Pro | Image2text, Video2text |

### 3.3 可灵O1完整参数（已提取）
```json
{
  "properties": {
    "ratio": { "default": "16:9", "enum": ["16:9","1:1","9:16"] },
    "duration": { "default": 5, "enum": [5, 10] },
    "quality": { "default": "low", "enum": ["low","high"] },
    "modeType": {
      "items": ["mixed2video","frames2video","videoEdit2video","audio2video","singleImage2video"]
    }
  }
}
```

### 3.4 可灵3.0完整参数（已提取）
```json
{
  "properties": {
    "duration": { "min": 5, "max": 15, "step": 1, "default": 5 },
    "enableSound": { "default": "on" },
    "smartStoryboard": { "displayName": "智能分镜", "default": false }
  }
}
```

### 3.5 全能图片模型V2完整参数（已提取）
```json
{
  "properties": {
    "ratio": {
      "enum": ["auto","1:1","9:16","16:9","3:4","4:3","3:2","2:3","4:5","5:4","21:9"],
      "default": "16:9"
    },
    "quality": { "enum": ["1K","2K","4K"], "default": "2K" },
    "cameraControl": true,
    "magic": true,
    "focus": true,
    "searchable": { "default": 1 }
  }
}
```

---

## 四、API 端点汇总

| API | 方法 | 认证 | 状态 |
|-----|------|------|------|
| `/api/tool_spec/list` | GET | JWT Bearer | ✅ 成功（86KB） |
| `/api/agent/whitelist/verify` | GET | JWT Bearer | ✅ 成功 |
| `/api/canvas/project/detail` | GET | JWT Bearer | ❌ 未授权 |
| `/api/canvas/project/list` | GET | JWT Bearer | ❌ Not Found |
| `/api/canvas/project/draft/update` | POST | JWT Bearer | ❌ 未授权 |
| `/api/task/generation/progress/batch` | POST | JWT Bearer | ❌ 未授权 |

---

## 五、研究结论

### 5.1 LibTV StarVideo 2.0
- **展示层**：5步流程/5大工具/架构图可见
- **内部机制**：需登录态Chrome profile才能研究
- **tool_spec**：86KB 完整模型参数已获取 ✅

### 5.2 LibTV Canvas
- **工作流结构**：4节点（脚本→角色→视频×2）已知
- **项目数据**：需canvas专属认证（JWT不够）
- **模型参数**：tool_spec已完整获取 ✅

### 5.3 对漫舟的借鉴价值
1. **模型参数**：可灵的ratio/duration/quality/modeType参数可直接对标漫舟分镜Skill
2. **智能分镜**：`smartStoryboard`开关 = 可灵O3的AI自动分镜建议
3. **多模态**：`enableSound` = 视频生成时自带音效

---

## 六、后续研究计划

| 优先级 | 任务 | 状态 |
|--------|------|------|
| ~~P0~~ | ~~用华哥Chrome profile进入StarVideo 2.0工作台~~ | ✅ 已完成（通过Canvas模板项目进入）|
| ~~P1~~ | ~~抓取Canvas项目内部workflow JSON~~ | ✅ 已完成（10个节点完整截图）|
| ~~P2~~ | ~~StarVideo 2.0各环节截图+操作流程~~ | ✅ 已完成（11张截图）|
| P3 | 三平台对比分析更新 | 待定 |

---

## 七、研究成果汇总（2026-03-25）

### 7.1 可落地数据清单

| 数据类型 | 文件 | 数据量 |
|---------|------|--------|
| StarVideo 2.0 工作流节点配置 | `LibTV-StarVideo2-小说漫剧工作流节点深度研究.md` | 10个节点完整配置 |
| StarVideo 2.0 节点截图 | `canvas/starvideo2-*.png` | 11张 |
| LibTV Canvas 节点配置 | `LibTV-Canvas-工作流节点深度研究.md` | 4个节点完整配置 |
| LibTV Canvas 节点截图 | `canvas/01-04-*.png` | 4张 |
| 工具规格 API 数据 | `LibTV-Canvas-API突破研究.md` | 86KB，62个工具 |
| tool_spec.json 原始数据 | `LibTV/tool_spec.json` | 116KB |

### 7.2 StarVideo 2.0 核心发现

1. **StarVideo 2.0 是 Canvas 模板**，非独立产品
2. **"小说漫剧工作流"** = Canvas 上的一个模板项目
3. **10个节点**：脚本生成 / 3种分镜 / 3种视频生成 / 视频合成 / 文字生音乐 / 图片反推 / 自己编写
4. **可灵 3.0 核心参数**：时长3-15s / 内置音效 / 智能分镜
5. **@引用素材** = 节点间数据传递机制
6. **无独立配音节点** = LibTV 最大短板

### 7.3 对漫舟借鉴清单

| 借鉴项 | LibTV 来源 | 漫舟实现 |
|--------|----------|---------|
| 分镜节点三模式（剧本/视频/角色）| StarVideo 2.0 | manzhou-storyboard 增加参考类型字段 |
| 画幅/分辨率参数内化 | StarVideo 2.0 节点设置 | manzhou-storyboard 提取为独立参数 |
| 智能分镜开关 | 可灵3.0 smartStoryboard | manzhou-storyboard 可选功能 |
| 内置音效 | 可灵3.0 enableSound | manzhou-sfx 已有（更强大）|
| 节点引用机制 | @引用素材 | manzhou 引用上游Skill输出 |
