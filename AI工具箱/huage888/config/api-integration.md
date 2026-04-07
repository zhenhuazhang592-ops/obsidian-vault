# config/api-integration.md — qwen-max API 集成规范

> huage888 系统 | 核心推理引擎
> 版本：v1.0 | 用途：qwen-max API 调用规范 + 各 Agent 参数配置

---

## 一、架构定位

```
Claude Code（编排层）
    │
    ├── 读取 agents/*.md，拼好 system prompt + user prompt
    ├── 调用 python3 config/qwen_pipeline.py
    ├── qwen-max 生成内容
    ├── 解析 JSON 返回
    └── Claude Code 做审核、质检、组装输出
```

**Claude Code 不直接生成内容**，只做编排和质量守门。
**qwen-max 负责所有内容生成**：讲戏本、角色提示词、场景提示词、道具提示词、分镜脚本。

---

## 二、快速配置

```bash
# 1. 设置环境变量
export QWEN_API_KEY="your-api-key-here"

# 2. 确认 Python 环境
python3 --version  # 推荐 3.10+

# 3. 安装依赖
pip install openai

# 4. 测试调用
python3 config/qwen_pipeline.py --test
```

---

## 三、qwen_pipeline.py 使用方法

### 基本调用

```bash
# 调用格式
python3 config/qwen_pipeline.py \
  --system "你是一个专业的导演..." \
  --user "请分析以下剧本..." \
  --agent director \
  --output outputs/01-director-analysis.md
```

### 各 Agent 调用示例

```bash
# 阶段一：导演讲戏
python3 config/qwen_pipeline.py \
  --system "$(cat agents/director.md | grep -A999 '## 你是谁')" \
  --user "请分析剧本：$(cat docs/剧本.md)" \
  --agent director \
  --output outputs/01-director-analysis.md

# 阶段二A：角色提示词
python3 config/qwen_pipeline.py \
  --system "$(cat agents/art-designer.md | grep -A999 '## 你是谁')" \
  --user "基于讲戏本生成角色提示词：$(cat outputs/01-director-analysis.md)" \
  --agent art-designer \
  --output assets/character-prompts.md

# 阶段二B：道具提示词
python3 config/qwen_pipeline.py \
  --system "$(cat agents/prop-designer.md | grep -A999 '## 你是谁')" \
  --user "基于讲戏本生成道具提示词：$(cat outputs/01-director-analysis.md)" \
  --agent prop-designer \
  --output assets/prop-prompts.md

# 阶段三：分镜脚本
python3 config/qwen_pipeline.py \
  --system "$(cat agents/storyboard-artist.md | grep -A999 '## 你是谁')" \
  --user "基于讲戏本生成视频提示词：$(cat outputs/01-director-analysis.md)" \
  --agent storyboard-artist \
  --output outputs/02-storyboard-script.md
```

### 纯 API 调用（返回 stdout）

```bash
# 不写文件，只返回内容
python3 config/qwen_pipeline.py \
  --system "你是导演..." \
  --user "分析剧本..." \
  --agent director

# 指定模型
python3 config/qwen_pipeline.py \
  --system "..." \
  --user "..." \
  --agent director \
  --model qwen-max   # 默认 qwen-max，可选 qwen-plus

# 指定温度
python3 config/qwen_pipeline.py \
  --system "..." \
  --user "..." \
  --agent director \
  --temperature 0.75
```

---

## 四、Agent 参数配置

> **参数已迁移至 `config/prompts-registry.md`**（含温度/max_tokens/top_p/上下文字节预算/项目级覆盖规范）。
> 本表仅保留快速参考，详细调参说明见 `prompts-registry.md`。

| Agent | Temperature | Top-P | 用途 | 优先级 |
|-------|------------|-------|------|--------|
| director | 0.75 | 0.95 | 剧本分析 + 讲戏本 | P0 |
| art-designer | 0.65 | 0.95 | 角色 + 场景提示词 | P0 |
| prop-designer | 0.60 | 0.95 | 道具提示词 | P1 |
| storyboard-artist | 0.55 | 0.95 | 分镜脚本 | P0 |
| script-review | 0.40 | 0.90 | 阶段一审核 | P1 |
| art-review | 0.40 | 0.90 | 阶段二审核 | P1 |
| storyboard-review | 0.40 | 0.90 | 阶段三审核 | P1 |

> **视频模型选型**：详见 `config/video-model-registry.md`，含 Doubao/Kling/Wan/Vidu/Gemini Veo 量化参数表及选型速查。
> **提示词管理**：详见 `config/prompts-registry.md`，含参数升级规范和 qwen_pipeline.py 集成指南。

---

## 五、API 参数规范

### Base URL

```
https://dashscope.aliyuncs.com/compatible-mode/v1
```

### 模型

| 模型 | 适用场景 | 成本 | 推荐 |
|------|---------|------|------|
| `qwen-max` | 高质量内容生成 | 高 | **首选** |
| `qwen-plus` | 快速迭代测试 | 中 | 开发调试用 |
| `qwen-turbo` | 超快响应 | 低 | 不推荐（质量不足）|

### 请求格式

```python
# 标准调用
{
    "model": "qwen-max",
    "messages": [
        {"role": "system", "content": "..."},
        {"role": "user", "content": "..."}
    ],
    "temperature": 0.75,
    "top_p": 0.95,
    "max_tokens": 8192,
    "stream": False,
    "response_format": {"type": "text"}
}
```

### 返回格式

```json
{
  "id": "...",
  "model": "qwen-max",
  "choices": [{
    "message": {
      "role": "assistant",
      "content": "生成的内容..."
    },
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": 1200,
    "completion_tokens": 3500,
    "total_tokens": 4700
  }
}
```

### 错误处理

| 错误码 | 含义 | 处理方式 |
|--------|------|---------|
| 401 | API Key 无效 | 检查 QWEN_API_KEY |
| 429 | 限流 | 等待 30s 后重试，最多 3 次 |
| 500 | 服务端错误 | 等待 10s 后重试，最多 3 次 |
| 600 | 无权限/余额不足 | 检查账户余额 |

---

## 六、Claude Code 调用规范

### 调用时机

```
Claude Code（编排层）永远不直接生成内容。
遇到以下任务时，必须调用 qwen_pipeline.py：
  - 生成导演讲戏本（阶段一）
  - 生成角色提示词（阶段二A）
  - 生成场景提示词（阶段二A）
  - 生成道具提示词（阶段二B）
  - 生成分镜脚本（阶段三）
  - 质量审核打分（各阶段末尾）
```

### 调用前检查

```
1. 确认 QWEN_API_KEY 已设置
2. 确认 agents/ 对应 Agent 文件存在
3. 确认有足够的 max_tokens（qwen-max 最大支持 8K 输出）
4. 确认 --output 文件路径父目录存在
```

### 调用后处理

```
1. 检查 stderr 是否有错误
2. 检查返回内容是否为空
3. 检查返回内容是否包含 error
4. 将返回内容写入 --output 文件
5. Claude Code 做二次审核（合规 + 业务）
```

---

## 七、与旧版（v1.0）的差异

| 维度 | v1.0（已废弃）| v2.0（当前）|
|------|-------------|-------------|
| 推理引擎 | Claude Code 直接生成 | qwen-max API 生成 |
| 调用方式 | Agent prompt 内嵌 | 独立 Python 脚本 |
| 输出质量 | 不稳定 | 结构化，稳定 |
| 一致性 | 依赖 Agent 自觉 | 规则锁定 |
