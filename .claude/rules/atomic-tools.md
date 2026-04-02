# 工具原子化原则

> 来源：learn-claude-code s02 Tool Use
> 目的：每个工具做一件事，通过组合生成复杂行为

## 规则

1. **工具职责单一**
   - Read = 读文件
   - Write = 写文件（覆盖）
   - Edit = 精确替换
   - Glob = 找文件
   - Grep = 搜内容
   - Bash = 系统命令
   - Agent = 子代理

2. **不发明组合工具**
   - 不用 `read_and_edit`、`batch_write` 这类打包操作
   - 复杂行为靠 Agent 工具编排，而非新工具

3. **危险命令拦截**
   - `rm -rf`、`git reset --hard`、`--force push` 等高危操作 → 先确认用户
   - 不跳过 hooks 或 gpg 签名验证

## 违反处理

发现发明新组合工具 → 用现有原子工具重写。
