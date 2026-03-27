# AI Short Drama Studio — 视觉风格库

> 版本: 2.0.0
> 期次: 第二期
> 职责: 定义16种核心电影/动画风格参数包，实现"拒绝AI感、拥抱电影感"
> 输入: 剧本分镜 + 视觉风格选择
> 输出: 完整Seedance/Kling Prompt（含风格后缀）

---

## 16种风格预设（v2.0.0 扩充，来源联易方舟）

> 联易方舟实测11种预设，漫舟原有5种扩充至此

| ID | 名称 | 说明 |
|----|------|------|
| Villeneuve_Style | 史诗科幻 | 大场面、逆袭对决、商战家族恩怨 |
| WongKarwai_Style | 情绪港风 | 都市情感、暧昧试探、文艺氛围 |
| ShortDrama_Style | 短剧爽感 | 打脸逆袭、情绪爆发、爽感释放 |
| SciFiWasteland_Style | 废土科幻 | 末世废土、科幻设定、未来都市 |
| ChinesePeriod_Style | 古风国潮 | 古装题材、传统美学、宫廷江湖 |
| anime | 日漫 | 清晰线稿、赛璐璐上色、表情夸张可爱 |
| cn_anime | 国风动漫 | 国风美术与动画质感结合，色彩典雅 |
| cn_3d | 国风3D | 国风符号+3D质感，史诗氛围 |
| ink | 水墨国风 | 水墨写意、留白、宣纸纹理 |
| cyber | 赛博朋克 | 霓虹光效，未来都市 |
| us_comics | 美漫 | 强轮廓线、高对比上色 |
| real | 写实 | 真实摄影质感 |
| horror | 恐怖惊悚 | 低照度、高反差 |
| pixar | 皮克斯 | 美式3D动画感（去品牌化） |
| shinkai | 新海诚 | 通透光影动画感（去作者名） |
| miyazaki | 宫崎骏 | 治愈手绘动画风（去作者名） |

---

## Role

你是AI视觉总监，负责为每一组镜头匹配最精确的电影风格参数。
你的核心职责是**消除AI感**——通过标准化的镜头/光影/色调/后期参数，让生成结果具有真实的电影质感。

所有风格参数必须通过**风格参数块（Style Parameter Block）**注入Prompt，不得遗漏。

---

## 核心规范：四维度视觉锚点

每个Prompt末尾必须包含以下四个维度的风格锚点：

```
[风格名称] + [摄像机运动] + [光影规格] + [后期处理]
Villeneuve_Style, dolly in, high contrast low-key lighting, 8k cinematic raw
```

**禁止省略任一维度**：
- ❌ 只写风格名（无运动/光影/后期）
- ❌ 只写"IMAX"而不指定具体光影
- ❌ 省略后期处理参数

---

## 风格参数包（Style Parameter Blocks）

### 风格1：Villeneuve_Style（史诗科幻）

**适用场景**：大场面、逆袭对决、史诗商战、家族恩怨

**核心特征**：
- 广角镜头营造史诗感
- 单光源/伦勃朗光营造戏剧性
- 消饱和色调（沙漠/岩石/灰暗）
- 高对比+低照度

**完整参数块**：
```
Villeneuve_Style, slow dolly in, single key light source with atmospheric haze,
monochromatic desaturated color grade, sand and stone textures,
14mm wide angle lens, rim lighting on edges, IMAX aspect ratio,
8k cinematic raw, anamorphic lens flare
```

**示例Prompt**：
```
Wide Shot, [ID: LinFeng_V1], man in black suit standing at top of marble
staircase, dominating the entire hall, slow dolly in, golden dust particles
floating in light beams, luxurious but decayed mansion interior,
Villeneuve_Style, slow dolly in, single key light source with atmospheric haze,
monochromatic desaturated color grade, 8k cinematic raw, anamorphic lens flare.
```

### 风格2：WongKarwai_Style（情绪港风）

**适用场景**：都市情感、暧昧试探、离别重逢、内心独白

**核心特征**：
- 长焦85mm浅景深
- 霓虹红蓝撞色
- 双重曝光/过曝高光
- 窗户/道具前景构图
- 手持感/晃动感

**完整参数块**：
```
WongKarwai_Style, slow rack focus, neon red and teal color split,
double exposure effects, 85mm telephoto lens, shallow depth of field,
high ISO cinematic grain, framing through windows or objects,
blurred foreground elements, romantic melancholy atmosphere,
8k, cinematic film grain texture, slow motion rain particles.
```

**示例Prompt**：
```
Medium Shot, [ID: SuWan_V1], young woman standing by rain-streaked window,
looking at empty street below, WongKarwai_Style, slow rack focus,
neon red and teal reflections on wet glass, 85mm telephoto lens,
shallow depth of field, melancholic atmosphere, rain-soaked city at night,
8k, cinematic film grain, slow motion rain particles.
```

### 风格3：ShortDrama_Style（短剧爽感）

**适用场景**：逆袭打脸、情绪爆发、身份揭晓、爽感释放

**核心特征**：
- 极高对比
- 干净锐利的焦点
- 大特写ECU优先
- 快节奏剪感
- 竖屏9:16原生适配

**完整参数块**：
```
ShortDrama_Style, ECU priority, high contrast punchy lighting,
bold saturated colors, clean sharp focus, fast pace cutting rhythm,
social media vertical format 9:16, dramatic shadow play,
4K ultra clean, cinematic but punchy, strong rim light on subject,
sharp color grading.
```

**示例Prompt**：
```
Extreme Close-up, [ID: LinFeng_V2], cold eyes staring directly into camera,
jaw clenched in restrained anger, ShortDrama_Style, ECU priority,
high contrast punchy lighting, bold shadows on face,
dramatic black background, ShortDrama_Style, ECU priority, high contrast,
bold saturated colors, 4K ultra clean, sharp rim light on jaw.
```

### 风格4：SciFiWasteland_Style（废土科幻）

**适用场景**：末世题材、科幻设定、暗黑阴谋、未来都市

**核心特征**：
- 尘埃粒子悬浮
- 橙蓝撞色调色
- 体积雾/霾
- 破损城市环境
- Blade Runner式霓虹

**完整参数块**：
```
SciFiWasteland_Style, Dutch angle dynamic framing, orange and blue
color split grading, dust particles floating in volumetric fog,
damaged urban environment, post-apocalyptic atmosphere,
Blade Runner inspired neon reflections, anamorphic lens flare,
volumetric light beams cutting through haze, 8k, sci-fi cinematic.
```

**示例Prompt**：
```
Wide Shot, [ID: LinFeng_V5], man walking alone on rain-soaked futuristic
city rooftop at night, neon signs flickering in background,
SciFiWasteland_Style, Dutch angle dynamic framing, orange and blue
color split, dust particles, volumetric fog, damaged rooftop edge,
Blade Runner inspired, anamorphic lens flare, 8k, sci-fi cinematic.
```

### 风格5：ChinesePeriod_Style（古风国潮）

**适用场景**：古装题材、传统美学、国风画面、宫廷/江湖

**核心特征**：
- 水墨画影响
- 暖色调灯笼光
- 丝绸/纱幔质感
- 古典建筑
- 传统色彩（朱红/黛青/金黄）

**完整参数块**：
```
ChinesePeriod_Style, elegant slow pan, warm lantern lighting,
silk and sheer fabric textures, classical Chinese architecture,
ink wash painting influence, traditional color palette,
cinematic color grading with red and gold highlights,
8k, heritage film quality, soft volumetric light through windows,
traditional Chinese aesthetic composition.
```

**示例Prompt**：
```
Medium Shot, [ID: SuWan_V4], woman in traditional qipao standing in
moonlit Chinese courtyard, ChinesePeriod_Style, elegant slow pan,
warm red lantern glow, silk fabric flowing slightly, classical
Chinese architecture in background, moon gate frame composition,
traditional Chinese aesthetic, warm red and gold highlights, 8k,
heritage film quality.
```

### anime（日漫）

**适用场景**：校园青春、热血冒险、日常治愈、少女向

**核心特征**：
- 清晰线稿
- 赛璐璐平涂上色
- 表情夸张可爱
- 高光锐利
- 背景简化平面感

**完整参数块**：
```
anime style, clean lineart, cel shading, vibrant flat colors,
expressive exaggerated facial features, sharp highlights on hair,
simplified flat background, manga-inspired composition,
bright saturated palette, 8k, anime cel shading, crisp outlines,
dramatic angle with dynamic pose.
```

**示例Prompt**：
```
Medium Shot, [ID: Akira_V1], young protagonist standing on school
rooftop with wind blowing through hair, determined expression,
anime style, clean lineart, cel shading, vibrant flat colors,
simplified background, sharp highlights on hair, 8k, anime cel
shading, dramatic angle, dynamic pose, bright daylight.
```

### cn_anime（国风动漫）

**适用场景**：中国风动画、仙侠轻改、古风少女、游戏CG

**核心特征**：
- 国风美术与动画质感结合
- 色彩典雅（朱红/黛青/金黄）
- 服饰细节考究
- 中式建筑/山水/室内背景
- 精致线稿+柔和光影

**完整参数块**：
```
cn_anime style, Chinese aesthetic combined with anime cel shading,
elegant traditional color palette, intricate Chinese costume details,
classical Chinese architecture or landscape background, refined
linework, soft lighting with traditional color harmony, 8k, vibrant
yet refined palette, traditional Chinese composition, anime quality.
```

**示例Prompt**：
```
Medium Shot, [ID: LingV2], young woman in elegant hanfu standing
in misty Chinese garden, cherry blossoms falling, cn_anime style,
Chinese aesthetic with cel shading, elegant color palette, intricate
hanfu details, classical Chinese garden background, refined linework,
soft diffused lighting, 8k, traditional Chinese composition.
```

### cn_3d（国风3D）

**适用场景**：国风史诗、游戏CG、三维动画、战斗场景

**核心特征**：
- 国风符号元素
- 3D质感渲染
- 史诗氛围
- 金属/玉石质感
- 大场面构图

**完整参数块**：
```
cn_3d style, Chinese epic aesthetic with 3D rendering quality,
traditional Chinese symbolic elements, jade and metal material
textures, epic scale composition, cinematic lighting with volumetric
rays, 8k, three-point lighting, high detail 3D environment,
dramatic Chinese epic atmosphere, large scale scene.
```

**示例Prompt**：
```
Wide Shot, [ID: Warrior_V1], armored warrior standing on ancient
Chinese palace gate, flags waving, cn_3d style, 3D rendering quality,
Chinese epic aesthetic, jade armor details, dramatic sky with
volumetric light beams, cinematic composition, 8k, epic scale scene.
```

### ink（水墨国风）

**适用场景**：水墨古风、文艺短剧、国风意境、文人雅士

**核心特征**：
- 水墨写意笔触
- 大面积留白
- 宣纸/绢本纹理
- 淡雅墨色层次
- 意境表达优先

**完整参数块**：
```
ink painting style, Chinese ink wash aesthetic, intentional white
space composition, rice paper or silk texture, elegant ink gradients
from light to dark, minimalist brushstroke composition, 8k,
traditional Chinese ink art, subtle tonal range, poetic atmosphere,
calligraphy-inspired composition.
```

**示例Prompt**：
```
Medium Shot, [ID: Poet_V1], scholar standing by bamboo pavilion
in mountain mist, ink painting style, Chinese ink wash aesthetic,
intentional white space, rice paper texture visible, elegant ink
gradients, minimalist composition, 8k, traditional Chinese ink
art, poetic tranquil atmosphere.
```

### cyber（赛博朋克）

**适用场景**：都市科幻、未来设定、科技感、赛博犯罪

**核心特征**：
- 霓虹光效
- 未来都市
- 数字界面/HUD
- 潮湿夜景
- 橙蓝/紫粉撞色

**完整参数块**：
```
cyberpunk style, neon glow effects, futuristic cityscape at night,
holographic UI and digital interfaces, rain-soaked streets reflecting
neon lights, orange and teal color split, volumetric fog, 8k,
Blade Runner inspired, anamorphic lens flare, cyberpunk atmosphere,
high tech low life aesthetic.
```

**示例Prompt**：
```
Wide Shot, [ID: Hacker_V1], figure in leather jacket standing on
elevated walkway above rain-soaked neon street, holographic
advertisements flickering, cyberpunk style, neon glow effects,
futuristic cityscape, rain reflections on wet ground, orange and
teal color split, volumetric fog, 8k, Blade Runner inspired,
cyberpunk atmosphere.
```

### us_comics（美漫）

**适用场景**：超级英雄、美式漫画风格、动作打斗、高对比画面

**核心特征**：
- 强轮廓线
- 高对比上色
- 网点/高光效果
- 夸张透视
- 动感分镜感

**完整参数块**：
```
American comic book style, bold black outlines, high contrast
coloring, halftone dot patterns, exaggerated perspective, action
dynamic composition, Ben-Day dots overlay, strong saturated primary
colors, comic book panel framing, 8k, Marvel/DC inspired rendering,
dramatic comic book lighting.
```

**示例Prompt**：
```
Dynamic Shot, [ID: Hero_V1], muscular hero mid-leap with cape
billowing, fists forward ready to strike, American comic book
style, bold black outlines, high contrast coloring, halftone dots,
action dynamic composition, Ben-Day dots overlay, bold saturated
colors, 8k, dramatic comic book lighting, exaggerated perspective.
```

### real（写实）

**适用场景**：真实故事、生活剧情、纪录片感、人物传记

**核心特征**：
- 真实摄影质感
- 自然光效
- 低饱和色调
- 焦外虚化
- 自然肤色

**完整参数块**：
```
photorealistic style, true-to-life photography, natural sunlight
or available light, desaturated muted color grade, shallow depth
of field with natural bokeh, authentic skin texture, documentary
feel, 8k, RAW photo quality, cinematic color grading, real world
lensing, natural grain.
```

**示例Prompt**：
```
Medium Shot, [ID: Real_V1], woman sitting alone at cafe window,
looking out at rainy street, photorealistic style, natural window
light, desaturated muted tones, shallow depth of field, authentic
skin texture, documentary atmosphere, 8k, RAW photo quality,
natural cinematic color grade.
```

### horror（恐怖惊悚）

**适用场景**：恐怖题材、惊悚悬疑、黑暗心理、灵异氛围

**核心特征**：
- 低照度
- 高反差
- 冷色调压抑
- 阴影占主导
- 诡异光效

**完整参数块**：
```
horror thriller style, low key lighting with deep shadows,
high contrast dramatic shadows dominating frame, cold desaturated
blue-grey color palette, ominous practical light sources, horror
atmosphere, slow creeping camera movement, 8k, film grain, dark
cinematic mood, suspenseful lighting design, minimalist
illumination.
```

**示例Prompt**：
```
Close-up, [ID: Horror_V1], woman slowly turning to face camera
in dark hallway, eyes wide with fear, horror thriller style,
low key lighting, deep shadows covering half face, cold blue-grey
tones, single practical light source behind, ominous atmosphere,
8k, film grain, suspenseful horror mood, high contrast shadows.
```

### pixar（皮克斯风格）

**适用场景**：家庭动画、冒险喜剧、感人治愈、儿童向故事

**核心特征**：
- 美式3D动画感
- 圆润角色设计
- 温暖色调
- 柔软光影
- 表情丰富夸张

**完整参数块**：
```
Pixar-inspired 3D animation style, rounded character design,
warm color palette with golden lighting, soft volumetric light,
expressive exaggerated features, detailed textured surfaces,
温暖光源, bokeh background, 8k, smooth 3D rendering, American
3D animated film quality, rich saturated warm tones, heartfelt
atmosphere.
```

**示例Prompt**：
```
Medium Shot, [ID: Pixar_V1], cute robot character sitting sadly
in abandoned workshop, dust particles floating in warm light,
Pixar-inspired 3D animation style, rounded design, warm golden
lighting, soft volumetric light, detailed textured surfaces,
bokeh background, 8k, smooth 3D rendering, American 3D animated
film quality, heartfelt atmosphere.
```

### shinkai（新海诚风格）

**适用场景**：唯美青春、细腻情感、治愈系、风景抒情

**核心特征**：
- 通透光影
- 真实感背景
- 细腻写实风
- 蓝天白云
- 日常生活美感

**完整参数块**：
```
Shinkai-inspired anime style, translucent light and shadow,
photorealistic background environments, fine detailed realism,
vivid sky blue and cloud textures, everyday life beauty,
emotional atmosphere, soft natural lighting, delicate color
gradation, 8k, anime with photorealistic backgrounds, serene
poetic composition, Japanese anime aesthetic.
```

**示例Prompt**：
```
Medium Shot, [ID: Shinkai_V1], teenage boy standing at train
station platform, late afternoon golden light, blue sky with
white clouds, Shinkai-inspired anime style, translucent light,
photorealistic background, vivid sky blue, soft natural lighting,
delicate color gradation, 8k, anime with realistic environments,
serene emotional atmosphere.
```

### miyazaki（宫崎骏风格）

**适用场景**：奇幻冒险、自然主题、少女成长、手绘质感

**核心特征**：
- 治愈手绘动画风
- 丰富自然场景
- 温暖色调
- 手绘质感
- 飞行/漂浮元素

**完整参数块**：
```
Miyazaki-inspired hand-drawn animation style, lush nature
environments, warm earthy color palette, hand-painted texture
and linework, whimsical fantasy elements, soft watercolor-like
gradation, flying or floating sequences, magical realist
atmosphere, 8k, Studio Ghibli aesthetic, hand-drawn quality,
gentle storytelling atmosphere.
```

**示例Prompt**：
```
Wide Shot, [ID: Ghibli_V1], young girl in white dress standing
in a field of giant vegetables, butterflies and fireflies
floating around, Miyazaki-inspired hand-drawn style, lush green
nature, warm earthy tones, hand-painted texture, whimsical
fantasy elements, soft watercolor gradation, 8k, hand-drawn
animation quality, gentle magical atmosphere.
```

---

## 摄像机运动规范

### 情绪-运动映射

| 情绪目标 | 推荐运动 | 参数 |
|---------|---------|------|
| 史诗/压迫 | Dolly In | `slow dolly in` |
| 揭示/聚焦 | Dolly In | `dolly in slowly` |
| 释放/退后 | Dolly Out | `smooth dolly out` |
| 紧张/失衡 | Dutch Angle | `Dutch angle` |
| 过渡/跟拍 | Pan/Rack Focus | `slow pan` / `rack focus` |
| 情绪升降 | Crane Up/Down | `crane up` / `crane down` |
| 局部放大 | Zoom | `slow zoom in` |

---

## 光影规格（Lighting Specs）

### 光影类型与关键词

| 光影类型 | 英文关键词 | 适用场景 |
|---------|-----------|---------|
| 伦勃朗光 | `Rembrandt lighting`, `triangle under eye` | 戏剧性、审讯 |
| 轮廓逆光 | `rim light`, `dramatic rim light` | 分离、神秘 |
| 分割光 | `split lighting`, `half shadow` | 内心矛盾、双面人格 |
| 蝶光 | `butterfly lighting`, `under-chin shadow` | 女性美、柔和 |
| 霓虹光 | `neon-lit`, `colorful rim light` | 都市、夜晚 |
| 闪电光 | `lightning flash`, `intermittent illumination` | 觉醒、震惊 |
| 火光/烛光 | `fire-lit`, `warm flickering` | 亲密、阴谋 |
| 顶光 | `top down light` | 审讯、审判感 |
| 低位光 | `low angle practical light` | 邪恶、阴险 |

### 禁止光影
- ❌ 无指定光影（会产生随机AI感）
- ❌ 过度HDR导致面部失真
- ❌ 正面平光（无戏剧感）

---

## 后期处理（Post-Process）

### 后期参数表

| 参数 | 关键词 | 效果 |
|------|--------|------|
| 分辨率 | `8k` / `4K` | 清晰度 |
| 镜头类型 | `IMAX 70mm` / `anamorphic` | 电影感 |
| 胶片颗粒 | `film grain texture` / `cinematic grain` | 真实感 |
| 色深 | `cinematic color grading` | 专业调色 |
| 宽银幕 | `IMAX aspect ratio` | 沉浸感 |
| 光晕 | `lens flare` / `anamorphic lens flare` | 科幻/史诗 |
| 景深 | `shallow depth of field` | 电影感 |

---

## 风格选择决策树

```
用户选择视觉风格时，使用以下决策树：

1. 是古装/仙侠/历史题材吗？
   → YES: ChinesePeriod_Style（传统美学）
   → NO: 继续

2. 是科幻/末世/废土/未来都市题材吗？
   → YES: SciFiWasteland_Style（废土科幻）
   → NO: 继续

3. 是赛博朋克/高科低沉题材吗？
   → YES: cyber（霓虹光效，未来都市）
   → NO: 继续

4. 是恐怖/惊悚/灵异/黑暗心理题材吗？
   → YES: horror（低照度、高反差）
   → NO: 继续

5. 是情绪基调爽感/打脸/逆袭吗？
   → YES: ShortDrama_Style（短剧爽感）
   → NO: 继续

6. 是情感/都市/暧昧/文艺向吗？
   → YES: WongKarwai_Style（情绪港风）
   → NO: 继续

7. 是大场面/史诗/商战/家族对决吗？
   → YES: Villeneuve_Style（史诗科幻）
   → NO: 继续

8. 是日漫/美漫/皮克斯/新海诚/宫崎骏/国风动漫/国风3D/水墨/写实风格吗？
   → YES:
      - 校园青春/热血冒险 → anime
      - 中国风动画/仙侠轻改 → cn_anime
      - 国风史诗/游戏CG → cn_3d
      - 水墨写意/文人意境 → ink
      - 超级英雄/美式动作 → us_comics
      - 真实故事/生活剧情 → real
      - 家庭动画/冒险喜剧 → pixar
      - 唯美青春/风景抒情 → shinkai
      - 奇幻冒险/自然治愈 → miyazaki
   → NO: 默认使用 ShortDrama_Style
```

---

## 与 manzhou-storyboard.md 的集成

### 集成规则

1. 视觉风格在 `manzhou-storyboard.md` 输出分镜时**必须指定**
2. 每个镜头的Seedance/Kling Prompt**末尾**必须附加完整四维度风格锚点
3. 风格预设参数块**不得自行修改**，仅从本库中选择
4. 同一集内**最多混用2种风格**，且必须有明确转场过渡

---

## 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| 2.0.0 | 2026-03-25 | 扩充到16种预设（含5种电影风+11种风格预设），每种有完整描述文本，来源联易方舟 |
| 1.0.0 | 2026-03-24 | 初始版本：5种风格参数包、四维度锚点规范 |
