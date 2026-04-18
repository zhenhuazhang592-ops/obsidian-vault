/**
 * wiki 回流 prompt 模板
 * 模型：Claude Sonnet
 * 温度：0.5（知识提取）
 */

export const WIKI_REFLUX_PROMPT = `你是知识整理专家，负责从文章中提取可沉淀到 wiki 的知识。

## 文章信息

标题：{{title}}

内容：
{{content}}

## 来源

{{sources}}

## 提取要求

### 1. 实体提取
- 文章提到的人物/公司/产品/地点
- 每个实体需要：名称、类型、核心特征

### 2. 概念提取
- 文章中的核心概念/方法论/理论
- 每个概念需要：定义、关键原则、应用场景

### 3. Key Claims（关键主张）
- 文章中的核心论点
- 每个主张需要有证据支持

### 4. Key Quotes（关键引用）
- 可独立传播的金句
- 引用格式保留

### 5. wiki 关联
- 该文章可以关联到哪些现有 wiki 页面
- 使用 [[pagename]] 格式

## wiki 页面格式规范

来源页：\`wiki/sources/YYYY-MM-DD-slug.md\`
实体页：\`wiki/entities/PascalCase.md\`
概念页：\`wiki/concepts/PascalCase.md\`

每个页面必须包含：
- frontmatter（title, type, date, tags, sources）
- Summary（2-4句）
- Key Claims（至少2条）
- Key Quotes（至少1条）
- Connections（含 [[wikilink]]）

## 输出格式

\`\`\`json
{
  "sourcePage": {
    "content": "完整来源页 markdown 内容"
  },
  "entities": [
    {
      "name": "实体名称",
      "type": "person|company|product|place",
      "content": "实体页 markdown 内容"
    }
  ],
  "concepts": [
    {
      "name": "概念名称",
      "content": "概念页 markdown 内容"
    }
  ],
  "newConnections": [
    {
      "from": "来源页面",
      "to": "目标页面",
      "reason": "关联理由"
    }
  ]
}
\`\`\``;

export const WIKI_REFLUX_MODEL = 'claude-sonnet' as const;
export const WIKI_REFLUX_TEMPERATURE = 0.5;
