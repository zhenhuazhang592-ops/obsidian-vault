# CLAUDE.md — huage888 短剧预生产系统

> 版本：v4.0 | 定位：预生产管理层 | 内容生成：qwen-max | 执行层：LibTV（用户手动）
> 核心目标：剧本 → qwen-max 生成全链路内容 → 用户照指南在 LibTV 手动生成 → 人审成片

---

## 一、系统定位

**huage888 是编排层，qwen-max 是内容生成引擎，LibTV 是执行层。**

三层分工：

```
huage888（编排层）              qwen-max（内容生成）       LibTV（执行层）
────────────────────────────────────────────────────────    ──────────────
✓ 读取 agents/*.md              ✓ 讲戏本生成             ✓ 模型调度
✓ 拼 system + user prompt       ✓ 角色提示词生成          ✓ prompt 优化
✓ 调用 qwen_pipeline.py         ✓ 场景提示词生成          ✓ 批量出图
✓ 解析返回内容                   ✓ 道具提示词生成           ✓ 批量出视频
✓ 质量审核                       ✓ 分镜脚本生成            ✓ 视频合成
✓ 写入 outputs/assets           ✓ 质量审核打分
✗ 不直接生成内容                  ✗ 不做编排决策            ✗ 不做剧本创作
✗ 不替 qwen-max 写 prompt        ✗ 不建立视觉圣经
```

**核心原则**：
- huage888（Claude Code）只做编排，不直接生成内容
- 所有内容生成调用 `python3 config/qwen_pipeline.py`
- qwen-max 负责所有文字内容生成（讲戏本/提示词/分镜脚本）
- LibTV 执行层由用户手动操作，不调 API

---

## 二、配置说明

### 2.1 qwen-max（内容生成引擎）

```bash
# 环境变量（必填）
export QWEN_API_KEY="your-api-key-here"

# 可选（默认已配置）
export QWEN_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
export QWEN_MODEL="qwen-max"   # 默认 qwen-max，可选 qwen-plus（调试用）

# 测试连接
python3 config/qwen_pipeline.py --test
```

**qwen_pipeline.py 调用规范：**
```bash
# 推荐：只传 --agent，自动拼接 agents/<name>.md + skills/<name>/SKILL.md
python3 config/qwen_pipeline.py \
  --agent director \
  --user "请分析以下剧本：..." \
  --output outputs/01-director-analysis.md

# 指定 skill（skill 名与 agent 名不同时）
python3 config/qwen_pipeline.py \
  --agent director \
  --skill custom-skill \
  --user "..."
```

**Agent 参数速查：**

| Agent | Temperature | 用途 |
|-------|------------|------|
| director | 0.75 | 讲戏本 |
| art-designer | 0.65 | 角色/场景提示词 |
| prop-designer | 0.60 | 道具提示词 |
| storyboard-artist | 0.55 | 分镜脚本 |
| *-review | 0.40 | 质量审核 |

详细参数（含 top_p/max_tokens/Token预算/项目覆盖规范）：详见 `config/prompts-registry.md`。
快捷参考：详见 `config/api-integration.md`。

### 2.2 LibTV（执行层，用户手动）

**LibTV Skill 入口**：`huage888` → 加载 `.claude/skills/libtv-skill/SKILL.md` → 生成操作指南 → 用户照做

**操作流程**：
1. huage888 调用 qwen-max 生成 JSON Spec → 生成操作指南
2. 用户打开 LibTV → 新建 Project → 按指南操作
3. 用户将返回的 element_id 填入资产注册表 → 继续下一步

---

## 三、系统架构

```
huage888（编排层 · Claude Code）
│
├── CLAUDE.md（制片人总控）
│       │
│       ├── config/
│       │   ├── visual-bible.md          ← 全局视觉锚点（所有 Agent 共享）
│       │   ├── video-model-registry.md  ← 视频模型能力矩阵（LibTV 选型依据）
│       │   ├── prompts-registry.md      ← Agent 参数配置（temperature/top_p/max_tokens）
│       │   ├── api-integration.md       ← qwen-max API 调用规范
│       │   └── qwen_pipeline.py         ← qwen-max 调用封装脚本
│       │
│       ├── agents/（qwen-max 的 system prompt 来源）│       │   ├── director.md              ← 阶段一：导演讲戏（较薄，角色定义）│       │   ├── art-designer.md          ← 阶段二A：角色/场景提示词（较薄）│       │   ├── prop-designer.md         ← 阶段二B：道具提示词（较薄）│       │   └── storyboard-artist.md     ← 阶段三：分镜脚本（较薄）│       │
│       ├── skills/（qwen-max 详细格式模板，较厚）│       │   ├── director-skill/SKILL.md  ← 导演讲戏格式规范│       │   ├── art-design-skill/SKILL.md ← 角色/场景 spec 格式│       │   └── storyboard-skill/SKILL.md ← 分镜脚本格式规范
│       │
│       └── .claude/skills/
│           └── libtv-skill/SKILL.md     ← LibTV 操作指南生成器
│
qwen-max（内容生成层）
│  config/qwen_pipeline.py
│
└── LibTV（执行层 · 用户手动）
        └── .claude/skills/libtv-skill/
            ├── SKILL.md                      ← 操作指南生成器
            └── scripts/                      ← 参考文件（不执行）
                └── _common.py                ← 结构化消息模板（供 huage888 引用）

---

## 三-2、qwen-max + LibTV 两阶段资产创建流程（核心）

```
huage888（编排层）              qwen-max（内容生成）          用户（LibTV 手动）
──────────────────────────────────────────────────────────────────────────

阶段一 ─────────────────────────────────────────────────────────────────────
Step 1  huage888 读取剧本
Step 2  huage888 拼 system(director.md) + user(剧本)
Step 3  huage888 调用 qwen_pipeline.py → 讲戏本
Step 4  qwen-max 生成 outputs/01-director-analysis.md

阶段二A（角色/场景）───────────────────────────────────────────────────────
Step 5  huage888 拼 system(art-designer.md) + user(讲戏本)
Step 6  huage888 调用 qwen_pipeline.py → assets/character-prompts.md + scene-prompts.md
Step 7  huage888 调用 qwen_pipeline.py → assets/character-front-view.json + scene-establishing.json

阶段二B（道具）────────────────────────────────────────────────────────────
Step 8  huage888 拼 system(prop-designer.md) + user(讲戏本道具清单)
Step 9  huage888 调用 qwen_pipeline.py → assets/prop-prompts.md

阶段二末尾（LibTV 手动）───────────────────────────────────────────────────
Step 10 huage888 加载 libtv-skill → 生成「角色正面图操作指南」
Step 11 用户在 LibTV 操作 → 拿到 element_id
Step 12 用户将 element_id 填入 assets/character-sheet.json / scene-sheet.json
Step 13 huage888 加载 libtv-skill → 生成「角色多角度操作指南」
Step 14 用户在 LibTV 操作 → 完成 Phase 2

阶段三 ─────────────────────────────────────────────────────────────────────
Step 15 huage888 读取 assets/03-asset-registry.md（含 element_id）
Step 16 huage888 拼 system(storyboard-artist.md) + user(讲戏本 + 资产注册表)
Step 17 huage888 调用 qwen_pipeline.py → outputs/02-storyboard-script.md

阶段三末尾（LibTV 手动）────────────────────────────────────────────────────
Step 18 huage888 加载 libtv-skill → 生成「分镜批量视频操作指南」
Step 19 用户在 LibTV 操作 → 生成视频片段 → 手动剪辑合成
```

**核心原则：huage888 编排 + qwen-max 生成内容 + 用户手动执行 LibTV。**

**LibTV 生图模型：nanobanana（固定，不可替换）**
**LibTV 生视频模型：Kling O1（推荐）或 Wan 2.6**

---

## 四、Visual Bible（全局视觉圣经）

> **这是整套系统的核心。** 所有 Agent 执行前必须读取，所有输出必须与此一致。

制片人收到剧本后，**第一步**生成或确认 `config/visual-bible.md`：

```markdown
# Global Visual Bible — [项目名]

## 项目基础

| 字段 | 内容 |
|------|------|
| 项目名称 | [填写] |
| 类型 | 短剧 / 漫剧 / 广告 / MV |
| 目标平台 | LibTV |
| 画面比例 | 9:16 竖屏 / 16:9 横屏 |
| 视觉风格 | [如：3D国漫CG / 日系动漫 / 写实都市] |
| 风格模板 | [从预设中选择，或填写具体描述；预设见下方风格模板库] |
| 当前版本 | v1.0（S01E01 建立） |

### 风格模板库（可直接引用）

| 模板名 | 关键词 | 适用场景 |
|--------|--------|---------|
| 赛博墨韵 | 赛博朋克+水墨，数据流+毛笔字，金色瞳孔+道姑髻 | 数字东方，短剧横屏 |
| 古风烟雨 | 青绿山水，写实古风，灰蓝冷调，烟雾朦胧 | 古装短剧，竖屏 |
| 日系动漫 | 扁平 shading，线条干净，低饱和，莫兰迪色 | 动漫短剧，竖屏 |
| 3D国漫CG | PBR材质，电影级光影，高对比度，写实渲染 | 精品短剧，横屏 |
| 写实都市 | 现代都市，自然光，暖色调，人物写实 | 都市短剧，9:16 |
| 自然纪录 | 微距摄影，阳光充沛，背景虚化，产品特写 | 广告/种草视频 |
| **中年修复术** | 半写实动漫，金继美学，今敏笔触，焦土暖调，岁月面孔 | 中年情感叙事，品牌故事片，竖屏/横屏均可 |
| **中年修复术+赛博墨韵** | 半写实+金继裂纹+金色瞳孔数字流，古今碰撞 | 品牌跨界短片，横屏 |

> 预设模板可组合使用（如"古风烟雨+自然纪录"），在整体风格中说明切换规则。

## 整体风格

- **美术风格**：[具体描述，3-5个关键词]
- **主色调**：[如：暖黄金色调，辅以冷蓝阴影]
- **整体饱和度**：高 / 中 / 低（莫兰迪）
- **对比度**：高 / 中 / 低
- **禁止色调**：[明确列出]

## 光影基准

| 场景类型 | 主光源方向 | 色温 | 强度 | 特殊效果 |
|---------|---------|------|------|---------|
| 日景-室内 | 侧窗光 | 中性偏暖 | 中 | 窗帘光影 |
| 夜景-室内 | 台灯暖光 | 暖黄 | 低 | 局部照明 |
| 夜景-室外 | 路灯顶光 | 冷白 | 低 | 霓虹补光 |

## 角色视觉锚点（六层身份锚点系统）

> 参考：moyin-creator 六层角色一致性系统。
> 每层必须填写，"无"也要写"无"，禁止留空。

### [角色名] | C[N]

| 层级 | 字段 | 内容 |
|------|------|------|
| 第1层 | **外貌特征** | [脸型+眼型+鼻型+肤色，3-5个结构词，无情绪词] |
| 第2层 | **发型发色** | [具体描述，黑长直/道姑髻/短发等] |
| 第3层 | **服装装备** | [本集具体服装，颜色+款式+材质+配饰] |
| 第4层 | **标志性元素** | [习惯动作/口头禅/疤痕/特殊配饰，无则写"无"] |
| 第5层 | **气质类型** | [如：清冷古典/阳光痞帅/威严霸气，用2-3个形容词] |
| 第6层 | **禁止变体** | [明确矛盾特征，如：禁止短发/禁止现代装/禁止写实人脸] |

| 字段 | 内容 |
|------|------|
| **变体清单** | [如有多个状态（如淋雨/反转），列出各变体差异] |
| **参考图** | [Phase1 完成后填入 element_id] |

### [角色名] | C[N+1]

[同上格式]

## 角色说话风格锚点（第7层）

> **来源：huobao-drama voice_style + ZJT behavior.speaking_style**
> 作用：确保台词风格跨集统一，分镜脚本和剧本创作必须遵守。
> 语气标签枚举（可组合）：书生腔 / 古典冷艳 / 阳光痞帅 / 威严霸气 / 诗意留白 / 冷/暖/痞

### [角色名] | C[N]

| 字段 | 内容 |
|------|------|
| 口癖/口头禅 | [角色专属词汇，3-5个] |
| 语气词 | [高频语气助词，如"也罢""嗯..."] |
| 句长偏好 | 短促有力 ≤10字 / 诗意留白 / 啰嗦解释型 |
| 情绪温度 | 冷（克制）/ 暖（关怀）/ 痞（调侃）/ 中性 |
| 禁止词汇 | [此角色绝对不说的词/语气，无则写"无"] |
| 语气标签 | [从枚举中选择1-2个：书生腔/古典冷艳/阳光痞帅/威严霸气/诗意留白] |

### [角色名] | C[N+1]

[同上格式]

## 场景视觉锚点

### [场景名] | S[N]

- **空间类型**：[室内/室外]
- **光源特征**：[固定光源]
- **氛围色调**：[主色调关键词]

## 道具视觉锚点

### [道具名] | P[N]

- **外观**：[形态+材质+颜色+标志性细节]
- **出现集数**：[首次出现]
- **状态变化**：[如有]

## 全局禁用规则

- ❌ 版权 IP 角色/场景（哈利波特/漫威/迪士尼等）
- ❌ 政治人物/政治符号
- ❌ 暴力血腥写实描述
- ❌ 未成年不当内容

## 版本变更记录

| 版本 | 集数 | 变更内容 | 日期 |
|------|------|---------|------|
| v1.0 | S01E01 | 初始建立 | [日期] |
```

---

## 五、三阶段流水线

### ▌启动前检查（刚性规则）

启动前检查（刚性规则）：

```
huage888 制片人执行：
1. ✅ 新建项目文件夹（必做）
   - 路径：projects/[集数名]/，如 projects/断桥奇遇-v3/
   - 结构：projects/[集数名]/
            ├── CLAUDE.md        ← 复制本文件作为本集说明
            ├── config/          ← visual-bible.md
            ├── assets/          ← 本集资产
            ├── outputs/         ← 本集输出
            └── docs/            ← 原始剧本等

2. 确认 QWEN_API_KEY 环境变量已设置
   python3 config/qwen_pipeline.py --test

3. 生成/确认 config/visual-bible.md
   - 已有 IP 资产时复用（如漠玫 IP），无则新建

4. 检查 assets/ 目录，列出已有资产

5. 宣布启动，说明本集新增/复用资产清单
```

**LibTV 项目管理（用户手动执行）：**
- 每个新剧集 → 用户在 LibTV 控制台新建一个独立 Project
- 每个新任务 → 用户在 LibTV 新建一个 Session
- 原因：避免旧项目历史消息污染新剧集生成结果

---

### ▌阶段一：导演讲戏（qwen-max 驱动）

```
huage888 读取：
  config/visual-bible.md + 剧本

huage888 拼 system prompt：
  agents/director.md 的「你是谁」+ 「核心约束」+ 「工作流程」

huage888 调用 qwen-max：
  python3 config/qwen_pipeline.py \
    --agent director \
    --user "请分析以下剧本：[粘贴剧本内容]" \
    --output outputs/01-director-analysis.md

qwen-max 输出：
  outputs/01-director-analysis.md（人物清单+场景清单+道具清单+分段讲戏）
```

**输出包含**：
- 人物清单（含角色锚点、资产状态）
- 场景清单（含光影设置）
- 道具清单（含分级和特写需求）
- 分段讲戏（画面+动作+台词+运镜+光影五维融合）
- 视觉圣经对照（每段落标注 ✅ / ⚠️）

**制片人审核**：
1. 业务审核（script-review-skill）→ PASS/FAIL
2. 合规审核（compliance-skill）→ PASS/FAIL
3. FAIL → 反馈打回（最多3轮）
4. PASS → 进入阶段二

---

### ▌阶段二：资产管理（qwen-max 驱动）

```
huage888 读取：
  config/visual-bible.md + outputs/01-director-analysis.md

huage888 调用 qwen-max（art-designer）：
  python3 config/qwen_pipeline.py \
    --agent art-designer \
    --user "基于讲戏本生成角色+场景提示词和 JSON spec：[粘贴 01-director-analysis.md]" \
    --output assets/character-prompts.md

  python3 config/qwen_pipeline.py \
    --agent art-designer \
    --user "基于讲戏本生成场景提示词：[粘贴 01-director-analysis.md]" \
    --output assets/scene-prompts.md

huage888 调用 qwen-max（prop-designer）：
  python3 config/qwen_pipeline.py \
    --agent prop-designer \
    --user "基于讲戏本道具清单生成提示词：[粘贴道具清单]" \
    --output assets/prop-prompts.md

huage888 读取 JSON spec → 生成 LibTV 操作指南 → 用户手动执行
```

**element_id 填入规则**：
- Phase1 返回的 element_id 填入 Phase2 JSON 的 `characters[].element_id` / `scenes[].element_id`
- 每个角色/场景独立 element_id，不可共享
- 大圣多变体（C002a/b/c）各自独立 element_id

---

### ▌阶段三：分镜脚本（qwen-max 驱动）

```
huage888 读取：
  config/visual-bible.md
  outputs/01-director-analysis.md
  assets/03-asset-registry.md（element_id + 场景图 URL）

huage888 调用 qwen-max：
  python3 config/qwen_pipeline.py \
    --agent storyboard-artist \
    --user "基于讲戏本和资产注册表生成分镜脚本：[粘贴相关内容]" \
    --output outputs/02-storyboard-script.md

huage888 读取分镜脚本 → 生成 LibTV 操作指南 → 用户手动执行
```

**分镜脚本格式**（LibTV 脚本节点兼容）：

```markdown
## 分镜脚本 | S01E01 | [剧名]

| 镜头号 | 景别 | 运镜 | 画面描述 | 台词 | 音效/音乐 | 主体 | 场景 | 时长 |
|-------|------|------|---------|------|----------|------|------|------|
| 01 | 全景 | 固定 | [建立镜头，描述环境] | — | [环境音] | C001 | S001 | 3s |
| 02 | 中景 | 推镜头 | [角色入场，描述动作] | [角色：台词] | — | C001 | S001 | 5s |
...
```

**制片人审核**：
1. 业务审核（storyboard-review-skill）→ 完整性 + 视觉圣经一致性
2. 合规审核（compliance-skill）
3. PASS → **执行 LibTV 视频生成流程**

**▌阶段三附：LibTV 视频生成流程（用户手动操作）**

```
huage888 执行：

1. 读取 assets/03-asset-registry.md（已填入所有 element_id）
2. 加载 .claude/skills/libtv-skill/SKILL.md
3. 读取 outputs/02-storyboard-script.md
4. 生成「分镜批量视频操作指南」（含角色库、场景库、分镜列表）
5. 向用户输出完整操作指南

用户执行：

1. 打开 LibTV → 新建 Project
2. 选择视频模型 Kling O1（或 Wan 2.6）
3. 按操作指南逐镜头发送 Prompt
4. 每个镜头生成完成 → 下载到本地
5. 手动剪辑合成 → 最终成片
```

---

## 六、最终交付物

```
outputs/
├── 01-director-analysis.md   ← 导演讲戏本 + 三张清单
└── 02-storyboard-script.md  ← 分镜脚本（LibTV脚本节点格式）

assets/
├── character-front-view.json ← Phase1：角色正面图 spec
├── character-sheet.json      ← Phase2：角色多角度 spec（待填 element_id）
├── scene-establishing.json  ← Phase1：场景全景图 spec
├── scene-sheet.json         ← Phase2：场景多角度 spec（待填 element_id）
├── 03-asset-registry.md     ← 资产注册表（element_id 追踪）
├── character-prompts.md     ← 角色描述词（旧版，人工参考）
└── scene-prompts.md        ← 场景描述词（旧版，人工参考）

config/
└── visual-bible.md          ← 全局视觉圣经（跨集维护）
```

---

## 七、审核标准

**PASS 标准**：加权平均分 ≥ 8，且无单项 < 6

**修改上限**：每阶段最多 3 轮；超出 → 输出问题清单请用户介入

| 异常 | 处理 |
|------|------|
| 剧本 > 5000 字 | 提示拆集（每集 2000-3000 字）|
| 视觉风格未声明 | 停止，要求用户补充 |
| 资产未上传 | 停止，先完成 LibTV 上传 |
| 合规红线触碰 | 立即停止，给出违规说明 |

---

## 八、跨集管理

新集启动时：
1. 确认 visual-bible.md 版本（无变更直接用）
2. 列出已有资产（C001/S001/P001 等已建立）
3. 告知 director：复用已有资产的编号
4. 新增角色/场景/道具 → 执行阶段二上传流程
