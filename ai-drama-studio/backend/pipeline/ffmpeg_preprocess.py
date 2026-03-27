"""ai-drama-studio/backend/pipeline/ffmpeg_preprocess.py"""
import subprocess
import os
import uuid
import json
from config import config


class FFmpegPreprocessor:
    """FFmpeg 视频预处理管线：标准化 → 压缩 → 格式统一"""

    def __init__(self):
        self.height = config.STANDARDIZED_HEIGHT  # 720
        self.fps = config.STANDARDIZED_FPS          # 12

    def standardize(self, input_path: str) -> tuple[str, dict]:
        """
        执行 FFmpeg 标准化转换。

        Returns:
            output_path: 标准化后的视频路径
            metadata: 视频元数据（时长、分辨率、帧率）
        """
        video_id = uuid.uuid4().hex[:8]
        output_filename = f"std_{video_id}.mp4"
        output_path = os.path.join(config.STANDARDIZED_DIR, output_filename)

        # 获取原始元数据
        metadata = self._get_metadata(input_path)

        # FFmpeg 命令
        cmd = [
            "ffmpeg",
            "-y",                              # 覆盖输出
            "-i", input_path,                  # 输入文件
            "-vf", f"scale=-2:{self.height},fps={self.fps}",  # 等比缩放至720p，12fps
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "28",                     # 压缩质量
            "-c:a", "aac",
            "-b:a", "128k",
            output_path
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg failed: {result.stderr}")

        # 获取输出文件元数据
        output_metadata = self._get_metadata(output_path)
        output_metadata["output_path"] = output_path

        return output_path, output_metadata

    def _get_metadata(self, video_path: str) -> dict:
        """用 ffprobe 获取视频元数据"""
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            video_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        data = json.loads(result.stdout)

        video_stream = next(
            (s for s in data["streams"] if s["codec_type"] == "video"), {}
        )

        # r_frame_rate 格式为 "30/1" → 30.0
        fps_str = video_stream.get("r_frame_rate", "0/1")
        if "/" in fps_str:
            num, den = fps_str.split("/")
            fps = float(num) / float(den)
        else:
            fps = float(fps_str)

        return {
            "duration": float(data["format"].get("duration", 0)),
            "width": video_stream.get("width", 0),
            "height": video_stream.get("height", 0),
            "fps": fps,
        }
