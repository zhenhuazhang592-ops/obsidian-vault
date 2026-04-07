#!/usr/bin/env python3
"""validate_outline.py — outline JSON 校验脚本

用法：
  python3 scripts/validate_outline.py <file.md>
  python3 scripts/validate_outline.py <file.md> --write
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config.outline_schema import EpisodeOutline


def extract_json_from_markdown(content: str) -> str:
    """提取 Markdown 中的 ```json ``` 块内容"""
    pattern = r"```(?:json)?\s*\n?(.*?)\n?```"
    matches = re.findall(pattern, content, re.DOTALL)
    if not matches:
        raise ValueError("Markdown 中未找到 ```json ``` 代码块")
    if len(matches) > 1:
        raise ValueError(f"找到 {len(matches)} 个 JSON 块，预期1个")
    return matches[0].strip()


def validate_and_load(content: str) -> EpisodeOutline:
    """校验并解析 JSON"""
    json_str = extract_json_from_markdown(content)
    data = json.loads(json_str)
    return EpisodeOutline.model_validate(data)


def main():
    args = sys.argv[1:]
    write_mode = "--write" in args
    if write_mode:
        args.remove("--write")

    if len(args) < 1:
        print("用法: validate_outline.py <file.md> [--write]")
        sys.exit(1)

    file_path = Path(args[0])
    if not file_path.exists():
        print(f"文件不存在: {file_path}")
        sys.exit(1)

    content = file_path.read_text(encoding="utf-8")

    try:
        outline = validate_and_load(content)
    except Exception as e:
        print(f"\nX JSON 校验失败: {e}")
        print(f"   文件: {file_path}")
        print(f"\n请修正后重新生成。")
        sys.exit(1)

    print(f"\n[OK] Schema 校验通过")
    print(f"   集数: {outline.episodeIndex}")
    print(f"   标题: {outline.title}")
    print(f"   角色: {len(outline.characters)} 个")
    print(f"   场景: {len(outline.scenes)} 个")
    print(f"   道具: {len(outline.props)} 个")
    print(f"   情绪曲线: {outline.emotionalCurve}")

    if write_mode:
        json_content = json.dumps(outline.model_dump(), ensure_ascii=False, indent=2)
        output = f"""---
episodeIndex: {outline.episodeIndex}
title: {outline.title}
chapterRange: {outline.chapterRange}
coreConflict: {outline.coreConflict}
charactersCount: {len(outline.characters)}
scenesCount: {len(outline.scenes)}
propsCount: {len(outline.props)}
---

# 大纲

```json
{json_content}
```
"""
        output_path = file_path
        output_path.write_text(output, encoding="utf-8")
        print(f"\n[FILE] 已写入: {output_path}")

    sys.exit(0)


if __name__ == "__main__":
    main()
