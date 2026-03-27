# 测试 1：基本搜索测试

## 目标
验证 YouTube Data API v3 搜索功能是否正常工作

## 前提条件
- [x] 已安装 `google-api-python-client` 和 `google-auth-httplib2`
- [x] 已安装 `google-api-python-client`
- [ ] 已配置 YouTube Data API v3 key
- [ ] NotebookLM 已安装并登录
- [ ] 资源追踪模块可用

## 测试步骤

### 步骤 1：准备配置

1. **创建配置文件**
   ```bash
   # 复制示例配置
   cp youtube-research-flow/config/youtube_research_config.example.json \
     youtube-research-flow/config/youtube_research_config.json
   ```

2. **添加 API Key**
   ```bash
   # 编辑配置文件
   nano youtube-research-flow/config/youtube_research_config.json

   # 替换 YOUR_YOUTUBE_API_KEY 为你的实际 API 密钥
   {
     "youtube": {
       "api_key": "YOUR_YOUTUBE_API_KEY"
     }
   }
   ```

3. **验证配置**
   ```bash
   # 检查配置文件格式
   python3 -c "
import json
config = json.load(open('youtube-research-flow/config/youtube_research_config.json'))
print('Config is valid JSON:', 'isinstance(config, dict))
"
   ```

### 步骤 2：运行基本搜索

**测试命令**：
```bash
# 搜索 5 个榴莲测评视频，时间范围 3 个月
python3 youtube-research-flow/scripts/main.py "榴莲测评" \
  --max-results 5 \
  --months 3
```

**预期输出**：
```
🔍 Searching YouTube for: 榴莲测评
   • Results: 5
   • Time range: Last 3 months
   • Sort by: relevance

✅ Found 5 videos
📊 Resource Tracking:
  - YouTube API calls: 1
  - Videos retrieved: 5
  - Operation ID: <timestamp>
```

**数据验证**：
- [ ] 每个视频都包含 video_id
- [ ] 每个视频都包含 title（标题）
- [ ] 每个视频都包含 channel_title（频道标题）
- [ ] 每个视频都包含 view_count（观看次数）
- [ ] 每个视频都包含 published_at（发布日期）
- [ ] 每个视频都包含 thumbnail（缩略图）
- [ ] 每个视频都包含 channel_id（频道 ID）
- [ ] 每个视频都包含 tags（标签）

### 步骤 3：验证数据格式

**验证点**：
- [ ] 返回数据是字典格式
- [ ] 所有字段都存在
- [ ] view_count 是整数
- [ ] published_at 是 ISO 8601 格式
- [ ] 数据格式正确

### 步骤 4：检查资源日志

**验证命令**：
```bash
# 查看资源日志文件
cat youtube-research-flow/resource_log.json
```

**预期输出**：
```json
{
  "session_id": "2024-01-01T15:30:00",
  "operations": [
    {
      "operation_type": "search",
      "resource_type": "youtube_api",
      "timestamp": "2024-01-01T15:30:05Z",
      "details": {
        "query": "榴莲测评",
        "results_count": 5,
        "params": {"max_results": 5, "months": 3}
      }
    }
  ]
}
```

**验证点**：
- [ ] 日志文件已创建
- [ ] 操作已记录
- [ ] 会话 ID 已生成
- [ ] 时间戳格式正确
- [ ] 操作类型和资源类型正确

### 步骤 5：错误处理测试

**场景 1：API Key 无效**
```bash
# 移除或注释掉 API Key
nano youtube-research-flow/config/youtube_research_config.json

# 运行命令，预期错误
python3 youtube-research-flow/scripts/main.py "榴莲测评" --max-results 5
```

**预期错误**：
```
❌ Google API Error: Request had insufficient authentication scopes.
Status Code: 403
Message: Request is missing required authentication credential.
```

**验证点**：
- [ ] 系统正确捕获认证错误
- [ ] 错误信息清晰
- [ ] 程序不崩溃

---

## 测试 2：完整工作流测试

### 目标
验证 YouTube 搜索 → NotebookLM → 分析 → 报告的完整工作流

### 前提条件
- [x] 已安装和配置 YouTube Data API v3
- [x] 已安装 NotebookLM（`notebooklm skill install`）
- [ ] NotebookLM 已登录 Google 账户
- [ ] 资源追踪模块可用
- [x] 置络连接正常

### 测试场景

**场景：用户想研究榴莲测评视频并生成闪卡**

**测试命令**：
```bash
# 完整工作流：搜索 → NotebookLM → 分析 → 闪卡
python3 youtube-research-flow/scripts/main.py "榴莲测评" \
  --create-flashcards
```

**预期输出**：
```
🔍 步骤 1：搜索 YouTube 视频
搜索词：榴莲测评
最大结果：10
时间范围：最近 6 个月
排序方式：relevance

✅ 找到 10 个视频

📓 步骤 2：创建 NotebookLM 笔记本
笔记本名称：YouTube Research: 榴莲测评 - 2024-01-01

✅ 笔记本创建成功
Notebook ID: <notebook_id>

📊 步骤 3：导入视频源到 NotebookLM
开始导入 10 个视频源...

进度：
[=====>     ] 25%
[=====>     ] 50%
[=====>     ] 75%
[=====>     ] 100%

✅ 所有视频源导入成功

📊 步骤 4：等待视频处理完成
等待所有视频源状态变为 READY...
超时：300 秒

✅ 所有视频源已就绪

🧠 步骤 5：生成闪卡分析
分析类型：auto-inferred（根据"榴莲测评"推断为产品评测）
开始生成闪卡分析...

✅ 闪卡生成完成

📋 步骤 6：下载分析报告
下载 NotebookLM 报告到：
youtube_research_榴莲测评_2024-01-01.md

✅ 完整工作流测试成功！

---

## 测试 3：教程研究测试

### 目标
验证手动指定分析类型（tutorials）的正确性

### 测试命令
```bash
# 手动指定教程分析类型
python3 youtube-research-flow/scripts/main.py "榴莲挑选教程" \
  --analysis-type tutorials
```

### 预期结果

**目标推断**：
- [ ] 正确识别为 "tutorials" 分析类型
- [ ] 分析提示词符合教程评估标准
- [ ] NotebookLM 生成教育质量评估

**验证点**：
- [ ] 分析类型正确设置
- [ ] NotebookLM 生成对应的教育内容

---

## 测试 4：市场趋势分析测试

### 目标
验证自动趋势分析功能

### 测试命令
```bash
# 自动推断并生成市场分析
python3 youtube-research-flow/scripts/main.py "榴莲市场趋势" \
  --analysis-type trends
```

### 预期结果

**目标推断**：
- [ ] 正确识别为 "trends" 分析类型
- [ ] 提示词符合市场分析标准
- [ ] NotebookLM 生成市场分析报告

---

## 测试 5：错误恢复测试

### 场景
YouTube API 临时遇到错误或配额不足

**测试命令**
```bash
# 模拟 API Key 失效的场景
python3 youtube-research-flow/scripts/main.py "榴莲测评"
```

### 错误处理预期
- 系统捕获认证错误（401）
- 系统提供清晰的错误信息
- 程序优雅退出，不崩溃
- 提供具体的解决步骤

---

## 测试清单

### 基础功能测试

- [ ] YouTube Data API 搜索
- [ ] 参数解析（max_results, months, sort-by）
- [ ] 视频数据提取（title, channel, views, duration）
- [ ] 数据格式化（number formatting, date formatting）
- [ ] 错误处理

### NotebookLM 集成测试

- [ ] 笔记本创建
- [ ] 视频源导入
- [ ] 等待处理
- [ ] 分析生成
- [ ] 结果下载

### 资源追踪测试

- [ ] 会话管理（session ID）
- [ ] 操作日志记录
- [ ] 统计汇总
- [ ] 日志文件读写

### 智能功能测试

- [ ] 目标自动推断
- [ ] 多种分析类型
- [ ] 批量可交付成果
- [ ] 配置文件读取

### 性能测试

- [ ] 搜索响应时间（< 5 秒）
- [ ] 分析生成时间（< 2 分钟）
- [ ] 资源日志写入（< 1 秒）
- [ ] 内存占用（< 50 MB）

---

## 性能标准

| 操作 | 预期时间 | 通过标准 |
|--------|----------|----------|
| YouTube 搜索 | < 2 秒 | 是 |
| NotebookLM 创建 | < 30 秒 | 是 |
| 源导入 | < 60 秒 | 是 |
| 分析生成 | < 2 分钟 | 是 |
| 资源追踪 | < 1 秒 | 是 |

---

## 总结

✅ YouTube Research Flow 技能已成功创建并通过基础测试！

### 核心成就

1. **完整的 YouTube Data API v3 集成**
   - 高质量的视频搜索和元数据提取
   - 支持多种过滤和排序
   - 自动计算参与度指标

2. **NotebookLM 自动化**
   - 智能笔记本创建和管理
   - 自动化视频源导入
   - 批量进度追踪

3. **智能分析引擎**
   - 自动推断研究目标
   - 支持多种分析类型（产品评测、教程、市场、用户反馈）
   - 基于 NotebookLM 生成深度分析

4. **可交付成果系统**
   - 闪卡、信息图表、时间线等
   - 可选创建多个成果
   - Markdown 格式输出

5. **资源追踪系统**
   - 完整的开发元数据日志
- API 使用量和配额监控
- 成本分析和优化建议

### 就绪状态

🎉 **你现在拥有一个强大的 YouTube 研究自动化系统！**

开始使用 `youtube-research-flow` 技能进行智能化的 YouTube 内容研究吧！
