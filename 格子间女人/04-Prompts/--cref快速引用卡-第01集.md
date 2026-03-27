# 《格子间女人》第01集 · --cref快速引用卡

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

### P01 - 空办公室（无角色）

```
无角色 → 无需--cref
```

### P02 - 潭斌侧脸屏幕反光

```
【【潭斌】】→ --cref [char_01_潭斌_V1.png] --cw 100
```

### P03 - 潭斌瞳孔放大（震惊）

```
【【潭斌】】→ --cref [char_01_潭斌_V2.png] --cw 80
```

### P04 - 潭斌走向窗前（坚定）

```
【【潭斌】】→ --cref [char_01_潭斌_V3.png] --cw 100
```

### P05 - 潭斌握手机（标准）

```
【【潭斌】】→ --cref [char_01_潭斌_V1.png] --cw 100
```

### P06 - Tony接电话

```
【【余永麟】】→ --cref [char_02_Tony_V1.png] --cw 100
```

### P07 - 分屏通话

```
【【潭斌】】→ --cref [char_01_潭斌_V2.png] --cw 80
【【余永麟】】→ --cref [char_02_Tony_V2.png] --cw 100
```

### P08 - 潭斌挂断电话

```
【【潭斌】】→ --cref [char_01_潭斌_V2.png] --cw 80
```

### P09 - 电梯口对峙

```
【【潭斌】】→ --cref [char_01_潭斌_V1.png] --cw 100
【【曾婵贞】】→ --cref [char_03_ZengCZ_V1.png] --cw 100
```

### P10 - 电梯内独自

```
【【潭斌】】→ --cref [char_01_潭斌_V3.png] --cw 100
```

### P11 - 会议室全景

```
【【潭斌】】→ --cref [char_01_潭斌_V1.png] --cw 100
【【乔利维】】→ --cref [char_04_QiaoLW_V1.png] --cw 100
```

### P12 - 曾婵贞点指

```
【【曾婵贞】】→ --cref [char_03_ZengCZ_V2.png] --cw 100
【【潭斌】】→ --cref [char_01_潭斌_V2.png] --cw 80
```

### P13 - 宣布负责普达

```
【【曾婵贞】】→ --cref [char_03_ZengCZ_V2.png] --cw 100
【【潭斌】】→ --cref [char_01_潭斌_V2.png] --cw 80
```

### P14 - 乔利维威胁

```
【【乔利维】】→ --cref [char_04_QiaoLW_V2.png] --cw 100
【【潭斌】】→ --cref [char_01_潭斌_V3.png] --cw 100
```

### P15 - 方芳送茶

```
【【方芳】】→ --cref [char_05_FangF_V1.png] --cw 100
【【潭斌】】→ --cref [char_01_潭斌_V1.png] --cw 100
```

### P16 - 名单上停住

```
【【潭斌】】→ --cref [char_01_潭斌_V3.png] --cw 100
```

### P17 - 短信陌生号码

```
【【潭斌】】→ --cref [char_01_潭斌_V2.png] --cw 80
```

### P18 - 指尖悬停CBD

```
【【潭斌】】→ --cref [char_01_潭斌_V3.png] --cw 100
```

---

## Seedance Prompt模板

### 完整Seedance Prompt格式（第02镜头示例）

```
Wide establishing shot, empty corporate office floor at night, rows of overhead fluorescent lights switching off one by one in domino effect down corridor, cold blue moonlight streaming through floor-to-ceiling windows illuminating vast space, single warm desk lamp glowing in far corner creating halo of amber light, 【【潭斌】】in dark navy blazer sitting at desk, side profile view catching screen glow reflected on her face, camera: static WS, yaw 0°, pitch 0°, dolly slow push inward 0.5m over 6s, facing camera indirectly (profile), action: char_01 sits upright, hands resting on desk, expression neutral-focused, slight tension in jaw, environment light: cool monitor blue-white light on face, warm amber desk lamp in background blur, WongKarwai_Style, slow rack focus from background lamp to screen glow, neon red and teal color split, 85mm telephoto lens, shallow depth of field, high ISO cinematic grain, romantic melancholy atmosphere
--cref [char_01_潭斌_V1.png] --cw 100
Cinematic lighting, film grain, 35mm lens, f/2.8 depth of field
```

### 多人同镜格式（第07镜头示例）

```
Medium shot, split-screen phone call conversation, left side: 【【潭斌】】speaking into phone, right side: 【【余永麟】】listening on sofa, TanBin's voice low and measured with controlled emotion, Tony's expression becomes serious and still, camera: MCU alternating, yaw 0° then cut to Tony, pitch 0°, dolly static with slow zoom on TanBin 0.2m then shift to Tony, facing camera directly (both sides face camera for phone call), action: char_01 takes deep breath, lowers head slightly, speaks into phone with quiet determination; char_02 goes silent, jaw tightens, TV noise fades in background, environment light: char_01 side: cold blue phone light on face, ambient dark office; char_02 side: TV multi-color flickering light, WongKarwai_Style, slow rack focus between speaker and listener, neon teal and purple color split between two call sides, 85mm telephoto lens, shallow depth of field, high ISO cinematic grain, romantic melancholy atmosphere
--cref [char_01_潭斌_V2.png] --cw 80
--cref [char_02_Tony_V2.png] --cw 100
Cinematic lighting, film grain, 35mm lens, f/2.8 depth of field
```

---

## --cw权重说明

| 场景 | --cw | 说明 |
|------|------|------|
| 同表情/同服装 | 100 | 完全一致 |
| 情绪微调（震惊/坚定） | 80 | 允许轻微表情变化 |
| 远景（WS/MS） | 80 | 远景对面部要求较低 |
| 换场景/换服装 | 100 | 必须完全一致 |

---

## 快速测试建议

### 测试顺序
1. **P02**（潭斌侧脸）— 单人，标准表情
2. **P03**（瞳孔放大）— 单人，震惊表情，验证--cw 80
3. **P07**（分屏通话）— 双人，验证多人--cref
4. **P18**（指尖悬停）— 情绪高点，验证氛围

### 测试Prompt提取方法
1. 复制对应镜头的`videoPrompt`字段内容
2. 找到`【【角色名】】`位置
3. 替换为对应的`--cref [文件名] --cw 权重`
4. 在Prompt末尾添加`Cinematic lighting, film grain, 35mm lens, f/2.8 depth of field`

---

*--cref快速引用卡 v6.3.0 · 生成完毕*
