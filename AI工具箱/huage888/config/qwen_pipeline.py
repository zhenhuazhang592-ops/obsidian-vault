#!/usr/bin/env python3
"""
qwen_pipeline.py — qwen-max API 调用封装脚本

huage888 系统的核心推理引擎，所有内容生成通过此脚本调用 qwen-max。

用法：
  python3 config/qwen_pipeline.py --test

  # 方式1：直接传 system + user
  python3 config/qwen_pipeline.py \
    --system "你是一个专业的导演..." \
    --user "请分析以下剧本..."

  # 方式2（推荐）：传 agent + user，自动拼接 agents/*.md + skills/*.md
  python3 config/qwen_pipeline.py \
    --agent director \
    --user "请分析以下剧本..." \
    --output outputs/01-director-analysis.md

  # 方式3：显式指定 skill 文件
  python3 config/qwen_pipeline.py \
    --agent director \
    --skill director \
    --user "请分析以下剧本..."

  # 指定模型和温度（覆盖 agent 默认值）
  python3 config/qwen_pipeline.py \
    --agent director \
    --user "..." \
    --model qwen-plus \
    --temperature 0.8

  # 开启任务追踪（状态 + 事件，输出到 .huage888/）
  python3 config/qwen_pipeline.py --agent director --user "..." --track

  # 静默模式（不输出事件到控制台，写入日志文件）
  python3 config/qwen_pipeline.py --agent director --user "..." --no-emit

环境变量：
  QWEN_API_KEY   必填
  QWEN_BASE_URL  可选，默认 https://dashscope.aliyuncs.com/compatible-mode/v1
  QWEN_MODEL     可选，默认 qwen-max
"""

import argparse
import os
import re
import sys
import time
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# 路径配置（相对于本脚本所在目录）
# ─────────────────────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).parent
BASE_DIR = SCRIPT_DIR.parent  # huage888 根目录
SCRIPTS_DIR = BASE_DIR / "scripts"

# 添加 scripts/ 到 Python 路径（task_state / event_emitter）
sys.path.insert(0, str(SCRIPTS_DIR))

try:
    from openai import OpenAI
except ImportError:
    print("错误：缺少 openai 库。请运行：pip install openai", file=sys.stderr)
    sys.exit(1)

# 延迟导入追踪模块（仅在 --track 时使用，避免硬依赖）
_task_state_module = None
_event_emitter_module = None


def _lazy_task_state():
    global _task_state_module
    if _task_state_module is None:
        from task_state import TaskManager, TaskState, TaskType
        _task_state_module = (TaskManager, TaskState, TaskType)
    return _task_state_module


def _lazy_event_emitter(log_file: str | None = None, emit_console: bool = True):
    global _event_emitter_module
    if _event_emitter_module is None:
        from event_emitter import (
            EventEmitter, ConsoleSink, JSONLSink,
        )
        _event_emitter_module = (EventEmitter, ConsoleSink, JSONLSink)
    EventEmitter, ConsoleSink, JSONLSink = _event_emitter_module

    sinks = []
    if emit_console:
        sinks.append(ConsoleSink(color=True, progress_bar=True))
    if log_file:
        sinks.append(JSONLSink(log_file))
    return EventEmitter(sinks=sinks if sinks else None)


# ─────────────────────────────────────────────────────────────────────────────
# Agent 默认参数
# ─────────────────────────────────────────────────────────────────────────────

AGENT_DEFAULTS = {
    "director":          {"temperature": 0.75, "top_p": 0.95, "max_tokens": 8192},
    "art-designer":      {"temperature": 0.65, "top_p": 0.95, "max_tokens": 8192},
    "prop-designer":     {"temperature": 0.60, "top_p": 0.95, "max_tokens": 8192},
    "storyboard-artist": {"temperature": 0.55, "top_p": 0.95, "max_tokens": 8192},
    "script-review":     {"temperature": 0.40, "top_p": 0.90, "max_tokens": 4096},
    "art-review":        {"temperature": 0.40, "top_p": 0.90, "max_tokens": 4096},
    "storyboard-review": {"temperature": 0.40, "top_p": 0.90, "max_tokens": 4096},
}

DEFAULT_MODEL = "qwen-max"
MAX_RETRIES = 3
RETRY_DELAY = 30  # 秒

AGENTS_DIR = BASE_DIR / "agents"
SKILLS_DIR = BASE_DIR / "skills"


# ─────────────────────────────────────────────────────────────────────────────
# Skill 文件加载（两层拼接）
# ─────────────────────────────────────────────────────────────────────────────

def strip_front_matter(content: str) -> str:
    """去掉 YAML front matter，只留正文"""
    md_match = re.match(r"^---\s*\n.*?\n---\s*\n(.*)$", content, re.DOTALL)
    return md_match.group(1).strip() if md_match else content.strip()


def load_skill_content(skill_name: str) -> str:
    """
    加载 skill 文件的完整正文（不含 front matter）。
    查找路径（按优先级）：
      skills/<skill_name>/SKILL.md
      skills/<skill_name>.md
      skills/<skill_name>-skill.md               （兼容 director-skill.md）
      skills/<stripped>-skill.md                 （兼容 storyboard-artist → storyboard-skill.md）
      skills/<stripped>.md                       （兼容 storyboard-artist → storyboard.md）
    其中 strip_suffix 按顺序去掉：-designer → -artist → -review → -er
    """
    AGENT_TO_SKILL_BASE = {
        "art-designer":     "art-design",
        "prop-designer":    "prop-design",
        "storyboard-artist": "storyboard",
    }

    def strip_suffix(name: str) -> str:
        """去掉常见 agent 后缀，还原为 skill 文件名"""
        for suffix in ["-designer", "-artist", "-review", "-er"]:
            if name.endswith(suffix):
                return name[: -len(suffix)]
        return name

    base = AGENT_TO_SKILL_BASE.get(skill_name, strip_suffix(skill_name))
    candidates = [
        SKILLS_DIR / skill_name / "SKILL.md",
        SKILLS_DIR / f"{skill_name}.md",
        SKILLS_DIR / f"{skill_name}-skill.md",
        SKILLS_DIR / f"{base}-skill.md",
        SKILLS_DIR / f"{base}.md",
    ]
    for path in candidates:
        if path.exists():
            content = path.read_text(encoding="utf-8")
            print(f"  加载 skill：{path.relative_to(BASE_DIR)}", file=sys.stderr)
            return strip_front_matter(content)
    print(f"  警告：skill 文件不存在 [{skill_name}]，跳过", file=sys.stderr)
    return ""


def build_system_prompt(agent_name: str, skill_name: str | None) -> str:
    """
    构建完整的 system prompt：

    层级1：agents/<agent_name>.md（角色定义，必有）
    层级2：skills/<skill_name>/SKILL.md（格式模板+质量清单，按需）

    如果 skill_name 未指定，默认与 agent_name 相同。
    """
    agent_file = AGENTS_DIR / f"{agent_name}.md"
    if not agent_file.exists():
        raise FileNotFoundError(f"agent 文件不存在：{agent_file}")

    agent_content = agent_file.read_text(encoding="utf-8")
    print(f"  加载 agent：{agent_file.relative_to(BASE_DIR)}", file=sys.stderr)

    skill_name = skill_name or agent_name
    skill_content = load_skill_content(skill_name)

    parts = [agent_content]
    if skill_content:
        parts.append("\n---\n\n## 详细执行规范（来自 skill）\n\n")
        parts.append(skill_content)

    return "\n".join(parts)


# ─────────────────────────────────────────────────────────────────────────────
# 客户端初始化
# ─────────────────────────────────────────────────────────────────────────────

def get_client() -> OpenAI:
    api_key = os.environ.get("QWEN_API_KEY", "")
    if not api_key:
        print("错误：请设置 QWEN_API_KEY 环境变量", file=sys.stderr)
        print("  export QWEN_API_KEY='your-api-key-here'", file=sys.stderr)
        sys.exit(1)

    base_url = os.environ.get(
        "QWEN_BASE_URL",
        "https://dashscope.aliyuncs.com/compatible-mode/v1"
    )

    return OpenAI(api_key=api_key, base_url=base_url)


# ─────────────────────────────────────────────────────────────────────────────
# 核心调用（支持可选的事件追踪）
# ─────────────────────────────────────────────────────────────────────────────

def call_qwen(
    system: str,
    user: str,
    model: str = DEFAULT_MODEL,
    temperature: float | None = None,
    top_p: float | None = None,
    max_tokens: int | None = None,
    # ── 追踪参数（可选）───────────────────────────────────────────────
    emitter=None,
    task_id: str | None = None,
    task_name: str = "qwen-call",
) -> str:
    """
    调用 qwen-max，返回 assistant 的 content。
    429 / 500 错误自动重试，最多 MAX_RETRIES 次。

    Args:
        emitter: EventEmitter 实例，用于发送事件（可选）
        task_id: 任务 ID（emitter 开启时必填）
        task_name: 任务名称（用于事件输出）
    """
    client = get_client()

    defaults = {"temperature": 0.7, "top_p": 0.95, "max_tokens": 8192}
    temperature = temperature if temperature is not None else defaults["temperature"]
    top_p = top_p if top_p is not None else defaults["top_p"]
    max_tokens = max_tokens if max_tokens is not None else defaults["max_tokens"]

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]

    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            if emitter and task_id:
                emitter.emit_task_progress(
                    task_id, task_name,
                    status="api_call",
                    message=f"调用 API（第 {attempt}/{MAX_RETRIES} 次）...",
                    progress=0.5,
                )

            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens,
                stream=False,
            )
            content = response.choices[0].message.content

            if not content or not content.strip():
                print("警告：API 返回内容为空", file=sys.stderr)
                return ""

            if emitter and task_id:
                emitter.emit_task_progress(
                    task_id, task_name,
                    status="complete",
                    message="生成完成",
                    progress=1.0,
                )

            return content

        except Exception as e:
            last_error = str(e)

            if "429" in last_error or "rate_limit" in last_error.lower():
                msg = f"限流，{RETRY_DELAY}s 后重试（第 {attempt}/{MAX_RETRIES} 次）"
                print(msg, file=sys.stderr)
                if emitter and task_id:
                    emitter.emit_task_progress(
                        task_id, task_name,
                        status="retry",
                        message=msg,
                        progress=-1,
                    )
                time.sleep(RETRY_DELAY)
                continue

            if "500" in last_error or "InternalServerError" in last_error:
                msg = f"服务端错误，10s 后重试（第 {attempt}/{MAX_RETRIES} 次）"
                print(msg, file=sys.stderr)
                if emitter and task_id:
                    emitter.emit_task_progress(
                        task_id, task_name,
                        status="retry",
                        message=msg,
                        progress=-1,
                    )
                time.sleep(10)
                continue

            # 不可重试的错误
            if emitter and task_id:
                emitter.emit_task_error(task_id, task_name, error=str(e))
            print(f"API 调用失败：{e}", file=sys.stderr)
            sys.exit(1)

    # 全部重试失败
    if emitter and task_id:
        emitter.emit_task_error(task_id, task_name, error=f"重试 {MAX_RETRIES} 次后仍失败：{last_error}")
    print(f"重试 {MAX_RETRIES} 次后仍失败：{last_error}", file=sys.stderr)
    sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────────
# 测试模式
# ─────────────────────────────────────────────────────────────────────────────

def test_connection():
    print("=" * 60)
    print("huage888 qwen-max 连接测试")
    print("=" * 60)

    client = get_client()
    model = os.environ.get("QWEN_MODEL", DEFAULT_MODEL)

    print(f"模型：{model}")
    print(f"Base URL：{client.base_url}")

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是一个专业的短剧分镜导演。"},
                {"role": "user", "content": "用一句话介绍你自己。"}
            ],
            temperature=0.7,
            max_tokens=100,
            stream=False,
        )
        content = response.choices[0].message.content
        usage = response.usage

        print(f"\n状态：✅ 连接成功")
        print(f"回复：{content}")
        print(f"Token：prompt={usage.prompt_tokens}, completion={usage.completion_tokens}, total={usage.total_tokens}")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"\n状态：❌ 连接失败", file=sys.stderr)
        print(f"错误：{e}", file=sys.stderr)
        err_str = str(e)
        if "401" in err_str or "authentication" in err_str.lower():
            print("\n诊断：API Key 无效或未设置", file=sys.stderr)
        elif "403" in err_str:
            print("\n诊断：权限不足，可能余额为 0", file=sys.stderr)
        elif "connection" in err_str.lower():
            print("\n诊断：网络连接问题", file=sys.stderr)
        return False


# ─────────────────────────────────────────────────────────────────────────────
# 参数解析
# ─────────────────────────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(
        description="qwen-max API 调用脚本（huage888 核心推理引擎）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # 两类调用方式（互斥）
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--agent", "-a", default="",
                       help="Agent 名称，自动拼接 agents/<name>.md + skills/<name>/SKILL.md")

    parser.add_argument("--skill", "-k", default=None,
                        help="Skill 名称（默认等于 --agent），指定要加载的 skills/<name>/SKILL.md")

    parser.add_argument("--system", "-s",
                        help="System prompt（覆盖 --agent 模式）")
    parser.add_argument("--user", "-u",
                        help="User prompt（任务内容）")
    parser.add_argument("--system-file",
                        help="从文件读取 system prompt（覆盖 --agent 模式）")
    parser.add_argument("--user-file",
                        help="从文件读取 user prompt")

    parser.add_argument("--model", "-m", default=DEFAULT_MODEL,
                        help=f"模型名称，默认 {DEFAULT_MODEL}")
    parser.add_argument("--temperature", "-t", type=float,
                        help="Temperature，随机性控制")
    parser.add_argument("--top-p", type=float,
                        help="Top-p，采样范围控制")
    parser.add_argument("--max-tokens", type=int,
                        help="最大输出 token 数")
    parser.add_argument("--output", "-o",
                        help="输出文件路径（直接写入，不打印到 stdout）")
    parser.add_argument(
        "--asset-library",
        action="store_true",
        default=False,
        help="自动加载 assets/library/ 的 manifest，拼入 system prompt 资产引用"
    )
    parser.add_argument("--asset-output",
                        dest="asset_output", default=None,
                        help="将 outline JSON 中的 characters/scenes/props 提取写入指定文件")
    parser.add_argument("--test", action="store_true",
                        help="测试 API 连接，不执行内容生成")

    # ── 追踪参数 ──────────────────────────────────────────────────────
    tracking = parser.add_argument_group("追踪参数（可选）")
    tracking.add_argument(
        "--track", action="store_true", default=False,
        help="开启任务追踪（状态持久化 + 事件推送）"
    )
    tracking.add_argument(
        "--no-track", action="store_true", default=False,
        help="禁用任务追踪（覆盖 --track）"
    )
    tracking.add_argument(
        "--log-file",
        default=None,
        help="事件日志文件路径（默认 .huage888/events.jsonl）"
    )
    tracking.add_argument(
        "--no-emit", action="store_true", default=False,
        help="禁用控制台事件输出（静默模式，仍写入 --log-file）"
    )
    tracking.add_argument(
        "--tasks-dir",
        default=None,
        help="任务状态持久化目录（默认 .huage888/tasks）"
    )

    return parser.parse_args()


def load_prompt_from_file(path: str) -> str:
    """从文件读取 prompt"""
    if not os.path.exists(path):
        raise FileNotFoundError(f"文件不存在：{path}")
    with open(path, encoding="utf-8") as f:
        return f.read()


# ─────────────────────────────────────────────────────────────────────────────
# 主函数
# ─────────────────────────────────────────────────────────────────────────────

def main():
    args = parse_args()

    # 测试模式
    if args.test:
        ok = test_connection()
        sys.exit(0 if ok else 1)

    # ── 追踪初始化 ───────────────────────────────────────────────────
    do_track = args.track and not args.no_track
    emit_console = not args.no_emit

    emitter = None
    task_manager = None
    task_id = None
    task_name = f"qwen-{args.agent or 'adhoc'}"

    if do_track:
        log_file = args.log_file or str(BASE_DIR / ".huage888" / "events.jsonl")
        emitter = _lazy_event_emitter(log_file=log_file, emit_console=emit_console)

        if emit_console:
            TaskManager, _, _ = _lazy_task_state()
            tasks_dir = args.tasks_dir or str(BASE_DIR / ".huage888" / "tasks")
            task_manager = TaskManager(tasks_dir=tasks_dir)
            task_id = task_manager.create(
                task_type="qwen",
                name=task_name,
                params={
                    "agent": args.agent,
                    "model": args.model,
                    "temperature": args.temperature,
                    "output": args.output,
                },
            )
            print(f"\n📊 任务追踪已开启（ID: {task_id}）", file=sys.stderr)

    # ── 构建 system prompt ────────────────────────────────────────────

    if args.system or args.system_file:
        if args.system_file:
            system = load_prompt_from_file(args.system_file)
        else:
            system = args.system

        if not system or not system.strip():
            print("错误：system prompt 为空", file=sys.stderr)
            sys.exit(1)

    elif args.agent:
        print(f"\n📦 构建 system prompt（agent={args.agent}, skill={args.skill or '(默认=agent)'}）",
              file=sys.stderr)
        system = build_system_prompt(args.agent, args.skill)
        print(f"  system prompt 长度：{len(system)} 字符", file=sys.stderr)

    else:
        print("错误：请提供 --agent 或 --system", file=sys.stderr)
        sys.exit(1)

    # ── 资产库注入（--asset-library）──────────────────────────────
    if args.asset_library and args.agent and args.agent != "outline":
        try:
            sys.path.insert(0, str(BASE_DIR / "scripts"))
            from asset_library import AssetLibrary

            lib = AssetLibrary()
            # 从 user 内容中推断项目名
            project_hint = ""
            user_content = args.user or ""
            for kw in ["漠玫传", "漠玫", "断桥", "漠玫IP"]:
                if kw in user_content:
                    project_hint = "漠玫传"
                    break

            if project_hint:
                assets = lib.list_by_project(project_hint)
                lines = ["\n\n## 可用资产（来自 assets/library/）"]
                for atype, names in assets.items():
                    if names:
                        lines.append(f"### {atype}:")
                        for n in names:
                            refs = lib.resolve(n, atype.rstrip("s"))
                            lines.append(f"- {n}: {refs}")
                if len(lines) > 1:
                    asset_context = "\n".join(lines)
                    system = system + asset_context
                    print(f"\n[Asset Library] 发现 {sum(1 for a in assets.values() for _ in a)} 个资产", file=sys.stderr)
        except Exception as e:
            print(f"\n[WARN] 资产库加载失败: {e}", file=sys.stderr)

    # ── 构建 user prompt ──────────────────────────────────────────────

    if not args.user and not args.user_file:
        print("错误：请提供 --user 或 --user-file", file=sys.stderr)
        sys.exit(1)

    if args.user_file:
        user = load_prompt_from_file(args.user_file)
    else:
        user = args.user

    if not user.strip():
        print("错误：user prompt 为空", file=sys.stderr)
        sys.exit(1)

    # ── 加载 agent 默认参数 ──────────────────────────────────────────

    temperature = args.temperature
    top_p = args.top_p
    max_tokens = args.max_tokens

    if args.agent and args.agent in AGENT_DEFAULTS:
        defaults = AGENT_DEFAULTS[args.agent]
        temperature = temperature or defaults["temperature"]
        top_p = top_p or defaults["top_p"]
        max_tokens = max_tokens or defaults["max_tokens"]

    # ── 追踪：发射 task_start ─────────────────────────────────────────

    if emitter and task_id:
        emitter.emit_task_start(task_name, params={"agent": args.agent, "model": args.model})
        TaskState, _, _ = _lazy_task_state()
        task_manager.update(task_id, TaskState.RUNNING)

    # ── 调用 API ─────────────────────────────────────────────────────

    print(f"\n🤖 调用 qwen-max（model={args.model}, temp={temperature}）", file=sys.stderr)
    content = call_qwen(
        system=system,
        user=user,
        model=args.model,
        temperature=temperature,
        top_p=top_p,
        max_tokens=max_tokens,
        emitter=emitter,
        task_id=task_id,
        task_name=task_name,
    )

    # ── 追踪：发射 task_end ──────────────────────────────────────────

    if emitter and task_id:
        emitter.emit_task_end(
            task_id, task_name,
            result={"output": args.output or "<stdout>", "length": len(content)},
            elapsed=0,  # 不知道实际耗时，设为 0
            result_preview=f"{len(content)}字符" + (f" → {args.output}" if args.output else ""),
        )
        TaskState, _, _ = _lazy_task_state()
        task_manager.update(
            task_id, TaskState.SUCCESS,
            result={"output": args.output, "length": len(content)},
        )

    # ── 输出 ─────────────────────────────────────────────────────────

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(content, encoding="utf-8")
        print(f"\n✅ 已写入：{args.output}", file=sys.stderr)
        print(f"   字符数：{len(content)}", file=sys.stderr)

        # ── 提取 assets 写入独立文件 ──────────────────────────────────
        if args.asset_output:
            try:
                import json

                def extract_json_from_markdown(text: str) -> str:
                    """从 Markdown 中提取 JSON：优先取 ```json ``` 块，否则取首个大括号段"""
                    block_match = re.search(r"```json\s*\n(.*?)\n```", text, re.DOTALL)
                    if block_match:
                        return block_match.group(1).strip()
                    first_brace = text.find("{")
                    last_brace = text.rfind("}")
                    if first_brace != -1 and last_brace > first_brace:
                        return text[first_brace : last_brace + 1]
                    return "{}"

                json_str = extract_json_from_markdown(content)
                data = json.loads(json_str)
                assets = {
                    "characters": data.get("characters", []),
                    "scenes": data.get("scenes", []),
                    "props": data.get("props", []),
                }
                asset_path = Path(args.asset_output)
                asset_path.parent.mkdir(parents=True, exist_ok=True)
                asset_path.write_text(
                    json.dumps(assets, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                print(f"\n📦 资产表已写入: {asset_path}", file=sys.stderr)
            except Exception as e:
                print(f"\n⚠️ 资产提取失败（不影响主输出）: {e}", file=sys.stderr)
    else:
        print("\n" + "=" * 60, file=sys.stderr)
        print("qwen-max 返回内容：", file=sys.stderr)
        print("=" * 60)
        print(content)


if __name__ == "__main__":
    main()
