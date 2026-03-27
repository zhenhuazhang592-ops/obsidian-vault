"""漫舟拉片智能体 - CLI 入口"""
import argparse
import asyncio
import logging
import sys
import time
from pathlib import Path

from .types import LapianConfig
from .pipeline import LapianPipeline
from .exporters.obsidian import ObsidianExporter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("manzhou_lapian")


def parse_args() -> LapianConfig:
    parser = argparse.ArgumentParser(
        prog="manzhou-lapian",
        description="漫舟拉片智能体 - 视频 → Obsidian 分镜笔记",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  manzhou-lapian 格子间女人-第01集.mp4
  manzhou-lapian input.mp4 -o ~/Obsidian/拉片分析
  manzhou-lapian input.mp4 -c ../cdp.json -m gemini --threshold 30.0
        """,
    )
    parser.add_argument(
        "video_path",
        help="视频文件路径（支持 MP4 / MOV / AVI / WebM）",
    )
    parser.add_argument(
        "-o", "--output",
        default="./拉片分析",
        help="Obsidian 笔记输出目录（默认：./拉片分析）",
    )
    parser.add_argument(
        "-c", "--cdp",
        default=None,
        help="CDP 资产库 JSON 文件路径",
    )
    parser.add_argument(
        "-m", "--model",
        default="gemini",
        choices=["zhipu", "claude", "gemini"],
        help="AI 分析模型（默认：gemini）",
    )
    parser.add_argument(
        "-t", "--threshold",
        type=float,
        default=27.0,
        help="PySceneDetect 场景阈值（默认：27.0）",
    )
    parser.add_argument(
        "-n", "--shots-per-shot",
        type=int,
        default=3,
        choices=[1, 2, 3, 4, 5],
        help="每镜头抽帧数量（默认：3）",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅测试 pipeline，不生成笔记",
    )

    args = parser.parse_args()

    return LapianConfig(
        video_path=args.video_path,
        output_dir=args.output,
        cdp_path=args.cdp,
        model=args.model,
        threshold=args.threshold,
        shots_per_shot=args.shots_per_shot,
        dry_run=args.dry_run,
    )


async def main_async(config: LapianConfig):
    pipeline = LapianPipeline(config)

    start_total = time.time()
    done_shots = 0

    def on_progress(phase: str, current: int, total: int):
        nonlocal done_shots
        if phase == "AI分析":
            done_shots = current
            total_shots = total
            pct = int(current / total * 100) if total else 0
            print(f"\r  镜 {current:02d}/{total_shots} 完成 [{pct}%]  ", end="", flush=True)

    pipeline.set_progress_callback(on_progress)

    # 打印头部
    video_file = Path(config.video_path).name
    video_size = Path(config.video_path).stat().st_size if Path(config.video_path).exists() else 0
    size_str = f"{video_size / 1024 / 1024:.1f}MB" if video_size > 0 else "未知"

    print(f" 漫舟拉片智能体 v1.0")
    print(f" 输入：{video_file}（{size_str}）")
    print(f" 输出：{config.output_dir}/")
    if config.cdp_path:
        print(f" CDP：{config.cdp_path}")
    print(f" 模型：{config.model} | 阈值：{config.threshold}")
    print()

    try:
        # Step 1: 标准化 → 镜头检测 → 抽帧 → AI分析
        print(f" [1/4] 视频标准化 → 720p 12fps ... ", end="", flush=True)
        t0 = time.time()
        result = await pipeline.run()
        print(f"done ({time.time()-t0:.0f}s)")

        if config.dry_run:
            print("dry-run 模式，跳过笔记生成")
            return

        # Step 5: 生成笔记
        print(f" [5/5] 生成 Obsidian 笔记 ... ", end="", flush=True)
        t1 = time.time()
        exporter = ObsidianExporter()
        output_path = exporter.export(result)
        print(f"done ({time.time()-t1:.0f}s)")

        elapsed = time.time() - start_total
        print()
        print(f" 完成（{elapsed:.0f}s）")
        print(f"   {output_path}")
        print(f"   {result.output_dir}/.assets/{result.video_id}/（{sum(len(s.extracted_frames) for s in result.shots)}张关键帧）")

    except Exception as e:
        logger.error(f"执行失败: {e}")
        import traceback; traceback.print_exc()
        sys.exit(1)


def main():
    config = parse_args()

    # 验证输入文件
    if not Path(config.video_path).exists():
        print(f" 错误：视频文件不存在：{config.video_path}", file=sys.stderr)
        sys.exit(1)

    asyncio.run(main_async(config))


if __name__ == "__main__":
    main()
