# 漫舟 · 记忆

## 当前任务仪表盘
> 最后更新：2026-03-26

**当前项目**：AI漫剧生产 · 漫舟智能体系统建设
**当前阶段**：✅ P0-P5全部完成 → **✅ 漫舟拉片智能体v1.0完成**（CLI模式）

**漫舟拉片智能体v1.0（2026-03-26）：**
- ✅ `ai-drama-studio/manzhou_lapian/` — 新CLI包（10个Task全部完成）
- 架构：单次CLI，输出Obsidian Markdown（TapNow 14列格式）
- 输出：Obsidian单笔记 + `.assets/` 关键帧附件
- CDP集成：自动注入角色/场景ID（【【char_XX】】/【【loc_XX】】）
- 复用：`backend/pipeline/`（FFmpeg + PySceneDetect + AIAnalyzer）
- 端到端测试：34镜/134s视频 → 86关键帧 → 1440行笔记（370s）
- ⚠️ 已知问题：Zhipu GLM-4V模型未完全遵循JSON schema，建议使用Claude/Gemini

**启动命令**：
```bash
cd ai-drama-studio
./backend/venv/bin/python -m manzhou_lapian <视频路径> -o <输出目录> -c <CDP路径> -m gemini
```

**设计文档**：`docs/plans/2026-03-26-manzhou-lapian-design.md`
**实施计划**：`docs/plans/2026-03-26-manzhou-lapian-implementation.md`

---

## Phase2 实施进度

> 共14个任务，预计14次提交
**阻塞点**：无

| 任务 | 文件 | 状态 |
|------|------|------|
| Task 1 | manzhou-cdp-schema.md | ✅ 完成 |
| Task 2 | manzhou-character-consistency.md（aliases） | ✅ 完成 |
| Task 3 | manzhou-ip-parser.md（aliases+CDP） | ✅ 完成 |
| Task 4 | manzhou-concept.md | ✅ 完成 |
| Task 5 | manzhou-outline.md | ✅ 完成 |
| Task 6 | manzhou-script.md（@引用） | ✅ 完成 |
| Task 7 | manzhou-storyboard.md（固定时长+ID+多Shot） | ✅ 完成 |
| Task 8 | manzhou-item-generator.md | ✅ 完成 |
| Task 9 | manzhou-incremental.md | ✅ 完成 |
| Task 10 | manzhou-cdp-schema.md（补充道具系统） | ✅ 完成 |
| Task 11 | manzhou-cost-estimator.md | ✅ 完成 |
| Task 12 | manzhou-visual-style.md | ✅ 完成 |
| Task 13 | manzhou-bgm.md + manzhou-sfx.md | ✅ 完成 |
| Task 14 | manzhou-master.md（CDP引用）/ manzhou-audio.md / manzhou-safety.md | ✅ 完成 |

---

## 一键拉片Agent（v1.0 — CLI模式）

**状态**：✅ 开发完成，端到端测试通过（34镜/134s视频 → 370s完成）
**代码位置**：`ai-drama-studio/manzhou_lapian/`（Python CLI）
**重构说明**：取消前端Web界面，改为单次CLI，输出Obsidian Markdown笔记

### 技术栈
- Python 3.12 / FFmpeg / PySceneDetect / Jinja2
- AI：Gemini 2 Flash / Claude Sonnet 4 / Zhipu GLM-4V（三后端）
- 复用：`backend/pipeline/`（FFmpeg + PySceneDetect + AIAnalyzer）

### 包结构
```
manzhou_lapian/
├── __init__.py
├── __main__.py          # python -m manzhou_lapian 入口
├── cli.py               # argparse CLI
├── pipeline.py          # pipeline串联器
├── cdp.py              # CDP资产库读取器
├── prompts.py          # TapNow 14列 Prompt 模板
├── types.py             # 数据类型（ShotAnalysis/LapianConfig/LapianResult/CDPData）
└── exporters/
    └── obsidian.py      # Obsidian Markdown 笔记生成器
```

### CLI用法
```bash
./backend/venv/bin/python -m manzhou_lapian input.mp4 -c ../cdp.json -m gemini
```

### 输出格式（Obsidian笔记）
- **Frontmatter**：uid/title/created/video/video_duration/video_shots/analysis_model/scene_threshold/tags
- **分镜总览**：14列汇总表格
- **镜头详情**：景别+角度+运镜(含Yaw/Pitch)+色温K值+Audio Layer四分栏+imagePrompt+videoPrompt
- **关键帧**：`.assets/{video_id}/` 含Wikilink引用

### 端到端测试结果
- 视频：7.3MB / 134s / 34镜头 / 12fps
- 抽帧：86张关键帧
- 总耗时：370秒
- 输出：1440行Obsidian Markdown笔记
- ⚠️ 建议使用Claude/Gemini（Zhipu GLM-4V的JSON schema遵循度较差）

---

## 竞品研究成果（2026-03-25完成）

→ `memory/竞品研究成果可落地性分析.md` — **完整分析报告**

**核心结论速览**：
- **联易方舟** → 🔴 P0级，CDP JSON Schema + Prompt模板**可直接落地**
- **TapNow** → 🟡 P1级，5步分镜法 + 14列Schema **增强漫舟**
- **NanoPhoto** → 🟢 P2级，10+维度体系扩展设计视野
- **LibTV** → ❌ 零可落地（登录墙+Shadow DOM）
- **漫舟** → ✅ 全链路覆盖，竞品研究加速P0-P3迭代

**立即可用的成果**（下次迭代优先级）：
1. CDP JSON Schema → 漫舟标准资产包格式
2. 镜头时长固定秒数（从"范围"升级）
3. 角色/场景ID引用机制
4. 11种风格预设完整描述
5. 道具系统（漫舟目前缺失）
6. 增量追加机制（第02集多集支持）
7. **剧本创意/大纲模板**（新增！漫舟缺失的二级结构）
8. **@引用变量机制**（上下文追踪）
9. **润色/续写模板库**（去AI味）

---

## 索引

| 文件 | 内容 |
|------|------|
| `memory/manzhou-skills.md` | Skill 完整清单与版本记录 |
| `memory/竞品研究成果可落地性分析.md` | **竞品研究完整分析报告（2026-03-25）** |
| `memory/竞品Prompt模板评分表.md` | **Prompt模板评分总表（31+模板，TOP15排名）** |
| `memory/tapnow-research.md` | TapNow 逆向工程完整结论 |
| `memory/tools-workflow.md` | 工具链与工作流 |
| `docs/plans/2026-03-26-manzhou-lapian-implementation.md` | 漫舟拉片v1.0实施计划 |

---

## 第一性原理（全局指导）

1. **不假设我清楚想要什么** — 动机或目标不清晰时，停下来讨论
2. **路径不是最短的直接说** — 目标清晰但有更好办法时，建议更好的
3. **追根因不打补丁** — 遇到问题找本质，每个决策回答"为什么"
4. **说重点砍信息** — 输出砍掉不改变决策的内容

---

## 漫舟 Agent

- Skill: `.claude/projects/-Users-huage-Obsidian-Vault/skills/manzhou.md`
- 记忆系统: `comic/_memory/`
- 提示词合集: `comic/_prompts/`

---

## 关键文件路径

- 牛油果资源配置：`/Users/huage/Obsidian Vault/牛油果漫剧资源配置清单.md`
- 牛油果执行方案：`/Users/huage/Obsidian Vault/牛油果漫剧项目执行方案.md`
- LibTV研究主报告：`/Users/huage/Obsidian Vault/AI漫剧工具研究/LibTV-Canvas-深度研究报告.md`
- 联易方舟研究：`/Users/huage/Obsidian Vault/AI漫剧工具研究/联易方舟/`
