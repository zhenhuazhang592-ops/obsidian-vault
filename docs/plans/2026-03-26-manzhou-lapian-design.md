# 漫舟拉片智能体 · 设计文档

> 版本：v1.0
> 日期：2026-03-26
> 状态：已批准，待实施

---

## 一、目标与定位

### 1.1 核心目标

接收一个视频文件 → 输出 Obsidian 本地笔记（含分镜表 + 关键帧图 + AI 分镜分析 + videoPrompt）

### 1.2 对标

**TapNow 一键拉片**（14列分镜表），但：
- 输出为 Obsidian Markdown（本地文件，可直接编辑）
- 集成漫舟 CDP 资产体系（角色 ID / 场景 ID 自动标记）
- AI 分镜分析包含 videoPrompt（可用于后续 AI 漫剧生产）
- Audio Layer 采用漫舟 v6.2 四分栏规范

### 1.3 交互形式

**单次 CLI**：`manzhou-lapian <视频路径> [选项]`

不保留 Web UI，不保留 HTTP 服务。极简单一入口。

---

## 二、技术架构

### 2.1 目录结构

```
ai-drama-studio/
├── backend/                    # 保留：Pipeline 模块（复用）
│   ├── config.py
│   └── pipeline/
│       ├── ffmpeg_preprocess.py
│       ├── scene_detect.py
│       ├── frame_extract.py
│       └── ai_analyzer.py
│
├── manzhou_lapian/            # 新增：拉片智能体
│   ├── __init__.py
│   ├── __main__.py            # 入口：python -m manzhou_lapian
│   ├── cli.py                 # argparse 参数解析
│   ├── pipeline.py            # 串联 backend/pipeline
│   ├── cdp.py                 # CDP 角色/场景库注入
│   ├── prompts.py             # AI 分析 Prompt（含 TapNow 格式）
│   ├── types.py              # 数据类型定义
│   └── exporters/
│       └── obsidian.py       # Obsidian 笔记生成器
│
├── src/                        # 删除（React 前端）
├── routes.py                   # 删除（SSE 路由）
└── package.json                # 精简（移除前端依赖）
```

### 2.2 数据流

```
输入视频
   │
   ▼
FFmpeg 标准化（720p 12fps）
   │
   ▼
PySceneDetect 镜头边界检测
   │  → shots: [{shot_id, start_time, end_time, duration_sec}]
   ▼
动态抽帧（每镜头 2-3 帧）
   │  → 帧图片保存至 output_dir/.assets/{video_id}/
   ▼
AI 分镜分析（多后端）
   │  → 输入：帧图片 base64 + CDP 上下文
   │  → 输出：14 列分镜数据 + imagePrompt + videoPrompt
   ▼
Obsidian 笔记生成
   │  → 主笔记：{集数} 拉片分析.md
   │  → 附件：.assets/{video_id}/shot_XX_fX.jpg
   ▼
完成（输出路径告知用户）
```

---

## 三、输出格式：TapNow 14 列 × 漫舟增强

### 3.1 分镜表字段

| # | 字段 | 说明 | 示例 |
|---|------|------|------|
| 1 | **镜号** | 序号 | 01, 02, 03... |
| 2 | **开始时间** | 秒，精确到 0.1s | 0.0, 8.0, 15.2 |
| 3 | **时长** | 秒 | 8.0, 7.2, 3.5 |
| 4 | **结束时间** | 秒 | 8.0, 15.2, 18.7 |
| 5 | **景别** | TapNow 体系 + 漫舟缩写 | 近景(CU) / MCU / MS / WS / ELS |
| 6 | **相机角度** | TapNow 体系 | 平视 / 俯拍 / 仰拍 / 过肩 |
| 7 | **运镜方式** | TapNow 体系 + 漫舟数值 | 固定 / 推 / 拉 / 摇 / 移 + **Yaw/Pitch/Dolly** |
| 8 | **光影风格** | TapNow + Deakins 五定律 | 三点布光 / 自然光 / **Roger Deakins光影五定律** |
| 9 | **景深** | TapNow 扩展 | Shallow / Deep / f/1.4 / Shallow-DoF |
| 10 | **分镜描述** | 中文叙事，含 CDP 角色标记 | 含 `【【char_01_谭斌】】` |
| 11 | **画面描述** | 主体+场景+光影，含色温K值 | 5200K（晨光）/ 3200K（台灯） |
| 12 | **台词** | 对白文字 | "这周必须签约了。" / 无 |
| 13 | **音效** | Audio Layer 四分栏 | MUSIC/SFX-AMBIENT/SFX-NARRATIVE/SFX-EMOTION |
| 14 | **关键帧图** | 本地附件路径 | `![[./.assets/shot_01_f1.jpg]]` |

### 3.2 Obsidian 笔记完整模板

```markdown
---
uid: lapian-{series}-{episode}-{date}
title: {series} 第{episode}集 拉片分析
created: {YYYY-MM-DD HH:mm}
video: {filename}
video_duration: {total}s
video_shots: {count}
analysis_model: {model}
scene_threshold: {threshold}
tags: [拉片分析, {series}]
series: {series}
episode: {episode}
---

# {series} 第{episode}集 拉片分析

> **分析时间**：{YYYY-MM-DD HH:mm}
> **视频时长**：{total}s | **镜头数**：{count} | **AI模型**：{model}
> **场景阈值**：{threshold}

---

## 分镜总览

| 镜 | 时间 | 时长 | 景别 | 角度 | 运镜 | 光影 | 景深 | 分镜描述 | 台词 |
|----|------|------|------|------|------|------|------|---------|------|
| 01 | 00:00–00:08 | 8s | MS | 平视 | 固定 | 自然光 | Shallow | 【【char_01_谭斌】】站在落地窗前，俯瞰CBD天际线，神情沉思... | 无 |
| 02 | 00:08–00:15 | 7s | MCU | 平视 | 固定 | 侧逆光 | Shallow | 【【char_01_谭斌】】低头看手机屏幕，眉头微皱... | "这周必须签约了。" |

> [!TIP] 场景统计
> - 全剧共 **{count}** 镜头
> - 固定镜头 **{n}** 个 / 运动镜头 **{n}** 个
> - 有台词镜头 **{n}** 个 / 无台词镜头 **{n}** 个
> - 平均镜头时长：**{avg}s**

---

## 镜 01 | 00:00–00:08 | 8s

**景别**：MS（中景）| **角度**：平视 | **运镜**：固定（Static）| **Yaw/Pitch/Dolly**：0° / 0° / z
**光影**：自然光·窗光 | **色温**：5200K | **景深**：Shallow（f/2.8）

**【画面描述】**
女主谭斌身着黑色职业套装、白衬衫，站在上海CBD写字楼落地窗前。晨光从左侧窗框打入，在深灰色地毯上投下长方形光斑。窗外可见陆家嘴天际线，建筑玻璃幕墙反射晨曦微光。女主侧身面向窗户，表情若有所思，目光落在窗外远处。

**【分镜描述】**
谭斌站在落地窗前，俯瞰CBD天际线，晨光从左侧窗框斜射入，她侧身而立，表情若有所思。这是开篇定调镜头，用城市天际线交代女主角的职业背景与处境。

**【角色】** `【【char_01_谭斌】】` | **【【loc_01_上海CBD办公室】】**
**【道具】**：无 | **【叙事功能】**：环境交代 | **【视觉钩子】**：城市天际线 + 逆光轮廓

**【台词】** 无

**【Viseme标注】** 无（无对话）

**【Audio Layer】**
```
MUSIC:         piano_ambient—0-8s—渐入（0→-18dB）
SFX-AMBIENT:   office_ambience—0-8s—持续（空调+远处人声）
SFX-NARRATIVE: 无
SFX-EMOTION:   无
```

**【关键帧】**
![[./.assets/{video_id}/shot_01_f1.jpg]]
![[./.assets/{video_id}/shot_01_f2.jpg]]

**【imagePrompt】**
> A young professional Chinese woman in a black suit with white blouse stands by a floor-to-ceiling window in a modern Shanghai CBD office. Morning sunlight streams in from the left window frame, casting a rectangular light patch on the dark grey carpet. The Shanghai skyline with Lujiazui buildings is visible through the window, their glass facades reflecting the early morning light. She stands in three-quarter profile facing the window, looking thoughtfully at the city below. Cinematic 2.35:1 aspect ratio, shallow depth of field (f/2.8), soft ambient office lighting with natural window light as main source. Color temperature: 5200K (morning daylight). Award-winning commercial photography style.

**【videoPrompt v6.2】**
```
[00:00-00:08]
shot_size=MS | yaw=0° | pitch=0° | dolly=z
char_01_谭斌 | standing by window looking at skyline, three_quarter_profile
lighting=natural_window_light_soft_ambient | key=5200K | style=cool_tone
lip_sync=idle
[MUSIC:piano_ambient-0-8s-fade_in]
[SFX:office_ambience-0-8s]
STYLE:cinematic_2.35:1 | manzhou_v6.2
```

**【转场】** → 硬切（Hard Cut）至 镜 02

---

## 镜 02 | 00:08–00:15 | 7s
...
```

---

## 四、AI 分析 Prompt 设计

### 4.1 System Prompt

```markdown
你是资深电影分镜分析师，专门分析中文职场剧/都市剧/短剧。

请仔细观看提供的关键帧图片（每镜2-3帧，含时间戳），
严格按以下14列JSON格式输出每个镜头的分析结果。

【【CDP角色库】】
{cdp_context}

【【输出格式 - 严格JSON，无markdown包裹】】
{
  "shot_number": 1,
  "start_time": 0.0,
  "duration": 8.0,
  "end_time": 8.0,
  "shot_size": "MS",
  "camera_angle": "平视",
  "camera_movement": "固定",
  "yaw": 0,
  "pitch": 0,
  "dolly": "z",
  "lighting_style": "自然光·窗光",
  "color_temperature": 5200,
  "depth_of_field": "Shallow",
  "description": "中文分镜描述，如涉及已知角色必须用【【char_XX_名称】】和【【loc_XX_名称】】标记",
  "visual_description": "画面主体+场景+光影描述，必须含色温K值",
  "dialogue": "台词（如有，否则写'无'）",
  "viseme": "V0-V11音素序列（如无台词写'无'）",
  "audio_layer": {
    "MUSIC": "类型-起始秒-终止秒-曲线",
    "SFX_AMBIENT": "类型-起始秒-终止秒",
    "SFX_NARRATIVE": "类型-起始秒-终止秒",
    "SFX_EMOTION": "类型-起始秒-终止秒"
  },
  "keyframe_times": [0.0, 4.0],
  "transition": "硬切",
  "narrative_function": "环境交代/情绪铺垫/高潮/转场",
  "visual_hook": "视觉亮点描述",
  "props": "道具（如无写'无'）",
  "imagePrompt": "英文AI视频生成Prompt（100-150词，强调主体特征和视觉风格）",
  "videoPrompt": "中文videoPrompt（景别+运镜数值+角色ID+光影+Lip-sync+Audio Layer+风格后缀）"
}

【【镜头识别规则】】
- 景别：ECU(特写<5%) / CU(5-15%) / MCU(15-30%) / MS(30-50%) / WS(50-80%) / ELS(>80%)
- 角度：平视 / 俯拍(高角>20°) / 仰拍(低角>20°) / 过肩(OS)
- 运镜：固定 / 推(Dolly-in) / 拉(Dolly-out) / 摇(Pan) / 移(Track) / 跟随(Follow)
- 色温：火光1800K / 白炽灯2700K / 日出日落3200K / 办公室日光5200K / 阴天6500K / 阴影8000K
- 台词：完整对白，逐字记录；无台词写"无"
- 角色识别：若画面人物在CDP中存在，必须用【【char_XX】】标记
```

### 4.2 CDP 上下文注入格式

```python
cdp_context = """
【【char_01_谭斌】】：女，26岁，上海CBD写字楼白领。黑色职业套装，白衬衫，及肩短发，清冷气质。
【【char_02_潘父】】：谭斌之父，50多岁，退休教师。
【【loc_01_上海CBD办公室】】：现代写字楼，落地窗，灰色地毯，深色办公家具。
【【loc_02_谭家客厅】】：老式公房，暖色调，布艺沙发，书架。
"""
```

---

## 五、CLI 设计

### 5.1 参数定义

| 参数 | 简写 | 默认值 | 说明 |
|------|------|--------|------|
| `video_path` | 位置参数 | 必填 | 视频文件路径 |
| `--output` | `-o` | `./{series}/拉片分析/` | Obsidian 笔记输出目录 |
| `--cdp` | `-c` | 无 | CDP JSON 文件路径（注入角色上下文） |
| `--model` | `-m` | config 默认 | AI 模型：zhipu / claude / gemini |
| `--threshold` | `-t` | 27.0 | PySceneDetect 场景阈值 |
| `--shots-per-shot` | `-n` | 3 | 每镜头抽帧数量（1-5） |
| `--dry-run` | - | False | 仅测试 pipeline，不生成笔记 |

### 5.2 用法示例

```bash
# 基础
manzhou-lapian 格子间女人-第01集.mp4

# 指定输出目录
manzhou-lapian input.mp4 -o ~/Obsidian\ Vault/格子间女人/拉片分析

# 注入CDP，自动识别角色ID
manzhou-lapian input.mp4 -c ../AI漫剧生产/漫舟资产库/格子间女人-cdp.json

# 指定AI模型
manzhou-lapian input.mp4 -m gemini

# 组合
manzhou-lapian input.mp4 -o ~/Obsidian/格子间女人/拉片 \
    -c ../漫舟资产库/格子间女人-cdp.json -m gemini --threshold 30.0

# 测试模式
manzhou-lapian input.mp4 --dry-run
```

### 5.3 进度输出

```
◈ 漫舟拉片智能体 v1.0
│ 输入：格子间女人-第01集.mp4（2m37s / 157s）
│ 输出：~/Obsidian Vault/格子间女人/拉片分析/
│ CDP：格子间女人-cdp.json（6角色 / 3场景）
│ 模型：gemini-2.0-flash
│
◈ [1/5] 视频标准化 → 720p 12fps ... done (4s)
◈ [2/5] 镜头检测（18个镜头）... done (3s)
◈ [3/5] 关键帧提取（54帧）... done (8s)
◈ [4/5] AI 分镜分析（18镜）...
  ✓ 镜 01 完成 [00:00–00:08] MS·固定·自然光 (2.1s)
  ✓ 镜 02 完成 [00:08–00:15] MCU·固定·侧逆光 (1.9s)
  ...
◈ [5/5] 生成 Obsidian 笔记 ...

✓ 完成（38s）
  📄 第01集 拉片分析.md
  📁 .assets/lapian_0188b47/（54张关键帧）
```

---

## 六、模块详细设计

### 6.1 `manzhou_lapian/types.py`

```python
from dataclasses import dataclass, field
from typing import Literal

@dataclass
class AudioLayer:
    music: str = "无"
    sfx_ambient: str = "无"
    sfx_narrative: str = "无"
    sfx_emotion: str = "无"

@dataclass
class ShotAnalysis:
    shot_number: int
    start_time: float
    end_time: float
    duration: float
    shot_size: str
    camera_angle: str
    camera_movement: str
    yaw: int = 0        # 水平角（度）
    pitch: int = 0      # 垂直角（度）
    dolly: str = "z"    # z=固定, in=推, out=拉
    lighting_style: str = ""
    color_temperature: int = 0  # K值
    depth_of_field: str = ""
    description: str = ""       # 分镜描述（叙事）
    visual_description: str = "" # 画面描述
    dialogue: str = "无"
    viseme: str = "无"
    audio_layer: AudioLayer = field(default_factory=AudioLayer)
    keyframe_times: list[float] = field(default_factory=list)
    transition: str = "硬切"
    narrative_function: str = ""
    visual_hook: str = ""
    props: str = "无"
    imagePrompt: str = ""
    videoPrompt: str = ""

@dataclass
class LapianResult:
    video_path: str
    video_duration: float
    total_shots: int
    analysis_model: str
    scene_threshold: float
    shots: list[ShotAnalysis] = field(default_factory=list)
    output_dir: str = ""
    video_id: str = ""
```

### 6.2 `manzhou_lapian/pipeline.py`

```python
class LapianPipeline:
    """串联 backend/pipeline 模块，统一入口"""

    def __init__(self, config: LapianConfig):
        self.cfg = config

    async def run(self, video_path: str) -> LapianResult:
        # 1. 标准化
        preprocessor = FFmpegPreprocessor()
        std_path, metadata = preprocessor.standardize(video_path)

        # 2. 镜头检测
        detector = SceneDetector(threshold=self.cfg.threshold)
        shots = detector.detect(std_path)

        # 3. 抽帧
        extractor = FrameExtractor()
        frame_dir = self.cfg.output_dir / ".assets" / self.cfg.video_id
        frames = extractor.extract_shot_frames(std_path, shots, frame_dir)

        # 4. AI分析
        analyzer = AIAnalyzer(provider=self.cfg.model)
        cdp = CDPReader(self.cfg.cdp_path).read() if self.cfg.cdp_path else {}
        analyzed = []
        for i, (shot, frame_result) in enumerate(zip(shots, frames)):
            result = await analyzer.analyze_shot(shot, frame_result, cdp)
            analyzed.append(result)
            self._emit_progress("ai_analysis", i+1, len(shots))

        return LapianResult(
            video_path=video_path,
            video_duration=metadata["duration"],
            total_shots=len(shots),
            analysis_model=self.cfg.model,
            scene_threshold=self.cfg.threshold,
            shots=analyzed,
            output_dir=str(self.cfg.output_dir),
            video_id=self.cfg.video_id,
        )
```

### 6.3 `manzhou_lapian/cdp.py`

```python
class CDPReader:
    """读取漫舟资产库，生成 AI 可用上下文"""

    def read(self, path: str) -> dict:
        data = json.load(open(path))
        chars = data.get("characters", {})
        locs = data.get("locations", {})

        ctx_lines = []
        for cid, c in chars.items():
            ctx_lines.append(f"【【{cid}】】：{c.get('description','')}")
        for lid, l in locs.items():
            ctx_lines.append(f"【【{lid}】】：{l.get('description','')}")

        return {"characters": chars, "locations": locs,
                "context": "\n".join(ctx_lines)}
```

### 6.4 `manzhou_lapian/exporters/obsidian.py`

```python
class ObsidianExporter:
    """生成 Obsidian Markdown 笔记"""

    def __init__(self, template: str = DEFAULT_TEMPLATE):
        self.template = template

    def export(self, result: LapianResult, output_dir: Path) -> Path:
        # 1. 创建附件目录
        assets_dir = output_dir / ".assets" / result.video_id
        assets_dir.mkdir(parents=True, exist_ok=True)

        # 2. 复制关键帧图片
        for shot in result.shots:
            for frame_path in shot.extracted_frames:
                shutil.copy(frame_path, assets_dir / frame_path.name)

        # 3. 生成笔记
        markdown = self._render(result, assets_dir)
        filename = self._build_filename(result)
        output_path = output_dir / filename
        output_path.write_text(markdown, encoding="utf-8")

        return output_path

    def _render(self, result: LapianResult, assets_dir: Path) -> str:
        # 渲染 Jinja2 模板
        return self.template.render(
            result=result,
            assets_dir=assets_dir,
            date=datetime.now().strftime("%Y-%m-%d %H:%M"),
        )
```

---

## 七、实施计划

### Phase 1：基础设施（Day 1）
- [ ] 创建 `manzhou_lapian/` 目录结构
- [ ] 实现 `types.py`（数据类型）
- [ ] 实现 `cdp.py`（CDP读取器）
- [ ] 实现 `pipeline.py`（串联 backend）

### Phase 2：AI 分析（Day 1）
- [ ] 实现 `prompts.py`（TapNow 14列 Prompt + CDP注入）
- [ ] 修改 `backend/pipeline/ai_analyzer.py` 支持 CDP 上下文注入
- [ ] 修改 `backend/pipeline/ai_analyzer.py` 输出 TapNow 14列格式

### Phase 3：输出（Day 2）
- [ ] 实现 `exporters/obsidian.py`（笔记生成器）
- [ ] 完善 `exporters/obsidian.py`（总览表格 + 分镜详情 + 关键帧嵌入）
- [ ] 实现 `cli.py`（argparse + 进度输出）

### Phase 4：清理（Day 2）
- [ ] 删除 `src/` 目录
- [ ] 删除 `routes.py` SSE 路由
- [ ] 精简 `package.json`
- [ ] 更新启动说明文档

### Phase 5：测试（Day 2）
- [ ] 用《格子间女人》第01集跑完整流程
- [ ] 验证 Obsidian 笔记格式正确
- [ ] 验证关键帧图片嵌入正确
- [ ] 验证 CDP 角色标记正确

---

## 八、依赖关系

```
Python 3.12+
├── ffmpeg（系统命令）
├── scenedetect
├── openai（智谱GLM-4V兼容）
├── anthropic（Claude）
├── google-generativeai（Gemini）
└── jinja2（模板渲染）
```

---

## 九、风险与对策

| 风险 | 对策 |
|------|------|
| AI 分镜分析格式不稳定 | Prompt 加入严格 JSON Schema 约束 + 三层截断修复 |
| 帧图片路径中文名乱码 | 统一使用 video_id（UUID）命名，不使用原始文件名 |
| 镜头数过多导致 token 溢出 | 分批分析（每批 10 镜），进度实时写入 |
| CDP 角色未识别 | 降级处理：仅用通用描述，不强制要求【【】】标记 |
