"""ai-drama-studio/backend/config.py"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # ── AI Provider ──────────────────────────────────────────
    # 支持: openai (智谱GLM-4V) | claude | gemini
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "openai")

    # 智谱 GLM-4V（OpenAI 兼容）
    ZHIPU_API_KEY: str = os.getenv("ZHIPU_API_KEY", "")
    ZHIPU_BASE_URL: str = "https://open.bigmodel.cn/api/paas/v4/"
    ZHIPU_MODEL: str = os.getenv("ZHIPU_MODEL", "glm-4v")

    # Anthropic
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    CLAUDE_MODEL: str = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")

    # Google Gemini
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

    # ── Storage ─────────────────────────────────────────────
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")
    FRAME_DIR: str = os.getenv("FRAME_DIR", "./frames")
    STANDARDIZED_DIR: str = os.getenv("STANDARDIZED_DIR", "./standardized")

    # ── PySceneDetect ────────────────────────────────────────
    SCENE_THRESHOLD: float = float(os.getenv("SCENE_THRESHOLD", "27.0"))
    MIN_SCENE_LEN: int = int(os.getenv("MIN_SCENE_LEN", "15"))

    # ── FFmpeg ───────────────────────────────────────────────
    STANDARDIZED_HEIGHT: int = 720
    STANDARDIZED_FPS: int = 12

config = Config()
