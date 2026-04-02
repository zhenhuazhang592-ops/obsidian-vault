---
name: mo-mei-visual
description: 漠玫视觉 · 生鲜电商视觉资产生产 Agent。用户上传实拍图，一键产出全平台主图、详情页、海报。触发词：做主图、生成电商图、漠玫视觉。
---

# 漠玫视觉 MoMei Visual Agent

## 快速开始

### 输入格式

**方式一：自然语言**
```
上传实拍图 + 产品信息：
- 品名：墨西哥哈斯牛油果
- 品类：牛油果
- 产地：墨西哥米却肯州
- 核心卖点：奶油般绵密口感，油脂含量高达20%
- 规格：1kg / 2kg
- 价格：68-128元
```

**方式二：JSON**
```json
{
  "品名": "墨西哥哈斯牛油果",
  "品类": "avocado",
  "产地": "墨西哥米却肯州",
  "核心卖点": "奶油般绵密口感，油脂含量高达20%",
  "规格": "1kg / 2kg",
  "价格": "68-128元"
}
```

### 执行流程

```
Step 1: 品类分析
  · 读取 prompts/product-analysis.md
  · 调用 Qwen3-Max 分析品类和风格推荐
  · 输出：品类标签 + 场景关键词

Step 2: 场景合成
  · 读取对应场景 prompt（prompts/scene-*.md）
  · 调用 baoyu-image-gen（--provider doubao --ref <实拍图>）
  · 4 种场景各生成 1 张

Step 3: 智能裁切（✅ Phase 1）
  · 调用 scripts/smart-crop.ts
  · 基础图 → 全平台 7 种尺寸

Step 4: 海报合成（📅 Phase 2）
  · 调用 scripts/poster-compose.ts
  · 输出：横版 + 竖版

Step 5: 详情页文案 + HTML（📅 Phase 2）
  · 读取 prompts/detail-copy.md
  · 调用 Qwen3-Max 生成详情页内容
  · 调用 baoyu-markdown-to-html 输出 HTML
```

### 输出目录

```
output/<slug>/
├── main-taobao-1:1.png      # 淘宝 800×800
├── main-taobao-3:4.png      # 淘宝 800×1066
├── main-jd-1:1.png          # 京东 800×800
├── main-pdd-1:1.png         # 拼多多 800×800
├── main-pdd-3:4.png         # 拼多多 800×1200
├── main-douyin-3:4.png      # 抖音 800×1066
├── main-douyin-9:16.png    # 抖音 1080×1920
├── poster-h.png             # 横版海报 1920×800（📅 Phase 2）
├── poster-v.png             # 竖版海报 1080×1920（📅 Phase 2）
└── index.html               # 详情页（📅 Phase 2）
```

## Prompt 文件

| 文件 | 用途 |
|------|------|
| `prompts/scene-minimal.md` | 极简净色场景 |
| `prompts/scene-origin.md` | 原产地场景 |
| `prompts/scene-lifestyle.md` | 生活场景代入 |
| `prompts/scene-daoju.md` | 极简+精致道具场景 |
| `prompts/product-analysis.md` | 品类分析与风格推荐 |
| `prompts/detail-copy.md` | 详情页文案生成 |
| `prompts/poster-overlay.md` | 海报合成 prompt |

## 脚本

| 脚本 | 用途 | 状态 |
|------|------|------|
| `scripts/smart-crop.ts` | 智能裁切（Sharp） | ✅ Phase 1 |
| `scripts/poster-compose.ts` | 海报合成（Sharp） | 📅 Phase 2 |

## 参考文档

| 文件 | 内容 |
|------|------|
| `references/brand-colors.md` | 品牌色彩规范 |
| `references/platform-specs.md` | 全平台尺寸规格 |
| `references/style-guide.md` | 场景风格详细说明 |
