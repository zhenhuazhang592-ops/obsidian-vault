#!/usr/bin/env python3
"""即刻创作 · 主入口 CLI"""
import argparse, sys, os

sys.path.insert(0, os.path.dirname(__file__))

def main():
    parser = argparse.ArgumentParser(description="即刻创作 v1.0")
    parser.add_argument("--project", help="项目名")
    parser.add_argument("--script", help="剧本文本路径")
    parser.add_argument("--step", action="store_true", help="分步交互模式")
    parser.add_argument("--continue", dest="continue_proj", help="继续已有项目")
    args = parser.parse_args()

    print("即刻创作 v1.0")
    print("=" * 40)

    if args.continue_proj:
        print(f"继续项目: {args.continue_proj}")
    else:
        print("新建项目引导...")
        print("（完整功能在 Task 11 实现）")

if __name__ == "__main__":
    main()
