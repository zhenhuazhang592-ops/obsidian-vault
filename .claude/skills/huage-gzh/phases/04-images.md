# Phase 04：配图方案 + 生成

## 执行条件

- Phase 03（正文写作）已完成
- `[输出目录]/05-正文.md` 存在

## 执行步骤

### Step 6.1：规划配图方案

调用 Qwen3-Max 根据正文内容规划配图：

```bash
python3 /Users/huage/Obsidian\ Vault/.claude/skills/huage-gzh/scripts/qwen_client.py \
  plan_image_scheme \
  "$(cat [输出目录]/05-正文.md)" \
  "[topic]"
```

输出格式：

```
## 封面图

- 类型：[类型]
- 风格：[风格]
- 配色：[关键词]
- 画面描述：[50字描述]
- 尺寸：900x500px

## 文章配图（共N张）

### 配图1：[位置]
- 类型：[类型]
- 风格：[风格]
- 画面描述：[30字]
```

### Step 6.2：展示配图方案（用户确认）

```
## 配图方案

### 封面图
- 类型：[类型]
- 风格：[风格]
- 画面描述：[描述]
- 生成模型：Doubao-Seedream-4.5

### 文章配图（共N张）

| 编号 | 位置 | 类型 | 风格 | 描述 |
|------|------|------|------|------|
| 01 | H2论点1后 | 信息图 | 写实 | [描述] |
| 02 | H2论点2后 | 场景图 | 插画 | [描述] |
| ... | ... | ... | ... | ... |

确认这个方案吗？确认后开始生成图片。
（图片生成预计需要 2-5 分钟）
```

### Step 6.3：用户确认后生成图片

**封面生成**：`baoyu-cover-image`

```bash
# 封面图生成
/baoyu-cover-image [输出目录]/05-正文.md \
  --type [类型] \
  --palette [配色] \
  --aspect 16:9 \
  --output [输出目录]/06-封面图/cover.png
```

**配图生成**：`baoyu-article-illustrator`

```bash
# 配图生成（每张配图）
# 参考 phases/04-images-images.md 的提示词生成流程
# 调用 Doubao-Seedream-4.5 后端
/baoyu-article-illustrator [输出目录]/05-正文.md \
  --type [类型] \
  --style [风格] \
  --backend doubao-seedream-4.5 \
  --output [输出目录]/07-配图/
```

**Doubao-Seedream-4.5 提示词要求**：
- 必须翻译为英文
- 包含画面描述 + 风格关键词 + 技术参数
- 示例：
```英文
A split-screen comparison of ripe and unripe avocados on a wooden
cutting board, soft morning light, photorealistic style, shallow
depth of field, warm tones, 16:9 aspect ratio, no text.
```

### Step 6.4：下载并保存图片

- 图片下载到：`[输出目录]/06-封面图/` 和 `[输出目录]/07-配图/`
- 更新 `05-正文.md` 中的图片占位符为实际文件路径

### Step 6.5：更新正文中的图片路径

编辑 `[输出目录]/05-正文.md`，将占位符替换为实际图片路径：

```
# 替换前
![配图描述](图片文件路径)

# 替换后
![配图描述](../07-配图/01-type-slug.png)
```

## 错误处理

| 场景 | 处理 |
|------|------|
| Doubao-Seedream-4.5 失败 | 回退到 baoyu-image-gen 其他后端（OpenAI DALL-E / Google Imagen），告知用户后端切换 |
| 图片生成超时 | 告知用户，询问是否继续等待或使用其他后端 |
| 用户取消 | 停在当前步骤，跳过图片生成，进入 Phase 05 |

## 下一步

配图完成（或跳过） → 进入 Phase 05：`phases/05-output.md`（HTML排版预览）
