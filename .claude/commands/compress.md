---
name: compress
description: 手动触发上下文压缩（自动触发无需命令）
---

# /compress

## 功能

手动触发上下文压缩。当前的上下文如果超过 60K tokens，自动压缩中间部分，保留头部（system prompt）和尾部（最近 20K tokens）。

## 使用

```
/compress
```

## 说明

大多数情况下压缩是**自动触发**的，无需手动调用。只有在需要立即释放上下文空间时使用此命令。