#!/usr/bin/env python3
"""即刻创作 · 主入口 CLI"""
import argparse, sys, os, json, sqlite3, subprocess, pathlib, logging

_ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(_ROOT))

from tools.inquirer import ask_choice, ask_text, ask_yes_no, show_progress

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("jike")

DB_PATH = _ROOT / "db" / "jike.db"
OUTPUT_DIR = _ROOT / "output"


def spawn_agent(agent_file: str) -> subprocess.Popen:
    """启动 Agent 子进程"""
    return subprocess.Popen(
        [sys.executable, agent_file],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        cwd=str(_ROOT),
    )


def agent_call(proc: subprocess.Popen, action: str, params: dict) -> dict:
    """向 Agent 发消息并获取 done 结果"""
    msg = json.dumps({"action": action, "params": params}) + "\n"
    proc.stdin.write(msg)
    proc.stdin.flush()
    for line in proc.stdout:
        line = line.strip()
        if not line:
            continue
        m = json.loads(line)
        t = m.get("type")
        if t == "stream":
            print(m.get("token", ""), end="", flush=True)
        elif t == "tool_call":
            logger.info(f"[tool] {m.get('tool')}")
        elif t == "done":
            return m.get("result", {})
        elif t == "error":
            raise RuntimeError(f"Agent error: {m.get('message', '')}")
    return {}


def close_agent(proc: subprocess.Popen):
    try:
        proc.stdin.close()
        proc.wait(timeout=5)
    except Exception:
        proc.kill()


def run_new_project():
    """新建项目引导"""
    name = ask_text("项目名称")
    script_path = ask_text("剧本文件路径")
    script_text = pathlib.Path(script_path).read_text(encoding="utf-8")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute(
        "INSERT INTO t_project (name, type, status) VALUES (?, 'short_drama', 'active')",
        (name,),
    )
    project_id = cur.lastrowid
    conn.commit()
    conn.close()

    output = OUTPUT_DIR / name
    output.mkdir(exist_ok=True)
    logger.info(f"项目已创建: {name} (ID: {project_id})")

    # 阶段1: 故事线
    print("\n" + "═" * 50)
    print("  阶段 1: 故事线生成")
    print("═" * 50)

    from agents.storyline_agent import StorylineAgent
    storyline_agent = StorylineAgent()
    storyline = storyline_agent._generate_storyline(script_text)

    print("\n生成结果:")
    print(json.dumps(storyline, ensure_ascii=False, indent=2))

    if not ask_yes_no("故事线是否通过？", True):
        print("请修改剧本后重试")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO t_storyline (project_id, name, content, state) VALUES (?, ?, ?, 'approved')",
        (project_id, f"{name}-故事线", json.dumps(storyline, ensure_ascii=False)),
    )
    conn.commit()
    conn.close()

    # 阶段2: 大纲 + 导演审核
    print("\n" + "═" * 50)
    print("  阶段 2: 大纲生成 + 导演审核")
    print("═" * 50)

    from agents.outline_agent import OutlineAgent
    from agents.director_agent import DirectorAgent

    outline_agent = OutlineAgent()
    director = DirectorAgent()

    outline = outline_agent._generate_outline(storyline)
    print("\n大纲生成结果:")
    print(json.dumps(outline, ensure_ascii=False, indent=2))

    review = director._review_outline(outline)
    print(f"\n导演审核: {review.get('verdict', 'UNKNOWN')}")
    for s in review.get("suggestions", []):
        print(f"  建议: {s}")

    if review.get("verdict") == "FAIL":
        if not ask_yes_no("大纲未通过，是否忽略并继续？", False):
            return

    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO t_outline (project_id, episode_index, title, data, state) VALUES (?, ?, ?, ?, ?)",
        (
            project_id,
            outline.get("episodeIndex", 1),
            outline.get("title", "未命名"),
            json.dumps(outline, ensure_ascii=False),
            review.get("verdict", "PASS"),
        ),
    )
    conn.commit()
    conn.close()

    # 阶段3: 资产提取
    print("\n" + "═" * 50)
    print("  阶段 3: 资产提取")
    print("═" * 50)

    from agents.asset_agent import AssetAgent
    asset_agent = AssetAgent()
    assets = asset_agent._extract_assets(outline)
    print(f"提取到 {len(assets)} 个资产")
    for asset in assets[:5]:
        print(f"  - {asset.get('name', '?')} ({asset.get('type', 'unknown')})")
    if len(assets) > 5:
        print(f"  ... 还有 {len(assets) - 5} 个")

    if ask_yes_no("是否生成资产参考图（需 Seedream API）？", False):
        print("Seedream API 占位运行（mock=True），跳过实际生成")
        print("  华哥填入 API Key 后替换 adapters/image/seedream_adapter.py")

    # 阶段4: 分镜脚本
    print("\n" + "═" * 50)
    print("  阶段 4: 分镜脚本生成")
    print("═" * 50)

    from agents.segment_agent import SegmentAgent
    from agents.shot_agent import ShotAgent

    segment_agent = SegmentAgent()
    shot_agent = ShotAgent()

    seg_result = segment_agent._segment_script(script_text)
    segments = seg_result.get("segments", [])
    print(f"生成 {len(segments)} 个片段")

    all_shots = []
    for seg in segments:
        shots = shot_agent._generate_shots(seg, assets)
        all_shots.extend(shots.get("shots", []))
        print(f"  片段{seg.get('index', '?')}: {len(shots.get('shots', []))} 个分镜")

    print(f"\n共生成 {len(all_shots)} 个分镜")

    # 阶段5-6: 占位
    print("\n" + "═" * 50)
    print("  阶段 5-6: 分镜图 + 视频生成")
    print("═" * 50)
    print("  → Seedream / Seedance 2.0 占位运行")
    print("  → 华哥提供 SDK 文档后替换对应 adapter")

    # 输出文件
    (output / "storyline.json").write_text(
        json.dumps(storyline, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output / "outline.json").write_text(
        json.dumps(outline, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output / "segments.json").write_text(
        json.dumps(seg_result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output / "shots.json").write_text(
        json.dumps({"shots": all_shots}, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output / "manifest.json").write_text(
        json.dumps(
            {
                "project": name,
                "project_id": project_id,
                "phases_completed": ["storyline", "outline", "segments", "shots"],
                "phases_pending": ["asset_images", "shot_images", "videos"],
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print(f"\n项目输出: {output}")
    print("文件: storyline.json / outline.json / segments.json / shots.json / manifest.json")


def main():
    parser = argparse.ArgumentParser(
        description="即刻创作 v1.0  ·  AI 漫剧工厂",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="示例:\n  python3 jike.py --step\n  python3 jike.py --continue myproject",
    )
    parser.add_argument("--step", action="store_true", help="交互式分步模式")
    parser.add_argument("--continue", dest="continue_proj", help="继续已有项目")
    args = parser.parse_args()

    print("═" * 56)
    print("  即刻创作 v1.0  ·  AI 漫剧工厂")
    print("  text: qwen/deepseek  |  image: seedream  |  video: seedance")
    print("═" * 56)

    if args.step:
        run_new_project()
    elif args.continue_proj:
        logger.info(f"继续项目: {args.continue_proj}（功能开发中）")
    else:
        choice = ask_choice(
            "请选择操作",
            ["新建项目（交互式）", "继续已有项目", "仅生成视频"],
        )
        if choice == 0:
            run_new_project()
        elif choice == 1:
            logger.info("继续项目功能开发中，使用 --continue 参数")
        else:
            logger.info("视频生成功能开发中")


if __name__ == "__main__":
    main()
