#!/bin/bash
# 漫舟导演Agent 启动脚本
# 用法: ./manzhou.sh run ./格子间女人

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/manzhou/cli.py"

# 预置LibTV Access Key
export LIBTV_ACCESS_KEY="sk-libtv-fccc89e8edcb460b830a5295d9993f7b"

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 需要Python3，请先安装"
    exit 1
fi

# 检查依赖
python3 -c "import yaml" 2>/dev/null || {
    echo "⚠️  缺少pyyaml，正在安装..."
    pip3 install pyyaml
}

# 执行
exec python3 "$PYTHON_SCRIPT" "$@"
