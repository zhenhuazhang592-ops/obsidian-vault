# S0: 解析小说

## 任务

输入用户提供的小说原文，提取创作所需的基础信息。

## 输入

用户粘贴的小说文本（xxx字），或 Obsidian 笔记路径。

## 输出文件

`S0-解析报告.md`

## 引用声明

> 本步骤为起始步骤，无上游引用。

## 输出内容

```yaml
时代背景:
  period: [具体年代，如1940年代中国农村]
  location: [地理区域]
  social_environment: [社会环境描述]
  material_culture: [物质文化特征]

故事基调:
  tone: [悲情/温暖/悬疑/热血等]
  emotional_arc: [情感走向描述]
  target_audience: [目标受众]

章节结构:
  - chapter: 第X章
    title: 章节名
    core_event: 核心事件（一句话）
    characters_involved: [主要角色列表]
    key_scenes: [关键场景列表]

主要角色（不超过10个）:
  - id: char_xxx
    name: 角色名
    one_line: 一句话描述
    first_appearance: 第X章

关键场景（不超过10个）:
  - id: scene_xxx
    name: 场景名
    one_line: 一句话描述
    era_consistency: [年代一致性说明]

故事主线:
  one_sentence: [一句话概括核心冲突]
  theme: [核心主题]
```

## 约束

- 时代背景必须从原文提取，不能推断
- 角色不超过10个，选取戏份最多的
- 场景不超过10个，选取有画面表现的
- 章节结构只列核心事件，不展开细节
