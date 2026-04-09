#!/usr/bin/env python3
"""视频师 Agent —— 调用 Seedance 生成视频"""
import json, sys, pathlib, sqlite3
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from agents.base_agent import BaseAgent
from adapters.base import AdapterRegistry

import json as _json
_config = _json.loads(
    pathlib.Path(__file__).parent.parent.joinpath("config/jike_config.json").read_text()
)


class VideoAgent(BaseAgent):
    name = "video"

    def __init__(self):
        super().__init__()
        self.cfg = _config
        self.db_path = pathlib.Path(__file__).parent.parent / "db" / "jike.db"

        # 视频 adapter
        vid_adapter_name = self.cfg.get("video_adapter", "seedance")
        vid_model_cfg = self.cfg["models"].get(vid_adapter_name, {})
        self.video_adapter = AdapterRegistry.get(vid_adapter_name, vid_model_cfg)

    def handle_action(self, action: str, params: dict) -> dict:
        if action == "generate":
            return self._generate_video(
                params.get("shot_id"),
                params.get("reference_image"),
            )
        if action == "poll":
            return self._poll_video(params.get("task_id"))
        return {"error": f"Unknown action: {action}"}

    def _generate_video(self, shot_id: int, reference_image: str | None = None) -> dict:
        conn = sqlite3.connect(self.db_path)
        row = conn.execute(
            "SELECT prompt, motion_prompt, duration FROM t_shot WHERE id = ?",
            (shot_id,),
        ).fetchone()
        conn.close()

        if not row:
            return {"error": f"Shot {shot_id} not found"}

        prompt, motion_prompt, duration = row
        video_prompt = motion_prompt or prompt or ""

        result = self.video_adapter.invoke(
            prompt=video_prompt,
            reference_image=reference_image,
            duration=int(duration) if duration else 4,
        )

        # 记录到数据库
        conn2 = sqlite3.connect(self.db_path)
        conn2.execute(
            """INSERT INTO t_video (shot_id, model, state)
               VALUES (?, ?, 'pending')""",
            (shot_id, self.cfg["models"].get(self.cfg.get("video_adapter"), {}).get("model", "")),
        )
        conn2.commit()
        conn2.close()

        return result

    def _poll_video(self, task_id: str) -> dict:
        return self.video_adapter.poll(task_id)


if __name__ == "__main__":
    VideoAgent().run()
