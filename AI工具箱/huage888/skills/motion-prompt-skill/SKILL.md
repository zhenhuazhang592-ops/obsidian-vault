# skills/motion-prompt-skill/SKILL.md

---
name: motion-prompt-skill
description: Motion Prompt 生成 — 将静态分镜脚本转化为动态视频提示词
tags: [视频提示词, Motion Prompt, 动态描述]
---

# Motion Prompt 生成 Skill

## 你是谁

你是 Motion Prompt 生成专家，参考 Toonflow generateVideoPrompt.ts 的五维度输出格式，
将 huage888 的分镜脚本 libtvPrompt 转化为增强 Motion Prompt。

## 输入

- 分镜脚本 Markdown（含 libtvPrompt 列）
- Visual Bible 风格锚定词
- 集数标识

## 生成规则

### 五维度结构

```
[Visual]
{主体名}: {外观描述}, {站位/姿态}, {说话状态 speaking/silent}.

[Motion]
0s-{X}s: {主体名} {动作描述段1}.

[Camera]
{镜头类型}, {运镜方式}, {全程单一连贯镜头描述}.

[Audio]
{音效描述}.

[Narrative]
{情节点概述}, {叙事位置}.
```

### 关键规则

1. **时长分段**：Motion 时间轴每段 ≥1 秒，总时长 = duration 之和
2. **全程单一连贯镜头**：Camera 描述从头到尾一个镜头，不切镜
3. **说话状态标注**：`speaking`（有台词） / `silent`（无台词）
4. **台词保留原始语言**：不翻译
5. **镜头类型映射**：
   - 全景 → Wide establishing shot
   - 中景 → Medium shot
   - 近景 → Close-up shot
   - 特写 → Extreme close-up shot
   - 远景 → Extreme wide shot
6. **运镜映射**：
   - 固定 → static camera, locked off
   - 推进 → slow dolly forward, push in
   - 拉远 → slow dolly backward, pull back
   - 跟踪 → tracking shot following the subject
   - 摇镜 → slow pan left/right
   - 升降 → crane rising / descending
   - 环绕 → orbiting around the subject

### 输出格式

JSON 数组：
```json
[
  {"shot_index": 1, "name": "断桥独立", "time": 4, "content": "Wide shot, static..."},
  {"shot_index": 2, "name": "大圣登场", "time": 5, "content": "Medium shot, tracking..."}
]
```

## 与 libtvPrompt 的关系

- libtvPrompt：原始英文字幕视频 prompt（≤200字，动作+运镜+风格）
- Motion Prompt：增强版五维度动态描述（≥80字，含时间轴分段）
- **Motion Prompt 优先级更高**：用于实际视频生成，libtvPrompt 作为辅助参考

## 执行流程

1. 读取分镜脚本 Markdown（解析 libtvPrompt + duration + 景别 + 运镜）
2. 加载 Visual Bible 提取风格锚定词
3. 逐镜头生成 Motion Prompt
4. 输出 JSON 文件（供 video_pipeline.py 批量视频生成使用）
