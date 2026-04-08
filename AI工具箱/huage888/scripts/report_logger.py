#!/usr/bin/env python3
"""report_logger.py — 轻量 JSONL 埋点模块

用法：
    from report_logger import ReportLogger

    logger = ReportLogger(project="漠玫传", episode="S01E01")
    logger.log_stage_start(stage=1, name="outline", model="qwen-plus")
    # ... 执行阶段 ...
    logger.log_stage_end(stage=1, name="outline", status="success",
                        output_file="outputs/S01E01/outline.md", review_result="PASS")

    logger.log_shot(shot_number=1, description="漠玫立于断桥",
                    image_prompt="...", asset_id="A001")
"""

import json
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal

BASE_DIR = Path(__file__).parent.parent
LOG_DIR = BASE_DIR / ".huage888" / "production_logs"


class ReportLogger:
    def __init__(self, project: str, episode: str):
        self.project = project
        self.episode = episode
        self.session_id = uuid.uuid4().hex[:8]
        self._log_dir = LOG_DIR / project / episode
        self._log_dir.mkdir(parents=True, exist_ok=True)
        self._jsonl_path = self._log_dir / "pipeline.jsonl"

    def _write_event(self, event_type: str, data: dict):
        """追加写入一条 JSONL 事件"""
        event = {
            "event": event_type,
            "session_id": self.session_id,
            "project": self.project,
            "episode": self.episode,
            "ts": datetime.now().isoformat(),
            **data,
        }
        with open(self._jsonl_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

    def log_pipeline_start(self, report_level: str = "stage"):
        self._write_event("pipeline_start", {"report_level": report_level})

    def log_pipeline_end(self, report_level: str = "stage",
                          total_duration: float = 0.0,
                          summary: dict | None = None):
        self._write_event("pipeline_end", {
            "report_level": report_level,
            "total_duration_seconds": total_duration,
            "summary": summary or {},
        })

    def log_stage_start(self, stage: int, name: str, model: str = ""):
        self._write_event("stage_start", {
            "stage": stage,
            "name": name,
            "model": model,
        })

    def log_stage_end(self, stage: int, name: str,
                      status: Literal["success", "failed", "skipped"] = "success",
                      output_file: str = "",
                      review_result: Literal["PASS", "FAIL", "WARNING", ""] = "",
                      prompt_id: str = "",
                      retry_count: int = 0,
                      error_message: str = "",
                      duration_seconds: float = 0.0,
                      model: str = ""):
        self._write_event("stage_end", {
            "stage": stage,
            "name": name,
            "status": status,
            "output_file": output_file,
            "review_result": review_result,
            "prompt_id": prompt_id,
            "retry_count": retry_count,
            "error_message": error_message,
            "duration_seconds": duration_seconds,
            "model": model,
        })

    def log_shot(self, shot_number: int,
                 description: str = "",
                 image_prompt: str = "",
                 image_asset_id: str = "",
                 motion_prompt: str = "",
                 video_url: str = "",
                 duration_seconds: int = 0,
                 model: str = "",
                 quality_score: float | None = None,
                 notes: str = ""):
        self._write_event("shot", {
            "shot_number": shot_number,
            "description": description,
            "image_prompt": image_prompt,
            "image_asset_id": image_asset_id,
            "motion_prompt": motion_prompt,
            "video_url": video_url,
            "duration_seconds": duration_seconds,
            "model": model,
            "quality_score": quality_score,
            "notes": notes,
        })

    def log_manual_note(self, content: str):
        """人工备注（shot 级别可写）"""
        self._write_event("manual_note", {"content": content})
