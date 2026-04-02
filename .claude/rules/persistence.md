# 状态持久化原则

> 来源：learn-claude-code s07 Task System
> 目的：任务状态跨会话存活，不依赖内存

## 规则

1. **任务状态必须落在磁盘上，不在内存里**
   - MEMORY.md = 当前会话仪表盘（内存）
   - `.tasks/` = 持久化任务图（磁盘）
   - 每次任务完成 → 同时更新 MEMORY.md 仪表盘 + .tasks/ JSON

2. **大目标拆成任务 JSON，而非 TODO 列表**
   - 格式：`{"id": 1, "subject": "...", "status": "in_progress", "blockedBy": [], "owner": ""}`
   - 任务之间用 `blockedBy` 表达依赖
   - 任务完成自动解锁依赖者

3. **长目标中途断档时，从 .tasks/ 恢复，不重新规划**

## 违反处理

发现违反 → 在 MEMORY.md 仪表盘"阻塞点"记录，等用户确认后修正。
