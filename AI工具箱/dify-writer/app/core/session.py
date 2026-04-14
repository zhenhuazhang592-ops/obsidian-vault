# Session state management with atomic checkpoint writes
import json
import os
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from app.core.config import SESSIONS_DIR


class SessionState:
    """Session state with atomic checkpoint writes."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.state_file = SESSIONS_DIR / session_id / "checkpoint.json"
        self.state: dict = {
            "session_id": session_id,
            "topic": None,
            "platform": None,
            "framework": None,
            "style_profile": None,
            "outline": None,
            "article_draft": None,
            "polished_article": None,
            "quality_score": None,
            "revisions": 0,
            "checkpoint_enabled": True,
            "last_checkpoint": None,
            "resume_from": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

    def update(self, **kwargs) -> None:
        """Update session state fields."""
        for key, value in kwargs.items():
            if key in self.state:
                self.state[key] = value
        self.state["updated_at"] = datetime.now(timezone.utc).isoformat()

    def write_checkpoint(self) -> None:
        """
        Write checkpoint atomically: tmp + rename.
        Handles disk full and permission errors.
        """
        session_dir = SESSIONS_DIR / self.session_id
        session_dir.mkdir(parents=True, exist_ok=True)

        self.state["last_checkpoint"] = datetime.now(timezone.utc).isoformat()

        # Write to temp file first, then atomic rename
        tmp_fd, tmp_path = tempfile.mkstemp(
            dir=session_dir,
            prefix=".checkpoint.",
            suffix=".tmp",
        )
        try:
            with os.fdopen(tmp_fd, "w") as f:
                json.dump(self.state, f, ensure_ascii=False, indent=2)
            os.replace(tmp_path, self.state_file)
        except OSError as e:
            # Clean up temp file if rename failed
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise RuntimeError(
                f"Failed to write checkpoint: {e}"
            ) from e

    @classmethod
    def load(cls, session_id: str) -> Optional["SessionState"]:
        """Load session state from checkpoint, or None if not found."""
        state_file = SESSIONS_DIR / session_id / "checkpoint.json"
        if not state_file.exists():
            return None
        try:
            with open(state_file) as f:
                state = json.load(f)
            instance = cls(session_id)
            instance.state = state
            return instance
        except (OSError, json.JSONDecodeError) as e:
            raise RuntimeError(
                f"Failed to load checkpoint for {session_id}: {e}"
            ) from e

    @classmethod
    def create(cls, topic: str, platform: str) -> "SessionState":
        """Create new session with topic and platform."""
        session_id = str(uuid.uuid4())
        instance = cls(session_id)
        instance.update(topic=topic, platform=platform)
        return instance
