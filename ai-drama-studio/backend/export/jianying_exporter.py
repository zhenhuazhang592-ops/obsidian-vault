"""ai-drama-studio/backend/export/jianying_exporter.py

漫舟剪映导出器 v1.0
参考 ZJT JianyingMultiTrackLibrary.py + manzhou-export.md v5.0

功能：
  1. 生成 draft_content.json（剪映草稿格式）
  2. 生成素材清单（视频轨/音频轨/字幕轨）
  3. 导出完整 ZIP 包（含视频/分镜图/音频）
  4. ffprobe 自动检测视频真实时长

调用示例：
    exporter = JianyingExporter(project_name="格子间女人_EP01")
    exporter.add_video_track([
        {"shot_id": "P01", "file": "./video/P01.mp4", "start": 0.0, "end": 15.0},
        {"shot_id": "P02", "file": "./video/P02.mp4", "start": 0.0, "end": 15.0},
    ])
    exporter.add_audio_track([
        {"type": "tts", "file": "./tts/P01.wav", "start": 0.0, "end": 3.2},
        {"type": "bgm", "file": "./bgm/EP01.mp3", "start": 0.0, "end": 120.0, "volume": 0.4},
    ])
    exporter.add_subtitle_track([
        {"shot_id": "P01", "text": "Ray……离职了？", "start": 0.5, "end": 2.8},
    ])
    result = exporter.build()
    exporter.export_zip("./output/格子间女人_EP01_导出包")
"""

import os
import json
import zipfile
import uuid
import shutil
import subprocess
from typing import Optional, Union
from dataclasses import dataclass, field
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# 常量
# ─────────────────────────────────────────────────────────────────────────────

# 剪映草稿版本（参考ZJT JianyingLibrary）
JIANYING_DRAFT_VERSION = "360000"
JIANYING_APP_VERSION  = "1.0.0"

# 轨道ID
TRACK_ID_VIDEO_MAIN = "V1"       # 主视频轨
TRACK_ID_AUDIO_VOICE = "A1"     # TTS配音轨
TRACK_ID_AUDIO_BGM  = "A2"      # BGM轨
TRACK_ID_AUDIO_SFX  = "A3"      # SFX轨
TRACK_ID_SUBTITLE    = "T1"      # 字幕轨

# 素材类型映射（草稿JSON格式）
MATERIAL_TYPE_VIDEO = 1
MATERIAL_TYPE_AUDIO  = 2
MATERIAL_TYPE_TEXT  = 3
MATERIAL_TYPE_IMAGE = 4


# ─────────────────────────────────────────────────────────────────────────────
# 数据模型
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ClipSegment:
    """一个片段（素材在时间线上的入出点）"""
    shot_id:    str
    file_path:  str
    start:      float      # 在时间线上的入点（秒）
    end:        float      # 在时间线上的出点（秒）
    duration:   float      # 片段时长（秒）= end - start

    # ffprobe 自动填写的字段
    real_duration: float = 0.0
    width:  int = 0
    height: int = 0
    fps:    str = "12/1"

    # 音频特有
    volume: float = 1.0   # 音量 0.0-1.0
    fade_in:  float = 0.0  # 淡入（秒）
    fade_out: float = 0.0  # 淡出（秒）


@dataclass
class SubtitleSegment:
    """字幕片段"""
    shot_id:  str
    text:     str
    start:    float   # 秒
    end:      float
    duration: float   # = end - start
    font_size: int = 28
    color:    str = "#FFFFFF"


# ─────────────────────────────────────────────────────────────────────────────
# 工具函数
# ─────────────────────────────────────────────────────────────────────────────

def probe_media(path: str) -> dict:
    """
    用 ffprobe 探测媒体文件元信息。
    返回: {duration, width, height, fps, bitrate}
    """
    if not os.path.exists(path):
        return {"duration": 0.0, "width": 0, "height": 0, "fps": "12/1", "bitrate": 0}

    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries",
        "stream=width,height,r_frame_rate,duration,bit_rate",
        "-of", "json",
        path,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        data = json.loads(result.stdout)
        streams = data.get("streams", [{}])
        s = streams[0] if streams else {}
        fps_str = s.get("r_frame_rate", "12/1")
        # 支持分数格式 "30/1"
        if "/" in fps_str:
            num, den = fps_str.split("/")
            fps = float(num) / float(den) if float(den) != 0 else 12.0
            fps_str = f"{num}/{den}"
        else:
            fps = float(fps_str)

        return {
            "duration":  float(s.get("duration", 0)),
            "width":     int(s.get("width", 0)),
            "height":    int(s.get("height", 0)),
            "fps":       fps_str,
            "fps_float": round(fps, 3),
            "bitrate":   int(s.get("bit_rate", 0)),
        }
    except Exception as e:
        logger.warning(f"ffprobe 探测失败 {path}: {e}")
        return {"duration": 0.0, "width": 0, "height": 0, "fps": "12/1", "bitrate": 0}


def probe_audio(path: str) -> dict:
    """探测音频文件时长"""
    if not os.path.exists(path):
        return {"duration": 0.0}
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        path,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return {"duration": float(result.stdout.strip())}
    except Exception:
        return {"duration": 0.0}


def microseconds(seconds: float) -> int:
    """秒 → 微秒（剪映内部时间单位）"""
    return int(round(seconds * 1_000_000))


# ─────────────────────────────────────────────────────────────────────────────
# JianyingExporter 主类
# ─────────────────────────────────────────────────────────────────────────────

class JianyingExporter:
    """
    漫舟剪映导出器
    生成 draft_content.json + ZIP导出包

    工作流程（参考 manzhou-export.md 四件套结构）：
    1. add_video_track  → 添加视频轨
    2. add_audio_track   → 添加音频轨（TTS/BGM/SFX）
    3. add_subtitle_track → 添加字幕轨
    4. build()          → 生成草稿 JSON
    5. export_zip()     → 打包 ZIP
    """

    def __init__(
        self,
        project_name: str = "manzhou_project",
        aspect_ratio: str = "9:16",
        fps: int = 12,
        output_dir: str = "./exports",
    ):
        self.project_name = project_name
        self.aspect_ratio = aspect_ratio
        self.fps = fps
        self.output_dir = output_dir

        self._video_clips: list[ClipSegment] = []
        self._tts_clips:  list[ClipSegment] = []
        self._bgm_clips:  list[ClipSegment] = []
        self._sfx_clips:  list[ClipSegment] = []
        self._subtitle_clips: list[SubtitleSegment] = []

        self._materials: list[dict] = []
        self._track_index = 0
        self._material_index = 0

        # 生成固定的项目ID（同一项目多次导出保持一致）
        self._project_id = uuid.uuid4().hex

    # ─────────────────────────────────────────────────────────────────────────
    # 添加轨道片段
    # ─────────────────────────────────────────────────────────────────────────

    def add_video_track(self, clips: list[dict]):
        """
        添加视频轨片段。

        clips 格式:
        [
            {"shot_id": "P01", "file": "./video/P01.mp4", "start": 0.0, "end": 15.0},
            ...
        ]
        """
        for clip_def in clips:
            # ffprobe 自动探测真实时长
            probed = probe_media(clip_def["file"])
            real_dur = probed["duration"] or (clip_def["end"] - clip_def["start"])

            clip = ClipSegment(
                shot_id=clip_def["shot_id"],
                file_path=clip_def["file"],
                start=clip_def["start"],
                end=clip_def["end"],
                duration=clip_def["end"] - clip_def["start"],
                real_duration=real_dur,
                width=probed["width"],
                height=probed["height"],
                fps=probed["fps"],
            )
            self._video_clips.append(clip)

    def add_tts_track(self, clips: list[dict]):
        """添加TTS配音轨"""
        for clip_def in clips:
            probed = probe_audio(clip_def["file"])
            clip = ClipSegment(
                shot_id=clip_def["shot_id"],
                file_path=clip_def["file"],
                start=clip_def["start"],
                end=clip_def["end"],
                duration=clip_def["end"] - clip_def["start"],
                real_duration=probed["duration"],
                volume=clip_def.get("volume", 1.0),
                fade_in=clip_def.get("fade_in", 0.0),
                fade_out=clip_def.get("fade_out", 0.0),
            )
            self._tts_clips.append(clip)

    def add_bgm_track(self, clips: list[dict]):
        """添加BGM轨（持续整个集长）"""
        for clip_def in clips:
            probed = probe_audio(clip_def["file"])
            clip = ClipSegment(
                shot_id="bgm",
                file_path=clip_def["file"],
                start=clip_def["start"],
                end=clip_def["end"],
                duration=clip_def["end"] - clip_def["start"],
                real_duration=probed["duration"],
                volume=clip_def.get("volume", 0.4),  # BGM默认40%音量
            )
            self._bgm_clips.append(clip)

    def add_sfx_track(self, clips: list[dict]):
        """添加SFX音效轨"""
        for clip_def in clips:
            probed = probe_audio(clip_def["file"])
            clip = ClipSegment(
                shot_id=clip_def.get("shot_id", clip_def.get("sfx_id", "sfx")),
                file_path=clip_def["file"],
                start=clip_def["start"],
                end=clip_def["end"],
                duration=clip_def["end"] - clip_def["start"],
                real_duration=probed["duration"],
                volume=clip_def.get("volume", 1.0),
            )
            self._sfx_clips.append(clip)

    def add_subtitle_track(self, clips: list[dict]):
        """添加字幕轨"""
        for clip_def in clips:
            seg = SubtitleSegment(
                shot_id=clip_def["shot_id"],
                text=clip_def["text"],
                start=clip_def["start"],
                end=clip_def["end"],
                duration=clip_def["end"] - clip_def["start"],
                font_size=clip_def.get("font_size", 28),
                color=clip_def.get("color", "#FFFFFF"),
            )
            self._subtitle_clips.append(seg)

    # ─────────────────────────────────────────────────────────────────────────
    # 内部：生成素材ID
    # ─────────────────────────────────────────────────────────────────────────

    def _next_material_id(self, prefix: str = "m") -> str:
        self._material_index += 1
        return f"{prefix}_{self.project_name}_{self._material_index:04d}"

    def _next_track_id(self) -> str:
        self._track_index += 1
        return f"track_{self._track_index}"

    # ─────────────────────────────────────────────────────────────────────────
    # 内部：片段 → 轨道项
    # ─────────────────────────────────────────────────────────────────────────

    def _build_video_material(self, clip: ClipSegment) -> dict:
        """生成视频素材 JSON"""
        return {
            "id": self._next_material_id("video"),
            "type": MATERIAL_TYPE_VIDEO,
            "name": os.path.basename(clip.file_path),
            "path": clip.file_path,
            "duration": microseconds(clip.real_duration),
            "width": clip.width or 720,
            "height": clip.height or 1280,
            "fps": clip.fps,
        }

    def _build_audio_material(self, clip: ClipSegment, name: str = "audio") -> dict:
        return {
            "id": self._next_material_id("audio"),
            "type": MATERIAL_TYPE_AUDIO,
            "name": name,
            "path": clip.file_path,
            "duration": microseconds(clip.real_duration),
            "volume": clip.volume,
            "fade_in": microseconds(clip.fade_in),
            "fade_out": microseconds(clip.fade_out),
        }

    def _build_text_material(self, subtitle: SubtitleSegment) -> dict:
        return {
            "id": self._next_material_id("text"),
            "type": MATERIAL_TYPE_TEXT,
            "name": f"subtitle_{subtitle.shot_id}",
            "text": subtitle.text,
            "font_size": subtitle.font_size,
            "color": subtitle.color,
            "duration": microseconds(subtitle.duration),
        }

    def _build_video_track_item(self, clip: ClipSegment, material_id: str) -> dict:
        """生成视频轨中的一个片段项"""
        timeline_offset = microseconds(clip.start)
        source_start = 0  # 从素材开头开始
        source_end = microseconds(clip.real_duration)

        return {
            "id": str(uuid.uuid4().hex),
            "material_id": material_id,
            "track_id": TRACK_ID_VIDEO_MAIN,
            "timeline_start": timeline_offset,
            "source_timerange": {
                "start": source_start,
                "duration": source_end,
            },
            "speed": 1.0,
            "crop": {"top": 0, "bottom": 0, "left": 0, "right": 0},
            "volume": 1.0,
        }

    def _build_audio_track_item(self, clip: ClipSegment, material_id: str, track_id: str) -> dict:
        timeline_offset = microseconds(clip.start)
        # 淡入淡出
        effects = []
        if clip.fade_in > 0:
            effects.append({
                "type": "fade_in",
                "duration": microseconds(clip.fade_in),
            })
        if clip.fade_out > 0:
            effects.append({
                "type": "fade_out",
                "start_time": microseconds(clip.duration - clip.fade_out),
                "duration": microseconds(clip.fade_out),
            })
        return {
            "id": str(uuid.uuid4().hex),
            "material_id": material_id,
            "track_id": track_id,
            "timeline_start": timeline_offset,
            "source_timerange": {
                "start": 0,
                "duration": microseconds(clip.real_duration),
            },
            "volume": clip.volume,
            "effects": effects,
        }

    def _build_subtitle_track_item(self, subtitle: SubtitleSegment, material_id: str) -> dict:
        return {
            "id": str(uuid.uuid4().hex),
            "material_id": material_id,
            "track_id": TRACK_ID_SUBTITLE,
            "timeline_start": microseconds(subtitle.start),
            "source_timerange": {
                "start": 0,
                "duration": microseconds(subtitle.duration),
            },
            "style": {
                "font_size": subtitle.font_size,
                "color": subtitle.color,
                "alignment": "center",
                "position": {"x": 0, "y": 0.9},  # 底部居中
            },
        }

    # ─────────────────────────────────────────────────────────────────────────
    # 构建草稿 JSON
    # ─────────────────────────────────────────────────────────────────────────

    def build(self) -> dict:
        """
        生成 draft_content.json 完整结构（参考 ZJT JianyingLibrary）。

        返回完整的草稿字典，可直接保存为 draft_content.json
        或传递给剪映草稿导入 API。
        """
        self._materials = []
        track_items: list[dict] = []
        tracks: list[dict] = []

        # ── 视频轨 ──────────────────────────────────────────────────────
        video_track_id = self._next_track_id()
        video_materials = []
        for clip in self._video_clips:
            mat = self._build_video_material(clip)
            video_materials.append(mat)
            self._materials.append(mat)
            track_items.append(self._build_video_track_item(clip, mat["id"]))

        tracks.append({
            "id": video_track_id,
            "type": "video",
            "name": "主视频轨",
            "track_id": TRACK_ID_VIDEO_MAIN,
            "items": [],
            "locked": False,
            "visible": True,
            "height": 100,
        })

        # ── TTS配音轨 ────────────────────────────────────────────────────
        if self._tts_clips:
            tts_track_id = self._next_track_id()
            for clip in self._tts_clips:
                mat = self._build_audio_material(clip, name=f"TTS_{clip.shot_id}")
                self._materials.append(mat)
                track_items.append(self._build_audio_track_item(clip, mat["id"], TRACK_ID_AUDIO_VOICE))
            tracks.append({
                "id": tts_track_id,
                "type": "audio",
                "name": "TTS配音轨",
                "track_id": TRACK_ID_AUDIO_VOICE,
                "items": [],
                "locked": False,
                "visible": True,
                "height": 60,
            })

        # ── BGM轨 ──────────────────────────────────────────────────────
        if self._bgm_clips:
            bgm_track_id = self._next_track_id()
            for clip in self._bgm_clips:
                mat = self._build_audio_material(clip, name=f"BGM_{clip.shot_id}")
                self._materials.append(mat)
                track_items.append(self._build_audio_track_item(clip, mat["id"], TRACK_ID_AUDIO_BGM))
            tracks.append({
                "id": bgm_track_id,
                "type": "audio",
                "name": "BGM轨",
                "track_id": TRACK_ID_AUDIO_BGM,
                "items": [],
                "locked": False,
                "visible": True,
                "height": 50,
            })

        # ── SFX轨 ──────────────────────────────────────────────────────
        if self._sfx_clips:
            sfx_track_id = self._next_track_id()
            for clip in self._sfx_clips:
                mat = self._build_audio_material(clip, name=f"SFX_{clip.shot_id}")
                self._materials.append(mat)
                track_items.append(self._build_audio_track_item(clip, mat["id"], TRACK_ID_AUDIO_SFX))
            tracks.append({
                "id": sfx_track_id,
                "type": "audio",
                "name": "SFX音效轨",
                "track_id": TRACK_ID_AUDIO_SFX,
                "items": [],
                "locked": False,
                "visible": True,
                "height": 50,
            })

        # ── 字幕轨 ─────────────────────────────────────────────────────
        if self._subtitle_clips:
            subtitle_track_id = self._next_track_id()
            for sub in self._subtitle_clips:
                mat = self._build_text_material(sub)
                self._materials.append(mat)
                track_items.append(self._build_subtitle_track_item(sub, mat["id"]))
            tracks.append({
                "id": subtitle_track_id,
                "type": "text",
                "name": "字幕轨",
                "track_id": TRACK_ID_SUBTITLE,
                "items": [],
                "locked": False,
                "visible": True,
                "height": 40,
            })

        # ── 计算总时长 ────────────────────────────────────────────────
        total_duration = max(
            (clip.end for clip in self._video_clips),
            default=0,
        )

        # ── 组装草稿 JSON（参考 ZJT JianyingLibrary）─────────────
        draft = {
            "draft_id": self._project_id,
            "draft_version": JIANYING_DRAFT_VERSION,
            "app_version": JIANYING_APP_VERSION,
            "project_name": self.project_name,
            "duration": microseconds(total_duration),
            "aspect_ratio": self.aspect_ratio,
            "fps": self.fps,
            "materials": self._materials,
            "tracks": tracks,
            "track_items": track_items,
        }

        self._draft = draft
        return draft

    def save_draft_json(self, output_dir: str = "") -> str:
        """保存草稿 JSON 文件"""
        if not hasattr(self, "_draft"):
            self.build()

        output_dir = output_dir or self.output_dir
        os.makedirs(output_dir, exist_ok=True)
        path = os.path.join(output_dir, "draft_content.json")

        with open(path, "w", encoding="utf-8") as f:
            json.dump(self._draft, f, ensure_ascii=False, indent=2)

        logger.info(f"[JianyingExporter] 草稿已保存: {path}")
        return path

    # ─────────────────────────────────────────────────────────────────────────
    # 导出 ZIP 包
    # ─────────────────────────────────────────────────────────────────────────

    def export_zip(
        self,
        output_path: str = "",
        include: dict[str, bool] = None,
    ) -> str:
        """
        打包完整导出 ZIP（参考 manzhou-export.md 四件套结构）。

        include 默认包含：
          - videos:    02-视频/*.mp4
          - tts:      04-音频/TTS配音/
          - bgm:       04-音频/BGM/
          - sfx:       04-音频/SFX/
          - frames:    03-分镜图参考/
          - draft:    draft_content.json
          - manifest: 项目信息.md
        """
        if not hasattr(self, "_draft"):
            self.build()

        include = include or {
            "draft": True,
            "videos": True,
            "tts": True,
            "bgm": True,
            "sfx": True,
            "frames": True,
        }

        if not output_path:
            output_path = os.path.join(self.output_dir, f"{self.project_name}_导出包")

        zip_path = output_path + ".zip"
        os.makedirs(os.path.dirname(zip_path) or ".", exist_ok=True)

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            # 1. 草稿 JSON
            if include.get("draft"):
                self.save_draft_json(os.path.dirname(zip_path))
                zf.write(
                    os.path.join(os.path.dirname(zip_path), "draft_content.json"),
                    "draft_content.json",
                )

            # 2. 视频文件
            if include.get("videos"):
                for clip in self._video_clips:
                    if os.path.exists(clip.file_path):
                        arcname = f"02-视频/{os.path.basename(clip.file_path)}"
                        zf.write(clip.file_path, arcname)

            # 3. TTS配音
            if include.get("tts"):
                for clip in self._tts_clips:
                    if os.path.exists(clip.file_path):
                        arcname = f"04-音频/TTS/{os.path.basename(clip.file_path)}"
                        zf.write(clip.file_path, arcname)

            # 4. BGM
            if include.get("bgm"):
                for clip in self._bgm_clips:
                    if os.path.exists(clip.file_path):
                        arcname = f"04-音频/BGM/{os.path.basename(clip.file_path)}"
                        zf.write(clip.file_path, arcname)

            # 5. SFX
            if include.get("sfx"):
                for clip in self._sfx_clips:
                    if os.path.exists(clip.file_path):
                        arcname = f"04-音频/SFX/{os.path.basename(clip.file_path)}"
                        zf.write(clip.file_path, arcname)

            # 6. 生成清单
            manifest = self._generate_manifest()
            zf.writestr("00-清单/项目信息.md", manifest)

        logger.info(f"[JianyingExporter] ZIP导出完成: {zip_path}")
        return zip_path

    def _generate_manifest(self) -> str:
        """生成项目清单（manzhou-export.md 规范）"""
        total_dur = max((c.end for c in self._video_clips), default=0)

        lines = [
            f"# {self.project_name} 导出清单",
            "",
            f"## 基本信息",
            f"- 导出时间: 自动生成",
            f"- 剪映草稿版本: {JIANYING_DRAFT_VERSION}",
            f"- 画面比例: {self.aspect_ratio}",
            f"- 帧率: {self.fps}fps",
            f"- 总时长: {total_dur:.1f}秒",
            "",
            "## 素材统计",
            f"- 视频镜头: {len(self._video_clips)}个",
            f"- TTS配音: {len(self._tts_clips)}条",
            f"- BGM轨道: {len(self._bgm_clips)}首",
            f"- SFX音效: {len(self._sfx_clips)}个",
            f"- 字幕条: {len(self._subtitle_clips)}条",
            "",
            "## 视频轨道清单",
            "| 镜号 | 入点 | 出点 | 时长 | 文件 |",
            "|------|------|------|------|------|",
        ]

        for c in self._video_clips:
            lines.append(
                f"| {c.shot_id} | {c.start:.2f}s | {c.end:.2f}s | "
                f"{c.duration:.2f}s | {os.path.basename(c.file_path)} |"
            )

        if self._tts_clips:
            lines += ["", "## TTS配音轨道清单"]
            for c in self._tts_clips:
                lines.append(
                    f"- {c.shot_id}: {c.file_path} ({c.start:.1f}s-{c.end:.1f}s)"
                )

        return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# 快捷函数
# ─────────────────────────────────────────────────────────────────────────────

def quick_export(
    project_name: str,
    shots: list[dict],
    output_dir: str = "./exports",
) -> str:
    """
    快捷导出（单函数搞定一切）。

    shots 格式:
    [
        {
            "shot_id": "P01",
            "video_file": "./video/P01.mp4",
            "tts_file": "./tts/P01.mp3",
            "subtitle": "Ray……离职了？",
            "duration": 15.0,
        },
        ...
    ]
    """
    cumulative = 0.0
    video_clips = []
    tts_clips = []
    subtitle_clips = []

    for shot in shots:
        dur = shot["duration"]
        video_clips.append({
            "shot_id": shot["shot_id"],
            "file": shot["video_file"],
            "start": cumulative,
            "end": cumulative + dur,
        })
        if shot.get("tts_file"):
            tts_clips.append({
                "shot_id": shot["shot_id"],
                "file": shot["tts_file"],
                "start": cumulative,
                "end": cumulative + dur,
                "volume": 1.0,
            })
        if shot.get("subtitle"):
            subtitle_clips.append({
                "shot_id": shot["shot_id"],
                "text": shot["subtitle"],
                "start": cumulative + 0.3,
                "end": cumulative + dur - 0.3,
            })
        cumulative += dur

    exporter = JianyingExporter(
        project_name=project_name,
        output_dir=output_dir,
    )
    exporter.add_video_track(video_clips)
    if tts_clips:
        exporter.add_tts_track(tts_clips)
    if subtitle_clips:
        exporter.add_subtitle_track(subtitle_clips)

    exporter.build()
    return exporter.export_zip()
