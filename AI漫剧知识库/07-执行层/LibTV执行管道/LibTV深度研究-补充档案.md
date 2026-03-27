# LibTV深度研究 · 补充档案

> 来源：`AI漫剧工具研究/LibTV/`（深度研究报告，2026-03-25）
> 对应源码：`/Users/huage/Downloads/libtv-skills-main/skills/libtv-skill/`
> 整合日期：2026-03-26

---

## 一、研究文档来源

| 文件 | 内容 | 可落地 |
|------|------|--------|
| `LibTV-Canvas-API突破研究.md` | tool_spec API 86KB + 模型参数 | **新增发现** |
| `LibTV-Canvas-工作流节点深度研究.md` | 4个Canvas节点完整配置 | 参考洞察 |
| `LibTV-StarVideo2-小说漫剧工作流节点深度研究.md` | StarVideo2模板 10节点完整配置 | 参考洞察 |
| `starvideo2/LibTV-StarVideo2-深度研究报告.md` | StarVideo2展示层/架构分析 | 参考洞察 |
| `00-LibTV研究总览.md` | 研究成果汇总 | 参考洞察 |
| `tool_spec.json` | API原始数据（116KB） | 存档 |

---

## 二、Canvas API能力（新发现）

> 以下能力在 libtv-skills-main 源码中未覆盖，属于通过 Chrome DevTools Protocol 拦截 XHR 获取的新发现。

### 2.1 tool_spec/list — 完整模型规格清单

**端点**：`GET /api/tool_spec/list`
**认证**：JWT Bearer token
**数据量**：86KB，62个工具
**来源文件**：`tool_spec.json`（已存档）

此接口可**动态查询平台所有可用模型**，libtv-skills源码只有5个硬编码脚本，无此接口。

```bash
# 漫舟复用方式：在 manzhou-director-v2 中增加模型发现步骤
# Step 0：调用 tool_spec/list 获取当日可用模型列表
# Step 1：根据分镜需求（文生图/图生视频/增强）筛选最佳模型
```

### 2.2 增强模型系列（libtv-skills 未覆盖）

| modelKey | modelName | 厂商 | 关键参数 | 漫舟价值 |
|----------|-----------|------|---------|---------|
| `topaz-image-upscaler` | Topazlabs图片放大 | Topazlabs | scale(2/4/6), style(5种) | 文生图后放大至4K |
| `topaz-video-upscaler` | Topazlabs视频放大 | Topazlabs | scale(2/4/6), frame_rate(30/60/90) | 视频超分+升帧 |
| `kling-video-enhance-o1` | 可灵O1增强 | Kling | resolution(1080p/2K/4K), frameRate, slowMotion | 视频后处理 |
| `seedance-2.0` | 生视频2.0 | 自研 | 待确认 | 新模型 |
| `wan-2.1` | Wan 2.1 | 自研 | 待确认 | 新模型 |

**漫舟复用价值**：LibTV执行管道目前只覆盖"生成"，增强/放大环节需手动处理。以上模型可将整个管线延伸为"生成→增强→导出"三段式。

### 2.3 Aurora 3 Prime — 多模态文本模型

| 字段 | 内容 |
|------|------|
| modelKey | `aurora-3-prime` |
| modelName | 多模态文本模型Pro |
| modeType | `image2text`（图生文）、`video2text`（视频生文） |

**漫舟复用价值**：
- **图生文**：`[SFX:]` 音效标注可借助 image2text 反推画面内容
- **视频生文**：视频生成结果可自动解析台词/场景描述，用于 Step 9 配音对齐

### 2.4 Nebula Ultra — 全能图片模型V2 完整参数

| 参数 | 选项 | 默认 |
|------|------|------|
| quality | 1K / 2K / 4K | 2K |
| ratio | auto / 1:1 / 9:16 / 16:9 / 3:4 / 4:3 / 3:2 / 2:3 / 4:5 / 5:4 / 21:9 | 16:9 |
| cameraControl | true（支持摄像机控制） | — |
| magic | true（魔法风格） | — |
| focus | true（对焦控制） | — |
| searchable | 联网搜索（开关） | 开启 |

**漫舟复用价值**：画幅 9:16 是竖屏短剧核心比例，cameraControl 可控制景深——这两个参数应固化到 manzhou-shot-script 的 Prompt 模板中。

### 2.5 可灵 3.0 完整参数（新增）

```json
{
  "modelKey": "kling-video-o3",
  "properties": {
    "duration": { "min": 5, "max": 15, "step": 1, "default": 5 },
    "enableSound": { "default": "on" },       // 新发现：内置音效
    "smartStoryboard": { "default": true }    // 新发现：AI自动分镜建议
  }
}
```

**漫舟复用价值**：
- `enableSound: on` → 生成视频时自带音效（与 manzhou-sfx 互补，不可替代）
- `smartStoryboard: true` → 可灵3.0内置AI分镜建议（漫舟分镜Skill的可选参考）

### 2.6 Canvas API 认证分层（新发现）

| API | 认证 | 状态 |
|-----|------|------|
| `/openapi/session` | Bearer JWT | libtv-skills已覆盖 |
| `/openapi/upload` | Bearer JWT | libtv-skills已覆盖 |
| `/api/tool_spec/list` | Bearer JWT | **新增发现** |
| `/api/canvas/project/detail` | Bearer JWT | ❌ 需额外canvas_token |
| `/api/canvas/project/draft/update` | Bearer JWT | ❌ 需额外canvas_token |

**结论**：Canvas 项目数据（workflow JSON）无法通过 libtv-skills 的 JWT token 获取，研究中的节点配置均来自截图分析，非API抓取。

---

## 三、StarVideo2工作流（新发现）

### 3.1 核心发现：StarVideo2 = Canvas 模板

> **重要**：`starvideo2/LibTV-StarVideo2-深度研究报告.md` 指出 StarVideo 2.0 是独立产品入口（`/tv`）。但 `LibTV-StarVideo2-小说漫剧工作流节点深度研究.md` 确认：**"小说漫剧工作流" = Canvas 上的一个模板项目**，非独立执行管道。

- **产品关系**：StarVideo 2.0（产品层）/ 小说漫剧工作流（Canvas模板层）/ Canvas API（执行层）
- **可研究性**：`/tv` URL 在无登录态浏览器返回404，需有登录态的Chrome profile

### 3.2 StarVideo2 vs 通用Canvas工作流

| 维度 | StarVideo2（小说漫剧模板）| 通用Canvas（libtv-skills）|
|------|--------------------------|--------------------------|
| 节点数量 | 10个 | 4个 |
| 分镜节点 | **3种**（剧本/视频/角色）| 0个 |
| 视频生成节点 | **3种**（首尾帧/首帧/文生视频）| 1个（首帧图生视频）|
| 合成节点 | **视频合成** | 无 |
| 音乐节点 | **文字生音乐**（纯音乐/音乐+歌词）| **音频生视频** |
| 反推节点 | **图片反推提示词** | 无 |
| 智能分镜 | Kling 3.0 内置（smartStoryboard）| 无 |
| 内置音效 | Kling 3.0 内置（enableSound）| 无 |
| 执行管道 | 无独立Python/API | 5个Python脚本 ✅ |

### 3.3 StarVideo2 节点清单（完整10个）

```
第一行（AI生成）
  节点1：脚本生成器 — 小说转剧本/短剧创作

第二行（分镜转换）
  节点2：剧本生成分镜脚本 — 镜头级拆分（景别/运镜/时长/台词）
  节点3：视频参考生成分镜脚本 — 视频参考驱动
  节点4：角色生成分镜脚本 — 角色图驱动

第三行（视频生成）
  节点5：首尾帧生成视频 — Kling 3.0 / 3-15s / enableSound / smartStoryboard
  节点6：首帧生成视频 — Kling 3.0 / 3-15s
  节点7：文生视频 — Kling 3.0

最右（剪辑）
  节点8：视频合成 — 多片段拼接成片

左侧边栏（素材）
  节点9：文字生音乐 — 仅音乐 / 音乐+歌词
  节点10：图片反推提示词 — 反推 / 结构化解析
  节点11：自己编写内容 — 手动输入剧本
```

### 3.4 StarVideo2 节点间数据流

```
剧本（手动或导入）
  ↓ @引用素材
脚本生成器（结构化剧本）
  ↓ @引用素材
剧本/视频/角色生成分镜脚本
  ↓ @引用素材
  ├→ 首尾帧生成视频 → 视频合成
  ├→ 首帧生成视频   → 视频合成
  ├→ 文生视频       → 视频合成
  └→ 文字生音乐（可选）
```

---

## 四、执行层补充判断

### 判断1：Canvas API新能力

| 新发现 | libtv-skills状态 | 漫舟复用价值 |
|--------|----------------|------------|
| `tool_spec/list` API | ❌ 未覆盖 | **高**：动态模型发现，支撑模型选型决策 |
| Topaz图片/视频放大 | ❌ 未覆盖 | **高**：后处理管线延伸 |
| Kling O1增强 | ❌ 未覆盖 | **中**：视频质量提升 |
| Aurora 3 Prime | ❌ 未覆盖 | **中**：图生文/视频生文辅助 |
| Nebula Ultra完整参数 | 部分覆盖（部分参数新）| **高**：9:16竖屏/cameraControl需固化 |
| 可灵3.0完整参数 | 部分覆盖 | **高**：enableSound/smartStoryboard新发现 |
| Canvas API认证分层 | 部分覆盖 | **低**：仅研究洞察，无新执行代码 |

### 判断2：StarVideo2独立执行层

**状态**：不需要新建

**原因**：
1. StarVideo2是Canvas模板，**无独立API执行管道**
2. 所有节点能力（分镜/视频生成/合成/音乐）在libtv-skills的5个脚本覆盖范围内
3. `tool_spec.json`（116KB）虽记录了模型规格，但不含StarVideo2专属API
4. 视频合成、文字生音乐等高级节点未发现独立Python封装

**补充说明**：若未来需要，可扩展方向：
- **tool_spec/list 调用封装**（动态模型发现）→ 新增 `query_models.py`
- **Topaz增强封装**（视频后处理）→ 新增 `enhance_media.py`
- **Aurora图生文封装**（内容解析）→ 新增 `analyze_media.py`

---

## 五、对漫舟的补充借鉴

### 5.1 可立即固化的参数

以下参数应从 Prompt 内描述**提取为独立字段**，参考LibTV节点设计：

```markdown
## 视频生成参数（从LibTV Canvas节点固化）

| 字段 | LibTV来源 | 选项 | 漫舟位置 |
|------|---------|------|---------|
| ratio（画幅）| 节点级别设置 | 9:16/16:9/1:1 | manzhou-shot-script |
| quality（质量）| 节点级别设置 | 1K/2K/4K | manzhou-shot-script |
| duration（时长）| 节点级别设置 | 3-15s（Kling3）| manzhou-shot-script |
| enableSound（音效）| Kling 3.0 | on/off | manzhou-shot-script（新增字段）|
| smartStoryboard（智能分镜）| Kling 3.0 | true/false | manzhou-director-control（参考）|
```

### 5.2 架构借鉴：@引用素材机制

LibTV的`@引用素材` = 节点间自动数据传递，漫舟目前是手动复制粘贴。

**漫舟当前状态**：
- manzhou-director-control 输出 → manzhou-shot-script（手动复制）
- manzhou-shot-script 输出 → LibTV执行（手动复制）

**优化方向**：定义标准接口契约，使Skill输出可直接作为下游输入，减少人工复制。

### 5.3 漫舟独有的能力（LibTV无法替代）

| 漫舟独有 | StarVideo2对应 | 说明 |
|---------|--------------|------|
| VO配音（`voice:`标签）| 无 | LibTV无配音节点 |
| BGM情绪曲线（`[BGM:]`）| 文字生音乐 | LibTV=纯音乐，无情绪曲线 |
| SFX六维音效（`[SFX:]`）| 无 | LibTV无音效节点 |
| 爆款算法（SRL/3-15-30）| 无 | StarVideo2无此模块 |
| 风控审核（manzhou-safety）| 无 | StarVideo2无此模块 |
| 声音克隆 | 无 | StarVideo2无此功能 |

---

## 六、补充结论

| 判断项 | 结论 | 行动 |
|--------|------|------|
| Canvas API新能力 | 有新增发现 | 在现有档案中标注，不新建文件 |
| StarVideo2独立执行层 | 不需要 | 标注原因，不新建目录 |
| tool_spec.json存档 | 已存档 | 位置：`AI漫剧工具研究/LibTV/tool_spec.json` |
| 漫舟执行层扩展建议 | 3个方向 | 记录在"补充说明"中，供后续迭代 |

---

*补充档案整合自：LibTV-Canvas-API突破研究.md / LibTV-Canvas-工作流节点深度研究.md / LibTV-StarVideo2-小说漫剧工作流节点深度研究.md / starvideo2/LibTV-StarVideo2-深度研究报告.md / 00-LibTV研究总览.md / tool_spec.json*
