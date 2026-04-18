# Phase 05：HTML排版 + 浏览器预览

## 执行条件

- Phase 03（正文写作）已完成
- Phase 04（配图）已完成或用户跳过

## 公众号图片规范（必须遵守）

| 图片类型 | 尺寸规格 | 纵横比 | 用途 |
|---------|---------|-------|------|
| 封面图 | 900 × 383 px | **2.35:1** | 公众号封面（生成时指定 `--ar 2.35:1`） |
| 封面图宽图版 | 900 × 383 px | **2.35:1** | 文章顶部横幅 |
| 文章配图 | 宽度 608 px（高度 810 px） | **3:4** | 内文插图（生成时指定 `--ar 3:4`） |

> ⚠️ 旧版 16:9 图片不符合公众号规范，必须使用 3:4 竖版。

## 执行步骤

### Step 7.0：选择排版主题（必须先执行）

**在生成 HTML 之前必须询问用户主题偏好：**

```
排版主题选项（4选1）：
1. modern（现代）⭐ 推荐 — 大圆角、药丸形标题、宽松行距
2. simple（简洁）— 现代极简风，不对称圆角，清爽留白
3. grace（优雅）— 文字阴影，圆角卡片，精致引用块
4. default（经典）— 传统排版，标题居中带底边

请选择一个主题（如不选，默认 modern）：
```

用户选择后记录主题名称，进入下一步。

---

### Step 7.1：复制图片到 HTML 输出目录

```bash
OUTPUT_DIR="/Users/huage/Obsidian Vault/写作知识库/01-资源库/[YYYY-MM-DD]/[slug]"
HTML_DIR="${OUTPUT_DIR}/08-排版预览"
PREVIEW_DIR="${HTML_DIR}/preview"

mkdir -p "$PREVIEW_DIR/imgs"

# 封面图（公众号标准 2.35:1）
cp "${OUTPUT_DIR}/06-封面图/cover-wx.png" "$PREVIEW_DIR/imgs/cover.png"

# 文章配图（公众号标准 3:4 竖版）
cp "${OUTPUT_DIR}/07-配图/img-01.png" "$PREVIEW_DIR/imgs/"
cp "${OUTPUT_DIR}/07-配图/img-02.png" "$PREVIEW_DIR/imgs/"
cp "${OUTPUT_DIR}/07-配图/img-03.png" "$PREVIEW_DIR/imgs/"
cp "${OUTPUT_DIR}/07-配图/img-04.png" "$PREVIEW_DIR/imgs/"
cp "${OUTPUT_DIR}/07-配图/img-05.png" "$PREVIEW_DIR/imgs/"
cp "${OUTPUT_DIR}/07-配图/img-06.png" "$PREVIEW_DIR/imgs/"
```

---

### Step 7.2：Markdown 转 HTML（使用选定主题）

使用 `baoyu-markdown-to-html`，`--theme` 参数使用用户在 Step 7.0 选中的主题：

```bash
SKILL_DIR="/Users/huage/Obsidian Vault/.claude/skills/baoyu-markdown-to-html"
npx -y bun ${SKILL_DIR}/scripts/main.ts \
  "${OUTPUT_DIR}/05-正文.md" \
  --theme [选定主题] \
  --color blue \
  --output "$PREVIEW_DIR"
```

---

### Step 7.3：浏览器预览

```bash
open "${PREVIEW_DIR}/index.html"
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
6. 发布后执行文章回流（Step 7.6）

---
🎉 文章创作完成！祝阅读量高高！
```

---

### Step 7.6：文章回流到 Wiki（新增）

**目标**：将完成的文章摄入 wiki，实现知识复利。

**触发时机**：
- 用户确认文章已发布
- 或用户主动要求回流

**执行步骤**：

#### 7.6.1 读取文章正文和缺口分析

```bash
# 读取文章正文
ARTICLE="${OUTPUT_DIR}/05-正文.md"

# 读取缺口分析（如果有）
GAP_ANALYSIS="${OUTPUT_DIR}/00-缺口分析.md"
```

#### 7.6.2 将文章摄入 wiki

调用 `/wiki-ingest` 将文章作为新来源摄入：

```bash
/wiki-ingest "${OUTPUT_DIR}/05-正文.md"
```

**摄入时处理**：
- 创建来源页：`wiki/sources/[YYYY-MM-DD]-[slug].md`
- 提取实体：文章中提及的人物/公司/产品
- 提取概念：文章中讨论的方法/理论
- 更新 index.md 和 log.md

#### 7.6.3 补充新发现到 wiki

如果 Step 1.5（缺口分析）识别了 wiki 中没有的新知识：

```
缺口分析中的"新发现"：
- [新发现1] — 需要创建/更新对应概念页
- [新发现2] — 需要创建/更新对应实体页
```

**执行**：
1. 读取 `00-缺口分析.md` 中的"新发现"列表
2. 对每个新发现：
   - 如是概念 → 调用 `/wiki-ingest` 或手动创建 `wiki/concepts/[ConceptName].md`
   - 如是实体 → 创建 `wiki/entities/[EntityName].md`
3. 告知用户新增了哪些 wiki 页面

#### 7.6.4 回流完成报告

```
## Wiki 回流完成

**来源页**：wiki/sources/[YYYY-MM-DD]-[slug].md ✅
**新增概念**：[Concept1], [Concept2]（如有）
**新增实体**：[Entity1]（如有）
**更新页面**：[已更新的关联页面]

### 知识复利效应

下次创作相关主题时：
1. /wiki-query [相关主题] 会自动找到这篇文章
2. 可复用文章中的观点、数据、引用
3. 避免重复研究，越写越快

---
📚 知识库已更新，写作能力持续进化！
```

---

## 输出

- `[输出目录]/08-排版预览/index.html`
- 浏览器已打开预览
- 完整产出报告

## 下一步

全部完成。如需调整，修改对应文件后重新执行相关 Phase。
