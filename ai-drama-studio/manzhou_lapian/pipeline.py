"""漫舟拉片智能体 - Pipeline 串联器"""
import asyncio
import logging
import uuid
import sys
from pathlib import Path
from typing import Callable, Optional

# manzhou_lapian 位于 ai-drama-studio/，backend/ 是兄弟目录
_backend_dir = str(Path(__file__).parent.parent / "backend")
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from pipeline.ffmpeg_preprocess import FFmpegPreprocessor
from pipeline.scene_detect import SceneDetector
from pipeline.frame_extract import FrameExtractor
from pipeline.ai_analyzer import AIAnalyzer
from manzhou_lapian.types import LapianConfig, LapianResult, ShotAnalysis, CDPData
from manzhou_lapian.cdp import CDPReader
from manzhou_lapian.prompts import build_system_prompt

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

        # ── Step 0: 确保标准化目录存在 ─────────────────────────────
        # config 使用相对路径 ./standardized/（相对于 backend/ 运行）
        import config as _cfg
        std_dir = Path(_cfg.config.STANDARDIZED_DIR)
        # 如果是相对路径，以 backend/ 为基准
        if not std_dir.is_absolute():
            std_dir = Path(__file__).parent.parent / "backend" / std_dir
        std_dir.mkdir(parents=True, exist_ok=True)

        # ── Step 1: 标准化 ─────────────────────────────────────────
        self._emit("标准化", 0, 1)
        preprocessor = FFmpegPreprocessor()
        std_path, metadata = preprocessor.standardize(video_path)
        duration = metadata.get("duration", 0)
        self._emit("标准化", 1, 1)

        # ── Step 2: 镜头检测 ───────────────────────────────────────
        self._emit("镜头检测", 0, 1)
        import config as _cfg
        _cfg.config.SCENE_THRESHOLD = self.cfg.threshold  # 覆盖 CLI 指定值
        detector = SceneDetector()
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
            # frame_result: {shot_id, frames: list[dict], keyframe_times: list[float]}
            frame_dicts = frame_result.get("frames", [])
            keyframe_times = frame_result.get("keyframe_times",
                                               [shot["start_time"],
                                                shot["end_time"]])

            # 替换为绝对路径（analyzer 用 frame["filename"] 查找文件）
            for fd in frame_dicts:
                fd["filename"] = str(frame_dir / fd["filename"])

            # 构建 Prompt（CDP 上下文注入 system prompt）
            system_prompt = build_system_prompt(
                shot_number=shot["shot_id"],
                start_time=shot["start_time"],
                end_time=shot["end_time"],
                duration=shot["duration_sec"],
                keyframe_times=keyframe_times,
                cdp_data=cdp_data,
            )

            # AI 分析
            result = await analyzer.analyze_shot_sync(
                shot_id=shot["shot_id"],
                start_time=shot["start_time"],
                end_time=shot["end_time"],
                duration=shot["duration_sec"],
                frame_paths=frame_dicts,
                job_id=video_id,
                shot_context="",  # CDP 上下文已在 system prompt 中
            )

            # 标准化为 TapNow 格式
            shot_analysis = AIAnalyzer.normalize_tapnow(result)
            shot_analysis.extracted_frames = [
                str(frame_dir / f["filename"]) for f in frame_dicts
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
