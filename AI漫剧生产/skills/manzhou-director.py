#!/usr/bin/env python3
"""
漫舟·导演版 - LibTV执行引擎

版本: 1.0.0
日期: 2026-03-26
功能: 将漫舟分镜脚本转化为LibTV执行指令，调用libtv-skills完成视频生成

使用方式:
    python3 manzhou-director.py --project "格子间女人" --episode 1 --mode full
    python3 manzhou-director.py --project "许三观卖血记" --episode 1 --mode libtv-only
"""

import argparse
import json
import os
import re
import sys
import ssl
import time
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any

# ============================================================================
# SSL修复：跳过证书验证
# ============================================================================
ssl._create_default_https_context = ssl._create_unverified_context

# ============================================================================
# 配置
# ============================================================================

LIBTV_DIR = os.environ.get(
    "LIBTV_DIR",
    "/Users/huage/Obsidian Vault/ai-drama-studio/libtv-skills-main/skills/libtv-skill"
)
LIBTV_SCRIPTS = os.path.join(LIBTV_DIR, "scripts")
LIBTV_ACCESS_KEY = os.environ.get("LIBTV_ACCESS_KEY", "")

# ============================================================================
# 工具函数
# ============================================================================

def run_script(script_name: str, args: List[str] = None, input_text: str = "") -> dict:
    """执行libtv-skills脚本"""
    script_path = os.path.join(LIBTV_SCRIPTS, script_name)
    cmd = ["python3", script_path] + (args or [])

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
            input=input_text if input_text else None,
            env={**os.environ, "LIBTV_ACCESS_KEY": LIBTV_ACCESS_KEY}
        )

        if result.returncode != 0:
            print(f"❌ 脚本执行失败: {script_name}")
            print(f"   错误: {result.stderr}")
            return {"error": result.stderr}

        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return {"raw": result.stdout}

    except subprocess.TimeoutExpired:
        return {"error": f"脚本超时: {script_name}"}
    except Exception as e:
        return {"error": str(e)}


def poll_for_result(session_id: str, last_seq: int = 0, max_wait: int = 180) -> dict:
    """轮询等待生成结果"""
    start_time = time.time()
    retries = 0

    print(f"   轮询中 (最多 {max_wait} 秒)...")

    while time.time() - start_time < max_wait:
        result = run_script("query_session.py", [session_id, "--after-seq", str(last_seq)])

        if "error" in result:
            retries += 1
            if retries >= 3:
                return {"status": "error", "error": result["error"]}
            time.sleep(8)
            continue

        messages = result.get("messages", [])
        if messages:
            for msg in messages:
                content = msg.get("content", "")
                # 检查是否包含结果
                if "libtv-res" in content or ".mp4" in content or ".png" in content:
                    return {"status": "complete", "messages": messages, "content": content}

            last_seq = max((msg.get("seq", 0) for msg in messages), default=last_seq)

        time.sleep(8)

    return {"status": "timeout"}


def extract_urls(content: str) -> List[str]:
    """从内容中提取URL"""
    pattern = r'https://libtv-res\.liblib\.art/[^\s"\'<>]+\.(?:png|jpg|jpeg|webp|mp4|mov|webm)'
    return re.findall(pattern, content)


# ============================================================================
# LibTV指令生成
# ============================================================================

def generate_libtv_instruction(
    shot: dict,
    director_notes: dict,
    character_cache: dict
) -> str:
    """
    核心能力：将漫舟分镜脚本翻译成LibTV友好的指令
    """

    shot_id = shot.get("shot_id", "P01")
    duration = shot.get("durationSec", 8)
    scene_function = director_notes.get("scene_function", "ACTION")
    emotion_level = director_notes.get("emotion_level", "L3")
    emotion_desc = director_notes.get("emotion_description", "")
    camera_action = director_notes.get("camera_action", "")
    forbidden = director_notes.get("forbidden_actions", [])

    # 场景功能标注
    function_desc = {
        "TENSION": "【张力场景】",
        "MOOD": "【氛围场景】",
        "REVEAL": "【揭示场景】",
        "ACTION": "【动作场景】",
        "CLIFFHANGER": "【悬念场景】",
        "TRANSITION": "【转场场景】"
    }

    # 角色描述
    char_ids = shot.get("characterIds", [])
    char_parts = []

    for char_id in char_ids:
        if char_id in character_cache:
            dna = character_cache[char_id]
            char_parts.append(f"""
角色：{dna.get('name', char_id)}
- 身份：{dna.get('identity', '')}
- 外貌：{dna.get('appearance', '')}
- 服装：{dna.get('outfit', '')}
- 表情风格：{dna.get('expression_style', '')}""")

    # 场景描述
    location = shot.get("locationId", "")
    scene_mood = director_notes.get("scene_mood", "")
    lighting = director_notes.get("lighting", "")

    # 画面内容
    script = shot.get("script", "")

    # 拼接指令
    instruction = f"""{function_desc.get(scene_function, '')}

【第{shot_id}镜 · {duration}秒 · {emotion_level}级情绪】

【角色】
{''.join(char_parts)}

【场景】
{location}
氛围：{scene_mood}
光线：{lighting}

【画面内容】
{script}

【运镜要求】
{camera_action}

【情绪氛围】
{emotion_level}级 - {emotion_desc}

【禁止项】
{', '.join(forbidden) if forbidden else '无特殊禁止'}
"""

    return instruction.strip()


# ============================================================================
# 分镜解析
# ============================================================================

def parse_storyboard(storyboard_path: str) -> List[dict]:
    """解析分镜脚本"""
    with open(storyboard_path, "r", encoding="utf-8") as f:
        content = f.read()

    shots = []

    # 简单解析 - 查找 | P01 | P02 | 等格式
    lines = content.split("\n")
    for line in lines:
        if "|" in line and ("P01" in line or "P02" in line or "shot" in line.lower()):
            # 解析分镜行
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 4:
                shot = {
                    "raw": line,
                    "parts": parts
                }
                shots.append(shot)

    return shots


# ============================================================================
# 主执行流程
# ============================================================================

def execute_project(
    project_name: str,
    episode: int = 1,
    mode: str = "full",
    start_step: int = 1
):
    """
    主执行流程

    mode:
        full - 从小说到视频完整执行
        libtv-only - 只执行LibTV部分（假设已有分镜）
    """

    print(f"""
╔══════════════════════════════════════════════════════════════╗
║           漫舟·导演版 v6.0.0  执行中                         ║
╠══════════════════════════════════════════════════════════════╣
║  项目: {project_name:<48} ║
║  集数: 第{episode:02d}集                                              ║
║  模式: {mode:<48} ║
╚══════════════════════════════════════════════════════════════╝
""")

    # 检查环境
    if not LIBTV_ACCESS_KEY:
        print("❌ 错误: LIBTV_ACCESS_KEY 未设置")
        print("   请运行: export LIBTV_ACCESS_KEY='your-key'")
        return

    # 初始化会话
    print("\n[Step 0] 初始化LibTV会话...")
    session_result = run_script("create_session.py", [""])

    if "error" in session_result:
        print(f"❌ 会话初始化失败: {session_result['error']}")
        return

    session_id = session_result.get("sessionId", "")
    project_uuid = session_result.get("projectUuid", "")
    project_url = session_result.get("projectUrl", "")

    print(f"✅ 会话已创建")
    print(f"   Session ID: {session_id}")
    print(f"   项目地址: {project_url}")

    # 完整模式
    if mode == "full" and start_step == 1:
        print("\n[Step 1] 短剧化改编...")
        print("   ⚠️ 待实现: 调用 manzhou-novel-adapter")

        print("\n[Step 2] IP解析...")
        print("   ⚠️ 待实现: 调用 manzhou-ip-parser")

        print("\n[Step 3] 剧本生成...")
        print("   ⚠️ 待实现: 调用 manzhou-script")

        print("\n[Step 4] 导演控制塔...")
        print("   ⚠️ 待实现: 调用 manzhou-director-control")

        print("\n[Step 5] 分镜脚本...")
        print("   ⚠️ 待实现: 调用 manzhou-shot-script")

        print("\n[Step 6] 角色参考图...")
        print("   ⚠️ 待实现: 生成角色参考图并上传")

    # 读取分镜
    storyboard_path = f"/Users/huage/Obsidian Vault/AI漫剧生产/{project_name}/03-分镜/第{episode:02d}集-分镜.md"

    if not os.path.exists(storyboard_path):
        print(f"\n❌ 分镜脚本不存在: {storyboard_path}")
        print("   请先运行 Step 1-5 生成完整资产")
        return

    print(f"\n[Step 7] 读取分镜脚本...")
    shots = parse_storyboard(storyboard_path)
    print(f"   ✅ 读取到 {len(shots)} 个镜头")

    # 角色缓存（示例）
    character_cache = {
        "char_01": {
            "name": "许三观",
            "identity": "丝厂工人",
            "appearance": "瘦高个，皮肤黝黑",
            "outfit": "旧蓝布衣裳",
            "expression_style": "憨厚中带精明"
        }
    }

    # 逐镜执行
    print(f"\n[Step 8] LibTV执行 ({len(shots)} 镜)...")

    results = []
    for i, shot in enumerate(shots[:3], 1):  # 先测试前3镜
        print(f"\n   🎬 正在生成 第{i}/{len(shots)} 镜...")

        # 生成指令
        director_notes = {
            "scene_function": "ACTION",
            "emotion_level": "L3",
            "emotion_description": "紧张",
            "camera_action": "稳定镜头",
            "forbidden_actions": []
        }

        instruction = generate_libtv_instruction(
            shot,
            director_notes,
            character_cache
        )

        # 发送指令
        send_result = run_script(
            "create_session.py",
            ["", "--session-id", session_id]
        )

        if "error" in send_result:
            print(f"   ❌ 发送失败: {send_result['error']}")
            continue

        # 轮询
        poll_result = poll_for_result(session_id)

        if poll_result["status"] == "complete":
            urls = extract_urls(poll_result.get("content", ""))
            results.append({
                "shot": i,
                "urls": urls,
                "status": "success"
            })
            print(f"   ✅ 完成 ({len(urls)} 个结果)")
        else:
            results.append({
                "shot": i,
                "status": "timeout" if poll_result["status"] == "timeout" else "error"
            })
            print(f"   ⚠️ {'超时' if poll_result['status'] == 'timeout' else '失败'}")

    # 下载结果
    print("\n[Step 9] 下载结果...")

    output_dir = f"/Users/huage/Obsidian Vault/AI漫剧生产/{project_name}/08-视频产出/EP{episode:02d}/"
    os.makedirs(output_dir, exist_ok=True)

    download_result = run_script(
        "download_results.py",
        [session_id, "--output-dir", output_dir]
    )

    if "error" not in download_result:
        downloaded = download_result.get("downloaded", [])
        print(f"   ✅ 下载完成 ({len(downloaded)} 个文件)")
    else:
        print(f"   ⚠️ 下载失败: {download_result.get('error', '未知错误')}")

    # 汇总
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                    漫舟·导演版 执行完成                        ║
╠══════════════════════════════════════════════════════════════╣
║  项目: {project_name:<48} ║
║  集数: 第{episode:02d}集                                              ║
║  成功: {len([r for r in results if r['status'] == 'success'])}/{len(results)} 镜                                          ║
║  项目画布: {project_url[:40]:<40} ║
║  输出目录: {output_dir[:40]:<40} ║
╚══════════════════════════════════════════════════════════════╝
""")


# ============================================================================
# 命令行入口
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="漫舟·导演版 - LibTV执行引擎",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python3 manzhou-director.py --project "许三观卖血记" --episode 1 --mode full
  python3 manzhou-director.py --project "格子间女人" --episode 1 --mode libtv-only
        """
    )

    parser.add_argument("--project", "-p", required=True, help="项目名称")
    parser.add_argument("--episode", "-e", type=int, default=1, help="集数 (默认: 1)")
    parser.add_argument("--mode", "-m", choices=["full", "libtv-only"], default="full",
                       help="执行模式 (默认: full)")
    parser.add_argument("--start-step", "-s", type=int, default=1,
                       help="起始Step (默认: 1)")

    args = parser.parse_args()

    execute_project(
        project_name=args.project,
        episode=args.episode,
        mode=args.mode,
        start_step=args.start_step
    )


if __name__ == "__main__":
    main()
