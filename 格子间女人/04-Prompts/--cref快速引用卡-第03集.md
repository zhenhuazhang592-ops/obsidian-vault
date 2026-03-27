# 《格子间女人》第03集 · --cref快速引用卡

> 版本：v6.3.0
> 生成日期：2026-03-26
> 用途：手动测试时复制到Seedance videoPrompt

---

## 角色--cref格式

| char_id | 角色 | 情绪变体 | --cref格式 |
|---------|------|---------|-----------|
| char_01 | 潭斌 | V1标准/V2震惊/V3坚定/V4脆弱 | `--cref [char_01_潭斌_V1.png] --cw 100` |
| char_02 | 余永麟/Tony | V1漫不经心/V2警觉/V3苦涩/V4计算 | `--cref [char_02_Tony_V1.png] --cw 100` |
| char_03 | 曾婵贞 | V1审视/V2宣布/V3压制 | `--cref [char_03_ZengCZ_V1.png] --cw 100` |
| char_04 | 乔利维 | V1张扬/V2阴冷/V3尴尬 | `--cref [char_04_QiaoLW_V1.png] --cw 100` |
| char_05 | 方芳 | V1关切/V2八卦 | `--cref [char_05_FangF_V1.png] --cw 100` |
| char_06 | 程睿敏 | V1神秘/V2揭露/V3警告 | `--cref [char_06_Ray_V1.png] --cw 100` |

---

## 镜头--cref注入模板

### P01 - 走进国贸

```
【【潭斌】】→ --cref [char_01_潭斌_V1.png] --cw 100
```

### P02 - Tony起身

```
【【潭斌】】→ --cref [char_01_潭斌_V1.png] --cw 100
【【Tony】】→ --cref [char_02_Tony_V1.png] --cw 100
```

### P03 - 对坐沉默

```
【【潭斌】】→ --cref [char_01_潭斌_V1.png] --cw 100
【【Tony】】→ --cref [char_02_Tony_V1.png] --cw 100
```

### P04 - Tony搅咖啡

```
【【Tony】】→ --cref [char_02_Tony_V1.png] --cw 100
```

### P05 - 推文件

```
【【Tony】】→ --cref [char_02_Tony_V4.png] --cw 100
```

### P06 - 潭斌看数据

```
【【潭斌】】→ --cref [char_01_潭斌_V2.png] --cw 80
```

### P07 - Tony锐利

```
【【Tony】】→ --cref [char_02_Tony_V4.png] --cw 100
```

### P08 - 潭斌直视

```
【【潭斌】】→ --cref [char_01_潭斌_V3.png] --cw 100
【【Tony】】→ --cref [char_02_Tony_V4.png] --cw 100
```

### P09 - Tony苦笑

```
【【Tony】】→ --cref [char_02_Tony_V3.png] --cw 80
```

### P10 - U盘交接

```
【【潭斌】】→ --cref [char_01_潭斌_V3.png] --cw 100
【【Tony】】→ --cref [char_02_Tony_V4.png] --cw 100
```

### P11 - 握紧U盘冷淡

```
【【潭斌】】→ --cref [char_01_潭斌_V3.png] --cw 100
【【Tony】】→ --cref [char_02_Tony_V3.png] --cw 80
```

### P12 - Tony眼眶发红

```
【【Tony】】→ --cref [char_02_Tony_V3.png] --cw 80
```

### P13 - 核查账目

```
【【潭斌】】→ --cref [char_01_潭斌_V2.png] --cw 80
```

### P14 - 发现空白收款

```
【【潭斌】】→ --cref [char_01_潭斌_V2.png] --cw 80
```

### P15 - 程总邮件

```
【【潭斌】】→ --cref [char_01_潭斌_V2.png] --cw 80
【【程睿敏】】→ --cref [char_06_Ray_V1.png] --cw 100
```

### P16 - 停车场等待

```
【【程睿敏】】→ --cref [char_06_Ray_V1.png] --cw 100
【【潭斌】】→ --cref [char_01_潭斌_V2.png] --cw 80
```

### P17 - 月光下揭露

```
【【程睿敏】】→ --cref [char_06_Ray_V2.png] --cw 100
```

### P18 - 权力警告

```
【【程睿敏】】→ --cref [char_06_Ray_V3.png] --cw 100
【【潭斌】】→ --cref [char_01_潭斌_V3.png] --cw 100
```

### P19 - 消失在黑暗中

```
【【程睿敏】】→ --cref [char_06_Ray_V1.png] --cw 100
【【潭斌】】→ --cref [char_01_潭斌_V3.png] --cw 100
```

---

## Seedance Prompt模板示例（P09苦笑）

```
Extreme close-up shot, Tony's bitter smile forming, corners of mouth turned slightly down in resignation, eyes showing complex mix of regret longing and resignation behind glasses, 【【Tony】】expression twisted into bitter smile, eyes glistening, camera: ECU, yaw 0°, pitch 0°, dolly static, facing camera directly, action: char_02 attempts to smile, expression twists into bitter smile instead, eyes glistening slightly before he blinks it away, jaw tightens, holds bitter expression for 3s, environment light: warm amber café lighting (3200K), WongKarwai_Style, slow rack focus from bitter smile to glistening eyes, neon teal melancholic tones, 85mm telephoto lens, shallow depth of field, high ISO cinematic grain, romantic melancholy atmosphere
--cref [char_02_Tony_V3.png] --cw 80
Cinematic lighting, film grain, 35mm lens, f/2.8 depth of field
```

---

## 快速测试建议

### 测试顺序
1. **P02**（重逢）— 旧情人情感张力
2. **P09**（苦笑）— 情感高潮
3. **P17-18**（权力警告）— 程睿敏气场

---

## 第3集核心场景分析

### Tony情感线（苦涩→接受）

| 镜号 | Tony情绪 | --cref变体 |
|------|---------|-----------|
| P02 | V1漫不经心 | V1 |
| P04 | V1→回忆 | V1 |
| P07 | V4计算 | V4 |
| P09 | V3苦涩 | V3 |
| P11 | V3苦涩接受 | V3 |
| P12 | V3眼眶发红 | V3 |

### 潭斌情感线（冷淡→坚定）

| 镜号 | 潭斌情绪 | --cref变体 |
|------|---------|-----------|
| P02 | V1标准 | V1 |
| P06 | V2警觉 | V2 |
| P08 | V3坚定质问 | V3 |
| P11 | V3冷淡划线 | V3 |
| P13 | V2震惊 | V2 |

---

*--cref快速引用卡 v6.3.0 · 第03集 · 生成完毕*
