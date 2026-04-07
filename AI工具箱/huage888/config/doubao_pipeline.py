#!/usr/bin/env python3
"""
doubao_pipeline.py — Doubao/即梦视频/图片 API 调用封装脚本

huage888 系统的自动化视频生成引擎，封装火山方舟 Ark API。

用法：
  python3 config/doubao_pipeline.py --test

  # 视频生成（文生视频）
  python3 config/doubao_pipeline.py \
    --video \
    --prompt "古风少女在赛博竹林中缓缓睁眼 --wm true --dur 5" \
    --output /tmp/video_001.mp4

  # 图片生成
  python3 config/doubao_pipeline.py \
    --image \
    --prompt "古风少女，黑色道姑髻，超写实，电影级，8K" \
    --output /tmp/character_001.png

  # 首尾帧视频
  python3 config/doubao_pipeline.py \
    --video \
    --prompt "小女孩长大了，戴上了眼镜" \
    --img1 /path/to/first.png \
    --img2 /path/to/last.png \
    --output /tmp/transition.mp4

  # 批量视频（从分镜脚本）
  python3 config/doubao_pipeline.py \
    --batch \
    --shots-file outputs/02-storyboard-script.md \
    --output-dir outputs/videos/

  # 指定模型
  python3 config/doubao_pipeline.py --video --prompt "..." \
    --model doubao-seedance-2-0-260128 \
    --output /tmp/v.mp4

环境变量：
  ARK_API_KEY    必填
  ARK_BASE_URL   可选，默认 https://ark.cn-beijing.volces.com/api/v3
"""

import argparse
import os
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

# 延迟导入追踪模块（仅在 --track 时使用）
_task_state_module = None
_event_emitter_module = None
_webhook_module = None


def _lazy_task_state():
    global _task_state_module
    if _task_state_module is None:
        from task_state import TaskManager, TaskState, TaskType
        _task_state_module = (TaskManager, TaskState, TaskType)
    return _task_state_module


def _lazy_event_emitter(log_file: str | None = None, emit_console: bool = True):
    global _event_emitter_module
    if _event_emitter_module is None:
        from event_emitter import EventEmitter, ConsoleSink, JSONLSink
        _event_emitter_module = (EventEmitter, ConsoleSink, JSONLSink)
    EventEmitter, ConsoleSink, JSONLSink = _event_emitter_module

    sinks = []
    if emit_console:
        sinks.append(ConsoleSink(color=True, progress_bar=True))
    if log_file:
        sinks.append(JSONLSink(log_file))
    return EventEmitter(sinks=sinks if sinks else None)


def _lazy_webhook():
    global _webhook_module
    if _webhook_module is None:
        from webhook_notifier import WebhookNotifier
        _webhook_module = WebhookNotifier
    return _webhook_module

import json

# ─────────────────────────────────────────────────────────────────────────────
# 路径配置
# ─────────────────────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).parent
BASE_DIR = SCRIPT_DIR.parent
SCRIPTS_DIR = BASE_DIR / "scripts"

# 添加 scripts/ 到 Python 路径
sys.path.insert(0, str(SCRIPTS_DIR))

# ─────────────────────────────────────────────────────────────────────────────
# 模型配置
# ─────────────────────────────────────────────────────────────────────────────

VIDEO_MODEL = "doubao-seedance-2-0-260128"   # 视频生成
IMAGE_MODEL = "doubao-seedream-5-0-260128"   # 图片生成
DEFAULT_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
DEFAULT_DURATION = 5
POLL_INTERVAL = 5   # 秒
POLL_TIMEOUT = 300  # 秒

# ─────────────────────────────────────────────────────────────────────────────
# 工具函数
# ─────────────────────────────────────────────────────────────────────────────

def get_env(key: str, default: str = "") -> str:
    val = os.environ.get(key, default)
    if not val:
        print(f"错误：请设置 {key} 环境变量", file=sys.stderr)
        print(f"  export {key}='your-key-here'", file=sys.stderr)
        sys.exit(1)
    return val


def http_post(url: str, headers: dict, body: dict | None = None) -> dict:
    """发送 POST 请求"""
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode() if body else None,
        headers=headers,
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body_text = e.read().decode()
        print(f"HTTP {e.code} 错误：{body_text}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"请求失败：{e}", file=sys.stderr)
        sys.exit(1)


def http_get(url: str, headers: dict) -> dict:
    """发送 GET 请求"""
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        print(f"GET 请求失败：{e}", file=sys.stderr)
        sys.exit(1)


def download_file(url: str, output_path: Path) -> None:
    """下载文件到本地"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        urllib.request.urlretrieve(url, str(output_path))
        print(f"  下载完成：{output_path}", file=sys.stderr)
    except Exception as e:
        print(f"  下载失败：{e}", file=sys.stderr)
        sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────────
# API 调用核心
# ─────────────────────────────────────────────────────────────────────────────

def create_video_task(
    prompt: str,
    img1: str | None = None,
    img2: str | None = None,
    duration: int = DEFAULT_DURATION,
    watermark: bool = False,
    model: str = VIDEO_MODEL,
    # ── 追踪参数（可选）─────────────────────────────────────────────
    emitter=None,
    task_id: str | None = None,
    task_name: str = "doubao-video",
) -> str:
    """
    创建视频生成任务，返回 task_id。
    支持：文生视频 / 图生视频 / 首尾帧视频
    """
    api_key = get_env("ARK_API_KEY")
    base_url = get_env("ARK_BASE_URL", DEFAULT_BASE_URL)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    # 构建 content
    content = [{"type": "text", "text": f"{prompt} --wm {'true' if watermark else 'false'} --dur {duration}"}]

    # 如果有参考图，添加图片
    if img1:
        content.append({"type": "image_url", "image_url": {"url": img1}})
    if img2:
        content.append({"type": "image_url", "image_url": {"url": img2}})

    payload = {
        "model": model,
        "content": content,
    }

    url = f"{base_url}/content_generation/tasks"
    print(f"  模型：{model}", file=sys.stderr)
    print(f"  时长：{duration}s", file=sys.stderr)
    if img1:
        print(f"  参考图1：{img1[:80]}...", file=sys.stderr)
    if img2:
        print(f"  参考图2：{img2[:80]}...", file=sys.stderr)

    result = http_post(url, headers, payload)
    if "id" not in result:
        print(f"  创建任务失败：{result}", file=sys.stderr)
        sys.exit(1)

    task_id = result["id"]
    print(f"  任务ID：{task_id}", file=sys.stderr)
    return task_id


def poll_video_task(
    task_id: str,
    output_path: Path,
    model: str = VIDEO_MODEL,
    # ── 追踪参数（可选）─────────────────────────────────────────────
    emitter=None,
    external_id: str | None = None,
    task_name: str = "doubao-video",
) -> None:
    """
    轮询视频任务状态，完成后下载。
    """
    api_key = get_env("ARK_API_KEY")
    base_url = get_env("ARK_BASE_URL", DEFAULT_BASE_URL)
    headers = {"Authorization": f"Bearer {api_key}"}

    url = f"{base_url}/content_generation/tasks/{task_id}"
    start_time = time.time()

    print(f"  轮询中（每 {POLL_INTERVAL}s）...", file=sys.stderr)

    while True:
        elapsed = time.time() - start_time
        if elapsed > POLL_TIMEOUT:
            print(f"  超时（>{POLL_TIMEOUT}s）", file=sys.stderr)
            sys.exit(1)

        result = http_get(url, headers)
        status = result.get("status", "unknown")

        if status == "succeeded":
            print(f"  ✅ 成功（{elapsed:.0f}s）", file=sys.stderr)
            video_url = result.get("content", {}).get("video_url", "")
            if not video_url:
                print(f"  错误：任务成功但无 video_url：{result}", file=sys.stderr)
                if emitter and task_id:
                    emitter.emit_task_error(task_id, task_name, error="任务成功但无 video_url")
                sys.exit(1)
            print(f"  视频URL：{video_url}", file=sys.stderr)
            if emitter and task_id:
                emitter.emit_task_end(
                    task_id, task_name,
                    result={"video_url": video_url, "output": str(output_path)},
                    elapsed=elapsed,
                    result_preview=f"{elapsed:.0f}s → {output_path.name}",
                )
            download_file(video_url, output_path)
            return

        elif status == "failed":
            error = result.get("error", {})
            msg = error.get("message", str(error))
            print(f"  ❌ 失败：{msg}", file=sys.stderr)
            sys.exit(1)

        else:
            print(f"  状态：{status}（{elapsed:.0f}s）", file=sys.stderr)
            if emitter and task_id:
                emitter.emit(
                    "task_progress",
                    task_id=task_id,
                    name=task_name,
                    status="polling",
                    message=f"Doubao 任务状态：{status}",
                    progress=-1,
                )

        time.sleep(POLL_INTERVAL)


def create_and_wait_video(
    prompt: str,
    output_path: Path,
    img1: str | None = None,
    img2: str | None = None,
    duration: int = DEFAULT_DURATION,
    watermark: bool = False,
    model: str = VIDEO_MODEL,
    # ── 追踪参数（可选）─────────────────────────────────────────────
    emitter=None,
    task_id: str | None = None,
    task_name: str = "doubao-video",
) -> None:
    """创建视频任务并等待完成"""
    api_key = get_env("ARK_API_KEY")
    base_url = get_env("ARK_BASE_URL", DEFAULT_BASE_URL)
    headers = {"Authorization": f"Bearer {api_key}"}

    if emitter and task_id:
        emitter.emit_task_start(task_name, params={"prompt": prompt[:50], "model": model})

    task_id_internal = create_video_task(
        prompt=prompt,
        img1=img1,
        img2=img2,
        duration=duration,
        watermark=watermark,
        model=model,
        emitter=emitter,
        task_id=task_id,
        task_name=task_name,
    )

    # 更新外部 task_id
    actual_task_id = task_id_internal or task_id

    poll_video_task(
        task_id=actual_task_id,
        output_path=output_path,
        model=model,
        emitter=emitter,
        external_id=actual_task_id,
        task_name=task_name,
    )


def create_and_wait_image(
    prompt: str,
    output_path: Path,
    model: str = IMAGE_MODEL,
) -> None:
    """创建图片任务并等待完成"""
    api_key = get_env("ARK_API_KEY")
    base_url = get_env("ARK_BASE_URL", DEFAULT_BASE_URL)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    # Seedream 图片生成走 OpenAI 兼容格式
    try:
        from openai import OpenAI
    except ImportError:
        print("错误：缺少 openai 库。请运行：pip install openai", file=sys.stderr)
        sys.exit(1)

    client = OpenAI(api_key=api_key, base_url=base_url)
    print(f"  模型：{model}", file=sys.stderr)

    try:
        response = client.images.generate(
            model=model,
            prompt=prompt,
            size="2K",
            extra_body={"watermark": False},
        )
        image_url = response.data[0].url
        print(f"  图片URL：{image_url}", file=sys.stderr)
        download_file(image_url, output_path)

    except Exception as e:
        print(f"  图片生成失败：{e}", file=sys.stderr)
        sys.exit(1)


def create_and_wait_image_with_ref(
    prompt: str,
    output_path: Path,
    ref_images: list[Path] | None = None,
    model: str = IMAGE_MODEL,
    aspect_ratio: str = "16:9",
) -> None:
    """
    带参考图的图片生成（img2img）。
    ref_images: 参考图本地路径列表，读取后转为 base64 注入 API。
    """
    api_key = get_env("ARK_API_KEY")
    base_url = get_env("ARK_BASE_URL", DEFAULT_BASE_URL)

    try:
        from openai import OpenAI
    except ImportError:
        print("错误：缺少 openai 库。请运行：pip install openai", file=sys.stderr)
        sys.exit(1)

    client = OpenAI(api_key=api_key, base_url=base_url)
    print(f"  模型：{model}", file=sys.stderr)

    # 读取参考图 → base64
    image_refs: list[str] = []
    if ref_images:
        for ref_path in ref_images:
            if ref_path.exists():
                data = ref_path.read_bytes()
                b64 = __import__("base64").b64encode(data).decode()
                image_refs.append(f"data:image/png;base64,{b64}")
                print(f"  参考图：{ref_path.name}", file=sys.stderr)

    # 构建 prompt：resource map + shot prompt
    resource_map = ""
    if image_refs:
        resource_map = "[Reference images attached. Maintain character/scene consistency with reference.]\n"

    full_prompt = resource_map + prompt

    # Seedream img2img
    size_map = {
        "16:9": "2K",
        "9:16": "2K",
        "1:1": "1K",
    }
    size = size_map.get(aspect_ratio, "2K")

    try:
        if image_refs:
            # 多参考图：使用 first_image + extra_images
            response = client.images.generate(
                model=model,
                prompt=full_prompt,
                size=size,
                extra_body={
                    "watermark": False,
                    "first_image": image_refs[0],
                    "extra_images": image_refs[1:],
                },
            )
        else:
            response = client.images.generate(
                model=model,
                prompt=full_prompt,
                size=size,
                extra_body={"watermark": False},
            )

        image_url = response.data[0].url
        print(f"  图片URL：{image_url}", file=sys.stderr)
        download_file(image_url, output_path)

    except Exception as e:
        print(f"  图片生成失败：{e}", file=sys.stderr)
        sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────────
# 测试模式
# ─────────────────────────────────────────────────────────────────────────────

def test_connection():
    print("=" * 60)
    print("huage888 Doubao API 连接测试")
    print("=" * 60)

    api_key = get_env("ARK_API_KEY")
    base_url = get_env("ARK_BASE_URL", DEFAULT_BASE_URL)

    print(f"Base URL：{base_url}")
    print(f"API Key：{api_key[:8]}...（已隐藏）")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    # 测试内容生成 API
    test_url = f"{base_url}/content_generation/tasks"
    payload = {
        "model": VIDEO_MODEL,
        "content": [{"type": "text", "text": "测试 prompt --wm true --dur 5"}],
    }

    try:
        result = http_post(test_url, headers, payload)
        if "id" in result:
            print(f"\n状态：✅ 连接成功")
            print(f"测试任务ID：{result['id']}")
            print(f"（任务已创建，可在控制台查看）")
        else:
            print(f"\n状态：⚠️ 响应异常：{result}")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"\n状态：❌ 连接失败")
        print(f"错误：{e}")
        return False


# ─────────────────────────────────────────────────────────────────────────────
# 批量处理
# ─────────────────────────────────────────────────────────────────────────────

def batch_from_shots(
    shots_file: Path,
    output_dir: Path,
    prompt_column: str = "libtvPrompt",
    duration: int = DEFAULT_DURATION,
    watermark: bool = True,
    emitter=None,
    task_name_prefix: str = "doubao-shot",
) -> None:
    """
    从分镜脚本批量生成视频。

    解析 shots_file 中的每个镜头，
    提取 libtvPrompt 列作为视频 Prompt，
    生成对应视频片段。

    shots_file 格式：Markdown 表格
    """
    if not shots_file.exists():
        print(f"错误：分镜文件不存在：{shots_file}", file=sys.stderr)
        sys.exit(1)

    content = shots_file.read_text(encoding="utf-8")

    # 简单解析 Markdown 表格
    lines = content.split("\n")
    shots = []
    for line in lines:
        # 找到 | 开头和结尾的行（排除标题分隔行）
        if line.startswith("|") and line.endswith("|") and not set(line[1:-1]).issubset({" ", "-", ":"}):
            # 跳过 markdown 表格分隔行（如 |---|---|）
            stripped = line.strip("| ")
            if all(c in "- |:" for c in stripped):
                continue
            # 提取 libtvPrompt 列（简化：找包含 prompt 的行）
            # 实际应用中应解析完整表格
            shots.append(line)

    print(f"  找到 {len(shots)} 个镜头", file=sys.stderr)
    output_dir.mkdir(parents=True, exist_ok=True)

    for i, shot_line in enumerate(shots):
        # 简化处理：每行作为 prompt 生成视频
        # 实际应解析 markdown 表格提取各列
        prompt = shot_line.strip("|").split("|")[-1].strip()
        if not prompt:
            continue

        output_path = output_dir / f"shot_{i+1:03d}.mp4"
        print(f"\n[镜头 {i+1:03d}] → {output_path.name}", file=sys.stderr)

        try:
            create_and_wait_video(
                prompt=prompt,
                output_path=output_path,
                duration=duration,
                watermark=watermark,
                emitter=emitter,
                task_name=f"{task_name_prefix}-{i+1:03d}",
            )
        except SystemExit:
            print(f"  跳过（出错）", file=sys.stderr)
            continue

    print(f"\n✅ 批量生成完成：{output_dir}", file=sys.stderr)


# ─────────────────────────────────────────────────────────────────────────────
# 参数解析
# ─────────────────────────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(
        description="Doubao API 调用脚本（huage888 视频/图片生成）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("--test", action="store_true",
                        help="测试 API 连接")

    mode = parser.add_argument_group("模式（互斥，必须选一个）")
    mode_group = mode.add_mutually_exclusive_group(required=True)
    mode_group.add_argument("--video", action="store_true",
                             help="视频生成（文生视频 / 图生视频 / 首尾帧）")
    mode_group.add_argument("--image", action="store_true",
                             help="图片生成")
    mode_group.add_argument("--batch", action="store_true",
                             help="批量视频（从分镜脚本）")

    parser.add_argument("--prompt", "-p",
                        help="视频/图片 Prompt")
    parser.add_argument("--model", "-m", default=VIDEO_MODEL,
                        help=f"模型 ID，默认 {VIDEO_MODEL}")
    parser.add_argument("--duration", "-d", type=int, default=DEFAULT_DURATION,
                        help=f"视频时长（秒），默认 {DEFAULT_DURATION}")
    parser.add_argument("--watermark", action="store_true", default=True,
                        help="添加水印（默认 True，加 --no-watermark 取消）")
    parser.add_argument("--no-watermark", action="store_true",
                        help="无水印（商业必须）")

    parser.add_argument("--img1",
                        help="首帧参考图 URL（首尾帧视频）")
    parser.add_argument("--img2",
                        help="尾帧参考图 URL（首尾帧视频）")

    parser.add_argument("--shots-file",
                        help="分镜脚本路径（批量模式）")
    parser.add_argument("--shots-column", default="libtvPrompt",
                        help="分镜脚本中 Prompt 列名，默认 libtvPrompt")
    parser.add_argument("--output-dir",
                        help="批量输出目录")

    parser.add_argument("--output", "-o",
                        help="单条输出文件路径")

    parser.add_argument(
        "--img-ref",
        action="append",
        dest="img_refs",
        default=[],
        help="参考图路径（可多次指定，用于 img2img）"
    )
    parser.add_argument(
        "--aspect-ratio",
        default="16:9",
        choices=["16:9", "9:16", "1:1"],
        help="图片宽高比"
    )

    # ── 追踪参数 ──────────────────────────────────────────────────
    tracking = parser.add_argument_group("追踪参数（可选）")
    tracking.add_argument("--track", action="store_true", default=False,
                          help="开启任务追踪（状态持久化 + 事件推送）")
    tracking.add_argument("--no-track", action="store_true", default=False,
                          help="禁用任务追踪")
    tracking.add_argument("--log-file",
                          default=None,
                          help="事件日志文件路径")
    tracking.add_argument("--no-emit", action="store_true", default=False,
                          help="禁用控制台事件输出")
    tracking.add_argument("--tasks-dir",
                          default=None,
                          help="任务状态持久化目录")
    # ── Webhook 参数 ───────────────────────────────────────────────
    webhook = parser.add_argument_group("Webhook 参数（可选）")
    webhook.add_argument("--webhook-url",
                          default=None,
                          help="任务完成时发送通知的 Webhook URL")
    webhook.add_argument("--webhook-secret",
                          default=None,
                          help="Webhook HMAC 签名密钥")

    return parser.parse_args()


# ─────────────────────────────────────────────────────────────────────────────
# 主函数
# ─────────────────────────────────────────────────────────────────────────────

def main():
    args = parse_args()

    # 测试模式
    if args.test:
        ok = test_connection()
        sys.exit(0 if ok else 1)

    # ── 追踪初始化 ─────────────────────────────────────────────────
    do_track = args.track and not args.no_track
    emit_console = not args.no_emit

    emitter = None
    task_manager = None
    task_id = None
    task_name = "doubao-video"

    if do_track:
        log_file = args.log_file or str(BASE_DIR / ".huage888" / "events.jsonl")
        emitter = _lazy_event_emitter(log_file=log_file, emit_console=emit_console)

        if emit_console:
            TaskManager, TaskState, _ = _lazy_task_state()
            tasks_dir = args.tasks_dir or str(BASE_DIR / ".huage888" / "tasks")
            task_manager = TaskManager(tasks_dir=tasks_dir)
            task_id = task_manager.create(
                task_type="video",
                name=task_name,
                params={
                    "model": args.model,
                    "duration": args.duration,
                },
            )
            print(f"\n📊 任务追踪已开启（ID: {task_id}）", file=sys.stderr)

    # ── Webhook 初始化 ────────────────────────────────────────────
    webhook_notifier = None
    if args.webhook_url:
        WebhookNotifier = _lazy_webhook()
        webhook_notifier = WebhookNotifier(
            url=args.webhook_url,
            secret=args.webhook_secret or "",
        )
        print(f"\n🔔 Webhook 已配置：{args.webhook_url[:50]}...", file=sys.stderr)

    # ── 追踪：发射 task_start ─────────────────────────────────────
    if emitter and task_id:
        emitter.emit_task_start(task_name, params={"model": args.model})
        TaskState, _, _ = _lazy_task_state()
        task_manager.update(task_id, TaskState.RUNNING)

    start_time = time.time()

    # ── 批量模式 ───────────────────────────────────────────────────
    if args.batch:
        if not args.shots_file:
            print("错误：批量模式需要 --shots-file", file=sys.stderr)
            sys.exit(1)
        output_dir = Path(args.output_dir) if args.output_dir else BASE_DIR / "outputs" / "videos"
        batch_from_shots(
            shots_file=Path(args.shots_file),
            output_dir=output_dir,
            prompt_column=args.shots_column,
            duration=args.duration,
            watermark=not args.no_watermark,
            emitter=emitter,
            task_name_prefix="doubao-batch",
        )
        return

    # 单条模式：必须有 prompt 和 output
    if not args.prompt:
        print("错误：请提供 --prompt", file=sys.stderr)
        sys.exit(1)

    if not args.output:
        print("错误：请提供 --output", file=sys.stderr)
        sys.exit(1)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    watermark = not args.no_watermark

    if args.image:
        print(f"\n🎬 生成图片", file=sys.stderr)
        print(f"  Prompt：{args.prompt[:80]}...", file=sys.stderr)
        ref_paths = [Path(p) for p in args.img_refs] if args.img_refs else None
        if ref_paths:
            create_and_wait_image_with_ref(
                prompt=args.prompt,
                output_path=output_path,
                ref_images=ref_paths,
                model=args.model or IMAGE_MODEL,
                aspect_ratio=args.aspect_ratio,
            )
        else:
            create_and_wait_image(
                prompt=args.prompt,
                output_path=output_path,
                model=args.model,
            )
        elapsed = time.time() - start_time
        print(f"\n✅ 已保存：{args.output}", file=sys.stderr)

        # ── 追踪结束 + Webhook ───────────────────────────────────────
        if emitter and task_id:
            emitter.emit_task_end(
                task_id, task_name,
                result={"output": str(args.output)},
                elapsed=elapsed,
                result_preview=f"{elapsed:.1f}s",
            )
            TaskState, _, _ = _lazy_task_state()
            task_manager.update(
                task_id, TaskState.SUCCESS,
                result={"output": str(args.output)},
            )
        if webhook_notifier:
            webhook_notifier.notify_task_complete(
                task_id=task_id or "unknown",
                task_name=task_name,
                result={"output": str(args.output)},
                elapsed=elapsed,
            )

    else:
        print(f"\n🎬 生成视频", file=sys.stderr)
        print(f"  Prompt：{args.prompt[:80]}...", file=sys.stderr)
        create_and_wait_video(
            prompt=args.prompt,
            output_path=output_path,
            img1=args.img1,
            img2=args.img2,
            duration=args.duration,
            watermark=watermark,
            model=args.model,
            emitter=emitter,
            task_id=task_id,
            task_name=task_name,
        )
        elapsed = time.time() - start_time
        print(f"\n✅ 已保存：{args.output}", file=sys.stderr)

        # ── 追踪结束 + Webhook ───────────────────────────────────────
        if emitter and task_id:
            emitter.emit_task_end(
                task_id, task_name,
                result={"output": str(args.output)},
                elapsed=elapsed,
                result_preview=f"{elapsed:.1f}s",
            )
            TaskState, _, _ = _lazy_task_state()
            task_manager.update(
                task_id, TaskState.SUCCESS,
                result={"output": str(args.output)},
            )
        if webhook_notifier:
            webhook_notifier.notify_task_complete(
                task_id=task_id or "unknown",
                task_name=task_name,
                result={"output": str(args.output)},
                elapsed=elapsed,
            )


if __name__ == "__main__":
    main()
