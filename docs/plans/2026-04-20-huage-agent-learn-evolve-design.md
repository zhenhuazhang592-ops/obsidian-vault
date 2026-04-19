# huage-agent 本能学习与进化系统 · 设计文档

> **状态**：CEO Review 通过（1 CRITICAL 修正 + 2 问题修正）
> **日期**：2026-04-20
> **版本**：v1.0.0

---

## 一、背景与目标

**问题**：huage-agent 设计文档（2026-04-18）中明确要求「本能学习进化」能力，但 Task 0-11 实现中完全漏掉。

**目标**：在 huage-agent CLI 中实现 `/learn`（从创作会话提取模式）和 `/evolve`（本能进化检查），集成到 `huage-agent write` 交互模式的 Stage 5 之后。

**范围**：文章创作全链路的所有有效模式 — 选题、定位、核心观点、大纲结构、钩子公式、去AI味写法、配图风格。

---

## 二、架构概览

```
huage-agent write [topic] -i（交互模式）
    ↓
Phase 0 → Stage 1 → 2 → 3 → 4 → 5
                                ↓
                           /learn 自动触发
                          （分析 session-meta.json）
                                ↓
                        自动化提取 → 用户确认 → 双写
                          ↓                    ↓
              huage-agent/.instincts/   .claude/instincts/projects/huage-agent/
              （项目层，TypeScript）     （Vault 全局，Markdown YAML）
                                ↓
                          /evolve 自动检查
                          （轻量进化判断）
                                ↓
                    confidence ≥ 0.9 → 触发 Vault Python 层写 Skill
```

**关键设计决策**：
- huage-agent 与 Vault 本能库分层存储：项目层自足、V Vault 全局共享
- `/learn` 集成在 write 交互模式内，无需单独命令
- `/evolve` 在每次 `/learn` 后自动触发，无需单独命令
- Skill 进化委派给 Vault Python 层，不在 TypeScript 内重复实现

---

## 三、核心模块

| 模块 | 文件 | 职责 |
|------|------|------|
| Session Meta 构建 | `src/learn/session-meta.ts`（新增） | 读取 outputDir 下所有 stage JSON，构建 session-meta.json |
| 模式提取器 | `src/learn/extractor.ts`（新增） | 分析 session-meta.json，提取创作模式 |
| Vault 桥接 | `src/learn/vault-bridge.ts`（新增） | 双写 Vault 全局本能 + 触发 Python Skill 层 |
| 本地进化 | `src/learn/evolve.ts`（新增） | 聚类检查、高 confidence 标记 |
| 引擎集成 | `src/index.ts`（修改） | FiveStageOrchestrator 完成后自动触发 learn 模块 |
| 输出元数据 | `output/YYYY-MM-DD-topic/session-meta.json` | 会话记录文件 |
| 项目本能库 | `huage-agent/.instincts/`（新增目录） | TypeScript 管理的项目层本能 |
| Vault 本能库 | `.claude/instincts/projects/huage-agent/`（新增） | Vault 全局本能存储 |

---

## 四、session-meta.json 格式

> **数据来源**：`session-meta.ts` 读取 `outputDir/` 下各 stage 的 confirmed JSON 文件（`stage1-confirmed.json`、`stage3-confirmed.json`、`stage5-confirmed.json` 等）构建，不依赖 orchestrator 函数返回值。

```json
{
  "topic": "...",
  "date": "2026-04-20",
  "outputDir": "...",
  "stages": {
    "topic": { "selected": "...", "alternatives": [...], "reason": "..." },
    "thesis": { "points": [{ "text": "...", "type": "insight|story|data" }] },
    "outline": {
      "type": "问题-方案式 | 故事线 | 对比式 | ...",
      "hooks": ["标题写法A", "开头写法B"],
      "sections": [{ "heading": "...", "function": "建立共鸣|提出方案|..." }]
    },
    "writing": { "wordCount": 3200, "sections": [...] },
    "polish": {
      "changes": [
        { "from": "空洞词X", "to": "具体Y", "reason": "去除AI腔" }
      ],
      "antiAiScore": 78
    }
  },
  "seoKeywords": ["关键词A", "关键词B"],
  "geoScore": 82,
  "wikiInjected": ["entity-X", "concept-Y"],
  "images": [{ "section": "...", "promptStyle": "...", "effective": true }]
}
```

---

## 五、模式提取逻辑

### 5.1 自动提取（extractor.ts）

从 session-meta.json 中提取以下模式：

| 模式类型 | 提取来源 | 字段 |
|------|--------|------|
| 选题模式 | topic.selected + alternatives | domain/topic-type |
| 定位模式 | 受众 + 差异化设定 | audience/angle |
| 观点类型 | thesis.points[].type | insight/story/data distribution |
| 大纲结构 | outline.type + sections[].function | structure-template |
| 钩子公式 | outline.hooks[] | hook-pattern |
| 去AI味写法 | polish.changes[].from/to | anti-ai-pattern |
| 配图风格 | images[].promptStyle | image-style |

### 5.2 本能文件格式

```yaml
---
id: huage-agent-钩子公式-20260420
trigger: "当写作公众号开头，需要在第一段建立读者共鸣时"
confidence: 0.6
domain: 文章开头
source: session-20260420
scope: huage-agent
---

# 公众号开头钩子：问题前置 + 情绪共鸣

## 行为
用具体问题开场（不是概念），问题要指向读者痛点，第一段不超过3句话就出现核心词。

## 证据
- 会话：2026-04-20
- 具体案例：[从 session-meta 引用]
- 用户确认：有

## 适用边界
- 适用于：观点型、问题解决型文章
- 不适用于：故事叙述型、个人感悟型
```

---

## 六、进化逻辑（evolve.ts）

### 6.1 进化条件

| 条件 | 动作 |
|------|------|
| 单一本能，confidence ≥ 0.9 | 标记为"可升级"，触发 vault-bridge |
| 同一 domain 多个本能，≥ 2 个，≥ 0.7 | 聚类建议，触发 vault-bridge |
| confidence < 0.7 | 仅更新 registry，不触发 Skill 层 |

### 6.2 进化流程

```
evolve.ts 检查项目本能
        ↓
confidence ≥ 0.9 OR 聚类达标
        ↓
vault-bridge.ts 通过 child_process.spawn 调用 Python
（python3 -c "import sys; sys.path.insert(0, '~/.claude/modules'); from instinct_evolver import InstinctEvolver; ..."）
        ↓
InstinctEvolver.evolve_to_skill() 生成 ~/.claude/skills/<name>/SKILL.md
```

---

## 七、与 Vault 本能库的接口

### 7.1 双写策略

每次 `/learn` 确认后，同时写入两个位置：

```
项目层：huage-agent/.instincts/YYYY-MM-DD-*.yaml
         ↕ 内容一致
Vault层：.claude/instincts/projects/huage-agent/YYYY-MM-DD-*.yaml
```

项目层由 TypeScript 直接管理，Vault 层通过 vault-bridge 同步。

### 7.2 vault-bridge.ts 接口

```typescript
// 写 Vault 全局本能
async writeVaultInstinct(instinct: Instinct): Promise<void>

// 触发 Python Skill 层
async triggerSkillEvolution(instincts: Instinct[]): Promise<void>

// 读取 Vault 本能（用于聚类检查）
async readVaultInstincts(): Promise<Instinct[]>
```

---

## 八、Engine 集成

修改 `src/index.ts`，在 `orchestrator.runInteractive()` 返回后（FiveStageOrchestrator 是 async void，调用后即 Stage 5 已完成）插入：

```typescript
// index.ts — orchestrator.runInteractive() 之后
// session-meta.ts 读取 outputDir 下所有 stage JSON，构建 session-meta.json
const sessionMeta = await SessionMetaBuilder.fromOutputDir(outputDir);
await sessionMeta.save(); // 写入 outputDir/session-meta.json

// extractor.ts 读取 session-meta.json，提取创作模式
const extractor = new PatternExtractor(sessionMeta);
const patterns = await extractor.extract();
extractor.printSummary(patterns); // 打印自动提取结果

// 用户确认/补充
const confirmed = await extractor.confirmWithUser(patterns);

// 双写
await extractor.saveToProject(confirmed); // → huage-agent/.instincts/
const vaultBridge = new VaultBridge();
await vaultBridge.writeVaultInstinct(confirmed); // → Vault ~/.claude/instincts/projects/huage-agent/

// 自动进化检查（每次 learn 后自动触发）
const evolve = new LocalEvolve();
const suggestions = await evolve.check(confirmed);
if (suggestions.length > 0) {
  await vaultBridge.triggerSkillEvolution(suggestions);
}
```

---

## 九、测试策略

| 测试 | 内容 |
|------|------|
| extractor.test.ts | 从 session-meta.json 提取各类模式 |
| evolve.test.ts | confidence 阈值判断、聚类逻辑 |
| vault-bridge.test.ts | 双写一致性、Python 脚本调用 |
| integration.test.ts | 完整 write → learn → evolve 流程 |

---

## 十、不包含范围

- Vault Python 层（`claude-mem/`）的 Skill 管理逻辑本身，不修改
- 非文章创作领域的本能（如短剧、代码）
- `/learn` 的独立 CLI 命令，全程集成在 write 交互模式内

---

## 十一、依赖

- Vault Python 层：已存在于 `~/.claude/modules/instinct_evolver.py`（`InstinctEvolver` 类）和 `~/.claude/modules/skill_manager.py`（`SkillManager` 类），vault-bridge.ts 通过 `spawn('python3', ['-c', inlineCode])` 直接调用，无需新建任何 Python 文件
- Node.js：`child_process.spawn` 用于调用 Python
- registry.json：本能文件通过 `InstinctEvolver.load_instincts()` 的 rglob 自动发现，无需手动维护 registry
- 无需新增 npm 依赖
