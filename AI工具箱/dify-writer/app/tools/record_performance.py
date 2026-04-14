# record_performance tool (Phase 2+ stub)
import json
from datetime import datetime, timezone
from pathlib import Path

from app.core.config import CACHE_DIR
from app.tools.base import BaseTool


class RecordPerformanceTool(BaseTool):
    """Record article performance metrics (Phase 2+ stub)."""

    name = "record_performance"
    description = "Record article performance metrics."

    def execute(
        self,
        article_id: str,
        metrics: dict,
        session_id: str | None = None,
        **kwargs,
    ) -> dict:
        """
        Record performance metrics to local JSON.

        Phase 2+: Will fetch real data from WeChat backend API.
        Current: User manually inputs metrics via Dify.
        """
        perf_dir = CACHE_DIR / "performance"
        perf_dir.mkdir(parents=True, exist_ok=True)

        record = {
            "article_id": article_id,
            "metrics": metrics,
            "session_id": session_id,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        }

        record_file = perf_dir / f"{article_id}.json"
        with open(record_file, "w") as f:
            json.dump(record, f, ensure_ascii=False, indent=2)

        return {
            "status": "recorded",
            "article_id": article_id,
            "file": str(record_file),
        }
