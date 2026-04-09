#!/usr/bin/env python3
"""
novel_manager.py — 小说原文管理器

对标 Toonflow t_novel 表，替代纯文件方案：
- 解析 TXT/JSON/JSONL 小说文件 → 章节结构化
- 存入 task_db.novels 表
- 供 OutlineAgent（storyline pipeline）读取

用法：
  python3 scripts/novel_manager.py import \
    --project 漠玫传 \
    --file docs/小说原文.txt

  python3 scripts/novel_manager.py list \
    --project 漠玫传

  python3 scripts/novel_manager.py dump \
    --project 漠玫传 \
    --chapters 1,2,3 \
    --format prompt  # 输出可直接喂给 OutlineAgent 的格式
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.task_db import TaskDB

BASE_DIR = Path(__file__).parent.parent


# ─────────────────────────────────────────────────────────────────────────────
# 章节解析器
# ─────────────────────────────────────────────────────────────────────────────

def parse_txt_chapters(content: str) -> list[dict]:
    """
    解析 TXT 小说文本，自动识别章节分割。

    支持格式：
      - 第1章 章节名
      - 第1章: 章节名
      - Chapter 1: Title
      - 【第一章】章节名
      - 第一节 章节名

    Returns:
        [{chapter_index, chapter, chapter_data}, ...]
    """
    # 章节标题正则（优先级从高到低）
    patterns = [
        # 第X章 章节名（中文）
        re.compile(r'^第\s*([零一二三四五六七八九十百千\d]+)\s*章[:：]?\s*(.+?)$', re.MULTILINE),
        # 【第一章】章节名
        re.compile(r'^【第\s*([零一二三四五六七八九十百千\d]+)\s*章】\s*(.+?)$', re.MULTILINE),
        # 第X节 / 第一节 章节名
        re.compile(r'^第\s*([零一二三四五六七八九十百千\d]+)\s*[节篇部]?\s*[:：]?\s*(.+?)$', re.MULTILINE),
        # Chapter 1: Title
        re.compile(r'^Chapter\s+(\d+)[:：]?\s*(.+?)$', re.MULTILINE | re.IGNORECASE),
        # 01. 章节名 / 01 章节名
        re.compile(r'^(\d+)[.、]\s*(.+?)$', re.MULTILINE),
    ]

    chapters = []
    chinese_nums = str.maketrans("零一二三四五六七八九", "0123456789")

    # 尝试用各正则拆分
    split_pattern = re.compile(
        r'(?=^第\s*[零一二三四五六七八九十百千\d]+\s*[章节篇部]|^Chapter\s+\d+|^【第\s*[零一二三四五六七八九十百千\d]+\s*章】|^\d+[.、]\s*)',
        re.MULTILINE,
    )

    parts = split_pattern.split(content)
    parts = [p.strip() for p in parts if p.strip()]

    if len(parts) <= 1:
        # 无法自动拆分，整篇作为一个章节
        return [{"chapter_index": 1, "chapter": "全文", "chapter_data": content.strip()}]

    idx = 1
    for part in parts:
        part = part.strip()
        if not part:
            continue
        # 取第一行作为章节名
        first_line = part.split('\n')[0].strip()
        # 去掉章节标记前缀，保留标题
        clean_title = first_line
        for pat in patterns:
            m = pat.match(first_line)
            if m:
                raw_num = m.group(1)
                title = m.group(2).strip() if m.lastindex >= 2 else ""
                # 转换中文数字
                try:
                    # 尝试转换中文数字
                    num_str = raw_num.translate(chinese_nums)
                    ch_idx = int(num_str)
                except ValueError:
                    ch_idx = idx
                clean_title = title if title else first_line
                chapters.append({
                    "chapter_index": ch_idx,
                    "chapter": clean_title,
                    "chapter_data": part,
                })
                idx += 1
                break
        else:
            # 未匹配章节正则，使用序号
            chapters.append({
                "chapter_index": idx,
                "chapter": clean_title[:40] or f"第{idx}节",
                "chapter_data": part,
            })
            idx += 1

    # 按 chapter_index 排序去重
    chapters.sort(key=lambda x: x["chapter_index"])
    # 重新编号（处理中文数字跳号情况）
    for i, ch in enumerate(chapters, 1):
        ch["chapter_index"] = i

    return chapters


def parse_json_chapters(content: str) -> list[dict]:
    """
    解析 JSON 格式小说文件。

    支持格式：
      - [{"chapter_index": 1, "chapter": "章名", "chapter_data": "..."}, ...]
      - {"chapters": [...]} 或 {"data": [...]} 或 {"sections": [...]}
      - {"chapter": "章名", "content": "..."}  # 单章格式
    """
    data = json.loads(content)

    # 包装格式
    for key in ("chapters", "data", "sections", "rows"):
        if isinstance(data, dict) and key in data:
            data = data[key]
            break

    if isinstance(data, dict):
        # 单章格式
        return [{
            "chapter_index": data.get("chapter_index", 1),
            "chapter": data.get("chapter", "第1章"),
            "chapter_data": data.get("chapter_data", data.get("content", "")),
        }]

    if not isinstance(data, list):
        raise ValueError(f"JSON 结构不支持：{type(data)}")

    # 标准化字段名
    result = []
    for i, item in enumerate(data, 1):
        result.append({
            "chapter_index": item.get("chapter_index", item.get("index", i)),
            "chapter": item.get("chapter", item.get("title", f"第{i}章")),
            "chapter_data": (
                item.get("chapter_data")
                or item.get("content")
                or item.get("text", "")
            ),
            "reel": item.get("reel", ""),
        })
    return result


def parse_novel_file(path: Path) -> list[dict]:
    """根据文件扩展名自动选择解析器"""
    ext = path.suffix.lower()
    content = path.read_text(encoding="utf-8")

    if ext in (".json", ".jsonl"):
        return parse_json_chapters(content)
    elif ext in (".txt", ".text", ".md"):
        return parse_txt_chapters(content)
    else:
        raise ValueError(f"不支持的文件格式：{ext}，支持：.txt/.md/.json/.jsonl")


# ─────────────────────────────────────────────────────────────────────────────
# NovelManager
# ─────────────────────────────────────────────────────────────────────────────

class NovelManager:
    """
    小说原文管理器

    核心职责：
    - 导入小说文件 → 章节结构化 → 存入 DB
    - 读取章节内容（用于 OutlineAgent 的 storyline 生成）
    - 故事线存储（storyline pipeline 产出）
    """

    def __init__(self, db: TaskDB | None = None):
        self._db = db or TaskDB()

    def import_file(
        self,
        project_id: int,
        file_path: str | Path,
        reel: str = "",
    ) -> int:
        """
        导入小说文件到 DB。

        Returns:
            导入的章节数量
        """
        chapters = parse_novel_file(Path(file_path))
        if reel:
            for ch in chapters:
                ch["reel"] = reel
        count = self._db.add_novel_chapters(project_id, chapters)
        print(f"[NovelManager] 导入 {count} 章（{Path(file_path).name}）")
        return count

    def get_chapters(
        self,
        project_id: int,
        chapter_indices: list[int] | None = None,
    ) -> list[dict]:
        """获取章节列表（不含完整原文，用于目录）"""
        return self._db.get_novel_chapters(project_id, chapter_indices)

    def get_chapter_raw(self, project_id: int, chapter_index: int) -> str | None:
        """获取单个章节原文"""
        return self._db.get_novel_chapter_raw(project_id, chapter_index)

    def get_storyline(self, project_id: int) -> dict | None:
        """获取故事线"""
        return self._db.get_storyline(project_id)

    def save_storyline(self, project_id: int, content: str, novel_ids: list[int] | None = None) -> int:
        """保存故事线"""
        return self._db.save_storyline(project_id, content, novel_ids)

    def dump_for_outline(
        self,
        project_id: int,
        chapter_indices: list[int] | None = None,
        max_chars: int = 50000,
    ) -> str:
        """
        导出章节内容为可喂给 OutlineAgent 的 prompt 格式。

        Args:
            project_id: 项目 ID
            chapter_indices: 指定章节（None = 全部）
            max_chars: 最大字符数（防止超出 context window）

        Returns:
            格式化的章节文本
        """
        chapters = self._db.get_novel_chapters(project_id, chapter_indices)
        if not chapters:
            return ""

        lines = []
        total = 0
        for ch in chapters:
            data = ch.get("chapter_data", "")
            if total + len(data) > max_chars:
                # 截断
                remaining = max_chars - total
                if remaining > 200:
                    lines.append(f"\n=== {ch['chapter']} ===\n")
                    lines.append(data[:remaining] + "\n[以下内容已截断...]")
                break
            lines.append(f"\n=== {ch['chapter']} ===\n")
            lines.append(data)
            total += len(data)

        result = "".join(lines)
        print(f"[NovelManager] dump {len(chapters)} 章，共 {total} 字")
        return result

    def dump_storyline_for_prompt(self, project_id: int) -> str:
        """导出故事线（已有 storyline 时，用于续写/对比）"""
        sl = self._db.get_storyline(project_id)
        if not sl:
            return ""
        return sl.get("content", "")


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def _cli():
    parser = argparse.ArgumentParser(description="小说原文管理器")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # import
    p_import = sub.add_parser("import", help="导入小说文件")
    p_import.add_argument("--project-id", type=int, required=True)
    p_import.add_argument("--file", required=True, help="小说文件路径")
    p_import.add_argument("--reel", default="", help="分卷名")

    # list
    p_list = sub.add_parser("list", help="列出章节")
    p_list.add_argument("--project-id", type=int, required=True)

    # dump
    p_dump = sub.add_parser("dump", help="导出章节内容")
    p_dump.add_argument("--project-id", type=int, required=True)
    p_dump.add_argument("--chapters", help="章节号，逗号分隔")
    p_dump.add_argument("--max-chars", type=int, default=50000)
    p_dump.add_argument("--format", default="text", choices=["text", "prompt"])

    # storyline
    p_sl = sub.add_parser("storyline", help="查看/保存故事线")
    p_sl.add_argument("--project-id", type=int, required=True)
    p_sl.add_argument("--save", help="保存故事线内容")

    args = parser.parse_args()
    nm = NovelManager()

    if args.cmd == "import":
        count = nm.import_file(args.project_id, args.file, args.reel)
        print(f"✅ 导入完成：{count} 章")

    elif args.cmd == "list":
        chapters = nm.get_chapters(args.project_id)
        print(f"共 {len(chapters)} 章：")
        for ch in chapters:
            data_len = len(ch.get("chapter_data", ""))
            print(f"  [{ch['chapter_index']:>3}] {ch['chapter']} ({data_len}字)")

    elif args.cmd == "dump":
        indices = None
        if args.chapters:
            indices = [int(x.strip()) for x in args.chapters.split(",")]
        if args.format == "prompt":
            content = nm.dump_for_outline(args.project_id, indices, args.max_chars)
            print(content)
        else:
            chapters = nm.get_chapters(args.project_id, indices)
            for ch in chapters:
                print(f"\n=== {ch['chapter']} ===\n{ch.get('chapter_data', '')}")

    elif args.cmd == "storyline":
        if args.save:
            nm.save_storyline(args.project_id, args.save)
            print("✅ 故事线已保存")
        else:
            sl = nm.get_storyline(args.project_id)
            if sl:
                print(sl.get("content", ""))
            else:
                print("（暂无故事线）")


if __name__ == "__main__":
    _cli()
