"""ai-drama-studio/backend/pipeline/frame_extract.py"""
import cv2
import os
from config import config


class FrameExtractor:
    """动态抽帧器：根据镜头时长智能选择抽帧位置"""

    def extract_shot_frames(
        self,
        video_path: str,
        fps: float,
        shots: list[dict],
        output_dir: str,
        job_id: str = "",
    ) -> list[dict]:
        """
        对每个镜头执行动态抽帧。

        抽帧策略（与方案文档完全一致）：
        - 时长 < 1s:   抽 1 帧（中间帧）
        - 1s ≤ 时长 ≤ 3s: 抽 2 帧（前20% + 后80%）
        - 时长 > 3s:  抽 3 帧（前10% + 中间 + 后90%）

        Returns:
            List[dict]: 每个镜头的 frame_paths（含相对URL）
        """
        os.makedirs(output_dir, exist_ok=True)
        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            raise RuntimeError(f"无法打开视频: {video_path}")

        results = []

        for shot in shots:
            start_frame = shot["start_frame"]
            end_frame = shot["end_frame"]
            duration_frames = end_frame - start_frame
            duration_sec = shot["duration_sec"]

            target_positions = self._smart_positions(duration_frames, duration_sec)
            frame_paths = []

            for j, pos_ratio in enumerate(target_positions):
                frame_idx = start_frame + int(duration_frames * pos_ratio)
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()

                if ret:
                    filename = f"shot_{shot['shot_id']:03d}_f{j+1}.jpg"
                    img_path = os.path.join(output_dir, filename)
                    # 质量 95%，避免 JPEG 伪影影响 AI 分析
                    cv2.imwrite(img_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
                    frame_paths.append({
                        "filename": filename,
                        # StaticFiles 挂载在 /frames，frames 按 job_id 子目录存储
                        "url": f"/frames/{job_id}/{filename}",
                        "frame_index": frame_idx,
                        "position_ratio": pos_ratio,
                    })

            results.append({
                "shot_id": shot["shot_id"],
                "frame_count": len(frame_paths),
                "frames": frame_paths,
            })

        cap.release()
        return results

    def _smart_positions(self, duration_frames: int, duration_sec: float) -> list[float]:
        """根据镜头时长返回抽帧位置比例列表"""
        if duration_sec < 1.0:
            return [0.5]
        elif duration_sec <= 3.0:
            return [0.2, 0.8]
        else:
            return [0.1, 0.5, 0.9]
