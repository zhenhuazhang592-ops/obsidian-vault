# 目录隔离原则

> 来源：learn-claude-code s12 Worktree Isolation
> 目的：并行工作用 worktree，任务 ID 绑定目录，上下文不污染

## 规则

1. **并行工作用 worktree**
   - 多集并行开发、实验性改写、资产并行生成 → 各占一个 worktree
   - `git worktree add -b wt/<name> .worktrees/<name> HEAD`

2. **工作树命名规范**
   ```
   .worktrees/
   ├── ep01-script/      # EP01 剧本开发
   ├── ep02-storyboard/  # EP02 分镜开发
   └── assets-gen/       # 资产并行生成
   ```

3. **任务 ID 绑定目录**
   - 任务 JSON 中记录 worktree 名称
   - 切换 worktree = 切换任务上下文
   - 合并回主分支前必须完成任务

4. **事件流可审计**
   - 关键操作写入 `.worktrees/events.jsonl`
   - 格式：`{"event": "worktree.create.after", "task_id": 1, "worktree": "ep01-script", "ts": "..."}`

## 违反处理

发现多任务共享同一目录导致冲突 → 建议拆 worktree。
