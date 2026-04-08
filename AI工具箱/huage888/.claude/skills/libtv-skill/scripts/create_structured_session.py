#!/usr/bin/env python3
"""
结构化会话创建脚本 — 用 JSON spec 精确控制 LibTV 任务

用法：
  # 查看可用 task_type 和 Schema
  python3 create_structured_session.py --schema

  # 方式1：直接传入 JSON 字符串
  python3 create_structured_session.py '{"task_type":"character_front_view",...}'

  # 方式2：传入 JSON 文件路径
  python3 create_structured_session.py /path/to/task.json

  # 方式3：管道输入
  cat task.json | python3 create_structured_session.py --stdin

  # 向已有会话追加（继续同一会话）
  python3 create_structured_session.py task.json --session-id SESSION_ID

  # 只生成消息预览（不调用 API）
  python3 create_structured_session.py task.json --dry-run

环境变量：
  LIBTV_ACCESS_KEY  必填
  OPENAPI_IM_BASE   可选，默认 https://im.liblib.tv
"""

import argparse
import json
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from _common import create_session, build_project_url, generate_structured_message, JSON_SCHEMA


def load_spec(src: str) -> dict:
    """从 JSON 字符串或文件路径加载 spec"""
    if os.path.isfile(src):
        with open(src, encoding="utf-8") as f:
            return json.load(f)
    try:
        return json.loads(src)
    except json.JSONDecodeError as e:
        print(f"JSON 解析错误：{e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="用结构化 JSON spec 创建 LibTV 会话",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("spec", nargs="?", default=None,
                        help="JSON spec（字符串或文件路径）")
    parser.add_argument("--stdin", action="store_true",
                        help="从 stdin 读取 JSON spec")
    parser.add_argument("--session-id", default="",
                        help="已有会话 ID，不传则创建新会话")
    parser.add_argument("--dry-run", action="store_true",
                        help="只生成消息内容，不调用 API")
    parser.add_argument("--schema", action="store_true",
                        help="打印 JSON Schema 并退出")
    args = parser.parse_args()

    # ── Schema ──────────────────────────────────────────────────────────────
    if args.schema:
        print(JSON_SCHEMA)
        return

    # ── 加载 spec ────────────────────────────────────────────────────────────
    if args.stdin:
        raw = sys.stdin.read()
        if not raw.strip():
            print("错误：stdin 为空", file=sys.stderr)
            sys.exit(1)
        spec = load_spec(raw)
    elif args.spec:
        spec = load_spec(args.spec)
    else:
        print("错误：请提供 JSON spec", file=sys.stderr)
        print(__doc__)
        sys.exit(1)

    # ── 生成消息 ──────────────────────────────────────────────────────────────
    message = generate_structured_message(spec)

    # ── Dry run ─────────────────────────────────────────────────────────────
    if args.dry_run:
        print("=" * 70)
        print(f"【DRY RUN】task_type: {spec.get('task_type', '')}")
        print("=" * 70)
        print(message)
        print("=" * 70)
        return

    # ── 调用 API ──────────────────────────────────────────────────────────────
    result = create_session(session_id=args.session_id, message=message)
    puuid = result.get("projectUuid", "")
    sid   = result.get("sessionId", "")
    out = {
        "projectUuid": puuid,
        "sessionId": sid,
        "projectUrl": build_project_url(puuid),
        "taskType": spec.get("task_type", ""),
        "projectName": spec.get("project", {}).get("name", ""),
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
