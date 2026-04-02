# 任务图驱动原则

> 来源：learn-claude-code s07 Task System
> 目的：大目标拆成任务图，依赖清晰，进度可追踪

## 规则

1. **大目标必须拆成任务图**
   - 不写"TODO：完成 XX 项目"
   - 写：`季任务 → 集任务 → 场景任务`，带依赖关系

2. **任务 JSON 字段规范**
   ```json
   {
     "id": 1,
     "subject": "写 EP01 剧本初稿",
     "description": "详细描述（可选）",
     "status": "pending|in_progress|completed",
     "blockedBy": [],
     "owner": "agent|human"
   }
   ```

3. **MEMORY.md 仪表盘 = 任务图的可读视图**
   - 每次会话：读 MEMORY.md → 从 .tasks/ 加载当前任务
   - 每次完成：更新 MEMORY.md + .tasks/ JSON

4. **并行任务识别**
   - `blockedBy: []` 的任务可以并行
   - 主动识别并行机会，不串行执行

## 违反处理

发现单条 TODO 超过 3 个子步骤 → 拆成任务 JSON。
