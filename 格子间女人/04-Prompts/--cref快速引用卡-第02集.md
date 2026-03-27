# 《格子间女人》第02集 · --cref快速引用卡

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

### P01 - 会议室评分表

```
【【潭斌】】→ --cref [char_01_潭斌_V1.png] --cw 100
【【曾婵贞】】→ --cref [char_03_ZengCZ_V2.png] --cw 100
【【乔利维】】→ --cref [char_04_QiaoLW_V1.png] --cw 100
```

### P02 - 乔利维握手

```
【【乔利维】】→ --cref [char_04_QiaoLW_V1.png] --cw 100
```

### P03 - 潭斌翻标书

```
【【潭斌】】→ --cref [char_01_潭斌_V2.png] --cw 80
```

### P04 - 快步走向洗手间

```
【【潭斌】】→ --cref [char_01_潭斌_V1.png] --cw 100
```

### P05 - 洗手间僵住

```
【【潭斌】】→ --cref [char_01_潭斌_V2.png] --cw 80
【【乔利维】】→ --cref [char_04_QiaoLW_V1.png] --cw 100
```

### P06 - 颤抖按录音

```
【【潭斌】】→ --cref [char_01_潭斌_V2.png] --cw 80
```

### P07 - 关掉录音

```
【【潭斌】】→ --cref [char_01_潭斌_V2.png] --cw 80
【【乔利维】】→ --cref [char_04_QiaoLW_V1.png] --cw 100
```

### P08 - 程睿敏步入

```
【【程睿敏】】→ --cref [char_06_Ray_V1.png] --cw 100
【【曾婵贞】】→ --cref [char_03_ZengCZ_V1.png] --cw 100
```

### P09 - 质问分数

```
【【程睿敏】】→ --cref [char_06_Ray_V1.png] --cw 100
【【乔利维】】→ --cref [char_04_QiaoLW_V3.png] --cw 80
```

### P10 - 目光交汇

```
【【程睿敏】】→ --cref [char_06_Ray_V1.png] --cw 100
【【潭斌】】→ --cref [char_01_潭斌_V2.png] --cw 80
```

### P11 - 停车场拦住

```
【【程睿敏】】→ --cref [char_06_Ray_V1.png] --cw 100
【【潭斌】】→ --cref [char_01_潭斌_V2.png] --cw 80
```

### P12 - FSK警告

```
【【程睿敏】】→ --cref [char_06_Ray_V1.png] --cw 100
【【潭斌】】→ --cref [char_01_潭斌_V2.png] --cw 80
```

### P13 - 消失在黑暗中

```
【【程睿敏】】→ --cref [char_06_Ray_V1.png] --cw 100
```

### P14 - 邮箱收到附件

```
【【潭斌】】→ --cref [char_01_潭斌_V2.png] --cw 80
```

### P15 - 看昵称困惑

```
【【潭斌】】→ --cref [char_01_潭斌_V2.png] --cw 80
```

### P16 - FSK组织架构

```
【【潭斌】】→ --cref [char_01_潭斌_V2.png] --cw 80
```

### P17 - 收到Tony短信

```
【【潭斌】】→ --cref [char_01_潭斌_V2.png] --cw 80
```

### P18 - 走向窗前

```
【【潭斌】】→ --cref [char_01_潭斌_V3.png] --cw 100
```

### P19 - 坚定回复

```
【【潭斌】】→ --cref [char_01_潭斌_V3.png] --cw 100
```

### P20 - 指尖悬停CBD

```
【【潭斌】】→ --cref [char_01_潭斌_V3.png] --cw 100
```

---

## Seedance Prompt模板示例（P12）

```
Close-up shot, Cheng Ruimin slightly leaning forward, lowering head to whisper, face alternately lit and shadowed by flickering parking garage lights creating dramatic effect, 【【程睿敏】】face calm as still water with underlying intensity, 【【潭斌】】frozen listening intently, camera: CU, yaw 0°, pitch 0°, dolly static, facing camera directly, action: char_06 leans forward with mysterious intensity, voice dropping to whisper, face half-illuminated by flickering light casting moving shadows, char_01 frozen listening intently, environment light: flickering fluorescent parking garage lights creating strobing shadow effect on face, WongKarwai_Style, slow rack focus shifting between illuminated and shadowed halves of face, neon teal cold tones, 85mm telephoto lens, shallow depth of field, high ISO cinematic grain, romantic melancholy atmosphere
--cref [char_06_Ray_V1.png] --cw 100
--cref [char_01_潭斌_V2.png] --cw 80
Cinematic lighting, film grain, 35mm lens, f/2.8 depth of field
```

---

## 快速测试建议

### 测试顺序
1. **P08**（程睿敏步入）— 气场测试
2. **P12**（FSK警告）— 双人对手戏
3. **P20**（指尖悬停CBD）— 情绪高点

---

*--cref快速引用卡 v6.3.0 · 第02集 · 生成完毕*
