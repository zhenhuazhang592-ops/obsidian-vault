#!/usr/bin/env python3
"""
storyboard_tools.py — 分镜师 Agent 工具调用执行器

解析 qwen-max 返回的 tool_call JSON，执行对应工具：
- getAssets     → 从项目目录读取资产信息
- getSegments   → 从讲戏本提取分段结构
- saveStoryboard → 保存分镜脚本到文件

用法（由 qwen_pipeline.py 调用）：
  python3 scripts/storyboard_tools.py get-assets --project projects/断桥奇遇/
  python3 scripts/storyboard_tools.py get-segments --project projects/断桥奇遇/
  python3 scripts/storyboard_tools.py save --file outputs/02-storyboard-script.md --content "..."

工具调用解析（供 pipeline 集成）：
  from storyboard_tools import parse_tool_calls, execute_tool_call
"""

import json
import re
import sys
from pathlib import Path
from typing import Any


# ─────────────────────────────────────────────────────────────────────────────
# 工具注册表
# ─────────────────────────────────────────────────────────────────────────────

class ToolRegistry:
    """工具注册表"""

    def __init__(self, project_path: str | Path | None = None):
        self.project_path = Path(project_path) if project_path else Path.cwd()
        self._asset_cache: dict | None = None
        self._segment_cache: list | None = None

    # ─────────────────────────────────────────────────────────────────────
    # getAssets
    # ─────────────────────────────────────────────────────────────────────

    def get_assets(self) -> str:
        """获取资产列表（角色/场景/道具）"""
        if self._asset_cache:
            return self._asset_cache

        # 优先从 03-asset-registry.md 读取
        registry_path = self.project_path / "assets" / "03-asset-registry.md"
        character_path = self.project_path / "assets" / "character-prompts.md"
        scene_path = self.project_path / "assets" / "scene-prompts.md"
        prop_path = self.project_path / "assets" / "prop-prompts.md"

        sections = []

        # 角色
        if registry_path.exists():
            content = registry_path.read_text(encoding="utf-8")
            characters = self._parse_registry_table(content, "角色主体")
            if characters:
                sections.append("【角色】\n" + "\n".join(characters))

        # 场景
        if registry_path.exists():
            content = registry_path.read_text(encoding="utf-8")
            scenes = self._parse_registry_table(content, "场景参考")
            if scenes:
                sections.append("【场景】\n" + "\n".join(scenes))

        # 道具（从 prop-prompts.md）
        if prop_path.exists():
            content = prop_path.read_text(encoding="utf-8")
            props = self._parse_prompts_section(content, "道具")
            if props:
                sections.append("【道具】\n" + "\n".join(props))

        # 兜底：尝试 character-prompts.md
        if not sections and character_path.exists():
            content = character_path.read_text(encoding="utf-8")
            chars = self._parse_prompts_section(content, "角色")
            if chars:
                sections.append("【角色】\n" + "\n".join(chars))

        if not sections:
            result = "暂无资产数据，请确认 assets/ 目录下有资产文件。"
        else:
            result = "<资产列表>\n" + "\n\n".join(sections) + "\n</资产列表>\n\n⚠️ 重要规则：\n1. 必须原封不动地使用上述资产名称，禁止使用近义词、缩写或任何变体\n2. 禁止在资产名称前后添加修饰词\n3. 禁止捏造资产列表中不存在的角色、场景、道具"

        self._asset_cache = result
        return result

    # ─────────────────────────────────────────────────────────────────────
    # getSegments
    # ─────────────────────────────────────────────────────────────────────

    def get_segments(self) -> str:
        """获取讲戏本的分段结构"""
        if self._segment_cache:
            return json.dumps(self._segment_cache, ensure_ascii=False, indent=2)

        analysis_path = self.project_path / "outputs" / "01-director-analysis.md"
        if not analysis_path.exists():
            return "暂无讲戏本数据，请确认 outputs/01-director-analysis.md 存在。"

        content = analysis_path.read_text(encoding="utf-8")
        segments = self._extract_segments(content)

        if not segments:
            return "从讲戏本中未找到分段结构，请确认文件格式包含分段信息。"

        self._segment_cache = segments
        return json.dumps(segments, ensure_ascii=False, indent=2)

    # ─────────────────────────────────────────────────────────────────────
    # saveStoryboard
    # ─────────────────────────────────────────────────────────────────────

    def save_storyboard(self, file: str, content: str) -> str:
        """保存分镜脚本到文件"""
        output_path = self.project_path / file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")
        return f"✅ 已保存分镜脚本：{output_path.relative_to(self.project_path)}"

    # ─────────────────────────────────────────────────────────────────────
    # 内部解析方法
    # ─────────────────────────────────────────────────────────────────────

    def _parse_registry_table(self, content: str, table_title: str) -> list[str]:
        """从资产注册表 Markdown 中提取表格内容"""
        lines = content.split("\n")
        in_table = False
        results = []

        for line in lines:
            if table_title in line:
                in_table = True
                continue
            if in_table:
                if line.startswith("### ") or line.startswith("## "):
                    break
                if line.startswith("|") and not all(c in "|-: " for c in line.strip("| ")):
                    cols = [c.strip() for c in line.strip("|").split("|")]
                    # 角色表：编号、名称、绑定镜头
                    # 场景表：编号、名称、绑定镜头
                    if len(cols) >= 3 and cols[0] and cols[1]:
                        code = cols[0].strip()
                        name = cols[1].strip()
                        shots = cols[2].strip() if len(cols) > 2 else ""
                        if code and name and shots:
                            results.append(f"- {name}（{code}）：绑定镜头 {shots}")
                        elif code and name:
                            results.append(f"- {name}（{code}）")

        return results

    def _parse_prompts_section(self, content: str, section: str) -> list[str]:
        """从 prompts 文件提取指定节的内容"""
        lines = content.split("\n")
        in_section = False
        results = []

        for line in lines:
            if f"## {section}" in line or f"### {section}" in line:
                in_section = True
                continue
            if in_section:
                if line.startswith("## ") or line.startswith("### ") or line.startswith("# "):
                    break
                stripped = line.strip()
                # 跳过空行、Markdown 分隔线
                if stripped and not stripped.startswith("---") and not stripped.startswith("|") and not stripped.startswith("**"):
                    # 提取角色/道具名称（格式：- **名称** 或 - 名称）
                    if stripped.startswith("- "):
                        name = stripped[2:].strip("**").strip()
                        if name:
                            results.append(f"- {name}")
                elif stripped.startswith("|") and not all(c in "|-: " for c in stripped.strip("| ")):
                    cols = [c.strip() for c in stripped.strip("|").split("|")]
                    if cols and cols[0]:
                        results.append(f"- {cols[0]}")

        return results[:10]  # 限制数量

    def _extract_segments(self, content: str) -> list[dict]:
        """从讲戏本提取分段结构"""
        segments = []
        lines = content.split("\n")
        current_segment = None

        for line in lines:
            stripped = line.strip()
            # 匹配段落标题，如 "## 第1段 悬念+仙气"
            if re.match(r"#{1,3}\s*第[一二三四五六七八九十\d]+段", stripped):
                if current_segment:
                    segments.append(current_segment)
                title = re.sub(r"^#{1,3}\s*", "", stripped).strip()
                current_segment = {"title": title, "shots": [], "emotion": ""}
            elif current_segment and stripped:
                # 提取镜头号
                shot_match = re.match(r"\|\s*(\d+)\s*\|", stripped)
                if shot_match:
                    shot_num = shot_match.group(1)
                    # 提取景别
                    cols = [c.strip() for c in stripped.strip("|").split("|")]
                    if len(cols) >= 4:
                        current_segment["shots"].append({
                            "shot": int(shot_num),
                            "shot_size": cols[1] if len(cols) > 1 else "",
                            "camera": cols[2] if len(cols) > 2 else "",
                            "description": cols[3] if len(cols) > 3 else "",
                        })

        if current_segment:
            segments.append(current_segment)

        return segments


# ─────────────────────────────────────────────────────────────────────────────
# 工具调用解析（供 pipeline 集成）
# ─────────────────────────────────────────────────────────────────────────────

TOOL_PATTERNS = [
    re.compile(r'\{[^{}]*"tool_call"\s*:\s*"([^"]+)"[^{}]*\}'),
    re.compile(r'```json\s*(\{[^}]*"tool_call"[^}]*\})\s*```', re.DOTALL),
]


def parse_tool_calls(text: str) -> list[dict]:
    """
    从 qwen-max 返回文本中解析工具调用。

    Returns:
        [{"name": "getAssets"}, {"name": "saveStoryboard", "file": "...", "content": "..."}]
    """
    results = []

    for pattern in TOOL_PATTERNS:
        for match in pattern.finditer(text):
            try:
                obj = json.loads(match.group(1) if pattern == TOOL_PATTERNS[1] else match.group(0))
                if "tool_call" in obj:
                    name = obj.pop("tool_call")
                    results.append({"name": name, **obj})
            except json.JSONDecodeError:
                continue

    return results


def execute_tool_call(tool: dict, project_path: str | Path | None = None) -> str:
    """
    执行单个工具调用。

    Args:
        tool: {"name": "getAssets"} 或 {"name": "saveStoryboard", "file": "...", "content": "..."}
        project_path: 项目目录

    Returns:
        工具执行结果文本
    """
    registry = ToolRegistry(project_path)
    name = tool["name"]

    if name == "getAssets":
        return registry.get_assets()
    elif name == "getSegments":
        return registry.get_segments()
    elif name == "saveStoryboard":
        return registry.save_storyboard(tool["file"], tool["content"])
    else:
        return f"❌ 未知工具：{name}"


def process_with_tools(
    response: str,
    project_path: str | Path | None = None,
    max_iterations: int = 3,
) -> tuple[str, list[str]]:
    """
    处理包含工具调用的响应，自动执行工具并追加结果。

    Args:
        response: qwen-max 原始返回文本
        project_path: 项目目录

    Returns:
        (清理后的文本, 工具结果列表)
    """
    tool_results = []
    current_text = response

    for _ in range(max_iterations):
        tools = parse_tool_calls(current_text)
        if not tools:
            break

        for tool in tools:
            result = execute_tool_call(tool, project_path)
            tool_results.append(f"\n[工具调用: {tool['name']}]\n{result}\n")

        # 清理已解析的工具调用 JSON
        cleaned = current_text
        for pattern in TOOL_PATTERNS:
            cleaned = pattern.sub("", cleaned)

        # 追加工具结果到文本末尾
        tool_output = "\n".join(tool_results)
        current_text = cleaned.rstrip() + "\n\n" + tool_output

    return current_text, tool_results


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def _cli():
    import argparse
    parser = argparse.ArgumentParser(description="分镜师工具调用执行器")
    sub = parser.add_subparsers(dest="cmd")

    p_assets = sub.add_parser("get-assets", help="获取资产列表")
    p_assets.add_argument("--project", default=".", help="项目目录")

    p_seg = sub.add_parser("get-segments", help="获取讲戏本分段")
    p_seg.add_argument("--project", default=".", help="项目目录")

    p_save = sub.add_parser("save", help="保存分镜脚本")
    p_save.add_argument("--file", "-f", required=True, help="输出文件路径")
    p_save.add_argument("--project", default=".", help="项目目录")
    p_save.add_argument("--content", "-c", required=True, help="分镜脚本内容")

    p_parse = sub.add_parser("parse", help="解析文本中的工具调用")
    p_parse.add_argument("--text", "-t", required=True, help="待解析文本")
    p_parse.add_argument("--project", default=".", help="项目目录")

    args = parser.parse_args()

    registry = ToolRegistry(args.project)

    if args.cmd == "get-assets":
        print(registry.get_assets())

    elif args.cmd == "get-segments":
        print(registry.get_segments())

    elif args.cmd == "save":
        print(registry.save_storyboard(args.file, args.content))

    elif args.cmd == "parse":
        result, _ = process_with_tools(args.text, args.project)
        print("=== 清理后文本 ===")
        print(result)


if __name__ == "__main__":
    _cli()
