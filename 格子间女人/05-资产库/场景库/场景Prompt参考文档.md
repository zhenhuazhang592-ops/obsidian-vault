# 《格子间女人》场景Prompt参考文档

> 项目：格子间女人
> 版本：v6.3.0
> 生成日期：2026-03-26
> 用途：imagePrompt生成分镜图参考 + videoPrompt场景一致性

---

## CDP场景ID映射

| loc_id | 场景名 | 时间 | 光线特点 | 出现集数 |
|--------|--------|------|---------|---------|
| loc_01 | MPL中国公司办公室 | 夜/深夜 | 冷蓝月光+台灯暖黄 | 第1-3集 |
| loc_02 | MPL大会议室 | 日 | 投影白光 | 第1-2集 |
| loc_03 | MPL电梯/走廊 | 夜 | 冷蓝走廊灯 | 第1集 |
| loc_04 | MPL茶水间 | 日 | 自然光+暖黄 | 第1集 |
| loc_05 | 潭斌家客厅 | 夜/凌晨 | 窗外城市光 | 第1-3集 |
| loc_06 | 国贸三期 | 日 | 自然光+咖啡厅暖黄 | 第3集 |

---

## 场景Prompt（分镜图生成用）

### loc_01 · MPL中国公司办公室（夜）

**场景描述**：几百平方米大开间，夜间仅剩一人的职场空间。冷蓝月光穿透落地窗，台灯是全场唯一暖色。

**光影规格**：
- 主光源：窗外冷蓝月光（5500K+）
- 辅光源：台灯暖黄（3200K）
- 色调：蓝灰+琥珀对比

**分镜图Prompt**：
```
anime style, wide establishing shot, empty corporate office at night,
hundreds of square meters of open office floor, single desk lamp glowing amber in corner,
rows of cubicles bathed in cold blue moonlight from floor-to-ceiling windows,
no people in frame, lonely vast space atmosphere,
Beijing CBD night view visible through windows,
WongKarwai_Style, neon red and teal color split,
slow rack focus from background lights to foreground desk lamp glow,
85mm telephoto lens, shallow depth of field, high ISO cinematic grain,
no text subtitles logos watermarks
```

**时间变体**：
- 深夜（21:00+）：冷蓝月光为主，台灯孤岛
- 凌晨（01:00+）：全暗，只剩手机/电脑屏幕光

---

### loc_01 · MPL地下停车场（夜）

**场景描述**：地下停车场灯光昏暗，程睿敏的车停在角落。月光从通风口射入。

**光影规格**：
- 主光源：荧光灯管（5500K，冷）
- 点光源：车灯（暖白）
- 色调：深蓝+阴影

**分镜图Prompt**：
```
anime style, underground parking garage at night,
dim flickering fluorescent lights casting moving shadows,
dark corner with car parked, moonlight shaft from vent shaft,
mysterious cold atmosphere, Beijing underground,
WongKarwai_Style, dramatic shadow contrast,
neon teal cold tones, single light creating rim lighting,
85mm telephoto lens, shallow depth of field, high ISO cinematic grain,
no text subtitles logos watermarks
```

---

### loc_02 · MPL大会议室（日）

**场景描述**：大会议室全景，投影仪亮白，大屏幕滚动数字。乔利维坐正中，潭斌缩角落。

**光影规格**：
- 主光源：投影仪白光（5500K）
- 辅光源：荧光天花板灯
- 色调：冷白+蓝色阴影

**分镜图Prompt**：
```
anime style, wide establishing shot, large conference room during day,
bright white projector screen showing scrolling data,
long conference table with executive chairs,
one figure at center (confident), one figure in far corner (peripheral),
dramatic contrast between spotlight and shadow,
ShortDrama_Style × WongKarwai_Style, high contrast,
fluorescent meeting room lighting,
85mm telephoto lens, shallow depth of field,
no text subtitles logos watermarks
```

---

### loc_03 · MPL电梯/走廊（夜）

**场景描述**：冷蓝走廊灯，电梯门打开的金属反光。高跟鞋节奏声。

**光影规格**：
- 主光源：荧光走廊灯（5500K）
- 色调：冷蓝+金属反光

**分镜图Prompt**：
```
anime style, narrow corridor with cold blue fluorescent lighting,
elevator doors in background with metal reflections,
pointed high heels clicking on marble floor (off frame sound cue),
single figure silhouette against corridor light,
WongKarwai_Style, neon teal corridor tones,
dramatic cold blue contrast, deep shadows,
85mm telephoto lens, shallow depth of field, high ISO cinematic grain,
no text subtitles logos watermarks
```

---

### loc_04 · MPL茶水间（日）

**场景描述**：茶水间暖光，方芳端热普洱。温馨的职场角落。

**光影规格**：
- 主光源：自然窗户光
- 辅光源：热水壶/台灯暖光（3200K）
- 色调：暖黄+琥珀

**分镜图Prompt**：
```
anime style, cozy break room / tea kitchen,
warm natural daylight from window,
FangFang holding hot Pu-erh tea cup in both hands,
steam rising from tea, intimate workplace corner,
WongKarwai_Style, warm amber tea room tones,
cozy atmosphere contrasting with cold office outside,
85mm telephoto lens, shallow depth of field,
no text subtitles logos watermarks
```

---

### loc_05 · 潭斌家客厅（夜）

**场景描述**：北京CBD夜景如星图，窗外灯火璀璨。潭斌靠在沙发上，手机屏幕蓝光。

**光影规格**：
- 主光源：窗外CBD城市光（暖金+冷蓝）
- 点光源：手机屏幕（冷蓝）
- 色调：城市灯光对比

**分镜图Prompt**：
```
anime style, living room at night in Beijing apartment,
floor-to-ceiling window showing stunning CBD night skyline,
countless building lights creating star-map effect,
TanBin leaning back on sofa, phone screen blue-white glow on face,
warm golden city glow from below, cold shadow on face,
WongKarwai_Style, Beijing CBD night lights creating constellation effect,
neon red and teal color split, romantic melancholy atmosphere,
85mm telephoto lens, shallow depth of field, high ISO cinematic grain,
no text subtitles logos watermarks
```

---

### loc_06 · 国贸三期咖啡厅（日）

**场景描述**：现代北京咖啡厅，靠窗位置，阳光与室内灯光交织。爵士乐背景。

**光影规格**：
- 主光源：自然阳光（暖）
- 辅光源：咖啡厅灯光（3200K）
- 色调：暖黄+咖啡色

**分镜图Prompt**：
```
anime style, modern Beijing café interior at GuoMao Sanqi,
floor-to-ceiling windows with natural daylight streaming in,
two figures sitting across café table from each other,
coffee cups 30cm apart, steam rising from cups,
warm amber café lighting, jazz music atmosphere,
WongKarwai_Style, romantic melancholy,
neon amber and warm tones, soft shadows,
85mm telephoto lens, shallow depth of field, high ISO cinematic grain,
no text subtitles logos watermarks
```

---

## 场景时间变体表

| loc_id | 场景 | 日间Prompt | 夜间Prompt | 凌晨Prompt |
|--------|------|-----------|-----------|-----------|
| loc_01 | MPL办公室 | 冷白荧光，全员在场 | 冷蓝月光，台灯孤岛 | 全暗，屏幕光 |
| loc_02 | MPL会议室 | 投影白光，正式 | — | — |
| loc_03 | MPL走廊 | 冷白荧光 | 冷蓝走廊灯 | 深暗 |
| loc_04 | 茶水间 | 自然光+暖黄 | — | — |
| loc_05 | 潭斌家 | CBD日光 | CBD灯火如星 | CBD灯火+手机光 |
| loc_06 | 国贸三期 | 自然光+暖咖啡 | — | — |

---

## 光影规格表（Roger Deakins五定律）

| 定律 | 说明 | 本剧应用 |
|------|------|---------|
| 动因光源 | 每个光源必须有物理来源 | 台灯/月光/投影/手机 |
| 短边主光 | 主光从镜头短边打来 | 窗外月光，侧45° |
| 平方反比衰减 | 近光亮，远光暗 | 台灯光圈 vs 办公室黑暗 |
| 色温逻辑 | 不同光源有不同色温 | 月光5500K+ / 台灯3200K |
| PBR材质 | 真实材质反射 | 金属/玻璃/皮肤 |

---

## 场景Prompt快速引用

| loc_id | 场景 | 关键词 |
|--------|------|--------|
| loc_01 | MPL办公室夜 | `empty office, cold blue moonlight, amber desk lamp` |
| loc_01 | 停车场夜 | `underground parking, flickering lights, shadow` |
| loc_02 | 会议室日 | `conference room, projector white light, contrast` |
| loc_03 | 走廊夜 | `corridor, cold blue fluorescent, elevator doors` |
| loc_04 | 茶水间日 | `tea room, warm amber, steam from tea` |
| loc_05 | 潭斌家夜 | `living room, Beijing CBD skyline, city lights` |
| loc_06 | 咖啡厅日 | `café, warm amber, jazz atmosphere` |

---

## 场景-镜头映射（示例：第01集）

| 镜号 | loc_id | 场景Prompt关键词 |
|------|--------|-----------------|
| P01 | loc_01 | `empty office, cold blue moonlight, amber desk lamp glow` |
| P02 | loc_01 | `office, computer screen glow, side profile` |
| P03 | loc_01 | `office, screen light on dilated pupils` |
| P04 | loc_01 | `window, CBD night view, palm on glass` |
| P05 | loc_01 | `phone screen blue light, office darkness` |
| P06 | loc_02 | `sofa, TV color flicker, casual T-shirt` |
| P09 | loc_03 | `elevator doors, cold blue corridor, high heels` |
| P10 | loc_03 | `elevator interior, metal reflections, closed doors` |
| P11 | loc_02 | `conference room, projector white, QiaoLW center` |
| P15 | loc_04 | `tea room, warm amber, steam, FangFang tea` |
| P17 | loc_05 | `sofa, phone glow, CBD night window` |
| P18 | loc_05 | `window, fingertip hover, CBD constellation` |

---

*场景Prompt参考文档 v6.3.0 · 生成完毕*
