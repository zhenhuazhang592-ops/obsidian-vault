# Claude Skills 最佳实践（md2wechat SKILL.md 规范）

> 来源：`/Users/huage/Downloads/md2wechat-skill-main/docs/SKILL-RULE.md`
> 版本：v2.0.5

---

## 核心原则

### 1. 简洁至上

Context window 是公共资源，每个 token 都要物有所值。

**默认假设**：Claude 已经很聪明，只添加它不知道的信息。

**挑战每一段落**：
- "Claude 真的需要这个解释吗？"
- "可以假设 Claude 知道这个吗？"
- "这段内容值得消耗这些 token 吗？"

### 2. 设置适当的自由度

根据任务脆弱性和可变性决定指令的具体程度：

| 自由度 | 适用场景 | 示例 |
|--------|----------|------|
| **高自由度** | 多种有效方法、依赖上下文判断 | 代码审查流程 |
| **中自由度** | 有首选模式、允许变化 | 生成报告（带模板） |
| **低自由度** | 易错、一致性关键、必须按序 | 数据库迁移 |

### 3. 在所有计划使用的模型上测试

| 模型 | 测试重点 |
|------|----------|
| **Haiku** | 是否提供足够指导？ |
| **Sonnet** | 是否清晰高效？ |
| **Opus** | 是否过度解释？ |

---

## Skill 结构

### YAML Frontmatter 要求

```yaml
---
name: max-64-chars, only-lowercase-numbers-hyphens
description: 非空，max-1024字符，说明做什么+何时使用
---
```

**name 字段规则**：
- 最多 64 字符
- 只能包含小写字母、数字、连字符
- 不能包含 XML 标签
- 禁用保留词: "anthropic", "claude"

**description 字段规则**：
- 必须非空
- 最多 1024 字符
- 不能包含 XML 标签
- **必须用第三人称**

---

## 命名约定

推荐使用 **动名词形式 (gerund form)**：

| 推荐 | 可接受 | 避免 |
|------|--------|------|
| `processing-pdfs` | `pdf-processing` | `helper`, `utils` |
| `analyzing-spreadsheets` | `spreadsheet-analysis` | `documents`, `data` |
| `managing-databases` | `process-pdfs` | `tools`, `files` |

---

## 描述写作技巧

**始终用第三人称**：
- ✅ `"Processes Excel files and generates reports"`
- ❌ `"I can help you process Excel files"`
- ❌ `"You can use this to process Excel files"`

**具体且包含关键术语**：
- ✅ `"Extracts text from PDFs using pdfplumber"`
- ❌ `"Helps you extract text"`

---

## md2wechat Skill 文件位置

| 平台 | 路径 |
|------|------|
| Claude Code / Codex / OpenCode | `skills/md2wechat/SKILL.md` |
| OpenClaw / ClawHub | `platforms/openclaw/md2wechat/SKILL.md` |

---

## 质量门控

新增图片 prompt 后必须执行：

```bash
gofmt -l .
GOCACHE=/tmp/md2wechat-go-build go test ./internal/promptcatalog ./cmd/md2wechat
GOCACHE=/tmp/md2wechat-go-build go test ./...
```

**必须校准高信号入口**：
- `README.md`
- `docs/DISCOVERY.md`
- `docs/FAQ.md`
- `skills/md2wechat/SKILL.md`
- `platforms/openclaw/md2wechat/SKILL.md`

---

## 防漂移原则

- 如果漏了主用途、默认比例、来源字段，测试应直接拦住
- 如果新增了高频 preset，但两套 skill 没同步，这次任务不能算完成
- 用户、Agent、CLI 三个层面的说法必须一致
