# 社交媒体与 UGC 风格提示词

## 核心特点

社交媒体内容强调：
- 病毒式传播
- 幽默有趣
- 视觉奇观
- 移动端优先

---

## 3.1 巨型橘猫 Meme 风格

**来源**: John (@johnAGI168)

**提示词结构**:
```
【Style】[风格], [视角], [质量], [特效]
【Duration】[时长]
【Scene】[场景]
[时间段] 镜头序号: [镜头类型].
[场景/动作描述]
Key detail: [关键细节]
[时间段] 镜头序号: [镜头类型].
[场景/动作描述]
[时间段] 镜头序号: [镜头类型].
[叙事感]: [描述]
```

**完整示例**:
```
【Style】Mockumentary, mobile Vlog perspective, hyperrealistic CG combined with real scenes, 8K quality, perfect fur physics simulation.
【Duration】15 seconds
【Scene】Hongya Cave in Chongqing or a busy overpass intersection (with magical 8D city feel).
[00:00-00:05] Shot 1: Visual spectacle (The Reveal).
The scene shows a bustling city street. The camera lifts up to reveal a **Gozilla-sized orange tabby cat** stuck between two skyscrapers.
Action: The giant cat is stuck because it's too fat, waving its huge paws with a pitiful expression, trying to pull itself out.
Detail: Cat fur is clearly visible in the sunlight, huge paw pads pressing against glass curtain walls, deforming the glass.

[00:05-00:10] Shot 2: Absurd interaction (The Interaction).
The camera switches to ground-level perspective. Traffic flows on the street, traffic lights flashing. The giant cat lowers its head, bringing its huge cat face close to the ground, curiously sniffing a bus waiting at a red light.
Action: The bus driver calmly reaches out and pets the giant cat's nose. The cat sneezes, instantly blowing away roadside leaves and pedestrians' hats (wind effect).

[00:10-00:15] Shot 3: Memetic ending (The Punchline).
The giant cat finally squeezes past the buildings and sits down on a cross-river bridge, causing the bridge deck to sink slightly (physical feedback).
Narrative sense: It lazily lies down and starts grooming itself, blocking the entire evening rush hour traffic. The camera finally freezes on its innocent big eyes.
```

---

## 4.1 超现实纪录片风格

**来源**: John (@johnAGI168)

**提示词结构**:
```
【Style】[类型], [质感], [光线], [语气]
【Duration】[时长]
【Main Character】[角色描述]
[时间段] 镜头序号: [状态].
[场景描述]
[动作描述]
Key detail: [关键细节 - 正常状态]
[时间段] 镜头序号: [BUG出现].
[动作描述]
High-impact moment (core climax): [核心冲突描述]
Director's note: [导演备注 - 效果要求]
[时间段] 镜头序号: [喜剧回调].
[动作描述]
Result: [结果]
```

**完整示例**:
```
【Style】Mockumentary (Vlog Style), hyperrealism, fixed-camera real-shot feel, natural lighting, with a slight suspenseful comedy tone.
【Duration】15 seconds
【Main Character】An ordinary young beautiful woman, in front of the bathroom sink at home.
[00:00-00:06] Shot 1: Daily setup (Normalcy).
Scene: In front of a regular bathroom mirror.
Action: The protagonist is brushing her teeth, mouth full of foam. She makes various funny faces (squinting, eyebrow-wiggling) at the mirror while brushing her teeth.
Key detail: At this point, the reflection in the mirror is completely normal, movements synchronized.

[00:06-00:11] Shot 2: BUG appears (The Glitch).
Action: After brushing teeth, the protagonist lowers her head to spit out foam, then turns around to leave the bathroom.
High-impact moment (core climax): Just as the protagonist's real body has turned and left the mirror frame, the "reflection" in the mirror **doesn't move**! That "reflection" still maintains the tooth-brushing pose, even mischievously raising eyebrows at the camera with a bad smile, staying for a full 2 seconds, before suddenly panicking and "fast-forwarding" to catch up with the original body's movements before disappearing.
Director's note: Must create an extremely realistic "network delay" feel, as if the reflection has independent consciousness.

[00:11-00:15] Shot 3: Comedic callback (The Punchline).
Action: The protagonist, who has already walked to the door, seems to sense something is wrong, suddenly turning back to look at the mirror.
Result: The mirror has now completely returned to normal, completely empty, only reflecting the opposite wall. The protagonist scratches her head in confusion, showing a life-questioning expression toward the camera. The frame freezes on the protagonist's confused face (comedy effect).
```

---

## UGC 风格提示词模板

### Meme/病毒内容

```markdown
【Style】[风格], [视角], [质量], [特效]
【Duration】[时长]
【Scene】[场景]

[00:00-00:05] Shot 1: [效果名称].
[主要描述]
[细节]

[00:05-00:10] Shot 2: [效果名称].
[主要描述]
[细节]

[00:10-00:15] Shot 3: [效果名称].
[叙事感]: [描述]
```

### 创意 Vlog

```markdown
【Style】[类型], [质感], [光线], [语气]
【Duration】[时长]
【Main Character】[角色描述]

[时间段] 镜头序号: [状态].
[场景描述]
[动作描述]
Key detail: [关键细节]

[时间段] 镜头序号: [转折].
[动作描述]
High-impact moment (core climax): [核心冲突]
Director's note: [效果要求]

[时间段] 镜头序号: [结果].
[动作描述]
Result: [结果]
```

---

## UGC 常用关键词

### 风格

| 关键词 | 说明 |
|-------|------|
| Mockumentary | 伪纪录片 |
| Vlog Style | Vlog风格 |
| Mobile Vlog | 手机Vlog |
| Hyperrealistic | 超真实 |
| Surrealism | 超现实主义 |

### 视角

| 关键词 | 说明 |
|-------|------|
| POV | 主观视角 |
| First-person | 第一人称 |
| Fixed-camera | 固定机位 |
| Handheld | 手持 |

### 质量

| 关键词 | 说明 |
|-------|------|
| 8K quality | 8K质量 |
| photorealistic | 照片级真实 |
| high fidelity | 高保真 |

### 特效

| 关键词 | 说明 |
|-------|------|
| CG combined | CG结合实拍 |
| physics simulation | 物理模拟 |
| wind effect | 风力效果 |
| motion blur | 动态模糊 |
