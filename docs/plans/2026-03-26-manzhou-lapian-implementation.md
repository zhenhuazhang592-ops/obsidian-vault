# 漫舟拉片智能体 · 实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将 ai-drama-studio 的 Web 前端重构为单次 CLI 工具，输出 Obsidian Markdown 笔记（TapNow 14列格式），复用现有 pipeline 模块。

**Architecture:** 新增 `manzhou_lapian/` Python 包，通过 CLI 入口串联 `backend/pipeline/`，最终生成 Obsidian 笔记；删除 React 前端和 SSE 路由。

**Tech Stack:** Python 3.12 / FFmpeg / PySceneDetect / Jinja2 / OpenAI SDK / Anthropic SDK / Gemini SDK

---

## 目录结构

```
ai-drama-studio/
├── backend/
│   ├── config.py                         ← 复用
│   └── pipeline/
│       ├── ffmpeg_preprocess.py          ← 复用
│       ├── scene_detect.py               ← 复用
│       ├── frame_extract.py               ← 复用
│       └── ai_analyzer.py                ← 修改：支持CDP注入+TapNow格式输出
│
├── manzhou_lapian/                       ← 新增（CLI包）
│   ├── __init__.py
│   ├── __main__.py                       ← 入口
│   ├── cli.py                            ← argparse
│   ├── pipeline.py                       ← pipeline串联
│   ├── cdp.py                            ← CDP读取器
│   ├── prompts.py                        ← AI分析Prompt
│   ├── types.py                          ← 数据类型
│   └── exporters/
│       └── obsidian.py                   ← Obsidian笔记生成
│
├── src/                                  ← 删除
├── routes.py                             ← 删除
└── package.json                          ← 精简
```

---

## Task 1: 创建 manzhou_lapian 包基础结构

**Files:**
- Create: `ai-drama-studio/manzhou_lapian/__init__.py`
- Create: `ai-drama-studio/manzhou_lapian/types.py`

**Step 1: 创建目录和空 `__init__.py`**

```bash
mkdir -p ai-drama-studio/manzhou_lapian/exporters
touch ai-drama-studio/manzhou_lapian/__init__.py
touch ai-drama-studio/manzhou_lapian/exporters/__init__.py
```

**Step 2: 创建 `types.py`**

```python
"""漫舟拉片智能体 - 数据类型定义"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AudioLayer:
    """Audio Layer v6.2 四分栏"""
    music: str = "无"          # MUSIC
    sfx_ambient: str = "无"    # SFX-AMBIENT
    sfx_narrative: str = "无" # SFX-NARRATIVE
    sfx_emotion: str = "无"   # SFX-EMOTION

    def to_markdown(self) -> str:
        lines = [
            f"MUSIC:         {self.music}",
            f"SFX-AMBIENT:   {self.sfx_ambient}",
            f"SFX-NARRATIVE: {self.sfx_narrative}",
            f"SFX-EMOTION:   {self.sfx_emotion}",
        ]
        return "\n".join(lines)


@dataclass
class ShotAnalysis:
    """单个镜头的分镜分析结果（TapNow 14列 + 漫舟增强）"""
    shot_number: int
    start_time: float
    end_time: float
    duration: float
    shot_size: str              # MS / CU / MCU / WS / ELS
    camera_angle: str           # 平视 / 俯拍 / 仰拍 / 过肩
    camera_movement: str        # 固定 / 推 / 拉 / 摇 / 移 / 跟随
    yaw: int = 0               # 水平角（度）
    pitch: int = 0             # 垂直角（度）
    dolly: str = "z"           # z=固定, in=推, out=拉
    lighting_style: str = ""   # 自然光 / 三点布光 / ...
    color_temperature: int = 0 # K值
    depth_of_field: str = ""   # Shallow / Deep / f/1.4
    description: str = ""       # 分镜描述（含【【char_XX】】标记）
    visual_description: str = ""  # 画面描述（含色温K值）
    dialogue: str = "无"
    viseme: str = "无"         # V0-V11 音素序列
    audio_layer: AudioLayer = field(default_factory=AudioLayer)
    keyframe_times: list[float] = field(default_factory=list)
    extracted_frames: list[str] = field(default_factory=list)  # 帧路径
    transition: str = "硬切"
    narrative_function: str = ""
    visual_hook: str = ""
    props: str = "无"
    imagePrompt: str = ""
    videoPrompt: str = ""


@dataclass
class LapianConfig:
    """CLI 配置"""
    video_path: str
    output_dir: str = "./拉片分析"
    cdp_path: Optional[str] = None
    model: str = "gemini"       # zhipu / claude / gemini
    threshold: float = 27.0    # PySceneDetect 阈值
    shots_per_shot: int = 3    # 每镜头抽帧数
    dry_run: bool = False


@dataclass
class LapianResult:
    """完整拉片结果"""
    video_path: str
    video_id: str
    video_duration: float
    total_shots: int
    analysis_model: str
    scene_threshold: float
    shots: list[ShotAnalysis] = field(default_factory=list)
    output_dir: str = ""
    video_filename: str = ""


@dataclass
class CDPData:
    """CDP 资产库数据"""
    characters: dict = field(default_factory=dict)
    locations: dict = field(default_factory=dict)

    def get_context(self) -> str:
        """生成 AI 可用的 CDP 上下文"""
        lines = []
        for cid, c in self.characters.items():
            desc = c.get("description", c.get("name", ""))
            lines.append(f"【【{cid}】】：{desc}")
        for lid, l in self.locations.items():
            desc = l.get("description", l.get("name", ""))
            lines.append(f"【【{lid}】】：{desc}")
        return "\n".join(lines) if lines else "无CDP上下文"
```

**Step 3: 验证类型定义**

```bash
cd ai-drama-studio
python -c "from manzhou_lapian.types import ShotAnalysis, LapianConfig, LapianResult, CDPData; print('types.py OK')"
```

Expected: `types.py OK`

**Step 4: Commit**

```bash
cd ai-drama-studio
git add manzhou_lapian/
git commit -m "feat(lapian): create manzhou_lapian package with types"
```

---

## Task 2: 实现 CDP 读取器

**Files:**
- Create: `ai-drama-studio/manzhou_lapian/cdp.py`
- Create: `ai-drama-studio/tests/test_cdp.py`

**Step 1: 创建测试文件**

```python
# tests/test_cdp.py
import pytest
import json
import tempfile
from pathlib import Path
from manzhou_lapian.cdp import CDPReader
from manzhou_lapian.types import CDPData


def test_read_valid_cdp():
    cdp_data = {
        "characters": {
            "char_01_谭斌": {"name": "谭斌", "description": "女，26岁，黑色职业套装。"},
            "char_02_潘总": {"name": "潘总", "description": "男，40岁，深色西装。"},
        },
        "locations": {
            "loc_01_办公室": {"name": "CBD办公室", "description": "落地窗，灰色地毯。"},
        }
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(cdp_data, f)
        path = f.name

    reader = CDPReader(path)
    result = reader.read()

    assert isinstance(result, CDPData)
    assert "char_01_谭斌" in result.characters
    assert "loc_01_办公室" in result.locations
    ctx = result.get_context()
    assert "【【char_01_谭斌】】" in ctx
    assert "【【loc_01_办公室】】" in ctx

    Path(path).unlink()


def test_read_missing_file():
    reader = CDPReader("/nonexistent/path.json")
    result = reader.read()
    assert isinstance(result, CDPData)
    assert result.characters == {}
    assert "无CDP上下文" in result.get_context()
```

**Step 2: 运行测试验证失败**

```bash
cd ai-drama-studio
pytest tests/test_cdp.py -v
```
Expected: ERROR - ModuleNotFoundError: No module named 'manzhou_lapian'

**Step 3: 实现 `cdp.py`**

```python
"""漫舟拉片智能体 - CDP 资产库读取器"""
import json
import logging
from pathlib import Path
from typing import Optional
from .types import CDPData

logger = logging.getLogger(__name__)


class CDPReader:
    """读取漫舟资产库，生成 AI 可用的上下文"""

    def __init__(self, path: Optional[str] = None):
        self.path = path

    def read(self) -> CDPData:
        """读取 CDP JSON 文件，返回 CDPData 对象"""
        if not self.path or not Path(self.path).exists():
            logger.warning(f"CDP文件不存在或未指定: {self.path}")
            return CDPData()

        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)

            characters = data.get("characters", {})
            locations = data.get("locations", {})

            logger.info(f"CDP加载成功: {len(characters)}角色 / {len(locations)}场景")
            return CDPData(characters=characters, locations=locations)

        except json.JSONDecodeError as e:
            logger.error(f"CDP JSON 解析失败: {e}")
            return CDPData()
        except Exception as e:
            logger.error(f"CDP读取异常: {e}")
            return CDPData()
```

**Step 4: 运行测试验证通过**

```bash
cd ai-drama-studio
pytest tests/test_cdp.py -v
```
Expected: PASS (2 tests)

**Step 5: Commit**

```bash
git add manzhou_lapian/cdp.py tests/test_cdp.py
git commit -m "feat(lapian): add CDPReader for asset library injection"
```

---

## Task 3: 实现 AI 分析 Prompt（TapNow 14列）

**Files:**
- Create: `ai-drama-studio/manzhou_lapian/prompts.py`
- Create: `ai-drama-studio/tests/test_prompts.py`

**Step 1: 创建测试文件**

```python
# tests/test_prompts.py
from manzhou_lapian.prompts import build_analysis_prompt


def test_build_prompt_without_cdp():
    prompt = build_analysis_prompt(shot_number=1, duration=8.0, cdp_context=None)
    assert "char_01" not in prompt
    assert "【【CDP角色库】】" not in prompt
    assert "14列" in prompt or "JSON" in prompt


def test_build_prompt_with_cdp():
    cdp_ctx = "【【char_01_谭斌】】：女，26岁。"
    prompt = build_analysis_prompt(shot_number=1, duration=8.0, cdp_context=cdp_ctx)
    assert "char_01_谭斌" in prompt
    assert "14列" in prompt or "shot_number" in prompt


def test_prompt_contains_required_fields():
    prompt = build_analysis_prompt(shot_number=1, duration=5.0)
    required = ["shot_number", "shot_size", "camera_angle", "camera_movement",
                "lighting_style", "depth_of_field", "description",
                "dialogue", "viseme", "audio_layer", "imagePrompt", "videoPrompt"]
    for field in required:
        assert field in prompt, f"Missing field: {field}"
```

**Step 2: 运行测试验证失败**

```bash
cd ai-drama-studio
pytest tests/test_prompts.py -v
```
Expected: ERROR - ModuleNotFoundError

**Step 3: 实现 `prompts.py`**

```python
"""漫舟拉片智能体 - AI 分析 Prompt 模板（TapNow 14列 × 漫舟 v6.2）"""
from .types import CDPData


SYSTEM_PROMPT_TEMPLATE = """你是资深电影分镜分析师，专门分析中文职场剧/都市剧/短剧。

请仔细观看提供的关键帧图片（每镜2-3帧，含时间戳区间 {start_time}s - {end_time}s，共{duration}s），
严格按以下14列JSON格式输出分析结果。

【【输出约束】】
- 严格JSON，无markdown包裹，无解释文字
- 字段不得缺失，未知字段写"无"或空字符串
- 角色识别必须用【【char_XX_名称】】标记（如画面人物在CDP中存在）
- 场景识别必须用【【loc_XX_名称】】标记

{cdp_section}

【【JSON输出格式】】
{{
  "shot_number": {shot_number},
  "start_time": {start_time},
  "end_time": {end_time},
  "duration": {duration},
  "shot_size": "MS",
  "camera_angle": "平视",
  "camera_movement": "固定",
  "yaw": 0,
  "pitch": 0,
  "dolly": "z",
  "lighting_style": "自然光",
  "color_temperature": 5200,
  "depth_of_field": "Shallow",
  "description": "中文分镜描述（叙事功能），含【【char_XX】】角色标记",
  "visual_description": "画面主体+场景+光影，含色温K值",
  "dialogue": "台词（如无写'无'）",
  "viseme": "V0-V11序列（如无台词写'无'）",
  "audio_layer": {{
    "MUSIC": "类型-起始秒-终止秒-曲线",
    "SFX_AMBIENT": "类型-起始秒-终止秒",
    "SFX_NARRATIVE": "类型-起始秒-终止秒",
    "SFX_EMOTION": "类型-起始秒-终止秒"
  }},
  "keyframe_times": [{keyframe_times}],
  "transition": "硬切",
  "narrative_function": "环境交代/情绪铺垫/高潮/转场",
  "visual_hook": "视觉亮点",
  "props": "道具（如无写'无'）",
  "imagePrompt": "英文AI视频生成Prompt（100-150词）",
  "videoPrompt": "中文videoPrompt（景别+运镜数值+角色ID+光影+Lip-sync+Audio+风格）"
}}

【【镜头识别规范】】
景别: ECU(<5%主体) / CU(5-15%) / MCU(15-30%) / MS(30-50%) / WS(50-80%) / ELS(>80%)
角度: 平视 / 俯拍(高角>20°) / 仰拍(低角>20°) / 过肩(OS)
运镜: 固定 / 推(Dolly-in) / 拉(Dolly-out) / 摇(Pan) / 移(Track) / 跟随(Follow)
色温: 火光1800K / 白炽灯2700K / 日出日落3200K / 办公室5200K / 阴天6500K / 阴影8000K
转场: 硬切 / 淡入淡出 / 黑场 / 白场
"""


def build_system_prompt(
    shot_number: int,
    start_time: float,
    end_time: float,
    duration: float,
    keyframe_times: list[float],
    cdp_data: CDPData = None,
) -> str:
    """构建完整的 system prompt"""
    cdp_section = ""
    if cdp_data:
        ctx = cdp_data.get_context()
        if ctx and ctx != "无CDP上下文":
            cdp_section = f"【【CDP角色库】】\n{ctx}\n\n【【规则】】若画面人物属于上述角色库，必须用对应【【char_XX】】标记。"

    return SYSTEM_PROMPT_TEMPLATE.format(
        shot_number=shot_number,
        start_time=start_time,
        end_time=end_time,
        duration=duration,
        cdp_section=cdp_section,
        keyframe_times=", ".join(str(t) for t in keyframe_times),
    )


def build_analysis_prompt(
    shot_number: int,
    duration: float,
    start_time: float = 0.0,
    end_time: float = 0.0,
    keyframe_times: list[float] = None,
    cdp_context: str = None,
) -> str:
    """构建用户分析 prompt（用于图片帧输入）"""
    if end_time == 0.0:
        end_time = start_time + duration
    if keyframe_times is None:
        keyframe_times = [start_time, start_time + duration / 2, end_time]

    cdp_section = ""
    if cdp_context:
        cdp_section = f"【【CDP角色库】】\n{cdp_context}\n\n"

    return f"""请仔细分析以下关键帧图片（镜号{shot_number}，{start_time:.1f}s - {end_time:.1f}s，共{duration:.1f}s），
严格按上方JSON格式输出。

{cdp_section}【【任务】】识别画面中的角色、场景、光影、运镜，生成完整分镜分析。
"""
```

**Step 4: 运行测试验证通过**

```bash
cd ai-drama-studio
pytest tests/test_prompts.py -v
```
Expected: PASS (3 tests)

**Step 5: Commit**

```bash
git add manzhou_lapian/prompts.py tests/test_prompts.py
git commit -m "feat(lapian): add TapNow 14-column analysis prompts"
```

---

## Task 4: 修改 AIAnalyzer 支持 TapNow 格式输出

**Files:**
- Modify: `ai-drama-studio/backend/pipeline/ai_analyzer.py`
- Create: `ai-drama-studio/tests/test_ai_analyzer.py`

**Step 1: 创建测试文件**

```python
# tests/test_ai_analyzer.py
from manzhou_lapian.types import ShotAnalysis, AudioLayer
from backend.pipeline.ai_analyzer import AIAnalyzer


def test_normalize_tapnow_format():
    """测试 TapNow 14列 JSON 标准化"""
    raw = {
        "shot_number": 1,
        "start_time": 0.0,
        "end_time": 8.0,
        "duration": 8.0,
        "shot_size": "MS",
        "camera_angle": "平视",
        "camera_movement": "固定",
        "yaw": 0,
        "pitch": 0,
        "dolly": "z",
        "lighting_style": "自然光",
        "color_temperature": 5200,
        "depth_of_field": "Shallow",
        "description": "【【char_01_谭斌】】站在落地窗前。",
        "visual_description": "女主站在落地窗前，晨光5200K。",
        "dialogue": "无",
        "viseme": "无",
        "audio_layer": {
            "MUSIC": "piano_ambient-0-8s-fade_in",
            "SFX_AMBIENT": "office-0-8s",
            "SFX_NARRATIVE": "无",
            "SFX_EMOTION": "无",
        },
        "keyframe_times": [0.0, 4.0],
        "transition": "硬切",
        "narrative_function": "环境交代",
        "visual_hook": "城市天际线",
        "props": "无",
        "imagePrompt": "A woman stands by a window...",
        "videoPrompt": "MS, 固定, 自然光...",
    }

    result = AIAnalyzer.normalize_tapnow(raw)

    assert isinstance(result, ShotAnalysis)
    assert result.shot_number == 1
    assert result.shot_size == "MS"
    assert result.lighting_style == "自然光"
    assert result.color_temperature == 5200
    assert isinstance(result.audio_layer, AudioLayer)
    assert result.audio_layer.music == "piano_ambient-0-8s-fade_in"


def test_normalize_flat_schema():
    """测试扁平 Schema 降级兼容（Zhipu 输出）"""
    raw = {
        "shot_number": 1,
        "start_time": 0.0,
        "end_time": 8.0,
        "duration": 8.0,
        "shot_size": "MS",
        "camera_movement": "固定",
        "lighting": "自然光",
        "color_palette": "冷色",
        "scene_description": "女主站在落地窗前",
        "dialogue": "无",
        "vo_emotion": "无",
        "sfx": "无",
        "bgm_style": "钢琴",
        "transition": "硬切",
        "generation_prompt": "A woman stands by window...",
    }

    result = AIAnalyzer.normalize_tapnow(raw)

    assert isinstance(result, ShotAnalysis)
    assert result.shot_size == "MS"
    assert result.description == "女主站在落地窗前"
    assert result.imagePrompt == "A woman stands by window..."
```

**Step 2: 运行测试验证失败**

```bash
cd ai-drama-studio
pytest tests/test_ai_analyzer.py -v
```
Expected: ERROR - AIAnalyzer.normalize_tapnow not defined

**Step 3: 在 `ai_analyzer.py` 末尾添加 `normalize_tapnow` 方法**

在 `ai_analyzer.py` 文件末尾（`@staticmethod _strip_code_fence` 之后）添加：

```python
    # ─────────────────────────────────────────────────────────────────────────
    # TapNow 14列标准化（新增，供 manzhou_lapian 调用）
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def normalize_tapnow(data: dict) -> "ShotAnalysis":
        """
        将 AI 输出的原始 JSON 标准化为 ShotAnalysis 对象。
        支持两种格式：
        - TapNow 14列（完整嵌套）
        - 扁平 Schema（Zhipu 降级输出）
        """
        from manzhou_lapian.types import ShotAnalysis, AudioLayer

        # ── Audio Layer ──
        raw_al = data.get("audio_layer", {})
        if isinstance(raw_al, dict):
            al = AudioLayer(
                music=raw_al.get("MUSIC", "无"),
                sfx_ambient=raw_al.get("SFX_AMBIENT", "无"),
                sfx_narrative=raw_al.get("SFX_NARRATIVE", "无"),
                sfx_emotion=raw_al.get("SFX_EMOTION", "无"),
            )
        elif isinstance(raw_al, str) and raw_al != "无":
            # 扁平格式降级
            al = AudioLayer(music=raw_al)
        else:
            al = AudioLayer()

        return ShotAnalysis(
            shot_number=data.get("shot_number", 1),
            start_time=data.get("start_time", 0.0),
            end_time=data.get("end_time", 0.0),
            duration=data.get("duration", 0.0),
            shot_size=data.get("shot_size", ""),
            camera_angle=data.get("camera_angle", ""),
            camera_movement=data.get("camera_movement", data.get("movement", "")),
            yaw=data.get("yaw", 0),
            pitch=data.get("pitch", 0),
            dolly=data.get("dolly", "z"),
            lighting_style=data.get("lighting_style", data.get("lighting", "")),
            color_temperature=data.get("color_temperature",
                                       data.get("color_temp", 0)),
            depth_of_field=data.get("depth_of_field", ""),
            description=data.get("description",
                                data.get("scene_description", "")),
            visual_description=data.get("visual_description", ""),
            dialogue=data.get("dialogue", "无"),
            viseme=data.get("viseme", "无"),
            audio_layer=al,
            keyframe_times=data.get("keyframe_times", []),
            extracted_frames=data.get("extracted_frames", []),
            transition=data.get("transition", "硬切"),
            narrative_function=data.get("narrative_function", ""),
            visual_hook=data.get("visual_hook", ""),
            props=data.get("props", "无"),
            imagePrompt=data.get("imagePrompt",
                                 data.get("generation_prompt", "")),
            videoPrompt=data.get("videoPrompt", ""),
        )
```

**Step 4: 运行测试验证通过**

```bash
cd ai-drama-studio
pytest tests/test_ai_analyzer.py -v
```
Expected: PASS (2 tests)

**Step 5: Commit**

```bash
git add backend/pipeline/ai_analyzer.py tests/test_ai_analyzer.py
git commit -m "feat(lapian): add normalize_tapnow() to AIAnalyzer"
```

---

## Task 5: 实现 pipeline 串联器

**Files:**
- Create: `ai-drama-studio/manzhou_lapian/pipeline.py`
- Create: `ai-drama-studio/tests/test_pipeline.py`

**Step 1: 创建测试文件**

```python
# tests/test_pipeline.py
from manzhou_lapian.pipeline import LapianPipeline
from manzhou_lapian.types import LapianConfig
import pytest


def test_config_defaults():
    config = LapianConfig(video_path="test.mp4")
    assert config.output_dir == "./拉片分析"
    assert config.model == "gemini"
    assert config.threshold == 27.0
    assert config.shots_per_shot == 3
    assert config.dry_run is False
```

**Step 2: 实现 `pipeline.py`**

```python
"""漫舟拉片智能体 - Pipeline 串联器"""
import asyncio
import logging
import uuid
from pathlib import Path
from typing import Callable, Optional

from ..backend.pipeline.ffmpeg_preprocess import FFmpegPreprocessor
from ..backend.pipeline.scene_detect import SceneDetector
from ..backend.pipeline.frame_extract import FrameExtractor
from ..backend.pipeline.ai_analyzer import AIAnalyzer
from .types import LapianConfig, LapianResult, ShotAnalysis, CDPData
from .cdp import CDPReader
from .prompts import build_system_prompt

logger = logging.getLogger(__name__)


class LapianPipeline:
    """串联 backend/pipeline 模块，统一执行拉片流程"""

    def __init__(self, config: LapianConfig):
        self.cfg = config
        self._progress_cb: Optional[Callable] = None

    def set_progress_callback(self, cb: Callable[[str, int, int], None]):
        """设置进度回调 (phase, current, total)"""
        self._progress_cb = cb

    def _emit(self, phase: str, current: int = 0, total: int = 0):
        if self._progress_cb:
            self._progress_cb(phase, current, total)

    async def run(self) -> LapianResult:
        video_path = self.cfg.video_path
        video_id = uuid.uuid4().hex[:12]
        video_filename = Path(video_path).name

        logger.info(f"开始拉片: {video_path} (video_id={video_id})")

        # ── Step 1: 标准化 ─────────────────────────────────────────
        self._emit("标准化", 0, 1)
        preprocessor = FFmpegPreprocessor()
        std_path, metadata = preprocessor.standardize(video_path)
        duration = metadata.get("duration", 0)
        self._emit("标准化", 1, 1)

        # ── Step 2: 镜头检测 ───────────────────────────────────────
        self._emit("镜头检测", 0, 1)
        detector = SceneDetector(threshold=self.cfg.threshold)
        shots = detector.detect(std_path)
        total_shots = len(shots)
        self._emit("镜头检测", 1, 1)

        # ── Step 3: 抽帧 ───────────────────────────────────────────
        self._emit("抽帧", 0, 1)
        frame_dir = Path(self.cfg.output_dir) / ".assets" / video_id
        frame_dir.mkdir(parents=True, exist_ok=True)
        extractor = FrameExtractor()
        frame_results = extractor.extract_shot_frames(
            video_path=std_path,
            fps=metadata["fps"],
            shots=shots,
            output_dir=str(frame_dir),
            job_id=video_id,
        )
        self._emit("抽帧", 1, 1)

        # ── Step 4: AI 分析 ────────────────────────────────────────
        # 加载 CDP
        cdp_data: CDPData = CDPData()
        if self.cfg.cdp_path:
            reader = CDPReader(self.cfg.cdp_path)
            cdp_data = reader.read()

        analyzer = AIAnalyzer()
        analyzed_shots: list[ShotAnalysis] = []

        for i, (shot, frame_result) in enumerate(zip(shots, frame_results)):
            frame_paths = frame_result["frames"]
            keyframe_times = frame_result.get("keyframe_times",
                                               [shot["start_time"],
                                                shot["end_time"]])

            # 构建 Prompt
            system_prompt = build_system_prompt(
                shot_number=shot["shot_id"],
                start_time=shot["start_time"],
                end_time=shot["end_time"],
                duration=shot["duration_sec"],
                keyframe_times=keyframe_times,
                cdp_data=cdp_data,
            )

            # AI 分析（复用现有 analyzer，保持向后兼容）
            result = await analyzer.analyze_shot_sync(
                shot_id=shot["shot_id"],
                start_time=shot["start_time"],
                end_time=shot["end_time"],
                duration=shot["duration_sec"],
                frame_paths=frame_paths,
                job_id=video_id,
                shot_context="",  # CDP 上下文已在 system prompt 中
            )

            # 标准化为 TapNow 格式
            shot_analysis = AIAnalyzer.normalize_tapnow(result)
            shot_analysis.extracted_frames = [
                str(frame_dir / f["filename"]) for f in frame_paths
            ]
            shot_analysis.keyframe_times = keyframe_times
            analyzed_shots.append(shot_analysis)

            self._emit("AI分析", i + 1, total_shots)

            logger.info(f"镜 {shot['shot_id']} 完成 [{shot['start_time']:.1f}-{shot['end_time']:.1f}s]")

        return LapianResult(
            video_path=video_path,
            video_id=video_id,
            video_duration=duration,
            total_shots=total_shots,
            analysis_model=self.cfg.model,
            scene_threshold=self.cfg.threshold,
            shots=analyzed_shots,
            output_dir=self.cfg.output_dir,
            video_filename=video_filename,
        )
```

**Step 3: 验证 pipeline 可以导入**

```bash
cd ai-drama-studio
python -c "from manzhou_lapian.pipeline import LapianPipeline; print('pipeline OK')"
```
Expected: `pipeline OK`

**Step 4: Commit**

```bash
git add manzhou_lapian/pipeline.py tests/test_pipeline.py
git commit -m "feat(lapian): add LapianPipeline orchestrator"
```

---

## Task 6: 实现 Obsidian 笔记生成器

**Files:**
- Create: `ai-drama-studio/manzhou_lapian/exporters/obsidian.py`
- Create: `ai-drama-studio/tests/test_obsidian_exporter.py`

**Step 1: 创建测试文件**

```python
# tests/test_obsidian_exporter.py
from manzhou_lapian.types import LapianResult, ShotAnalysis, AudioLayer
from manzhou_lapian.exporters.obsidian import ObsidianExporter
import tempfile
import json
from pathlib import Path


def test_export_basic(tmp_path):
    """测试生成 Obsidian 笔记"""
    result = LapianResult(
        video_path="/test.mp4",
        video_id="test123",
        video_duration=157.0,
        total_shots=2,
        analysis_model="gemini",
        scene_threshold=27.0,
        shots=[
            ShotAnalysis(
                shot_number=1,
                start_time=0.0,
                end_time=8.0,
                duration=8.0,
                shot_size="MS",
                camera_angle="平视",
                camera_movement="固定",
                lighting_style="自然光",
                description="【【char_01_谭斌】】站在落地窗前。",
                dialogue="无",
                audio_layer=AudioLayer(),
            ),
            ShotAnalysis(
                shot_number=2,
                start_time=8.0,
                end_time=15.0,
                duration=7.0,
                shot_size="MCU",
                camera_angle="平视",
                camera_movement="固定",
                lighting_style="侧逆光",
                description="【【char_01_谭斌】】低头看手机。",
                dialogue="这周必须签约了。",
                audio_layer=AudioLayer(music="piano-8-15s"),
            ),
        ],
        output_dir=str(tmp_path),
        video_filename="格子间女人-第01集.mp4",
    )

    exporter = ObsidianExporter()
    output_path = exporter.export(result)

    assert output_path.exists()
    content = output_path.read_text(encoding="utf-8")
    assert "# 格子间女人-第01集 拉片分析" in content
    assert "char_01_谭斌" in content
    assert "MS" in content
    assert "157.0s" in content or "157" in content
    assert "## 分镜总览" in content
    assert "## 镜 01" in content
    assert "## 镜 02" in content
    assert "piano-8-15s" in content  # Audio Layer


def test_frontmatter(tmp_path):
    """测试 frontmatter 字段"""
    result = LapianResult(
        video_path="/test.mp4",
        video_id="test456",
        video_duration=30.0,
        total_shots=1,
        analysis_model="gemini",
        scene_threshold=27.0,
        shots=[],
        output_dir=str(tmp_path),
        video_filename="test.mp4",
    )
    exporter = ObsidianExporter()
    output_path = exporter.export(result)
    content = output_path.read_text(encoding="utf-8")
    assert content.startswith("---")
    assert "uid:" in content
    assert "title:" in content
    assert "created:" in content
    assert "tags:" in content
```

**Step 2: 运行测试验证失败**

```bash
cd ai-drama-studio
pytest tests/test_obsidian_exporter.py -v
```
Expected: ERROR - ModuleNotFoundError

**Step 3: 实现 `obsidian.py`**

```python
"""漫舟拉片智能体 - Obsidian 笔记导出器"""
import shutil
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..types import LapianResult, ShotAnalysis

logger = logging.getLogger(__name__)


def _fmt_time(seconds: float) -> str:
    """秒 → MM:SS 格式"""
    m = int(seconds // 60)
    s = seconds % 60
    return f"{m:02d}:{s:04.1f}"


def _fmt_range(start: float, end: float) -> str:
    return f"{_fmt_time(start)}–{_fmt_time(end)}"


def _build_frontmatter(result: LapianResult) -> str:
    date = datetime.now().strftime("%Y-%m-%d %H:%M")
    # 从文件名推断 series/episode（如有）
    name = Path(result.video_filename).stem
    return f"""---
uid: lapian-{result.video_id}
title: {name} 拉片分析
created: {date}
video: {result.video_filename}
video_duration: {result.video_duration:.1f}s
video_shots: {result.total_shots}
analysis_model: {result.analysis_model}
scene_threshold: {result.scene_threshold}
tags: [拉片分析]
---

"""


def _build_overview_table(shots: list[ShotAnalysis]) -> str:
    header = "| 镜 | 时间 | 时长 | 景别 | 角度 | 运镜 | 光影 | 景深 | 分镜描述 | 台词 |"
    sep = "|------|------|------|------|------|------|------|------|---------|------|"
    rows = []
    for s in shots:
        desc_short = s.description[:30] + ("..." if len(s.description) > 30 else "")
        rows.append(
            f"| {s.shot_number:02d} | {_fmt_range(s.start_time, s.end_time)} | "
            f"{s.duration:.1f}s | {s.shot_size} | {s.camera_angle} | "
            f"{s.camera_movement} | {s.lighting_style} | {s.depth_of_field} | "
            f"{desc_short} | {s.dialogue[:20] if s.dialogue != '无' else '无'} |"
        )
    return "\n".join([header, sep] + rows)


def _build_stats(shots: list[ShotAnalysis]) -> str:
    total = len(shots)
    fixed = sum(1 for s in shots if s.camera_movement == "固定")
    moving = total - fixed
    has_dialogue = sum(1 for s in shots if s.dialogue != "无")
    no_dialogue = total - has_dialogue
    avg_dur = sum(s.duration for s in shots) / total if total else 0
    return f"""> [!TIP] 场景统计
> - 全剧共 **{total}** 镜头
> - 固定镜头 **{fixed}** 个 / 运动镜头 **{moving}** 个
> - 有台词镜头 **{has_dialogue}** 个 / 无台词镜头 **{no_dialogue}** 个
> - 平均镜头时长：**{avg_dur:.1f}s**

"""


def _build_shot_detail(s: ShotAnalysis, video_id: str) -> str:
    """生成单个镜头的详细分析区块"""
    yaw_pitch = f"| **Yaw/Pitch**：{s.yaw}° / {s.pitch}°" if s.yaw or s.pitch else ""
    dolly_str = f"**Dolly**：{s.dolly}" if s.dolly != "z" else ""
    viseme_str = f"**【Viseme】** {s.viseme}\n" if s.viseme != "无" else ""

    # 关键帧嵌入
    frames_md = ""
    for fp in s.extracted_frames[:3]:
        fname = Path(fp).name
        frames_md += f"![[./.assets/{video_id}/{fname}]]\n"

    audio_md = s.audio_layer.to_markdown() if s.audio_layer else "无"

    return f"""## 镜 {s.shot_number:02d} | {_fmt_range(s.start_time, s.end_time)} | {s.duration:.1f}s

**景别**：{s.shot_size} | **角度**：{s.camera_angle} | **运镜**：{s.camera_movement} {dolly_str} {yaw_pitch}
**光影**：{s.lighting_style} | **色温**：{s.color_temperature}K | **景深**：{s.depth_of_field}

**【画面描述】**
{s.visual_description or "（无画面描述）"}

**【分镜描述】**
{s.description}

**【台词】** {s.dialogue}

{viseme_str}**【Audio Layer】**
```
{audio_md}
```

**【叙事功能】**：{s.narrative_function or '—'} | **【视觉钩子】**：{s.visual_hook or '—'} | **【道具】**：{s.props}

**【关键帧】**
{frames_md}

**【imagePrompt】**
> {s.imagePrompt}

**【videoPrompt】**
```
{s.videoPrompt}
```

**【转场】** → {s.transition}

---

"""


class ObsidianExporter:
    """生成 Obsidian Markdown 笔记"""

    def __init__(self, series: str = "", episode: str = ""):
        self.series = series
        self.episode = episode

    def export(self, result: LapianResult) -> Path:
        output_dir = Path(result.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # 笔记文件名
        stem = Path(result.video_filename).stem
        output_path = output_dir / f"{stem} 拉片分析.md"

        # 组装内容
        content_parts = []

        # Frontmatter
        content_parts.append(_build_frontmatter(result))

        # 标题
        content_parts.append(f"# {stem} 拉片分析\n")

        # 统计信息
        content_parts.append(f"> **分析时间**：{datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        content_parts.append(f"> **视频时长**：{result.video_duration:.1f}s | **镜头数**：{result.total_shots} | **AI模型**：{result.analysis_model}\n")
        content_parts.append(f"> **场景阈值**：{result.scene_threshold}\n\n")

        # 分镜总览表格
        if result.shots:
            content_parts.append("## 分镜总览\n\n")
            content_parts.append(_build_overview_table(result.shots) + "\n\n")
            content_parts.append(_build_stats(result.shots))

        # 各镜头详情
        for shot in result.shots:
            content_parts.append(_build_shot_detail(shot, result.video_id))

        # 写入文件
        content = "".join(content_parts)
        output_path.write_text(content, encoding="utf-8")
        logger.info(f"笔记已生成: {output_path}")

        return output_path
```

**Step 4: 运行测试验证通过**

```bash
cd ai-drama-studio
pytest tests/test_obsidian_exporter.py -v
```
Expected: PASS (2 tests)

**Step 5: Commit**

```bash
git add manzhou_lapian/exporters/obsidian.py tests/test_obsidian_exporter.py
git commit -m "feat(lapian): add ObsidianExporter for Markdown output"
```

---

## Task 7: 实现 CLI 入口

**Files:**
- Create: `ai-drama-studio/manzhou_lapian/__main__.py`
- Create: `ai-drama-studio/manzhou_lapian/cli.py`

**Step 1: 实现 `cli.py`**

```python
"""漫舟拉片智能体 - CLI 入口"""
import argparse
import asyncio
import logging
import sys
import time
from pathlib import Path

from .types import LapianConfig
from .pipeline import LapianPipeline
from .exporters.obsidian import ObsidianExporter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("manzhou_lapian")


def parse_args() -> LapianConfig:
    parser = argparse.ArgumentParser(
        prog="manzhou-lapian",
        description="漫舟拉片智能体 - 视频 → Obsidian 分镜笔记",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  manzhou-lapian 格子间女人-第01集.mp4
  manzhou-lapian input.mp4 -o ~/Obsidian/拉片分析
  manzhou-lapian input.mp4 -c ../cdp.json -m gemini --threshold 30.0
        """,
    )
    parser.add_argument(
        "video_path",
        help="视频文件路径（支持 MP4 / MOV / AVI / WebM）",
    )
    parser.add_argument(
        "-o", "--output",
        default="./拉片分析",
        help="Obsidian 笔记输出目录（默认：./拉片分析）",
    )
    parser.add_argument(
        "-c", "--cdp",
        default=None,
        help="CDP 资产库 JSON 文件路径",
    )
    parser.add_argument(
        "-m", "--model",
        default="gemini",
        choices=["zhipu", "claude", "gemini"],
        help="AI 分析模型（默认：gemini）",
    )
    parser.add_argument(
        "-t", "--threshold",
        type=float,
        default=27.0,
        help="PySceneDetect 场景阈值（默认：27.0）",
    )
    parser.add_argument(
        "-n", "--shots-per-shot",
        type=int,
        default=3,
        choices=[1, 2, 3, 4, 5],
        help="每镜头抽帧数量（默认：3）",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅测试 pipeline，不生成笔记",
    )

    args = parser.parse_args()

    return LapianConfig(
        video_path=args.video_path,
        output_dir=args.output,
        cdp_path=args.cdp,
        model=args.model,
        threshold=args.threshold,
        shots_per_shot=args.shots_per_shot,
        dry_run=args.dry_run,
    )


async def main_async(config: LapianConfig):
    pipeline = LapianPipeline(config)

    start_total = time.time()
    done_shots = 0

    def on_progress(phase: str, current: int, total: int):
        nonlocal done_shots
        if phase == "AI分析":
            done_shots = current
            total_shots = total
            pct = int(current / total * 100) if total else 0
            print(f"\r  ✓ 镜 {current:02d}/{total_shots} 完成 [{pct}%]  ", end="", flush=True)

    pipeline.set_progress_callback(on_progress)

    # 打印头部
    video_file = Path(config.video_path).name
    video_size = Path(config.video_path).stat().st_size if Path(config.video_path).exists() else 0
    size_str = f"{video_size / 1024 / 1024:.1f}MB" if video_size > 0 else "未知"

    print(f"◈ 漫舟拉片智能体 v1.0")
    print(f"│ 输入：{video_file}（{size_str}）")
    print(f"│ 输出：{config.output_dir}/")
    if config.cdp_path:
        print(f"│ CDP：{config.cdp_path}")
    print(f"│ 模型：{config.model} | 阈值：{config.threshold}")
    print()

    try:
        # Step 1: 标准化
        print(f"◈ [1/4] 视频标准化 → 720p 12fps ... ", end="", flush=True)
        t0 = time.time()
        result = await pipeline.run()
        print(f"done ({time.time()-t0:.0f}s)")

        # Step 2: 镜头检测（已在 pipeline 中）
        # Step 3: 抽帧（已在 pipeline 中）
        # Step 4: AI 分析（已在 pipeline 中）

        # Step 5: 生成笔记
        print(f"◈ [5/5] 生成 Obsidian 笔记 ... ", end="", flush=True)
        t1 = time.time()
        exporter = ObsidianExporter()
        output_path = exporter.export(result)
        print(f"done ({time.time()-t1:.0f}s)")

        elapsed = time.time() - start_total
        print()
        print(f"✓ 完成（{elapsed:.0f}s）")
        print(f"  📄 {output_path}")
        print(f"  📁 {result.output_dir}/.assets/{result.video_id}/（{sum(len(s.extracted_frames) for s in result.shots)}张关键帧）")

    except Exception as e:
        logger.error(f"执行失败: {e}")
        import traceback; traceback.print_exc()
        sys.exit(1)


def main():
    config = parse_args()

    # 验证输入文件
    if not Path(config.video_path).exists():
        print(f"✗ 错误：视频文件不存在：{config.video_path}", file=sys.stderr)
        sys.exit(1)

    asyncio.run(main_async(config))


if __name__ == "__main__":
    main()
```

**Step 2: 创建 `__main__.py`**

```python
"""支持 python -m manzhou_lapian 调用"""
from .cli import main

if __name__ == "__main__":
    main()
```

**Step 3: 验证 CLI 可以运行**

```bash
cd ai-drama-studio
python -m manzhou_lapian --help
```
Expected: 显示帮助信息

```bash
cd ai-drama-studio
python -m manzhou_lapian  # 无参数
```
Expected: 显示 usage 和错误

**Step 4: Commit**

```bash
git add manzhou_lapian/__main__.py manzhou_lapian/cli.py
git commit -m "feat(lapian): add CLI entry point"
```

---

## Task 8: 清理前端代码

**Files:**
- Delete: `ai-drama-studio/src/` 目录
- Delete: `ai-drama-studio/routes.py`（SSE路由）
- Modify: `ai-drama-studio/package.json`（精简依赖）

**Step 1: 确认要删除的文件**

```bash
# 查看前端文件
ls ai-drama-studio/src/
ls ai-drama-studio/routes.py 2>/dev/null && echo "存在" || echo "不存在"
```

**Step 2: 删除前端目录**

```bash
rm -rf ai-drama-studio/src/
```

**Step 3: 检查 routes.py 是否存在**

如果存在，删除 SSE 相关内容，保留 FastAPI 必要部分：

```python
# 保留: main.py 中的 FastAPI app 实例创建（如果有）
# 删除: SSE /stream/{job_id} 和 /upload 路由
# 保留: health check 端点（如有）
```

**Step 4: 精简 package.json**

保留：react-scripts dev 依赖（如果有其他工具依赖）
如果只有前端依赖，可以简化为空的 `package.json` 或删除

**Step 5: Commit**

```bash
git add -A
git commit -m "refactor(lapian): remove React frontend, keep backend pipeline"
```

---

## Task 9: 端到端测试

**Files:**
- 使用真实视频文件测试完整流程

**Step 1: 准备测试视频**

```bash
# 查找已有的测试视频
ls ai-drama-studio/backend/standardized/
```

**Step 2: 运行完整流程**

```bash
cd ai-drama-studio
python -m manzhou_lapian \
    ../backend/standardized/std_xxxxxxxx.mp4 \
    -o /tmp/test-lapian-output \
    -m gemini \
    --threshold 27.0
```

**Step 3: 验证输出**

```bash
# 检查笔记文件
ls /tmp/test-lapian-output/
cat /tmp/test-lapian-output/*.md | head -100

# 检查关键帧
ls /tmp/test-lapian-output/.assets/*/

# 验证格式
# - frontmatter 存在
# - 分镜总览表格存在
# - 镜 01 / 镜 02 详情存在
# - imagePrompt / videoPrompt 存在
# - Audio Layer 四分栏存在
```

**Step 4: Commit**

```bash
git add -A
git commit -m "test(lapian): end-to-end test with real video"
```

---

## Task 10: 更新 MEMORY.md

**Step 1: 更新仪表盘状态**

将 MEMORY.md 中：
```
**当前阶段**：... → **🔄 漫舟拉片智能体重构中**
```

改为：
```
**当前阶段**：... → **✅ 漫舟拉片智能体v1.0完成**
```

**Step 2: 添加启动命令说明**

更新 MEMORY.md 的"一键拉片Agent"部分，添加新的 CLI 用法：
```markdown
**启动命令（CLI）**：
```bash
cd ai-drama-studio
python -m manzhou_lapian <视频路径> [选项]
```
```

---

## 依赖清单

```bash
# 新增依赖（requirements.txt）
jinja2>=3.1.0

# 已存在依赖（复用 backend/venv）
ffmpeg（系统命令）
scenedetect
openai
anthropic
google-generativeai
httpx
```

---

## 风险清单

| # | 风险 | 概率 | 影响 | 对策 |
|---|------|------|------|------|
| 1 | AI 输出 JSON 格式不稳定 | 中 | 中 | normalize_tapnow 加字段默认值兜底 |
| 2 | 帧图片路径含中文导致乱码 | 低 | 高 | 统一用 video_id 命名，不使用原始文件名 |
| 3 | 镜头数过多（>100）token 溢出 | 中 | 高 | 分批分析（每批 20 镜），进度实时写入 |
| 4 | CDP 角色未识别（AI 漏标） | 中 | 低 | 降级处理，仅用通用描述 |

---

## 实施顺序

```
Phase 1（Task 1-3）→ 基础设施（types / cdp / prompts）
Phase 2（Task 4）  → AIAnalyzer 扩展
Phase 3（Task 5-6）→ Pipeline + Exporter
Phase 4（Task 7）  → CLI 入口
Phase 5（Task 8）  → 清理前端
Phase 6（Task 9）  → 端到端测试
Phase 7（Task 10） → MEMORY.md 更新
```

**建议每个 Task 单独 commit，保持原子性。**
