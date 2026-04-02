# 漠玫视觉 · 品牌素材库

> 统一管理漠玫品牌视觉资产，包括 Logo、字体和水印。

## 目录说明

| 目录 | 内容 | 说明 |
|------|------|------|
| `logos/` | 品牌 Logo（SVG） | 横向 / 竖向 / 图标三种形态 |
| `fonts/` | 品牌字体文件（.ttf） | 需用户自行下载放置 |
| `watermarks/` | 水印素材（SVG） | 平铺水印模板 |

---

## Logo 使用规范

| 文件 | 形态 | 尺寸比 | 使用场景 |
|------|------|--------|---------|
| `logo-h.svg` | 横向 | 宽 > 高 | 横版海报右下角、详情页页脚 |
| `logo-v.svg` | 竖向 | 高 > 宽 | 竖版海报底部中央 |
| `logo-icon.svg` | 图标 | 1:1 | 小尺寸场景、App Icon、社交媒体头像 |

**颜色规范（漠玫绿）**
- 主色：`#2E7D32`（品牌绿）
- 辅色：`#FDFBF7`（米白）
- 点缀：`#D4A853`（暖金）

**使用注意事项**
- 禁止拉伸、变形、改变配色
- 最小可辨尺寸：横向 80px 宽，竖向 60px 高
- 背景色影响 Logo 可见性时，使用投影或描边增强对比

---

## 字体说明

漠玫视觉使用思源字体（Google Fonts，开源免费）。

| 用途 | 字体 | 字重 | 下载 |
|------|------|------|------|
| 品名 / 大标题 | 思源宋体（Noto Serif SC） | Bold (700) | [Google Fonts](https://fonts.google.com/specimen/Noto+Serif+SC) |
| 正文 / 副标题 | 思源黑体（Noto Sans SC） | Regular (400) | [Google Fonts](https://fonts.google.com/specimen/Noto+Sans+SC) |

**下载后放置：**
```
assets/fonts/
├── NotoSerifSC-Bold.ttf
└── NotoSansSC-Regular.ttf
```

**字体回退链（确保各平台可显示）**
- 思源宋体 Bold：`'Noto Serif SC', 'Source Han Serif SC', 'Source Han Serif CN', serif`
- 思源黑体 Regular：`'Noto Sans SC', 'Source Han Sans SC', 'Source Han Sans CN', sans-serif`

---

## 水印使用规范

### 平铺水印 `watermark-tile.svg`

- **用途**：详情页背景平铺，降低品牌感
- **透明度建议**：5-10%
- **使用方式**：在 CSS/设计工具中将透明度调至 `opacity: 0.07`
- **禁止**：将水印放置在产品主体上遮挡商品

---

## 更新记录

| 日期 | 更新内容 |
|------|---------|
| 2026-04-03 | 初始创建素材库目录结构 |
