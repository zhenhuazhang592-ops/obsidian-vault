# config/prompts-registry.md — 提示词注册表

> huage888 系统 | v1.0 | qwen-max 参数配置中心
> 版本：2026-04-05 | 替代 Toonflow t_prompts 表（Toonflow 无 temperature/max_token 配置）
>
> **设计原则**：
> - Toonflow 缺陷：temperature 全硬编码为 `temperature: 1`，无 per-agent 配置
> - huage888 改进：所有参数进注册表，支持 default + project override 双轨
> - qwen_pipeline.py 读取本文件，自动注入参数，无需手动指定

---

## 一、架构定位

```
agents/*.md      ← system prompt 骨架（角色定义，轻量，只读）
skills/*-skill.md ← 详细格式规范（结构模板，轻量，只读）
config/prompts-registry.md ← 参数配置（temperature/max_tokens/top_p，中量）
                                                 ↑
                              qwen_pipeline.py 读取此文件注入 API 调用
```

**双轨机制（Toonflow t_prompts 同款，Markdown 适配版）：**

| 轨道 | 用途 | 可写性 | 说明 |
|------|------|--------|------|
| `### [agent].default` | 工厂默认参数 | ❌ 只读 | 系统级，每次升级覆盖 |
| `### [agent].override` | 项目自定义 | ✅ 可写 | 项目级，覆盖 default，仅对本项目生效 |

**生效逻辑：**
```
activeParams = overrideParams ?? defaultParams
```

---

## 二、Agent 参数注册表

### 2.1 director（导演 · 阶段一）

```yaml
code: director
name: 导演讲戏
phase: 阶段一
priority: P0
model: qwen-max
temperature: 0.75
top_p: 0.95
max_tokens: 8192
top_k: 50
reasoning_depth: medium
output_format: text/markdown
system_prompt_file: agents/director.md
skill_file: skills/director-skill.md
input_template: |
  请分析以下剧本，生成导演讲戏本：
  [粘贴剧本内容]

  格式规范详见：skills/director-skill.md
  视觉圣经：config/visual-bible.md（如存在）
  ---
  必填输出字段：
  - 人物清单（含 C00X 编号 + 资产状态）
  - 场景清单（含 S00X 编号 + 光影设置）
  - 道具清单（含 P00X 编号 + 分级）
  - 分段讲戏（每段落含五维：画面+动作+台词+运镜+光影）
  - emotionalArc（情绪弧线，如：2(压抑)→5(对抗)→9(爆发)→3(余波)）
  - keyEvents（每段落四选一：起/承/转/合）
  - Visual Bible 对照（✅/⚠️偏离）
  ---
  输出文件：outputs/01-director-analysis.md
```

| 参数 | 值 | 选型依据 |
|------|-----|---------|
| temperature | 0.75 | 讲戏本需创意整合，适中偏高 |
| top_p | 0.95 | 高多样性，允许长尾词汇 |
| max_tokens | 8192 | 讲戏本篇幅长（含5段+）|
| reasoning_depth | medium | 分段讲戏需推理，非纯执行 |

**典型输出规模：** 3000-6000 字（4-6段讲戏 + 三张清单 + JSON Schema）

---

### 2.2 art-designer（服化道 · 阶段二A）

```yaml
code: art-designer
name: 角色/场景资产管理
phase: 阶段二A
priority: P0
model: qwen-max
temperature: 0.65
top_p: 0.95
max_tokens: 8192
top_k: 50
reasoning_depth: medium
output_format: text/markdown + application/json
system_prompt_file: agents/art-designer.md
skill_file: skills/art-design-skill.md
input_template: |
  基于讲戏本生成角色+场景资产 spec：

  1. 角色描述词：assets/character-prompts.md
     格式：skills/art-design-skill.md 的角色描述词格式
     每个角色含：appearance_tags（≥4个）+ outfit_tags（≥3个）+ views（≥4个视角）

  2. 角色 JSON Spec（LibTV Phase1）：assets/character-front-view.json
     格式：skills/art-design-skill.md 的 CharacterSchema

  3. 场景描述词：assets/scene-prompts.md
     格式：skills/art-design-skill.md 的场景描述词格式

  4. 场景 JSON Spec（LibTV Phase1）：assets/scene-establishing.json
     格式：skills/art-design-skill.md 的 SceneSchema

  必填引用：outputs/01-director-analysis.md 的 C00X/S00X 编号
  禁止引入讲戏本中没有的角色/场景描述
```

| 参数 | 值 | 选型依据 |
|------|-----|---------|
| temperature | 0.65 | 资产描述需稳定一致性，偏低 |
| top_p | 0.95 | 保持一定词汇多样性 |
| max_tokens | 8192 | 多角色×多场景×多视角，规模大 |
| reasoning_depth | medium | 标签拆分需推理 |

**典型输出规模：** 4000-8000 字（角色描述词 + 场景描述词 + JSON Spec × N）

---

### 2.3 prop-designer（道具师 · 阶段二B）

```yaml
code: prop-designer
name: 道具资产管理
phase: 阶段二B
priority: P1
model: qwen-max
temperature: 0.60
top_p: 0.95
max_tokens: 6144
top_k: 50
reasoning_depth: medium
output_format: text/markdown + application/json
system_prompt_file: agents/prop-designer.md
skill_file: skills/prop-design-skill.md
input_template: |
  基于讲戏本道具清单生成道具提示词：

  输出文件：assets/prop-prompts.md

  格式：skills/prop-design-skill.md 的道具描述词格式

  必填字段：
  - 外观描述（形态+材质+颜色+标志性细节）
  - 叙事功能
  - 状态变化记录（所有出现段落）
  - 文字锚点（分镜兜底用）

  仅处理一级（核心）道具
  二三级道具纳入场景描述，不单独出资产

  必填引用：outputs/01-director-analysis.md 的 P00X 编号
```

| 参数 | 值 | 选型依据 |
|------|-----|---------|
| temperature | 0.60 | 道具描述最需稳定性，数值最低 |
| top_p | 0.95 | 保持词汇多样性 |
| max_tokens | 6144 | 道具数量少于角色，规模中等 |

**典型输出规模：** 1500-4000 字（道具描述词 × N + JSON Schema）

---

### 2.4 storyboard-artist（分镜师 · 阶段三）

```yaml
code: storyboard-artist
name: 分镜脚本撰写
phase: 阶段三
priority: P0
model: qwen-max
temperature: 0.55
top_p: 0.95
max_tokens: 8192
top_k: 50
reasoning_depth: medium
output_format: text/markdown
system_prompt_file: agents/storyboard-artist.md
skill_file: skills/storyboard-skill.md
input_template: |
  基于讲戏本和资产注册表生成分镜脚本：

  输出文件：outputs/02-storyboard-script.md

  格式：skills/storyboard-skill.md 的分镜脚本格式

  必填引用：
  - outputs/01-director-analysis.md（讲戏本）
  - assets/03-asset-registry.md（已填 element_id + image_url）

  分镜脚本表格列：镜头号/景别/运镜/画面描述/台词/音效音乐/主体/场景/时长

  禁止引入讲戏本中没有的 C00X/S00X/P00X
  色调和光影必须与 config/visual-bible.md 一致
```

| 参数 | 值 | 选型依据 |
|------|-----|---------|
| temperature | 0.55 | 分镜最需稳定执行，数值最低 |
| top_p | 0.95 | 保持词汇多样性 |
| max_tokens | 8192 | 分镜脚本规模大（25+ 镜头）|
| reasoning_depth | medium | 镜头拆分需叙事推理 |

**典型输出规模：** 3000-7000 字（25 镜头 × 100-200 字/镜头 + 段落汇总）

---

## 三、审核 Agent 参数表

```yaml
code: script-review
name: 剧本/讲戏本审核
phase: 阶段一末尾
priority: P1
model: qwen-max
temperature: 0.40
top_p: 0.90
max_tokens: 2048
reasoning_depth: high  # 审核需深度推理，不惜牺牲速度
output_format: text/markdown
input_template: |
  审核以下讲戏本，给出 PASS/FAIL 及修改建议：
  [粘贴 outputs/01-director-analysis.md]
```

```yaml
code: art-review
name: 资产审核
phase: 阶段二末尾
priority: P1
model: qwen-max
temperature: 0.40
top_p: 0.90
max_tokens: 2048
reasoning_depth: high
output_format: text/markdown
input_template: |
  审核以下资产 spec，检查与讲戏本的一致性：
  [粘贴 assets/character-prompts.md / scene-prompts.md]
```

```yaml
code: storyboard-review
name: 分镜脚本审核
phase: 阶段三末尾
priority: P1
model: qwen-max
temperature: 0.40
top_p: 0.90
max_tokens: 2048
reasoning_depth: high
output_format: text/markdown
input_template: |
  审核以下分镜脚本，检查：
  1. 与讲戏本的叙事一致性
  2. 资产引用准确性（C00X/S00X/P00X）
  3. 视觉圣经一致性
  [粘贴 outputs/02-storyboard-script.md]
```

| 参数 | 审核 Agent 通用值 | 依据 |
|------|-----------------|------|
| temperature | 0.40 | 审核需稳定判断，不接受创意漂移 |
| top_p | 0.90 | 略保守，保证逻辑严谨 |
| max_tokens | 2048 | 审核输出简短，2048 足够 |
| reasoning_depth | high | 深度推理模式 |

---

## 四、Temperature 调参指南

> **来源：** qwen-max 官方 + huage888 实测经验

### 4.1 温度梯度设计原理

```
temperature 越高 → 创意越多 → 风险越大 → 一致性越低
temperature 越低 → 机械执行 → 稳定可控 → 但可能缺乏变化
```

| 数值区间 | 效果 | 适用场景 |
|---------|------|---------|
| 0.50–0.60 | 稳定执行，略有变化 | 分镜脚本、道具描述（必须稳定）|
| 0.60–0.70 | 平衡，略有创意 | 角色/场景资产描述 |
| 0.70–0.80 | 创意执行，仍受约束 | 导演讲戏本（需整合创意）|
| 0.80–0.90 | 高度创意 | 自由创作、对白生成 |
| 1.00 | 最大随机 | 不推荐（Toonflow 硬编码的陷阱）|

### 4.2 上下文字节预算参考

| Agent | 输入 Token 估算 | 输出 Token 估算 | 总 Token 估算 |
|--------|---------------|--------------|-------------|
| director | 剧本 2000-4000 + VB 1500 | 3000-6000 | 7000-12000 |
| art-designer | 讲戏本 3000 + VB 1500 | 4000-8000 | 9000-14000 |
| prop-designer | 讲戏本道具段 500-1500 | 1500-4000 | 2500-6000 |
| storyboard-artist | 讲戏本 3000 + 资产表 1000 | 3000-7000 | 7000-12000 |
| *-review | 内容 3000-8000 | 500-1500 | 4000-10000 |

> **max_tokens 设上限，不设下限**（模型自适应输出）

### 4.3 场景化温度调整

| 场景 | 基准温度 | 调整建议 |
|------|---------|---------|
| 古风/历史题材 | 各 Agent 基准 | 风格偏保守，top_p 可降至 0.90 |
| 奇幻/科幻题材 | 各 Agent 基准 +0.05 | 词汇创新需求高 |
| 喜剧/搞笑题材 | 各 Agent 基准 +0.05 | 对白需灵活 |
| 悬疑/惊悚题材 | 各 Agent 基准 -0.05 | 氛围词需精准 |
| 广告/产品植入 | 各 Agent 基准 | 产品信息需精确 |

---

## 五、项目级参数覆盖

> 格式：复制对应 agent 的 YAML，修改需要覆盖的字段
> 覆盖仅对本项目生效，不影响其他项目

### 示例：某项目特殊配置

```yaml
# === 项目覆盖层 ===
# 仅在 projects/本项目/ 目录下生效
# 覆盖规则：仅写被覆盖的字段，其余字段沿用 default

# 项目：漠玫传 S01E01（赛博墨韵，风格极端，无调参需求）
# director.override: 空（使用默认参数）

# 项目：某古风短剧（古风保守型，调整 top_p）
# director.override:
#   top_p: 0.90
# art-designer.override:
#   top_p: 0.90
```

### override 书写规范

```yaml
# ✅ 正确：只写被覆盖的字段
director.override:
  top_p: 0.90

# ❌ 错误：重复完整 YAML（容易遗漏更新）
# director.override:
#   temperature: 0.75  ← 与 default 重复
#   top_p: 0.90
#   max_tokens: 8192   ← 与 default 重复
```

---

## 六、qwen_pipeline.py 集成规范

> qwen_pipeline.py 必须读取本文件，动态注入参数

### 6.1 读取逻辑（pseudo-code）

```python
# qwen_pipeline.py 读取 prompts-registry.md 的逻辑：

def get_agent_params(agent_code: str, project_path: str = None) -> dict:
    # 1. 读取 default
    default = parse_yaml_block(f"config/prompts-registry.md", f"### {agent_code}.default")

    # 2. 若存在项目覆盖，读取 override
    if project_path:
        project_registry = f"{project_path}/config/prompts-registry.md"
        if exists(project_registry):
            override = parse_yaml_block(project_registry, f"### {agent_code}.override")
            return merge(default, override)  # override 覆盖 default
        else:
            return default
    else:
        return default
```

### 6.2 调用示例

```bash
# 旧写法（手动指定，已废弃）
python3 config/qwen_pipeline.py \
  --agent director \
  --temperature 0.75 \
  --max_tokens 8192 \
  --user "..."

# 新写法（自动注入，无需手动指定）
python3 config/qwen_pipeline.py \
  --agent director \
  --user "..."

# 项目级覆盖（自动探测项目路径）
cd projects/断桥奇遇/
python3 config/qwen_pipeline.py \
  --agent director \
  --user "..."
```

### 6.3 qwen_pipeline.py 改造检查清单

- [ ] 支持 `--agent` 自动从 `config/prompts-registry.md` 读取参数
- [ ] 自动探测 `projects/<name>/config/prompts-registry.md` 的 override
- [ ] `--temperature` / `--max_tokens` 作为手动覆盖 flag（优先级最高）
- [ ] 参数注入后打印实际使用的参数值（方便调试）

---

## 七、版本控制与升级

### 7.1 版本号规则

```
prompts-registry.md 版本号 = 语义化版本
主版本.次版本.修订号

- 主版本（Breaking）：Agent 参数大变（temperature 全部重调）
- 次版本（Feature）：新增 Agent / 新增参数
- 修订号（Patch）：措辞修改、注释修正
```

### 7.2 版本历史

| 版本 | 日期 | 变更内容 | 影响 Agent |
|------|------|---------|---------|
| v1.0 | 2026-04-05 | 初始建立，从 api-integration.md 参数表独立出来 | 全部 |

### 7.3 升级流程

当 `config/prompts-registry.md` 主版本升级时：

1. 将旧版本移入 `config/prompts-registry.history/vX.Y.Z.md`
2. 新版本写入 `config/prompts-registry.md`
3. 更新 `agents/` 下对应文件的 `temperature` 引用注释（如有）
4. 更新 `docs/execution-workflow.md` 参数说明（如有）

---

## 八、合规检查清单

> huage888 每次生成内容前，必须验证 registry 参数已正确加载

- [ ] qwen_pipeline.py 能读取 `config/prompts-registry.md`
- [ ] director / art-designer / prop-designer / storyboard-artist 均已注册
- [ ] 审核 Agent 均已注册（script-review / art-review / storyboard-review）
- [ ] 典型输出 Token 规模不超过 max_tokens
- [ ] 项目 override 格式规范（仅写被覆盖字段）
- [ ] qwen_pipeline.py 改造检查清单（Section 六）已全部完成
- [ ] 新增 Agent 时同步更新本文件

---

## 九、Doubao API 参数配置

> **新增（2026-04-07）**：doubao_pipeline.py 视频/图片生成参数

### 9.1 doubao_pipeline.py 参数

```bash
# 测试连接
python3 config/doubao_pipeline.py --test

# 视频生成
python3 config/doubao_pipeline.py --video \
  --prompt "..." \
  --duration 5 \
  --no-watermark \
  --output /tmp/v.mp4

# 图片生成
python3 config/doubao_pipeline.py --image \
  --prompt "..." \
  --output /tmp/img.png

# 首尾帧视频
python3 config/doubao_pipeline.py --video \
  --prompt "小女孩长大了..." \
  --img1 https://.../first.png \
  --img2 https://.../last.png \
  --output /tmp/trans.mp4
```

### 9.2 模型参数对照

| 任务 | 模型 | Model ID | 默认时长 | 水印 |
|------|------|---------|---------|------|
| 文生视频 | Seedance 2.0 | `doubao-seedance-2-0-260128` | 5s | `--wm false` |
| 图生视频 | Seedance 2.0 | `doubao-seedance-2-0-260128` | 5s | `--wm false` |
| 首尾帧视频 | Seedance 2.0 | `doubao-seedance-2-0-260128` | 5s | `--wm false` |
| 文生图片 | Seedream 5.0 | `doubao-seedream-5-0-260128` | — | `watermark=False` |

### 9.3 分镜脚本 → Doubao Prompt 转化

> 由 huage888 storyboard-artist 生成，交给 doubao_pipeline.py 执行

```
分镜脚本字段 → Doubao Prompt 规则：

镜头详解[画面描述]  →  直接作为 prompt 主体内容
运镜[运镜方式]     →  映射至 Doubao 运镜 Prompt 库（见 storyboard-skill.md Section 七）
光影[光源+色温+特效] →  追加至 prompt 末尾：光影：冷青色调，低强度，神秘氛围。
角色编号 C001       →  替换为漠玫/大圣等角色名
场景编号 S001       →  替换为赛博竹林等场景描述

完整 Doubao Prompt 格式：
[画面描述]，[运镜效果]，[光影描写]，[氛围] --wm false --dur [时长]
```
