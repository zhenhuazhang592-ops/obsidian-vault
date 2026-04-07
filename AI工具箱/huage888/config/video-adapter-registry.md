# 视频模型适配器注册表

> P0 架构：Adapter Registry 模式，统一管理多视频模型

---

## 架构

```
scripts/video_pipeline.py（统一入口）
    │
    ├── get_registry() → VideoAdapterRegistry（单例）
    │                       │
    │                       ├── DoubaoAdapter → 火山引擎 Ark API
    │                       └── KlingAdapter  → 可灵 API
    │
    └── prompts/templates/（Prompt 模板）
            ├── character-motion.txt
            ├── cyber-ink-video.txt
            └── ...
```

## 环境变量

| 变量 | 必填 | 适配器 | 说明 |
|------|------|--------|------|
| `ARK_API_KEY` | ✅ | Doubao | 火山引擎 API Key |
| `ARK_BASE_URL` | 否 | Doubao | 默认 `https://ark.cn-beijing.volces.com/api/v3` |
| `KLING_API_KEY` | ✅ | Kling | 可灵 API Key（HMAC 签名用） |
| `KLING_KEY_ID` | ✅ | Kling | 可灵 Key ID |
| `KLING_BASE_URL` | 否 | Kling | 默认 `https://api.klingai.com` |

## 快速使用

```bash
# 列出已注册适配器
python3 scripts/video_pipeline.py --list

# 测试连接
python3 scripts/video_pipeline.py --test

# Doubao 视频
python3 scripts/video_pipeline.py \
  --video --provider doubao \
  --prompt "古风少女在赛博竹林中缓缓睁眼" \
  --output /tmp/v.mp4

# Kling 视频（10秒，竖屏）
python3 scripts/video_pipeline.py \
  --video --provider kling \
  --model kling-o1-std-10s \
  --aspect 9:16 \
  --duration 10 \
  --prompt "..." \
  --output /tmp/v.mp4

# 使用 Prompt 模板
python3 scripts/video_pipeline.py \
  --video --provider doubao \
  --template mo-mei-character \
  --output /tmp/v.mp4

# 批量视频
python3 scripts/video_pipeline.py \
  --batch --provider doubao \
  --shots-file outputs/02-storyboard-script.md \
  --output-dir outputs/videos/
```

## 新增适配器

```python
# scripts/adapters/my_adapter.py
from .video_adapter_base import VideoAdapterBase, AdapterConfig

class MyAdapter(VideoAdapterBase):
    provider = "my-provider"
    default_video_model = "my-model-id"

    def _create_video_task(self, prompt, img1, img2, duration, model):
        # 实现...
        return task_id

    def _get_task_status(self, task_id):
        # 实现...
        return {"status": "...", "content": {...}}
```

注册到 `scripts/adapters/video_adapter_registry.py`：

```python
# 添加到 from_env() 方法
if os.environ.get("MY_API_KEY"):
    registry.register("my", MyAdapter(AdapterConfig(
        api_key=os.environ["MY_API_KEY"],
    )))
```
