#!/bin/bash
# 漫舟拉片智能体 v1.0 启动脚本
#
# 用法：
#   ./拉片.sh <视频路径> [选项]
#   ./拉片.sh input.mp4 -c ../cdp.json -m gemini
#
# 无参数时显示帮助

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_PYTHON="$SCRIPT_DIR/backend/venv/bin/python"
MANZHOU_MODULE="manzhou_lapian"

if [ $# -eq 0 ]; then
    "$VENV_PYTHON" -m "$MANZHOU_MODULE" --help
else
    "$VENV_PYTHON" -m "$MANZHOU_MODULE" "$@"
fi
