#!/usr/bin/env python3
"""交互式问答工具 —— 在 CLI 中收集用户输入"""


def ask_choice(prompt: str, options: list[str], default: int = 0) -> int:
    """选择式问答"""
    print(f"\n{prompt}")
    for i, opt in enumerate(options, 1):
        marker = " [默认]" if i == default + 1 else ""
        print(f"  [{i}] {opt}{marker}")
    while True:
        raw = input("请选择: ").strip()
        if not raw:
            return default
        try:
            idx = int(raw) - 1
            if 0 <= idx < len(options):
                return idx
        except ValueError:
            pass
        print("无效输入，请重新选择")


def ask_text(prompt: str, default: str = "") -> str:
    """文本输入"""
    suffix = f" [{default}]" if default else ""
    while True:
        raw = input(f"\n{prompt}{suffix}: ").strip()
        if raw:
            return raw
        if default:
            return default
        print("输入不能为空")


def ask_yes_no(prompt: str, default: bool = True) -> bool:
    """是/否问答"""
    suffix = " [Y/n]" if default else " [y/N]"
    while True:
        raw = input(f"{prompt}{suffix}: ").strip().lower()
        if not raw:
            return default
        if raw in ("y", "yes"):
            return True
        if raw in ("n", "no"):
            return False
        print("请输入 y 或 n")


def ask_multiline(prompt: str) -> str:
    """多行文本输入（输入空行结束）"""
    print(f"\n{prompt}")
    print("（输入空行结束）")
    lines = []
    while True:
        line = input()
        if not line.strip():
            break
        lines.append(line)
    return "\n".join(lines)


def show_progress(current: int, total: int, label: str = ""):
    """显示进度条"""
    if total == 0:
        print()
        return
    pct = current / total * 100
    filled = int(pct // 5)
    bar = "█" * filled + "░" * (20 - filled)
    end = "" if current < total else "\n"
    print(f"\r{label} [{bar}] {pct:.0f}% ({current}/{total})", end=end, flush=True)
