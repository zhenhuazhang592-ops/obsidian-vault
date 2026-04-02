# md2wechat README 归档

> 来源：`/Users/huage/Downloads/md2wechat-skill-main/README.md`
> 版本：v2.0.5

---

## 项目定位

**一句话理解**：用 Markdown 写文章 → 一键转换 → 自动发到微信草稿箱

## 适合用户

| 用户类型 | 痛点 | md2wechat 解决方案 |
|----------|------|-------------------|
| 内容创作者 | 微信编辑器太难用，排版花时间 | Markdown 写作，自动排版 |
| 产品经理 | 要发公告，但不会 HTML | 不用学代码，一行命令搞定 |
| 程序员 | 习惯 Markdown，讨厌微信编辑器 | 保持你的写作习惯 |
| AI 用户 | 用 AI 生成内容，但要手动复制粘贴 | AI 生成 → 微信草稿，无缝衔接 |

## 站点入口

- **国际站**: [md2wechat.com](https://www.md2wechat.com/)
- **国内站 / API 主站**: [md2wechat.cn](https://md2wechat.cn)
- **GitHub 项目**: [geekjourneyx/md2wechat-skill](https://github.com/geekjourneyx/md2wechat-skill)

---

## 五大核心功能

| 功能 | 命令 | 说明 | 适合谁 |
|------|------|------|--------|
| **Markdown 转换** | `convert` | 将 Markdown 转换为微信格式 HTML | 所有用户 |
| **风格写作** | `write` | 用创作者风格辅助写作，自动生成文章和封面提示词 | 写作小白、内容创作者 |
| **AI 去痕** | `humanize` | 去除 AI 生成痕迹，让文章听起来更自然、像人写的 | AI 写作用户 |
| **小绿书** | `create_image_post` | 创建图片消息（小绿书），最多 20 张图片 | 图片内容创作者 |
| **草稿推送** | `convert --draft` | 一键发送到微信草稿箱 | 需要频繁发布的用户 |

---

## 两种转换模式

| 模式 | 适合谁 | 特点 | 样式 |
|------|--------|------|------|
| **API 模式** | 追求稳定、快速 | 调用 md2wechat.cn API，秒级响应 | 简洁专业 |
| **AI 模式** | 追求精美排版 | 生成 AI request / prompt，样式更丰富 | 秋日暖光 / 春日清新 / 深海静谧 |

---

## 写作风格

当前内置风格：

| 风格 | 特点 | 适合内容 |
|------|------|----------|
| **Dan Koe** | 深刻但不晦涩，犀利但不刻薄，有哲学深度但接地气 | 个人成长、观点文章、评论 |

**自定义风格**：在 `writers/` 目录下创建 YAML 文件即可。

---

## Prompt Catalog

当前内置 prompt kind：

- `humanizer` - AI 去痕模板
- `refine` - 润色模板
- `image` - 图片生成模板（封面图、信息图、配图）

**覆盖顺序**：
1. `MD2WECHAT_PROMPTS_DIR`
2. `./prompts`
3. `~/.config/md2wechat/prompts`
4. 内置 prompt 资产

---

## 完整工作流程

```
┌─────────────────────────────────────────────────────────────────────┐
│                     阶段1：创作                                      │
│  你的想法 → 选择写作风格 → AI 生成文章 → 生成封面提示词               │
└─────────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│                     阶段2：制作                                      │
│  AI 生成封面图 → 上传到微信素材库 → 保存为 Markdown                   │
└─────────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│                     阶段3：发布                                      │
│  转换为微信格式 → 发送到草稿箱 → 在微信编辑器微调 → 发布！           │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 基础命令

```bash
# 先检查最终标题/摘要/发布风险
md2wechat inspect article.md

# 生成本地预览 HTML
md2wechat preview article.md

# 预览转换效果（不发送）
md2wechat convert article.md --preview

# 转换并保存为 HTML 文件
md2wechat convert article.md -o output.html

# 使用 AI 模式生成精美排版
md2wechat convert article.md --mode ai --theme autumn-warm --preview

# 发送到草稿箱
md2wechat convert article.md --draft --cover cover.jpg
```

---

## 文章元数据优先级

**标题**：`--title` → `frontmatter.title` → 正文首个 Markdown 标题 → `未命名文章`

**作者**：`--author` → `frontmatter.author`

**摘要**：`--digest` → `frontmatter.digest` → `frontmatter.summary` → `frontmatter.description`

**长度限制**：
- 标题：最多 32 个字符
- 作者：最多 16 个字符
- 摘要：最多 128 个字符
