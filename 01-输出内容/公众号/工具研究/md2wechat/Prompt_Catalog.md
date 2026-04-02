# md2wechat Prompt Catalog

> 版本：v2.0.5

---

## 概念

Prompt Catalog 用于承载可配置的提示词模板，支持用户覆盖和平台定制。

**设计原则**：不要把长 prompt 直接写进 Go 代码，优先落到 YAML 资产。

---

## 当前内置 prompt kind

| kind | 用途 |
|------|------|
| `humanizer` | AI 去痕模板 |
| `refine` | 润色模板 |
| `image` | 图片生成模板（封面图、信息图、配图） |

---

## prompt 覆盖顺序

```
1. MD2WECHAT_PROMPTS_DIR（环境变量）
2. ./prompts（当前目录）
3. ~/.config/md2wechat/prompts（用户配置）
4. 内置 prompt 资产
```

**含义**：纯二进制安装也能用默认 prompt，而用户和平台仍然可以覆盖。

---

## 图片 prompt

### 底层统一分类

图片 prompt 的底层统一归类为 `kind=image`。`cover` 和 `infographic` 是主要用途分组，不是两套独立系统。

### 判断能否兼用

优先看 `prompts show --json` 返回的：
- `primary_use_case`
- `compatible_use_cases`
- `recommended_aspect_ratios`
- `default_aspect_ratio`

---

## 发现命令

```bash
# 查看所有 prompt
md2wechat prompts list --json

# 查看图片 prompt
md2wechat prompts list --kind image --json

# 查看封面类 prompt
md2wechat prompts list --kind image --archetype cover --json

# 查看具体 prompt 详情
md2wechat prompts show cover-default --kind image --json
md2wechat prompts show cover-hero --kind image --archetype cover --tag hero --json
md2wechat prompts show infographic-victorian-engraving-banner --kind image --archetype infographic --tag victorian --json

# 渲染 prompt（替换变量）
md2wechat prompts render cover-default \
  --kind image \
  --var article_title='从 0 到 1 做好公众号封面' \
  --var article_summary='一份关于封面图策略的实战清单' \
  --json
```

---

## 新增图片 prompt 要求

**最小字段要求**：
- `name`
- `kind: image`
- `description`
- `version`
- `archetype`
- `primary_use_case`
- `recommended_aspect_ratios`
- `default_aspect_ratio`
- `metadata.author`
- `metadata.provenance`
- `template`

**按需补充**：
- `compatible_use_cases`
- `tags`
- `examples`
- `metadata.inspired_by`

**结构约束**：
- `default_aspect_ratio` 必须包含在 `recommended_aspect_ratios` 中
- 如果 prompt 可兼作封面/信息图，必须显式写 `compatible_use_cases`

---

## 新增 prompt 后必须执行

1. `gofmt -l .`
2. `GOCACHE=/tmp/md2wechat-go-build go test ./internal/promptcatalog ./cmd/md2wechat`
3. `GOCACHE=/tmp/md2wechat-go-build go test ./...`
4. 必须校准高信号入口：
   - `README.md`
   - `docs/DISCOVERY.md`
   - `docs/FAQ.md`
   - `skills/md2wechat/SKILL.md`
   - `platforms/openclaw/md2wechat/SKILL.md`
