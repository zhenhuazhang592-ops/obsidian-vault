# Phase 05：HTML排版 + 浏览器预览

## 执行条件

- Phase 03（正文写作）已完成
- Phase 04（配图）已完成或用户跳过

## 执行步骤

### Step 7.1：Markdown 转 HTML

使用 `baoyu-markdown-to-html`：

```bash
SKILL_DIR="/Users/huage/Obsidian Vault/.claude/skills/baoyu-markdown-to-html"
npx -y bun ${SKILL_DIR}/scripts/main.ts \
  "[输出目录]/05-正文.md" \
  --theme default \
  --color blue
```

### Step 7.2：选择主题（如果用户有偏好）

询问用户是否需要切换主题：

```
排版主题选项：
1. default（经典）- 传统排版，标题居中带底边，二级标题白字彩底
2. grace（优雅）- 文字阴影，圆角卡片，精致引用块
3. simple（简洁）- 现代极简风，不对称圆角，清爽留白
4. modern（现代）- 大圆角、药丸形标题、宽松行距

默认使用 default。如需切换，请告诉我主题名称。
```

### Step 7.3：复制图片到 HTML 同级目录

```bash
# 复制封面和配图到 HTML 同级 imgs/ 目录
mkdir -p "[HTML输出目录]/imgs"
cp "[输出目录]/06-封面图/cover.png" "[HTML输出目录]/imgs/cover.png"
cp "[输出目录]/07-配图/"*.png "[HTML输出目录]/imgs/" 2>/dev/null || true
```

### Step 7.4：浏览器预览

使用 `open` 命令或 gstack 打开 HTML 预览：

```bash
open "[HTML文件路径].html"
# 或使用 gstack
/browse open "[HTML文件路径].html"
```

### Step 7.5：完成报告

```
## 华哥公众号 · 文章完成

**主题**：[文章标题]
**风格**：[选定风格]
**字数**：[N] 字
**配图**：[封面×1 + 配图×N张]

### 产出文件

- 文章正文：写作知识库/01-资源库/[YYYY-MM-DD]/[slug]/05-正文.md
- 封面图：.../06-封面图/cover.png
- 配图：.../07-配图/
- HTML排版：.../08-排版预览/index.html

### 下一步

1. 打开 index.html 预览效果
2. 如需调整图片或文字，修改后重新生成 HTML
3. 确认无误后，复制 HTML 内容到微信公众号后台编辑器
4. 在公众号后台替换封面图和内文图片
5. 发布！

---
🎉 文章创作完成！祝阅读量高高！
```

## 输出

- `[输出目录]/08-排版预览/index.html`
- 浏览器已打开预览
- 完整产出报告

## 下一步

全部完成。如需调整，修改对应文件后重新执行相关 Phase。
