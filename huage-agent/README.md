# huage Agent

专注文章创作的独立 Agent，基于 Claude Agent SDK + Dan Koe 五阶段写作方法论。

## 安装

```bash
npm install
npm run build
```

## 使用

```bash
# 开始一篇文章
huage-agent write "我想写一篇关于时间管理的文章"

# 查询 wiki
huage-agent wiki query "知识管理"

# 健康检查
huage-agent wiki lint
```

## 工作流

1. 深度研究（Tavily + YouTube）
2. Dan Koe 五阶段（选题→观点→大纲→正文→润色）
3. SEO/GEO 优化
4. 配图 + HTML + wiki回流
