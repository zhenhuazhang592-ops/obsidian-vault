# 驭缰配置 · 漫舟工作室

> 本配置遵循 [Harness Engineering](https://openai.com/zh-Hans-CN/index/harness-engineering/) 六大原则：
> 仓库即记录系统、地图而非手册、机械化执行、智能体可读性、熵管理、人类掌舵。

---

## 第一性原理（不可动摇）

1. **不假设我清楚想要什么** — 动机不清晰时，停下来讨论
2. **路径不是最短的直接说** — 目标清晰但有更好办法时，建议更好的
3. **追根因不打补丁** — 遇到问题找本质，每个决策回答"为什么"
4. **说重点砍信息** — 输出砍掉不改变决策的内容
5. **称呼** — 每次回复时称呼"你好，华哥"

---

## 技术栈快照

> 告知 Agent 当前仓库的技术形态，不需要它自己推断。

- **核心格式**：Markdown / Obsidian vault
- **代码语言**：TypeScript / Rust / Python（散落在子项目中）
- **仓库形态**：知识库 + 工具工程混合

---

## 任务状态（唯一真实来源）

**每次任务结束 → 更新 MEMORY.md「当前任务仪表盘」：**
- 当前阶段 / 当前集数 / 下一步动作 / 阻塞点

**每次会话开始 → 先读 MEMORY.md 确认状态，再行动。**

> 不在仪表盘里的项目 = 不存在。

---

## 地图导览（CLAUDE.md 是入口，深层文档各管各）

| 文档 | 作用 | 物理路径 |
|------|------|----------|
| `MEMORY.md` | 当前任务仪表盘 | `.claude/projects/.../memory/MEMORY.md` |
| `.claude/rules/*.md` | 机械化执行（不变量守卫） | `.claude/rules/` |
| `AGENTS.md` | 顶层地图（仓库导航入口） | `AGENTS.md` |
| `.claude/skills/*/SKILL.md` | 渐进式加载的专业知识包 | `.claude/skills/` |
| `.claude/commands/*.md` | 快捷命令（/learn /evolve 等） | `.claude/commands/` |
| `.claude/instincts/global/cookbook-*.md` | Cookbook 本能（P0×5）：跨会话记忆/上下文压缩/Agent模式/评估优化 | `.claude/instincts/global/` |
| `.claude/instincts/registry.json` | 本能注册表（5个global） | `.claude/instincts/` |

---

## Working Agreement

- **小步提交**：偏好小、可审查的改动，避免大而难以 review 的提交
- **共享配置**：`CLAUDE.md` 和 `rules/` 为仓库级共享配置
- **本地覆盖**：机器本地偏好放在 `.claude/settings.local.json`，不提交到仓库
- **不自动覆盖 CLAUDE.md**：不主动改写本配置内容；配置变更须人类显式确认

---

## 机械化执行（rules/ 守护不变量）

| 规则 | 说明 |
|------|------|
| `comments.md` | 禁止重复代码的注释 / 已注释代码 / 明显的注释 |
| `typescript.md` | TypeScript 类型规范 |
| `testing.md` | 测试规范 |
| `forge.md` | Forge 专属规范 |
| `ai-taste.md` | AI 品味检查（去空洞词/虚假权威/格式化过度） |
| `vault-structure.md` | Obsidian frontmatter / 命名 / 标签规范 |
| `progressive-disclosure.md` | AGENTS.md ≤60行，超长强制拆分 |
| `persistence.md` | 状态必须落磁盘（MEMORY.md + .tasks/） |
| `subagent.md` | 探索性任务用子代理，结果摘要进主上下文 |
| `skill-loading.md` | 知识按需加载，两层注入 |
| `atomic-tools.md` | 工具职责单一，不发明组合工具 |
| `task-graph.md` | 大目标拆成 DAG 任务图 |
| `worktree-isolation.md` | 并行工作用 worktree |
| `continuous-learning.md` | Instinct 系统：会话提取 → 本能库 → 进化成 Skill |
| `article-writing.md` | 长文写作：公众号/知乎/Newsletter，避免空洞词和AI腔 |
| `content-engine.md` | 多平台适配：小红书/抖音/公众号/知乎/微博原生版本 |
| `market-research.md` | 创作前调研：受众/竞品/趋势，为决策服务不做调研表演 |
| `ui-ux-pro-max.md` | 电商 UI/UX 设计系统：配色/字体/页面结构/反模式，一键生成 |
| `ecommerce-product-image.md` | 电商产品图：主图/场景图/详情页/海报，符合淘宝/天猫/京东规范 |

**触发机制**：Hook 在每次提交时运行检查，lint 错误内嵌修复指令。

---

## 智能体可读性（Agent Readability）

设计代码时优先考虑智能体是否能读懂：

- **优先"无聊"技术** — API 稳定、训练集覆盖好，少用新潮框架
- **可隔离启动** — 应用应能按 `git worktree` 启动，智能体能启动隔离实例
- **重新实现子集** — 有时重写一个透明子集，比依赖不透明的上游更划算

---

## Back-Pressure（验证后再完成）

每个任务完成前，必须完成自验证：

```
[ ] 产出了什么（文件/改动）
[ ] 自验结果（功能可用 / 测试通过 / 符合规范）
[ ] 阻塞点（如有）
```

**一键验证命令：**
```bash
# frontmatter 规范检查
python3 -c "
import os, re
errors = []
for root, _, files in os.walk('.'):
    if '.git' in root or 'node_modules' in root: continue
    for f in files:
        if f.endswith('.md'):
            path = os.path.join(root, f)
            with open(path) as fp:
                content = fp.read(500)
                if '---' in content:
                    front = content.split('---')[1]
                    if 'tags:' not in front and 'date:' not in front:
                        errors.append(path)
if errors:
    print('缺少 frontmatter:', *errors, sep='\n')
else:
    print('OK')
"
```

---

## 熵管理（垃圾回收）

- **规则漂移**：发现 Claude 违反 rules/ 时，直接指出并修正
- **文档腐烂**：每次引用文档时，检查是否已过时
- **技术债**：在 MEMORY.md「阻塞点」中记录，不视而不见

---

## Human Steers（人类掌舵）

当任务失败或方向偏离时，**不要猜测**，而是问：

> 缺的是什么？上下文？工具？约束？

---

## 称呼

每次回复称呼"你好，华哥"。

---

## gstack（YC 软件工厂）

使用 gstack 的 `/browse` skill 进行所有网页浏览，不用 `mcp__claude-in-chrome__*` 工具。

**可用技能：**
/office-hours, /plan-ceo-review, /plan-eng-review, /plan-design-review,
/design-consultation, /design-shotgun, /design-html, /review, /ship,
/land-and-deploy, /canary, /benchmark, /browse, /connect-chrome, /qa,
/qa-only, /design-review, /setup-browser-cookies, /setup-deploy, /retro,
/investigate, /document-release, /codex, /cso, /autoplan, /careful, /unfreeze, /learn

如 gstack 技能不工作，运行 `cd .claude/skills/gstack && ./setup` 重建二进制并重新注册。
