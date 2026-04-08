#!/usr/bin/env python3
"""
huage888 → LibTV JSON Spec 转换器

把 huage888 输出的 assets/character-prompts.md 和 assets/scene-prompts.md
转换为 LibTV create_structured_session.py 可直接使用的 JSON spec 文件。

用法：
  # 一键转换全部资产
  python3 convert_to_libtv_spec.py assets/character-prompts.md assets/scene-prompts.md

  # 指定输出目录
  python3 convert_to_libtv_spec.py assets/character-prompts.md assets/scene-prompts.md --output assets/

  # 只转换角色
  python3 convert_to_libtv_spec.py assets/character-prompts.md --type character_front_view

  # 只转换场景
  python3 convert_to_libtv_spec.py assets/scene-prompts.md --type scene_establishing
"""

import argparse
import json
import os
import re
import sys


# ─────────────────────────────────────────────────────────────────────────────
# 解析 character-prompts.md
# ─────────────────────────────────────────────────────────────────────────────

def parse_character_prompts(md_content: str) -> dict:
    """从 character-prompts.md 解析出 Phase1 和 Phase2 JSON spec"""
    sections = _split_by_header(md_content, r"## (C\d+\S*)")
    project_name = _extract_project_name(md_content) or "未命名项目"

    phase1_chars = []
    phase2_chars = []

    for section_title, section_body in sections:
        if not section_title.startswith("C"):
            continue

        # 解析角色ID和名称
        # 格式：## C001 漠玫 · 主体描述词 或 ## C002 大圣 · 主体描述词
        match = re.match(r"(C\d+\S*)\s+(.+?)(?:\s*[-·]\s*.+)?$", section_title)
        if not match:
            match = re.match(r"(C\d+[a-z]?)\s*(.+)", section_title)
        if not match:
            continue

        char_id = match.group(1)
        char_name = match.group(2).strip()

        # 提取主体描述（从 LibTV 主体创建消息中提取）
        desc_blocks = _extract_code_blocks(section_body)
        full_description = ""
        for block in desc_blocks:
            # 跳过英文 prompt 块
            if re.search(r"[a-z]{5,}", block) and not re.search(r"[\u4e00-\u9fff].{5,}", block):
                continue
            if "发型：" in block or "脸型：" in block or "肤色：" in block:
                full_description = _clean_description(block)
                break

        # 提取 appearance_tags（从描述中自动拆分）
        appearance_tags = _extract_appearance_tags(full_description)
        outfit_tags = _extract_outfit_tags(full_description)

        # 提取禁止变体
        forbid_tags = _extract_forbid_tags(section_body)

        # 提取核心记忆点
        notes = _extract_memorable_points(section_body)

        # 提取分角度提示词（用于 views 推断）
        views = _extract_views_from_prompts(section_body, char_name)

        # Phase 1
        if full_description:
            phase1_chars.append({
                "id": char_id,
                "name": char_name,
                "description": full_description,
                "notes": notes or None,
            })

        # Phase 2（带 element_id 占位）
        if appearance_tags:
            phase2_chars.append({
                "id": char_id,
                "name": char_name,
                "element_id": f"elem_{char_id.lower()}_front_001",
                "appearance_tags": appearance_tags,
                "outfit_tags": outfit_tags,
                "forbid_tags": forbid_tags or None,
                "views": views if views else _default_views(),
                "notes": notes or None,
            })

    return {
        "project_name": project_name,
        "phase1": {
            "task_type": "character_front_view",
            "project": {"name": project_name},
            "characters": phase1_chars,
        },
        "phase2": {
            "task_type": "character_sheet",
            "project": {"name": project_name},
            "characters": phase2_chars,
        },
    }


def parse_scene_prompts(md_content: str) -> dict:
    """从 scene-prompts.md 解析出 Phase1 和 Phase2 JSON spec"""
    sections = _split_by_header(md_content, r"## (S\d+\S*)")
    project_name = _extract_project_name(md_content) or "未命名项目"

    phase1_scenes = []
    phase2_scenes = []

    for section_title, section_body in sections:
        if not section_title.startswith("S"):
            continue

        # 解析场景ID和名称
        match = re.match(r"(S\d+\S*)\s+(.+?)(?:\s*[-·]\s*.+)?$", section_title)
        if not match:
            match = re.match(r"(S\d+[a-z]?)\s*(.+)", section_title)
        if not match:
            continue

        scene_id = match.group(1)
        scene_name = match.group(2).strip()

        # 提取场景描述
        desc_blocks = _extract_code_blocks(section_body)
        full_description = ""
        lighting = ""
        for block in desc_blocks:
            if "光源" in block or "光线" in block or "色调" in block:
                lighting = _extract_lighting(block)
            if block.strip() and not re.search(r"^[a-z\s,]+$", block):
                full_description = _clean_scene_description(block)

        # 提取 scene_type_tags
        scene_type_tags = _extract_scene_type_tags(full_description)
        props_tags = _extract_props_tags(section_body)

        # 提取多角度视图
        views = _extract_scene_views(section_body, scene_name)

        # Phase 1
        if full_description:
            phase1_scenes.append({
                "id": scene_id,
                "name": scene_name,
                "description": full_description,
                "lighting": lighting or "自然光",
            })

        # Phase 2
        if scene_type_tags:
            phase2_scenes.append({
                "id": scene_id,
                "name": scene_name,
                "element_id": f"elem_{scene_id.lower()}_est_001",
                "description": full_description,
                "lighting": lighting or "自然光",
                "scene_type_tags": scene_type_tags,
                "props_tags": props_tags,
                "views": views if views else _default_scene_views(),
            })

    return {
        "project_name": project_name,
        "phase1": {
            "task_type": "scene_establishing",
            "project": {"name": project_name},
            "scenes": phase1_scenes,
        },
        "phase2": {
            "task_type": "scene_sheet",
            "project": {"name": project_name},
            "scenes": phase2_scenes,
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# 解析辅助函数
# ─────────────────────────────────────────────────────────────────────────────

def _split_by_header(content: str, pattern: str) -> list:
    """按标题分割 markdown 内容块"""
    lines = content.split("\n")
    sections = []
    current_title = ""
    current_body = ""

    for line in lines:
        if re.match(pattern, line.strip()):
            if current_title:
                sections.append((current_title, current_body.strip()))
            current_title = re.sub(r"^#+\s*", "", line.strip())
            current_body = ""
        else:
            current_body += line + "\n"

    if current_title:
        sections.append((current_title, current_body.strip()))
    return sections


def _extract_project_name(content: str) -> str:
    m = re.search(r"项目[：:]\s*(.+?)(?:\n|$)", content)
    return m.group(1).strip() if m else ""


def _extract_code_blocks(content: str) -> list:
    """提取 markdown 中的 code block 内容"""
    blocks = re.findall(r"```[\w]*\n(.*?)```", content, re.DOTALL)
    return [b.strip() for b in blocks if b.strip()]


def _clean_description(text: str) -> str:
    """清理中文描述，去掉标签格式"""
    text = re.sub(r"主体描述[：:]\s*", "", text)
    text = re.sub(r"[①②③④⑤]\s*", "", text)
    text = re.sub(r"禁止[出现]?[的]?[变体词]+[：:]\s*.+", "", text)
    text = re.sub(r"\n+", "，", text)
    text = re.sub(r"，+", "，", text)
    return text.strip("，.。 ").strip()


def _extract_appearance_tags(description: str) -> list:
    """从描述中自动拆解 appearance_tags"""
    tags = []
    patterns = [
        (r"发型[：:]\s*(.+?)[，,]", 0),
        (r"头发[：:]\s*(.+?)[，,]", 0),
        (r"脸型[：:]\s*(.+?)[，,]", 0),
        (r"眉毛[：:]\s*(.+?)[，,]", 0),
        (r"眼睛[：:]\s*(.+?)[，,]", 0),
        (r"鼻子[：:]\s*(.+?)[，,]", 0),
        (r"嘴唇[：:]\s*(.+?)[，,]", 0),
        (r"肤色[：:]\s*(.+?)[，,]", 0),
        (r"身材[：:]\s*(.+?)[，,]", 0),
        (r"气质[：:]\s*(.+?)[，,]", 0),
        (r"头饰[：:（(](.+?)[)）]", 0),
        (r"(金色[^\s，,，]{1,30})", 0),
        (r"(墨滴[^\n，,]{1,20})", 0),
    ]
    for pattern, _ in patterns:
        m = re.search(pattern, description)
        if m:
            tag = m.group(1).strip()
            if tag and len(tag) > 2 and tag not in tags:
                tags.append(tag)
    return tags if tags else [description[:50]]


def _extract_outfit_tags(description: str) -> list:
    """从描述中自动拆解 outfit_tags"""
    tags = []
    patterns = [
        (r"服装[：:]\s*(.+?)[，,]", 0),
        (r"上装[：:]\s*(.+?)[，,]", 0),
        (r"下装[：:]\s*(.+?)[，,]", 0),
        (r"鞋子[：:]\s*(.+?)[，,]", 0),
        (r"配饰[：:]\s*(.+?)[，,]", 0),
        (r"内搭[：:]\s*(.+?)[，,]", 0),
    ]
    for pattern, _ in patterns:
        m = re.search(pattern, description)
        if m:
            tag = m.group(1).strip()
            if tag and len(tag) > 2 and tag not in tags:
                tags.append(tag)
    return tags


def _extract_forbid_tags(section_body: str) -> list:
    """提取禁止变体词"""
    tags = []
    m = re.search(r"禁止[出现]?[的]?[变体词]+[：:]\s*(.+?)(?:\n|$)", section_body)
    if m:
        tags = [t.strip() for t in re.split(r"[/,，、]", m.group(1)) if t.strip()]
    return tags


def _extract_memorable_points(section_body: str) -> str:
    """提取核心记忆点"""
    points = re.findall(r"核心记忆点[）)]\s*[:：]?\s*(.+?)(?:\n|$)", section_body)
    if points:
        return "；".join(p.strip() for p in points if p.strip())
    m = re.search(r"标志性元素[：:]\s*(.+?)(?:\n|$)", section_body)
    if m:
        return m.group(1).strip()
    return ""


def _extract_views_from_prompts(section_body: str, char_name: str) -> list:
    """从分角度提示词段落推断 views 列表"""
    views = []
    angle_patterns = {
        "front view": ("正面", "front view", "full body", "neutral expression", "standing upright"),
        "3/4 view": ("3/4侧", "3/4 view", "full body", "neutral expression", "standing upright"),
        "side view": ("侧面", "side view", "full body", "neutral expression", "standing upright"),
        "back view": ("背面", "back view", "full body", "neutral expression", "standing upright"),
    }

    lines = section_body.split("\n")
    for line in lines:
        for angle_key, (label_cn, va, st, exp, pose) in angle_patterns.items():
            if angle_key.replace(" view", "") in line.lower() or label_cn in line:
                view_id = f"正-{label_cn}"
                views.append({
                    "view_id": view_id,
                    "label": f"{label_cn}无表情",
                    "view_angle": va,
                    "shot_type": st,
                    "expression": exp,
                    "pose": pose,
                    "background": "simple white background",
                })
                break

    # 去重
    seen = set()
    unique = []
    for v in views:
        if v["view_id"] not in seen:
            seen.add(v["view_id"])
            unique.append(v)
    return unique


def _default_views() -> list:
    return [
        {"view_id": "正-正面", "label": "正面全身无表情", "view_angle": "front view",
         "shot_type": "full body", "expression": "neutral expression",
         "pose": "standing upright", "background": "simple white background"},
        {"view_id": "正-3/4侧", "label": "3/4侧脸无表情", "view_angle": "3/4 view",
         "shot_type": "full body", "expression": "neutral expression",
         "pose": "standing upright", "background": "simple white background"},
        {"view_id": "正-侧面", "label": "纯侧面无表情", "view_angle": "side view",
         "shot_type": "full body", "expression": "neutral expression",
         "pose": "standing upright", "background": "simple white background"},
        {"view_id": "正-背面", "label": "全身背面无表情", "view_angle": "back view",
         "shot_type": "full body", "expression": "neutral expression",
         "pose": "standing upright", "background": "simple white background"},
    ]


def _clean_scene_description(text: str) -> str:
    """清理场景描述"""
    text = re.sub(r"场景描述[：:]\s*", "", text)
    text = re.sub(r"参考[：:]\s*[\u4e00-\u9fff]+", "", text)
    text = re.sub(r"[①②③④⑤]\s*", "", text)
    text = re.sub(r"\n+", "，", text)
    return text.strip("，.。 ").strip()


def _extract_lighting(text: str) -> str:
    m = re.search(r"光线[：:]\s*(.+?)[，,\n]", text)
    if m:
        return m.group(1).strip()
    m = re.search(r"色调[：:]\s*(.+?)[，,\n]", text)
    if m:
        return m.group(1).strip()
    return ""


def _extract_scene_type_tags(description: str) -> list:
    """从场景描述中提取 scene_type_tags"""
    tags = []
    # 提取关键词
    keywords = re.findall(r"[\u4e00-\u9fff]+(?:街|景|桥|湖|山|城|村|园|场|厅|室|楼|路|馆)[^\n，,]*", description)
    tags.extend([k.strip() for k in keywords[:3] if k.strip()])
    if "consistent" not in description.lower():
        tags.append("consistent environment, same scene")
    return tags if tags else ["consistent environment, same scene"]


def _extract_props_tags(section_body: str) -> list:
    """从场景段落中提取 props_tags"""
    tags = []
    # 提取陈设物品
    patterns = [
        r"[石木砖混泥土钢玻璃竹铜铁金银][^\s，,，.\n]{0,8}[物构筑设]",
        r"[\u4e00-\u9fff]+(?:灯|柱|栏|桌|椅|架|柜|帘|墙|瓦|石|水|树|花)[^\s，,，\n]{0,6}",
    ]
    for pattern in patterns:
        matches = re.findall(pattern, section_body)
        for m in matches:
            if len(m) > 2 and m not in tags:
                tags.append(m)
    if not tags:
        tags.append("consistent environment props")
    if "same" not in str(tags).lower():
        tags.append("same props, same furniture arrangement")
    return tags[:6]


def _extract_scene_views(section_body: str, scene_name: str) -> list:
    """从场景提示词推断 views"""
    views = []
    shot_patterns = [
        (r"全景", "wide establishing shot", "high angle"),
        (r"中景", "medium shot", "eye-level"),
        (r"近景|特写", "close-up detail shot", "eye-level"),
        (r"俯拍", "wide establishing shot", "high angle"),
    ]
    for keyword, st, ca in shot_patterns:
        if keyword in section_body:
            views.append({
                "view_id": f"{scene_name[:3]}-{st.split()[0]}",
                "label": f"{keyword}视角",
                "shot_type": st,
                "camera_angle": ca,
                "focus_subject": "the scene",
                "lighting": "as described",
                "time_of_day": "as described",
                "atmosphere": "dramatic shadows, volumetric light rays",
                "character_handling": "no characters",
            })
            break
    return views


def _default_scene_views() -> list:
    return [
        {"view_id": "全景-俯拍", "label": "全景俯拍", "shot_type": "wide establishing shot",
         "camera_angle": "high angle", "focus_subject": "the full scene",
         "lighting": "as described", "time_of_day": "as described",
         "atmosphere": "dramatic shadows, volumetric light rays",
         "character_handling": "no characters"},
        {"view_id": "中景-平视", "label": "中景平视", "shot_type": "medium shot",
         "camera_angle": "eye-level", "focus_subject": "the scene",
         "lighting": "as described", "time_of_day": "as described",
         "atmosphere": "atmospheric",
         "character_handling": "no characters"},
    ]


# ─────────────────────────────────────────────────────────────────────────────
# 主函数
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="把 huage888 的 character-prompts.md / scene-prompts.md 转换为 LibTV JSON spec",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("input", nargs="+", help="输入 markdown 文件路径")
    parser.add_argument("--output-dir", "-o", default=".",
                        help="输出目录（默认当前目录）")
    parser.add_argument("--dry-run", action="store_true",
                        help="只打印不写文件")
    parser.add_argument("--type", choices=["character", "scene", "all"],
                        default="all",
                        help="转换类型：character / scene / all（默认all）")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    for input_file in args.input:
        if not os.path.isfile(input_file):
            print(f"警告：文件不存在，跳过：{input_file}", file=sys.stderr)
            continue

        with open(input_file, encoding="utf-8") as f:
            content = f.read()

        is_character = "角色描述词" in content or re.search(r"## C\d+", content)
        is_scene = "场景描述词" in content or re.search(r"## S\d+", content)

        phase1_out = None
        phase2_out = None
        project_name = "未命名项目"

        if is_character and args.type in ("character", "all"):
            result = parse_character_prompts(content)
            project_name = result["project_name"]
            phase1_out = result["phase1"]
            phase2_out = result["phase2"]

        elif is_scene and args.type in ("scene", "all"):
            result = parse_scene_prompts(content)
            project_name = result["project_name"]
            phase1_out = result["phase1"]
            phase2_out = result["phase2"]

        # 输出 Phase1
        if phase1_out:
            out_file1 = os.path.join(
                args.output_dir,
                "character-front-view.json" if is_character else "scene-establishing.json"
            )
            if args.dry_run:
                print(f"\n{'='*60}\n[DRY RUN] {out_file1}\n{'='*60}")
                print(json.dumps(phase1_out, ensure_ascii=False, indent=2))
            else:
                with open(out_file1, "w", encoding="utf-8") as f:
                    json.dump(phase1_out, f, ensure_ascii=False, indent=2)
                print(f"✅ 生成：{out_file1}")

        # 输出 Phase2
        if phase2_out:
            out_file2 = os.path.join(
                args.output_dir,
                "character-sheet.json" if is_character else "scene-sheet.json"
            )
            if args.dry_run:
                print(f"\n{'='*60}\n[DRY RUN] {out_file2}\n{'='*60}")
                print(json.dumps(phase2_out, ensure_ascii=False, indent=2))
            else:
                with open(out_file2, "w", encoding="utf-8") as f:
                    json.dump(phase2_out, f, ensure_ascii=False, indent=2)
                print(f"✅ 生成：{out_file2}")

        print(f"📄 项目：{project_name}")


if __name__ == "__main__":
    main()
