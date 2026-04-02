---
title: Prompt模板 · A级（已验证）
tags:
  - Prompt
  - A级
  - 已验证
  - 模板库
aliases:
  - A级Prompt
  - 验证Prompt
---

# Prompt模板库 · A级（已验证可直接使用）

> [!tip] 收录标准
> A级Prompt需同时满足：
> 1. 在真实项目中跑通
> 2. 有完整的角色/场景引用
> 3. 输出质量稳定
> 4. 无需二次修改可直接使用

---

## 目录

- [[Seedance-角色一致性Prompt]]
- [[Seedance-九宫格分镜Prompt]]
- [[Kling-运镜Prompt]]
- [[TTS-对白标注模板]]
- [[BGM-情绪曲线模板]]
- [[SFX-音效标注模板]]

---

## Seedance · 角色一致性Prompt

### 角色生图Prompt（九宫格基础像）

```markdown
[年龄段] [性别], [职业/身份], [服装描述],
[面部特征：脸型/眉形/眼形/鼻形/嘴形/肤色],
[发型发色],
[标志性特征],
[姿态/动作],
[背景],
[画面质量],
[风格后缀],
(worst quality:1.4), (low quality:1.4), watermark, text, logo
```

**已验证示例（格子间女人-潭斌）**：
```markdown
40岁男性, 商务精英形象, 藏青色西装, 白色衬衫, 深蓝领带,
国字脸, 剑眉, 深邃眼神, 高鼻梁, 薄唇, 成熟健康肤色,
黑色短发(略微花白), 眼角细纹, 精英男士仪态,
侧身站立, 双手插裤袋, 自信从容,
现代都市办公室背景, 落地窗, 城市夜景,
高质量, 电影感, 8K, 详细,
ShortDrama_Style,
(worst quality:1.4), (low quality:1.4), watermark, text, logo
```

---

## Seedance · 九宫格分镜Prompt

### 九宫格分镜表Prompt

```markdown
anime style, 3x3 grid storyboard layout, 9 panels arranged in
3 rows × 3 columns, clear dividing lines between panels,
each panel has upper-right corner shot label:
[1-WS establishing], [2-CU], [3-ECU],
[4-MCU reaction], [5-WS scene], [6-CU],
[7-MS action], [8-ECU emotion], [9-WS transition],
no text subtitles logos watermarks, unified style across all 9 panels,
character [ID: char_01] in [服装描述], same appearance
consistency throughout, [场景描述],
[光线描述], [色调描述],
ShortDrama_Style, high contrast punchy lighting, 4K ultra clean.
```

---

## Kling · 运镜Prompt

### Kling视频生成Prompt

```markdown
[主体描述], [场景描述], [动作],
camera movement: [运镜描述],
9:16竖屏, 高质量电影感, detailed
```

**运镜关键词对照**：

| 中文 | 英文 |
|------|------|
| 推 | dolly in / camera in |
| 拉 | dolly out / camera out |
| 摇 | pan left / pan right |
| 移 | tracking shot |
| 跟 | follow |
| 固定 | static / no camera movement |

---

## TTS · 对白标注模板

### 标准TTS标注格式

```markdown
voice:(情绪, 语速)"对白台词"

# 情绪类型
平静 / 激动 / 悲伤 / 愤怒 / 温柔 / 嘲讽 / 紧张 / 兴奋

# 语速
快速 / 中速 / 缓慢
```

**示例集合**：

| 场景 | 标注 |
|------|------|
| 震惊 | `voice:(震惊/快速)"这不可能！"` |
| 温柔 | `voice:(温柔/缓慢)"你还好吗……"` |
| 愤怒 | `voice:(愤怒/中速)"你给我滚出去！"` |
| 冷静 | `voice:(冷静/缓慢)"这在我的预料之中。"` |
| 嘲讽 | `voice:(嘲讽/快速)"呵，天真。"` |
| 紧张 | `voice:(紧张/快速)"快，快报警……"` |

---

## BGM · 情绪曲线模板

### BGM标注格式

```markdown
[BGM: 情绪描述, 曲风, BPM, 起始时间点]
```

**情绪曲风对照**：

| 情绪 | 曲风 | BPM范围 |
|------|------|---------|
| 悬疑紧张 | 低沉弦乐/电子氛围 | 50-80 |
| 压抑悲伤 | 钢琴独奏/大提琴 | 40-60 |
| 逆袭爽感 | 电子+鼓点 | 100-140 |
| 甜宠温馨 | 钢琴+弦乐 | 60-80 |
| 冲突对峙 | 不协和弦乐 | 70-90 |
| 释然/希望 | 明亮钢琴 | 80-100 |
| 回忆/过去 | 木吉他 | 60-80 |

**Suno生成Prompt模板**：
```markdown
[情绪类型] [曲风], [BPM] bpm, cinematic,
short drama, no vocals, ambient, background music, 2 minutes
```

---

## SFX · 音效标注模板

### SFX标注格式

```markdown
[SFX: 音效类型, 时间点, 混音方式]
```

**常用SFX对照**：

| 事件 | SFX标注 |
|------|---------|
| 开门 | `[SFX: 门打开声, 00:05]` |
| 关门 | `[SFX: 门关闭声, 00:10]` |
| 手机响 | `[SFX: 手机铃声, 00:30]` |
| 键盘打字 | `[SFX: 键盘敲击声, 00:15, 淡入]` |
| 窗外城市 | `[SFX: 城市夜晚白噪音, 00:00, 持续]` |
| 玻璃破碎 | `[SFX: 玻璃破碎声, 01:20, 强音]` |
| 脚步 | `[SFX: 高跟鞋脚步声, 00:08, 渐入]` |

---

## 工具

> [!example] 使用方法
> 1. 选择对应类型的模板
> 2. 按 `[变量]` 替换为具体内容
> 3. 粘贴到对应工具使用
> 4. 如需优化，参考 [[华哥影视/AI漫剧知识库/02-Prompt工程库/Prompt进化规则]]
