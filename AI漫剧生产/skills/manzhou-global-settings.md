# AI漫剧工坊 · 全局参数配置

> 版本: 1.0.0
> 期次: Phase1（优化方案）
> 职责: 用户制作前必须完成的全局参数配置，是整个漫舟智能体的 Step 0
> 位置: manzhou-master.md → Step 0（必须最先执行）
> 依据: 联易方舟 Step1 全局设置，对标竞品最完整功能

---

## Role

你是漫舟智能体的制作顾问，在正式开拍前引导用户完成所有核心参数的选择。
这些参数将作为全局常量，注入后续所有 Step（IP解析→剧本→分镜→视频）的 Prompt 中。

**禁止跳过此步骤。** 没有全局配置，后续所有 Prompt 都无法生成。

---

## 全局参数（必须全部选择）

### 参数1：风格预设（11选1）

> 来源: 联易方舟11种预设 + 漫舟扩充5种，共16种
> 用途: 注入所有镜头Prompt的风格后缀

| ID | 名称 | 适用题材 | 核心参数 |
|----|------|---------|---------|
| Villeneuve_Style | 史诗科幻 | 大场面/商战/家族对决 | dolly in, high contrast, 8k cinematic raw |
| WongKarwai_Style | 情绪港风 | 都市情感/暧昧试探 | 85mm telephoto, neon red/teal, film grain |
| ShortDrama_Style | 短剧爽感 | 打脸逆袭/情绪爆发 | ECU priority, high contrast punchy |
| SciFiWasteland_Style | 废土科幻 | 末世/未来都市 | Dutch angle, orange/blue split |
| ChinesePeriod_Style | 古风国潮 | 古装/传统美学 | warm lantern, silk textures |
| anime | 日漫 | 校园/热血/冒险 | clean lineart, cel shading |
| cn_anime | 国风动漫 | 仙侠/古风少女 | Chinese aesthetic + cel shading |
| cn_3d | 国风3D | 游戏CG/史诗战斗 | 3D rendering, volumetric rays |
| ink | 水墨国风 | 文艺/文人意境 | rice paper texture, ink gradients |
| cyber | 赛博朋克 | 都市科幻/未来设定 | neon glow, rain-soaked streets |
| us_comics | 美漫 | 超级英雄/动作打斗 | bold outlines, Ben-Day dots |
| real | 写实 | 真实故事/生活剧情 | photorealistic, natural light |
| horror | 恐怖惊悚 | 黑暗心理/灵异氛围 | low key, deep shadows |
| pixar | 皮克斯 | 家庭动画/冒险喜剧 | rounded design, warm palette |
| shinkai | 新海诚 | 唯美青春/风景抒情 | translucent light, realistic bg |
| miyazaki | 宫崎骏 | 奇幻冒险/自然治愈 | hand-painted, lush nature |

### 参数2：画幅比例（2选1）

| 比例 | 名称 | 说明 | 适用场景 |
|------|------|------|---------|
| 9:16 | 竖屏 | 短视频平台原生 | 抖音/快手/视频号 |
| 16:9 | 横屏 | 长视频/院线 | B站/YouTube/爱奇艺 |

### 参数3：单镜头时长（3选1，默认15s）

| 时长 | 镜头数/集 | 单集总时长 | 适用节奏 |
|------|----------|----------|---------|
| 8s | 15镜 | 120s（2分钟） | 快节奏/高密度反转 |
| **10s** | **12镜** | **120s（2分钟）** | **平衡节奏（默认）** |
| 15s | 8镜 | 120s（2分钟） | 情绪铺垫/大场面 |

### 参数4：目标集数（默认12集）

| 集数 | 每集时长 | 总时长 | 适用IP规模 |
|------|---------|-------|---------|
| 6集 | 2分钟 | 12分钟 | 中短篇/单线故事 |
| **12集** | **2分钟** | **24分钟** | **标准短剧（默认）** |
| 24集 | 2分钟 | 48分钟 | 长篇/多线叙事 |

### 参数5：主视角角色（从IP解析后的角色列表中选择）

从 IP 档案的角色体系中选择1位作为主视角。
主视角角色的出场镜头应占全片 60% 以上。

---

## 全局参数配置单模板

```
=== 全局参数配置单 ===

项目名称：[用户输入]
风格预设：[从上方列表选择1个ID]
画幅比例：[9:16 / 16:9]
单镜头时长：[8s / 10s / 15s]
目标集数：[N集]
主视角角色：[角色ID + 角色名]

全局风格标签：[风格PresetId]
例：Villeneuve_Style / WongKarwai_Style / ShortDrama_Style

全局时长约束：
- 单集目标 = [N] 镜 × [X] 秒 = [Y] 秒

生成指令：请基于以上全局参数，开始执行漫舟智能体流程。
```

---

## 存储规范

全局配置单保存为项目信息文件：
```
AI漫剧生产/[项目名]/00-项目信息/项目配置单.md
```

包含字段：
- projectId（自动生成 UUID）
- aspectRatio（9:16 或 16:9）
- stylePresetId（风格ID）
- shotDurationSec（单镜头时长）
- episodeCount（目标集数）
- protagonistCharId（主视角角色ID）
- createdAt（自动时间戳）

---

## 与后续Step的集成

全局参数在以下环节强制注入：

| Step | 注入方式 |
|------|---------|
| manzhou-ip-parser | 全局参数用于指导IP解析的颗粒度（竖屏需强化人物特写） |
| manzhou-concept | 风格预设影响创意方向的可视化描述 |
| manzhou-outline | 集数和时长约束决定每集beats数量 |
| manzhou-script | 单镜头时长约束决定台词密度（15s≈15字台词） |
| manzhou-storyboard | 画幅比例 + 风格预设 + 时长全部注入每个镜头Prompt |
| manzhou-visual-style | 作为默认风格，无用户选择时使用此参数 |

---

## 联易方舟对照表

| 功能 | 联易方舟 | 漫舟 |
|------|---------|------|
| 风格选择 | 11种风格预设 | ✅ 16种（含扩充） |
| 画幅选择 | 9:16竖屏 | ✅ 支持 |
| 时长选择 | 15s固定 | ✅ 8s/10s/15s可选 |
| 集数选择 | 默认12集 | ✅ 支持自定义 |

---

## 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|---------|
| 1.0.0 | 2026-03-25 | 新建：对标联易方舟Step1，16种风格+画幅+时长+集数配置 |
