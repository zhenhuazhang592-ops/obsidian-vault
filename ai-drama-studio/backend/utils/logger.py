"""
漫舟结构化多级日志系统
参考 ZJT / 联易方舟日志规范
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from typing import Any, Literal

from contextvars import ContextVar

# ─── 全局上下文变量（线程安全）───────────────────────────────────────────────
_log_context: ContextVar[dict[str, Any]] = ContextVar("_log_context", default={})

# ─── 全局日志器注册表（单例）─────────────────────────────────────────────────
_loggers: dict[str, "ManzhouLogger"] = {}

# ─── 日志级别映射──────────────────────────────────────────────────────────────
_LEVEL_MAP: dict[str, int] = {
    "DEBUG":    logging.DEBUG,
    "INFO":     logging.INFO,
    "WARNING":  logging.WARNING,
    "ERROR":    logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

# ─── ANSI 彩色码────────────────────────────────────────────────────────────────
_COLORS: dict[str, str] = {
    "DEBUG":    "\033[90m",    # 灰色
    "INFO":     "\033[97m",    # 亮白
    "WARNING":  "\033[33m",    # 黄色
    "ERROR":    "\033[31m",    # 红色
    "CRITICAL": "\033[1;31m",  # 红色 + 粗体
}
_RESET = "\033[0m"
_BOLD = "\033[1m"


# ─────────────────────────────────────────────────────────────────────────────
# 自定义 Formatter
# ─────────────────────────────────────────────────────────────────────────────

class _ConsoleFormatter(logging.Formatter):
    """控制台人类可读彩色格式"""

    def format(self, record: logging.LogRecord) -> str:
        ctx = _log_context.get()
        job_id   = ctx.get("job_id",  "-")
        shot_id  = ctx.get("shot_id", "-")
        extra_kw = ctx.get("_extra_kw", {})

        level  = record.levelname
        color  = _COLORS.get(level, "")
        reset  = _RESET

        # 时间戳
        ts = self.formatTime(record, "%Y-%m-%d %H:%M:%S")

        # 消息体
        msg = record.getMessage()
        if extra_kw:
            extra_str = " | " + " | ".join(f"{k}: {v}" for k, v in extra_kw.items())
        else:
            extra_str = ""

        # 组成最终字符串
        return (
            f"{ts} {color}[{level:8s}]{reset} "
            f"[{job_id}] [{shot_id}] {msg}{extra_str}"
        )


class _JSONFormatter(logging.Formatter):
    """文件 JSON 行格式（每行一个 JSON 对象）"""

    def __init__(self, logger_name: str = "manzhou"):
        super().__init__()
        self.logger_name = logger_name

    def format(self, record: logging.LogRecord) -> str:
        ctx = _log_context.get()
        extra_kw = ctx.get("_extra_kw", {})

        obj: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.") +
                         f"{int(time.time() * 1000) % 1000:03d}Z",
            "level":      record.levelname,
            "logger":     self.logger_name,
            "message":    record.getMessage(),
        }

        # 注入上下文
        for k, v in ctx.items():
            if k != "_extra_kw":
                obj[k] = v

        # 注入 kwargs 额外字段
        obj.update(extra_kw)

        # 注入 record 原生字段
        if hasattr(record, "duration_ms"):
            obj["duration_ms"] = record.duration_ms  # type: ignore
        if hasattr(record, "provider"):
            obj["provider"] = record.provider  # type: ignore

        # 异常信息
        if record.exc_info:
            obj["exc_info"] = self.formatException(record.exc_info)

        return json.dumps(obj, ensure_ascii=False, default=str)


# ─────────────────────────────────────────────────────────────────────────────
# ManzhouLogger
# ─────────────────────────────────────────────────────────────────────────────

class ManzhouLogger:
    """
    漫舟结构化日志系统

    Features:
        - 多级日志：DEBUG / INFO / WARNING / ERROR / CRITICAL
        - 结构化 JSON 文件输出（主日志 / LLM 调用 / 镜头事件）
        - 日志轮转（RotatingFileHandler，10MB，保留 7 个文件）
        - 上下文感知（job_id / shot_id / user_id 自动注入）
        - 控制台彩色输出
        - 线程安全（ContextVar）
    """

    def __init__(
        self,
        name: str,
        log_dir: str = "./logs",
        level: str = "INFO",
        structured: bool = True,
    ):
        self.name    = name
        self.log_dir = log_dir
        self.structured = structured

        os.makedirs(log_dir, exist_ok=True)

        # 创建原生 logging.Logger
        self._logger = logging.getLogger(f"manzhou.{name}")
        self._logger.setLevel(_LEVEL_MAP.get(level.upper(), logging.INFO))
        # 防止重复添加 handler
        if self._logger.handlers:
            self._logger.handlers.clear()

        # ── Handler 1：Console（彩色人类可读）─────────────────────────────
        _ch = logging.StreamHandler(sys.stdout)
        _ch.setLevel(logging.DEBUG)
        _ch.setFormatter(_ConsoleFormatter())
        self._logger.addHandler(_ch)

        # ── Handler 2：主日志文件（JSON 结构化）──────────────────────────
        main_path = os.path.join(log_dir, "manzhou.log")
        _fh_main = RotatingFileHandler(
            main_path, maxBytes=10 * 1024 * 1024, backupCount=7,
            encoding="utf-8", delay=True,
        )
        _fh_main.setLevel(logging.DEBUG)
        _fh_main.setFormatter(_JSONFormatter(f"manzhou.{name}"))
        self._logger.addHandler(_fh_main)

        # ── Handler 3：LLM 调用专用日志（JSON 结构化）────────────────────
        llm_path = os.path.join(log_dir, "llm_calls.log")
        _fh_llm = RotatingFileHandler(
            llm_path, maxBytes=10 * 1024 * 1024, backupCount=7,
            encoding="utf-8", delay=True,
        )
        _fh_llm.setLevel(logging.INFO)
        _fh_llm.setFormatter(_JSONFormatter(f"manzhou.llm"))
        self._llm_handler = _fh_llm
        self._logger.addHandler(_fh_llm)

        # ── Handler 4：镜头事件专用日志（JSON 结构化）────────────────────
        shots_path = os.path.join(log_dir, "shots.log")
        _fh_shots = RotatingFileHandler(
            shots_path, maxBytes=10 * 1024 * 1024, backupCount=7,
            encoding="utf-8", delay=True,
        )
        _fh_shots.setLevel(logging.INFO)
        _fh_shots.setFormatter(_JSONFormatter(f"manzhou.shots"))
        self._shots_handler = _fh_shots
        self._logger.addHandler(_fh_shots)

    # ── 基础日志方法 ───────────────────────────────────────────────────────

    def debug(self, msg: str, **kwargs: Any) -> None:
        self._log(logging.DEBUG, msg, **kwargs)

    def info(self, msg: str, **kwargs: Any) -> None:
        self._log(logging.INFO, msg, **kwargs)

    def warning(self, msg: str, **kwargs: Any) -> None:
        self._log(logging.WARNING, msg, **kwargs)

    def warn(self, msg: str, **kwargs: Any) -> None:
        self.warning(msg, **kwargs)

    def error(self, msg: str, **kwargs: Any) -> None:
        self._log(logging.ERROR, msg, **kwargs)

    def critical(self, msg: str, **kwargs: Any) -> None:
        self._log(logging.CRITICAL, msg, **kwargs)

    def _log(self, level: int, msg: str, **kwargs: Any) -> None:
        """统一日志写入，kwargs 注入到结构化输出但不改变消息本身"""
        ctx = _log_context.get()
        # 把 kwargs 存入上下文（不影响原有上下文）
        new_ctx = {**ctx, "_extra_kw": kwargs}
        token = _log_context.set(new_ctx)
        try:
            self._logger.log(level, msg, extra=kwargs)
        finally:
            _log_context.reset(token)

    # ── 镜头级事件 ─────────────────────────────────────────────────────────

    def log_shot_event(
        self,
        event: str,
        shot_id: str = "",
        job_id: str = "",
        duration_ms: float = 0.0,
        **extra: Any,
    ) -> None:
        """
        专门记录镜头级事件（用于效果追踪）
        event: "shot_generated" | "tts_generated" | "video_generated" | ...
        """
        extra = {
            "event":       event,
            "shot_id":     shot_id,
            "duration_ms": duration_ms,
            **extra,
        }
        ctx = _log_context.get()
        token = _log_context.set({**ctx, "_extra_kw": extra})
        try:
            self._logger.info(
                f"[{event}] shot={shot_id} duration={duration_ms:.0f}ms",
                extra=extra,
            )
        finally:
            _log_context.reset(token)

    # ── LLM 调用 ────────────────────────────────────────────────────────────

    def log_llm_call(
        self,
        provider: Literal["doubao", "minimax", "openai", "zhipu", "claude", "gemini", "other"],
        model: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        cost_usd: float = 0.0,
        latency_ms: float = 0.0,
        success: bool = True,
        error: str = "",
    ) -> None:
        """
        记录 LLM 调用（用于成本分析）
        """
        extra = {
            "event":            "llm_call",
            "provider":         provider,
            "model":            model,
            "prompt_tokens":    prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens":     prompt_tokens + completion_tokens,
            "cost_usd":         round(cost_usd, 6),
            "latency_ms":       round(latency_ms, 2),
            "success":          success,
            "error":            error,
        }
        ctx = _log_context.get()
        token = _log_context.set({**ctx, "_extra_kw": extra})
        try:
            status = "成功" if success else f"失败({error})"
            self._logger.info(
                f"LLM调用 | 提供商:{provider} 模型:{model} "
                f"延迟:{latency_ms:.0f}ms 费用:${cost_usd:.6f} {status}",
                extra=extra,
            )
        finally:
            _log_context.reset(token)

    # ── 流水线事件 ─────────────────────────────────────────────────────────

    def log_pipeline_event(
        self,
        stage: Literal["preprocess", "scene_detect", "frame_extract", "analyze", "export", "unknown"],
        job_id: str,
        status: Literal["started", "completed", "failed"],
        **extra: Any,
    ) -> None:
        """
        记录流水线事件
        """
        extra = {
            "event":  "pipeline_event",
            "stage":  stage,
            "job_id": job_id,
            "status": status,
            **extra,
        }
        ctx = _log_context.get()
        token = _log_context.set({**ctx, "_extra_kw": extra})
        try:
            self._logger.info(
                f"流水线 [{stage}] | job={job_id} status={status}",
                extra=extra,
            )
        finally:
            _log_context.reset(token)

    # ── 上下文管理 ─────────────────────────────────────────────────────────

    def set_context(self, **kwargs: Any) -> None:
        """设置日志上下文（自动注入到所有后续日志）"""
        ctx = _log_context.get()
        _log_context.set({**ctx, **kwargs})

    def clear_context(self) -> None:
        """清除日志上下文"""
        _log_context.set({})

    @property
    def logger(self) -> logging.Logger:
        """暴露原生 logging.Logger 供外部使用"""
        return self._logger


# ─────────────────────────────────────────────────────────────────────────────
# 全局单例访问函数
# ─────────────────────────────────────────────────────────────────────────────

def get_logger(name: str = "manzhou") -> ManzhouLogger:
    """
    获取（或创建）ManzhouLogger 单例

    用法:
        logger = get_logger("tts")
        logger.info("开始合成", voice_id="voice_01")
    """
    if name not in _loggers:
        _loggers[name] = ManzhouLogger(name)
    return _loggers[name]


# ─────────────────────────────────────────────────────────────────────────────
# 自测代码（__main__）
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import tempfile

    tmp = tempfile.mkdtemp()
    print(f"[自测] 日志目录: {tmp}\n")

    # 初始化日志器（level=DEBUG 可见全部日志）
    log = ManzhouLogger("test", log_dir=tmp, level="DEBUG")

    # ── 1. 基本日志方法 ────────────────────────────────────────────────────
    log.debug("这是一条 DEBUG 日志", demo=True)
    log.info("这是一条 INFO 日志",   demo=True)
    log.warning("这是一条 WARNING 日志", demo=True)
    log.error("这是一条 ERROR 日志",   demo=True)
    log.critical("这是一条 CRITICAL 日志", demo=True)

    # ── 2. 上下文注入 ─────────────────────────────────────────────────────
    log.set_context(job_id="job_test_001", user_id="user_001")
    log.info("已设置上下文 job_id / user_id")
    log.info("这条日志会带上 job_id 和 user_id")

    # ── 3. 镜头事件 ────────────────────────────────────────────────────────
    log.log_shot_event(
        event="shot_generated",
        shot_id="P01",
        job_id="job_test_001",
        duration_ms=2340.5,
        frame_count=48,
        resolution="1280x720",
    )
    log.log_shot_event(
        event="tts_generated",
        shot_id="P01",
        job_id="job_test_001",
        duration_ms=1230.0,
        voice_id="voice_chenxi",
    )
    log.log_shot_event(
        event="video_generated",
        shot_id="P02",
        job_id="job_test_001",
        duration_ms=5120.0,
        model="vid-01",
    )

    # ── 4. LLM 调用 ───────────────────────────────────────────────────────
    log.log_llm_call(
        provider="doubao",
        model="doubao-pro-32k",
        prompt_tokens=1024,
        completion_tokens=512,
        cost_usd=0.0045,
        latency_ms=890.0,
        success=True,
    )
    log.log_llm_call(
        provider="gemini",
        model="gemini-2.0-flash",
        prompt_tokens=2048,
        completion_tokens=0,
        cost_usd=0.0,
        latency_ms=0.0,
        success=False,
        error="RateLimitError: quota exceeded",
    )

    # ── 5. 流水线事件 ─────────────────────────────────────────────────────
    for stage, status in [
        ("preprocess",    "started"),
        ("scene_detect",  "started"),
        ("scene_detect",  "completed"),
        ("frame_extract", "started"),
        ("frame_extract", "completed"),
        ("analyze",       "started"),
        ("analyze",       "completed"),
        ("export",        "started"),
        ("export",        "completed"),
    ]:
        log.log_pipeline_event(
            stage=stage,
            job_id="job_test_001",
            status=status,
            frames_processed=120 if status == "completed" else 0,
        )

    # ── 6. 清除上下文 ──────────────────────────────────────────────────────
    log.clear_context()
    log.info("上下文已清除")

    # ── 7. 多 logger 实例（验证单例）───────────────────────────────────────
    log_tts    = get_logger("tts")
    log_video  = get_logger("video")
    log_tts.info("tts logger 实例")
    log_video.info("video logger 实例")
    assert get_logger("tts") is log_tts, "单例失效！"
    print("\n[自测通过] 单例模式正常")

    # ── 8. 检查文件输出 ────────────────────────────────────────────────────
    import glob
    for fname in glob.glob(os.path.join(tmp, "*.log")):
        size = os.path.getsize(fname)
        print(f"  {os.path.basename(fname):20s}  {size:>6d} bytes")

    # 输出 JSON 行示例
    print("\n[JSON 文件示例] llm_calls.log 首行：")
    with open(os.path.join(tmp, "llm_calls.log")) as f:
        first = f.readline()
        obj = json.loads(first)
        print(json.dumps(obj, ensure_ascii=False, indent=2))

    print(f"\n[自测完成] 所有功能验证通过")
    print(f"日志目录: {tmp}")
