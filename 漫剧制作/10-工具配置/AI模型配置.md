# AI模型配置

## 大语言模型 (LLM)

### 推荐模型

| 模型 | 用途 | 特点 | API |
|-----|------|-----|-----|
| GPT-4 | 剧本/分镜生成 | 能力强 | OpenAI API |
| Claude 3 | 剧本/分镜生成 | 逻辑强 | Anthropic API |
| 通义千问 | 中文剧本 | 中文优化 | 阿里云 |
| 智谱清言 | 中文剧本 | 性价比高 | 智谱AI |

### 配置示例

```yaml
llm:
  provider: openai
  model: gpt-4-turbo
  api_key: ${OPENAI_API_KEY}

  parameters:
    temperature: 0.7
    max_tokens: 4000
    top_p: 0.9
```

---

## 文生图模型

### 推荐模型

| 模型 | 用途 | 特点 | 平台 |
|-----|------|-----|-----|
| Midjourney | 高质量图片 | 艺术感强 | Discord |
| Stable Diffusion | 批量生成 | 本地可部署 | 本地/云端 |
| DALL-E 3 | 快速出图 | 稳定性好 | OpenAI |
| Midjourney V6 | 角色一致性 | 强一致性 | Discord |
| Flux | 文字渲染 | 文字效果 | API |

### 配置示例

```yaml
image_model:
  provider: midjourney
  model: v6
  parameters:
    aspect_ratio: "9:16"
    style: "comic"
    quality: "high"
    seed: -1
```

---

## 图生视频模型

### 推荐模型

| 模型 | 用途 | 特点 | 平台 |
|-----|------|-----|-----|
| Runway Gen-2 | 视频生成 | 功能全面 | Web/API |
| Runway Gen-3 | 视频生成 | 质量更高 | Web/API |
| 可灵 | 中文优化 | 效果稳定 | 快手 |
| Pika | 快速生成 | 速度快 | Web |
| Luma | 物理效果 | 真实感 | Web |

### 配置示例

```yaml
video_model:
  provider: runway
  model: gen-2
  parameters:
    resolution: "1080x1920"
    duration: 4
    fps: 24
```

---

## 文本转语音 (TTS)

### 推荐模型

| 模型 | 用途 | 特点 | 平台 |
|-----|------|-----|-----|
| 11Labs | 多语言配音 | 自然流畅 | Web/API |
| 微软TTS | 稳定性 | 稳定可靠 | Azure |
| 剪映配音 | 快速制作 | 简单易用 | 客户端 |
| 讯飞语音 | 中文配音 | 中文优化 | API |

### 配置示例

```yaml
tts:
  provider: 11labs
  model: "eleven_multilingual_v2"
  parameters:
    voice_id: "custom_voice"
    stability: 0.5
    similarity_boost: 0.75
```

---

## 本地部署

### Stable Diffusion WebUI

```bash
# 安装
git clone https://github.com/AUTOMATIC1111/stable-diffusion-webui
cd stable-diffusion-webui
./webui.sh

# 常用参数
--api
--listen
--port 7860
--medvram
```

### ComfyUI 工作流

```
推荐插件:
- ComfyUI-Manager
- ComfyUI-Advanced-ControlNet
- ComfyUI_IPAdapter_plus
- ComfyUI-InstantID
```

---

## API调用示例

### Python 调用 OpenAI

```python
import openai

client = openai.OpenAI(api_key="your-api-key")

def generate_script(prompt):
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "你是专业编剧..."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=4000
    )
    return response.choices[0].message.content
```

### Python 调用 Midjourney

```python
import requests

def generate_image(prompt):
    # 通过API或Discord调用
    url = "https://api.midjourney.com/v2/imagine"
    headers = {"Authorization": "Bearer your-token"}
    data = {
        "prompt": prompt,
        "aspect_ratio": "9:16"
    }
    response = requests.post(url, json=data, headers=headers)
    return response.json()
```
