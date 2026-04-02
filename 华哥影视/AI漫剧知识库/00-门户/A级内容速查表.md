---
title: A级内容速查表
tags:
  - A级
  - 速查
  - 高频引用
---

# A级内容速查表

> [!tip] 这是什么
> 本表收录知识库中**评级为A（已验证可直接使用）**的内容，是日常制作时最频繁引用的精华。

---

## 一、高频使用的A级Skill（直接复制使用）

| 内容 | 文件 | 用途 |
|------|------|------|
| 主控Agent | [[manzhou-master]] | 接收小说输入，总调度全流程 |
| 导演版执行层 | [[manzhou-director-v2]] | LibTV一体化执行，Step 06-11核心 |
| 导演控制塔 | [[manzhou-director-control]] | Step 04，必执行，不可跳过 |
| 分镜脚本 | [[manzhou-shot-script]] | Step 06，集成Audio Layer |
| IP解析 | [[manzhou-ip-parser]] | Step 02，提取角色/场景/道具 |
| 剧本生成 | [[manzhou-script]] | Step 03，三维一体剧本 |
| 角色设计 | [[manzhou-character-design]] | Step 05，DNA三层锁 |
| 场景设计 | [[manzhou-scene-design]] | Step 05，场景基元 |
| TTS配音 | [[manzhou-tts-voice]] | Step 09，四维VO参数 |
| 视觉风格预设 | [[manzhou-visual-style]] | Step 05，5种风格包 |
| 风控审核 | [[manzhou-safety]] | Step 11，完整检查清单 |
| 爆款算法 | [[manzhou-hit-engine]] | SRL模型 + 3-15-30规则 |

---

## 二、Prompt模板（A级，直接复制）

### 2.1 剧本生成Prompt

```markdown
你是AI漫剧剧本专家。请将以下小说片段改编为AI视频生成专用的标准化剧本。

要求：
1. 删除旁白内心独白，转化为可见动作/对白
2. 每30秒一个小冲突，每60秒一个情绪转折
3. 保留原著核心人设和经典台词
4. 每场注明：场景/角色/对白/动作/情绪
```

来源：[[Step03-剧本生成]] · Skill：[[manzhou-script]]

### 2.2 分镜Prompt（七要素）

```markdown
## 镜头编号
- 时长：Xs
- 景别：特写/近景/中景/全景/远景
- 运镜：推/拉/摇/移/跟/固定
- 轴线：主轴方位（标注左/右）
- 情绪：情绪标签
- 节拍：SRL定位（Pressure/Release/Vacuum）
- image_prompt：[角色ID] + [场景ID] + [动作描述] + [风格标签]
- video_prompt：[image_prompt] + [运镜描述] + [时长] + [Audio Layer]
```

来源：[[Step06-分镜脚本]] · Skill：[[manzhou-shot-script]]

### 2.3 TTS配音标注格式

```markdown
voice:(平静/激动/悲伤/愤怒/温柔)[语速]"对白台词"
voice:(激动, 快速)"我不能接受这个结果！"
voice:(温柔, 缓慢)"你还好吗……"
```

来源：[[Step09-音频制作]] · Skill：[[manzhou-tts-voice]]

### 2.4 BGM情绪曲线标注

```markdown
[BGM: 情绪描述, 曲风, BPM, 起始时间点]
[BGM: 悬疑紧张, 电子氛围, 90, 00:00]
[BGM: 温柔抒情, 钢琴独奏, 60, 01:30]
```

来源：[[Step09-音频制作]] · Skill：[[manzhou-tts-voice]]

---

## 三、角色DNA三层锁（已验证）

### 第一层：外貌锁

```markdown
char_XX:
  面部: [脸型/眉形/眼形/鼻形/嘴形/肤色]
  体型: [身高/体型/仪态]
  年龄: [数字]岁
  特征: [标志性特征，如：左眉有疤/眼角痣]
```

### 第二层：风格锁

```markdown
char_XX_style:
  服装: [日常/职场/特殊场合]服装描述
  化妆: [妆容风格]
  道具: [随身物品]
  发型: [发型发色]
```

### 第三层：行为锁

```markdown
char_XX_behavior:
  表情习惯: [如：生气时皱眉/开心时眯眼]
  肢体语言: [如：紧张时摸耳朵/自信时双手叉腰]
  动态特征: [如：走路带风/说话时手势多]
```

来源：Skill [[manzhou-character-design]] · 案例：[[格子间女人-角色DNA]]

---

## 四、视频生成Prompt（已验证）

### Seedance 角色一致性Prompt模板

```markdown
[角色DNA外貌描述], [场景描述], [动作/表情], [情绪状态],
[年代背景], [画面风格], 高质量, 电影感, 8K, 详细,
(worst quality:1.4), (low quality:1.4), watermark, text, logo
```

### Kling 运镜Prompt模板

```markdown
[主体描述], [场景], [动作],
camera movement: [具体运镜描述],
[画面宽高比], 高质量电影感
```

来源：[[Seedance手册]] · [[Kling手册]]

---

## 五、风控检查清单（Step 11必用）

```markdown
## 风控检查清单

### 版权合规
- [ ] 原著/IP授权链完整
- [ ] 改编未超出授权范围
- [ ] 无第三方版权音乐/美术

### 内容合规
- [ ] 无违禁词（政治/色情/暴力/迷信）
- [ ] 无敏感话题擦边
- [ ] 平台规范符合（抖音/快手）

### 肖像权
- [ ] 角色设计不涉及真实公众人物
- [ ] AI生成内容无侵权风险

### 质量检查
- [ ] 音画同步
- [ ] 无明显穿帮/变形
- [ ] 时长符合平台要求
```

来源：Skill [[manzhou-safety]]

---

## 六、成本估算（快速参考）

| 环节 | 单集成本 | 说明 |
|------|---------|------|
| 视频生成（Seedance） | ¥20-50/镜 | 15镜 × ¥2-3 |
| 视频生成（Kling） | ¥30-80/镜 | 更高质量 |
| TTS配音 | ¥5-15/角色 | 按字数计 |
| BGM制作 | ¥10-30/首 | Suno生成 |
| 后期剪辑 | ¥50-100/集 | 剪映自动化 |

来源：Skill [[manzhou-cost-estimator]]

---

> [!warning] 使用前必读
> A级内容均为已验证内容，但在新项目中使用时：
> 1. 先确认风格预设是否匹配（[[Step05-资产库构建]]）
> 2. 角色DNA必须重新定义（不可跨项目复用角色）
> 3. 视频生成参数需根据具体模型版本微调
