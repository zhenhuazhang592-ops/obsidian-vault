# 漫舟一键拉片 Backend

> AI Short Drama Studio - 一键拉片功能后端服务

## 功能概述

将任意短剧/动画视频上传，自动完成：
1. FFmpeg 视频标准化（720p/12fps）
2. PySceneDetect 镜头边界检测
3. 智能动态抽帧
4. AI 分镜分析（SSE 流式输出）
5. 输出 14 列分镜表 + 视频生成 Prompt

## 快速启动

### 1. 安装系统依赖

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg
```

### 2. 安装 Python 依赖

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. 配置 API Key

```bash
cp .env.example .env
# 编辑 .env，填入 API Key
```

### 4. 启动

```bash
# 单独启动后端
cd backend
source venv/bin/activate
uvicorn main:app --reload --port 8000

# 前端+后端同时启动（项目根目录）
npm run dev:all
```

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/lapian/analyze` | 上传视频，启动流水线 |
| GET | `/api/lapian/stream/{job_id}` | SSE 流式获取分析结果 |
| GET | `/api/lapian/status/{job_id}` | 轮询流水线状态 |

## API 使用示例

### 1. 上传视频并获取 job_id

```bash
curl -X POST "http://localhost:8000/api/lapian/analyze" \
  -F "file=@test_video.mp4"
```

响应：
```json
{"job_id": "abc123...", "message": "流水线已启动，请通过 SSE 订阅结果"}
```

### 2. SSE 流式获取结果

```javascript
const es = new EventSource('http://localhost:8000/api/lapian/stream/abc123...')

es.addEventListener('status', (e) => {
  const data = JSON.parse(e.data)
  console.log(`进度: ${data.progress}% - ${data.phase_desc}`)
})

es.addEventListener('shot_complete', (e) => {
  const data = JSON.parse(e.data)
  console.log(`镜头 ${data.shot.shot_id} 分析完成`)
})

es.addEventListener('done', () => {
  console.log('分析完成')
  es.close()
})
```

## 技术架构

### 视频预处理（FFmpeg）

- 分辨率：标准化为 720p（等比缩放）
- 帧率：12fps
- 编码：H.264
- 压缩质量：CRF 28

### 镜头检测（PySceneDetect）

- 算法：ContentDetector（基于 HSV 色彩空间）
- 阈值：27.0（短视频/动画推荐值）
- 最小镜头长度：15帧

### 动态抽帧策略

| 镜头时长 | 抽帧数量 | 位置 |
|---------|---------|------|
| < 1秒 | 1帧 | 中间帧 |
| 1-3秒 | 2帧 | 前20% + 后80% |
| > 3秒 | 3帧 | 前10% + 中间 + 后90% |

### AI 分镜分析

- 支持 Claude / Gemini 双后端
- 输出 14 列结构化分镜表
- 生成视频生成 Prompt

## 分镜表输出格式（14列）

| 字段 | 说明 |
|------|------|
| shot_id | 镜号 |
| start_time | 开始时间（秒） |
| end_time | 结束时间（秒） |
| duration | 时长（秒） |
| shot_size | 景别（特写/近景/中景/全景等） |
| camera_movement | 运镜方式 |
| composition_rule | 构图法则 |
| angle | 拍摄角度 |
| lighting | 光影布局 |
| color_palette | 核心色调 |
| background_style | 背景风格 |
| subject_description | 主体外观描述 |
| subject_action | 主体动作 |
| prop_details | 道具细节 |
| narrative_function | 叙事功能 |
| visual_hook | 视觉亮点 |
| has_dialogue | 是否有台词 |
| dialogue | 台词内容 |
| vo_emotion | 配音情绪 |
| sfx | 音效 |
| bgm_style | BGM风格 |
| transition | 转场方式 |
| generation_prompt | AI视频生成Prompt |

## 流水线阶段

1. **视频标准化** — FFmpeg 转 720p/12fps（约10-20%时间）
2. **镜头边界检测** — PySceneDetect ContentDetector（阈值 27.0，约5-10%时间）
3. **关键帧提取** — 动态抽帧（约10-15%时间）
4. **AI分镜分析** — 并行分析每个镜头（约60-80%时间，SSE流式输出）

## 目录结构

```
backend/
├── main.py                  # FastAPI 应用入口
├── config.py                # 配置管理
├── requirements.txt         # Python 依赖
├── .env.example            # 环境变量模板
├── README.md              # 本文档
├── api/
│   └── routes.py          # API 路由
├── pipeline/
│   ├── ffmpeg_preprocess.py  # FFmpeg 视频标准化
│   ├── scene_detect.py       # PySceneDetect 镜头检测
│   ├── frame_extract.py      # 动态抽帧
│   └── ai_analyzer.py        # AI 分镜分析
├── prompts/
│   └── shot_analysis.py      # 分镜分析 Prompt
└── test_video/
    └── test_video.mp4       # 测试视频（38秒）
```

## 测试视频

```bash
# 测试视频：backend/test_video/test_video.mp4
# 包含 10 个不同颜色场景，共 38 秒
# 用于验证整个流水线是否正常工作
```

## 常见问题

### Q: 镜头检测不准确？
调整 `SCENE_THRESHOLD` 参数：
- 敏感度太高（镜头切分过多）：调高到 30-35
- 敏感度太低（镜头切分过少）：调低到 22-25

### Q: API 调用失败？
检查 `.env` 文件中的 API Key 是否正确配置。

### Q: 前端 SSE 连接失败？
确认后端已启动在 8000 端口，且 CORS 配置包含前端地址。
