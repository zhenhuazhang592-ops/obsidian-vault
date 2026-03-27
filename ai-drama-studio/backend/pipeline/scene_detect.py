"""ai-drama-studio/backend/pipeline/scene_detect.py"""
from scenedetect import open_video, SceneManager
from scenedetect.detectors import ContentDetector
from config import config
import logging

logger = logging.getLogger("pyscenedetect")


class SceneDetector:
    """PySceneDetect 镜头边界检测器

    使用 ContentDetector，基于 HSV 色彩空间逐帧比对，
    检测画面主体/场景变化触发镜头切分。
    """

    def __init__(self):
        self.threshold = config.SCENE_THRESHOLD  # 27.0（短视频/动画推荐值）
        self.min_scene_len = config.MIN_SCENE_LEN  # 15帧，防止误检

    def detect(self, video_path: str) -> list[dict]:
        """
        执行镜头边界检测。

        Returns:
            List[dict]: 每个镜头的 {shot_id, start_time, end_time, duration_sec}
        """
        video = open_video(video_path)
        scene_manager = SceneManager()

        detector = ContentDetector(
            threshold=self.threshold,
            min_scene_len=self.min_scene_len,
        )
        scene_manager.add_detector(detector)
        scene_manager.detect_scenes(video, show_progress=False)

        scene_list = scene_manager.get_scene_list()

        shots = []
        for i, (start, end) in enumerate(scene_list):
            start_sec = start.get_seconds()
            end_sec = end.get_seconds()
            duration = end_sec - start_sec

            shots.append({
                "shot_id": i + 1,
                "start_time": start_sec,
                "end_time": end_sec,
                "duration_sec": round(duration, 3),
                "start_frame": start.get_frames(),
                "end_frame": end.get_frames(),
            })

        logger.info(f"检测到 {len(shots)} 个镜头")
        return shots
