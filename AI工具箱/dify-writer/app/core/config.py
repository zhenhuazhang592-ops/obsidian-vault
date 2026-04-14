# Core configuration for Dify Writer MCP Server
import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent.parent.parent
CACHE_DIR = Path(os.environ.get("DIFY_WRITER_CACHE", "~/.cache/dify-writer")).expanduser()
SESSIONS_DIR = CACHE_DIR / "sessions"
IMAGES_DIR = CACHE_DIR / "images"

# Ensure directories exist
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# Auth
MCP_SERVER_KEY = os.environ.get("MCP_SERVER_KEY", "dev-local-key-change-in-production")

# External APIs
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "")
JIMENG_API_KEY = os.environ.get("JIMENG_API_KEY", "")

# Observability
LOG_FILE = CACHE_DIR / "mcp_server.log"
METRICS_FILE = CACHE_DIR / "metrics.json"

# Image cache limits (1GB max, 30-day TTL)
IMAGE_CACHE_MAX_BYTES = 1024 * 1024 * 1024  # 1GB
IMAGE_CACHE_TTL_DAYS = 30
