# 知识按需加载原则

> 来源：learn-claude-code s05 Skill Loading
> 目的：知识不是塞进 system prompt，是模型"问到时"才给

## 规则

1. **两层知识注入**
   - **Layer 1（system prompt）**：只放 skill 名称和一行描述（~100 tokens/skill）
   - **Layer 2（tool_result）**：模型调用 skill 时，返回完整内容

2. **Vault 现有结构等效映射**
   - `.claude/skills/*/SKILL.md` = Skill 知识单元（Layer 2）
   - CLAUDE.md 中 Skills 表格 = Layer 1 metadata
   - `rules/` = 机械执行规则，不需要加载内容，模型直接遵守

3. **不把完整文档塞进每次对话**
   - 长文档用 Glob/Grep 按需读取
   - 不用 `<file_content>` 或长 heredoc 填充 system prompt

## Skill 文件格式

```markdown
# skills/<name>/SKILL.md
---
name: <唯一标识>
description: <一行描述，用于 Layer 1>
tags: optional
---

# 标题

## 主体内容
```

## 违反处理

发现 system prompt 超长 → 指出并拆分，保留 skill 名称列表即可。
