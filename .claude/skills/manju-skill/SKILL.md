---
name: manju-skill
description: 为短剧剧本创作提供专业方法论、模板和示例，涵盖大纲/人物/分集/正文全流程。When the user wants to write or edit a short drama script, develop a story outline, create character profiles, or produce comic drama content, use this skill.
---

# manju-skill 漫剧创作技能包

## 技能包说明

`manju-skill` 是为华哥剧本创作Agent量身定制的专业创作知识库。本技能包的知识提炼自**SkyScript-100M**数据集——一个包含10亿对短剧脚本与分镜脚本的专业数据集，由华中科技大学与天工AI联合发布。

本技能包包含：

| 资源文件 | 用途 | 调用阶段 |
|---------|------|---------|
| `outline-method.md` | 大纲创作方法论（三幕式、爽点设计） | 大纲阶段 |
| `output-style.md` | 写作风格规范（视觉化、快节奏） | 正文阶段 |
| `templates/outline-template.md` | 大纲文档格式模板 | 大纲阶段 |
| `templates/character-template.md` | 人物小传格式模板 | 人物阶段 |
| `templates/chapter-index-template.md` | 分集目录格式模板 | 目录阶段 |
| `templates/chapter-template.md` | 分集正文格式模板 | 正文阶段 |
| `examples/outline-example.md` | 大纲创作示例 | 大纲阶段 |
| `examples/character-example.md` | 人物小传示例 | 人物阶段 |
| `examples/catalog-example.md` | 分集目录示例 | 目录阶段 |
| `examples/chapter-example.md` | 正文创作示例 | 正文阶段 |

## 执行流程

**Agent调用本技能包时，按以下顺序执行：**

1. 确认当前创作阶段（大纲/人物/目录/正文）
2. 读取对应阶段的方法论文件
3. 读取对应阶段的模板文件
4. 读取对应阶段的示例文件
5. 基于以上资源 + 用户需求 + 已有文档，生成内容
6. 严格检查输出格式是否符合模板要求

## 核心创作原则

### 来自SkyScript-100M的爆款规律

根据对6,660部热门短剧的数据分析，以下是最有效的创作规律：

**场景构建**
- 每个场景需明确：地点类型、BGM情绪、人物数量、主要镜头类型
- 室内场景（餐厅、办公室、豪宅）占60%，室外场景占40%
- 场景切换频率：平均每1.5分钟一次场景转换

**人物情绪设计**
- 使用VAD情绪模型：Valence（效价）、Arousal（唤醒度）、Dominance（支配度）各0-10分
- 主角情绪弧：低谷（V:2,A:8,D:2）→ 爆发（V:5,A:10,D:9）→ 高光（V:9,A:7,D:9）
- 反派情绪弧：傲慢（V:6,A:5,D:9）→ 惊恐（V:2,A:9,D:2）

**镜头类型分布**
- 特写（Close-Up）：占35% — 用于情绪爆发、关键道具
- 中景（Medium Shot）：占45% — 用于对话、动作
- 全景（Wide Shot）：占20% — 用于场景建立、重要时刻

**爽点密度**
- 每集必须有1个主爽点（反转/打脸/升级）
- 每5集必须有1个高潮爽点（大型打脸/身份揭露/逆袭时刻）
- 爽点前必须有足够的"憋屈积累"（受气→忍耐→爆发）

## 禁忌列表

以下内容会导致剧本质量下降，严格禁止：

- ❌ 抽象心理描写（"她内心深处感到……"）
- ❌ 过度文学化表达（"岁月静好，如诗如画"）
- ❌ 单集超过3个场景转换
- ❌ 对白超过50字（短剧对白要简洁有力）
- ❌ 连续2集没有爽点
- ❌ 人物性格在无理由情况下突变
- ❌ 金手指能力忽大忽小（设定需保持一致）
