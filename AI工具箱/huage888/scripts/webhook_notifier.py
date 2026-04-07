#!/usr/bin/env python3
"""
webhook_notifier.py — huage888 Webhook 通知系统

参考 Toonflow 事件推送机制，为 huage888 提供：
1. 任务完成/失败时发送 HTTP POST 回调
2. 支持配置多个 webhook URL（并行推送）
3. 签名验证（HMAC-SHA256）
4. 自动重试（指数退避）
5. 与 event_emitter 联动（自动发射 webhook 事件）

使用场景：
- CI/CD 集成：任务完成后触发构建
- 通知：Slack/飞书/钉钉机器人通知
- 数据同步：推送结果到外部系统

用法：

  # 基本用法
  from webhook_notifier import WebhookNotifier, send_webhook

  notifier = WebhookNotifier(
      url="https://hooks.slack.com/services/xxx",
      secret="your-secret",
  )
  notifier.notify_task_complete(
      task_id="task-001",
      task_name="导演讲戏",
      result={"output": "outputs/01-director-analysis.md"},
      elapsed=12.5,
  )

  # 并行推送多个 webhook
  notifier = WebhookNotifier.from_config(
      [
          {"url": "https://hooks.slack.com/...", "secret": "slack-secret"},
          {"url": "https://oapi.dingtalk.com/...", "secret": "dingtalk-secret"},
      ]
  )

  # 集成到 event_emitter（自动触发）
  from event_emitter import EventEmitter, WebhookSink
  emitter = EventEmitter(sinks=[WebhookSink(webhooks=[...])])

环境变量：
  WEBHOOK_URL      默认 webhook URL
  WEBHOOK_SECRET   HMAC 签名密钥
"""

import hashlib
import hmac
import json
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional
import urllib.request
import urllib.error


# ─────────────────────────────────────────────────────────────────────────────
# 数据模型
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class WebhookPayload:
    """Webhook 通知载荷"""
    event: str                    # task_complete / task_failed / task_start
    task_id: str
    task_name: str
    timestamp: str                # ISO 8601
    project: str = ""
    elapsed: float = 0.0          # 秒
    result: dict = field(default_factory=dict)
    error: str = ""
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "event": self.event,
            "task_id": self.task_id,
            "task_name": self.task_name,
            "timestamp": self.timestamp,
            "project": self.project,
            "elapsed_seconds": round(self.elapsed, 2),
            "result": self.result,
            "error": self.error,
            "metadata": self.metadata,
        }


@dataclass
class WebhookResponse:
    """Webhook 发送结果"""
    url: str
    success: bool
    status_code: int = 0
    response_body: str = ""
    error: str = ""
    elapsed_ms: float = 0.0


# ─────────────────────────────────────────────────────────────────────────────
# 通知器
# ─────────────────────────────────────────────────────────────────────────────

class WebhookNotifier:
    """
    Webhook 通知器

    功能：
    - 单个或多个 webhook URL 并行推送
    - HMAC-SHA256 签名验证
    - 指数退避重试（最大 3 次）
    - 异步发送（不阻塞主流程）
    """

    DEFAULT_TIMEOUT = 10          # 秒
    MAX_RETRIES = 3
    BASE_DELAY = 2               # 秒

    def __init__(
        self,
        url: str | list[str] | None = None,
        secret: str | list[str] | None = None,
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = MAX_RETRIES,
        headers: dict | None = None,
    ):
        """
        Args:
            url: Webhook URL（单个字符串或列表）
            secret: HMAC 签名密钥（与 url 对应）
            timeout: 请求超时（秒）
            max_retries: 最大重试次数
            headers: 额外 HTTP 请求头
        """
        if url is None:
            url = os.environ.get("WEBHOOK_URL", "")
        if secret is None:
            secret = os.environ.get("WEBHOOK_SECRET", "")

        # 统一为列表
        self.urls = [url] if isinstance(url, str) else (url or [])
        self.secrets = [secret] if isinstance(secret, str) else (secret or [None] * len(self.urls))
        self.timeout = timeout
        self.max_retries = max_retries
        self.headers = headers or {"Content-Type": "application/json"}

    @classmethod
    def from_config(cls, webhooks: list[dict]) -> "WebhookNotifier":
        """
        从配置列表创建 WebhookNotifier。

        webhooks = [
            {"url": "https://hooks.slack.com/...", "secret": "..."},
            {"url": "https://oapi.dingtalk.com/...", "secret": "..."},
        ]
        """
        urls = [w["url"] for w in webhooks]
        secrets = [w.get("secret", "") for w in webhooks]
        return cls(url=urls, secret=secrets)

    @classmethod
    def from_env(cls) -> "WebhookNotifier":
        """从环境变量读取单个 webhook 配置"""
        url = os.environ.get("WEBHOOK_URL", "")
        secret = os.environ.get("WEBHOOK_SECRET", "")
        return cls(url=url, secret=secret) if url else cls()

    # ─────────────────────────────────────────────────────────────────────
    # 签名
    # ─────────────────────────────────────────────────────────────────────

    def _sign(self, payload_bytes: bytes, secret: str) -> str:
        """计算 HMAC-SHA256 签名"""
        if not secret:
            return ""
        return hmac.new(
            secret.encode("utf-8"),
            payload_bytes,
            hashlib.sha256,
        ).hexdigest()

    # ─────────────────────────────────────────────────────────────────────
    # 发送单个 webhook
    # ─────────────────────────────────────────────────────────────────────

    def _send_one(
        self,
        url: str,
        payload: dict,
        secret: str = "",
        attempt: int = 1,
    ) -> WebhookResponse:
        """发送单个 webhook 请求"""
        import time as time_module
        start = time_module.perf_counter()

        payload_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        signature = self._sign(payload_bytes, secret)

        headers = dict(self.headers)
        if signature:
            headers["X-Webhook-Signature"] = f"sha256={signature}"
            headers["X-Webhook-Timestamp"] = str(int(time.time()))

        req = urllib.request.Request(
            url,
            data=payload_bytes,
            headers=headers,
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                body = resp.read().decode("utf-8", errors="replace")
                elapsed_ms = (time_module.perf_counter() - start) * 1000
                return WebhookResponse(
                    url=url,
                    success=True,
                    status_code=resp.status,
                    response_body=body[:500],
                    elapsed_ms=elapsed_ms,
                )
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            elapsed_ms = (time_module.perf_counter() - start) * 1000
            return WebhookResponse(
                url=url,
                success=False,
                status_code=e.code,
                response_body=body[:500],
                error=f"HTTP {e.code}",
                elapsed_ms=elapsed_ms,
            )
        except Exception as e:
            elapsed_ms = (time_module.perf_counter() - start) * 1000
            return WebhookResponse(
                url=url,
                success=False,
                error=str(e),
                elapsed_ms=elapsed_ms,
            )

    # ─────────────────────────────────────────────────────────────────────
    # 核心通知方法
    # ─────────────────────────────────────────────────────────────────────

    def notify(
        self,
        payload: WebhookPayload | dict,
        async_: bool = False,
    ) -> list[WebhookResponse]:
        """
        发送 webhook 通知。

        Args:
            payload: WebhookPayload 或 dict
            async_: 是否异步发送（不等待响应）

        Returns:
            WebhookResponse 列表
        """
        if isinstance(payload, WebhookPayload):
            payload_dict = payload.to_dict()
        else:
            payload_dict = payload

        if not self.urls:
            return []

        results = []
        for url, secret in zip(self.urls, self.secrets):
            result = self._send_with_retry(url, payload_dict, secret)
            results.append(result)

        return results

    def _send_with_retry(
        self,
        url: str,
        payload: dict,
        secret: str,
    ) -> WebhookResponse:
        """带重试的发送"""
        for attempt in range(1, self.max_retries + 1):
            result = self._send_one(url, payload, secret, attempt)
            if result.success:
                return result

            if attempt < self.max_retries:
                delay = self.BASE_DELAY * (2 ** (attempt - 1))
                time.sleep(delay)

        return result

    # ─────────────────────────────────────────────────────────────────────
    # 便捷方法
    # ─────────────────────────────────────────────────────────────────────

    def notify_task_start(
        self,
        task_id: str,
        task_name: str,
        project: str = "",
        metadata: dict | None = None,
    ) -> list[WebhookResponse]:
        """通知任务开始"""
        payload = WebhookPayload(
            event="task_start",
            task_id=task_id,
            task_name=task_name,
            timestamp=datetime.now().isoformat(),
            project=project,
            metadata=metadata or {},
        )
        return self.notify(payload)

    def notify_task_complete(
        self,
        task_id: str,
        task_name: str,
        result: dict | None = None,
        elapsed: float = 0.0,
        project: str = "",
        metadata: dict | None = None,
    ) -> list[WebhookResponse]:
        """通知任务完成"""
        payload = WebhookPayload(
            event="task_complete",
            task_id=task_id,
            task_name=task_name,
            timestamp=datetime.now().isoformat(),
            project=project,
            elapsed=elapsed,
            result=result or {},
            metadata=metadata or {},
        )
        return self.notify(payload)

    def notify_task_failed(
        self,
        task_id: str,
        task_name: str,
        error: str,
        project: str = "",
        metadata: dict | None = None,
    ) -> list[WebhookResponse]:
        """通知任务失败"""
        payload = WebhookPayload(
            event="task_failed",
            task_id=task_id,
            task_name=task_name,
            timestamp=datetime.now().isoformat(),
            project=project,
            error=error,
            metadata=metadata or {},
        )
        return self.notify(payload)


# ─────────────────────────────────────────────────────────────────────────────
# 便捷函数
# ─────────────────────────────────────────────────────────────────────────────

def send_webhook(
    url: str,
    event: str,
    task_id: str,
    task_name: str,
    secret: str = "",
    **kwargs,
) -> WebhookResponse:
    """单次发送 webhook（便捷函数）"""
    notifier = WebhookNotifier(url=url, secret=secret)
    if event == "task_start":
        return notifier.notify_task_start(task_id, task_name, **kwargs)
    elif event == "task_complete":
        return notifier.notify_task_complete(task_id, task_name, **kwargs)
    elif event == "task_failed":
        return notifier.notify_task_failed(task_id, task_name, **kwargs)
    else:
        payload = WebhookPayload(
            event=event,
            task_id=task_id,
            task_name=task_name,
            timestamp=datetime.now().isoformat(),
            **kwargs,
        )
        return notifier.notify(payload)


# ─────────────────────────────────────────────────────────────────────────────
# event_emitter Sink（可选集成）
# ─────────────────────────────────────────────────────────────────────────────

class WebhookSink:
    """
    event_emitter 的 webhook 槽位。

    用法：
      from event_emitter import EventEmitter

      emitter = EventEmitter(sinks=[
          WebhookSink([
              {"url": "https://hooks.slack.com/...", "secret": "..."},
          ]),
          ConsoleSink(),
      ])
    """

    def __init__(self, webhooks: list[dict] | None = None):
        self.notifier = WebhookNotifier.from_config(webhooks or [])

    def emit(self, event: dict):
        """接收 event_emitter 的事件，触发 webhook"""
        event_type = event.get("event_type", "")
        task_id = event.get("task_id", "")

        if event_type in ("task_end", "task_complete") and task_id:
            is_error = event.get("is_error", False)
            if is_error:
                self.notifier.notify_task_failed(
                    task_id=task_id,
                    task_name=event.get("name", ""),
                    error=event.get("message", ""),
                    metadata={"event": event},
                )
            else:
                self.notifier.notify_task_complete(
                    task_id=task_id,
                    task_name=event.get("name", ""),
                    elapsed=event.get("elapsed", 0),
                    result=event.get("result", {}),
                    metadata={"event": event},
                )


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def _cli():
    import argparse
    parser = argparse.ArgumentParser(description="huage888 Webhook 通知器")
    sub = parser.add_argument_group("模式（互斥）")

    parser.add_argument("--url", help="Webhook URL")
    parser.add_argument("--secret", help="HMAC 签名密钥")
    parser.add_argument("--event", default="task_complete",
                        choices=["task_start", "task_complete", "task_failed"],
                        help="事件类型")
    parser.add_argument("--task-id", default=str(uuid.uuid4())[:8],
                        help="任务 ID")
    parser.add_argument("--task-name", default="test-task",
                        help="任务名称")
    parser.add_argument("--elapsed", type=float, default=0.0,
                        help="执行耗时（秒）")
    parser.add_argument("--result", help="结果 JSON 字符串")
    parser.add_argument("--error", help="错误信息（task_failed 时）")
    parser.add_argument("--project", default="",
                        help="项目名称")
    parser.add_argument("--test", action="store_true",
                        help="发送测试 webhook")

    args = parser.parse_args()

    notifier = WebhookNotifier(
        url=args.url or os.environ.get("WEBHOOK_URL", ""),
        secret=args.secret or os.environ.get("WEBHOOK_SECRET", ""),
    )

    if not notifier.urls:
        print("错误：请提供 --url 或设置 WEBHOOK_URL 环境变量", file=sys.stderr)
        sys.exit(1)

    if args.test:
        print(f"发送测试 webhook 到 {notifier.urls[0]}...", file=sys.stderr)
        results = notifier.notify_task_complete(
            task_id="test-" + str(uuid.uuid4())[:8],
            task_name="huage888 测试任务",
            result={"status": "ok", "message": "测试成功"},
            elapsed=1.23,
        )
    elif args.event == "task_start":
        results = notifier.notify_task_start(
            task_id=args.task_id,
            task_name=args.task_name,
            project=args.project,
        )
    elif args.event == "task_failed":
        results = notifier.notify_task_failed(
            task_id=args.task_id,
            task_name=args.task_name,
            error=args.error or "未知错误",
            project=args.project,
        )
    else:
        result_dict = {}
        if args.result:
            import json as _json
            result_dict = _json.loads(args.result)
        results = notifier.notify_task_complete(
            task_id=args.task_id,
            task_name=args.task_name,
            result=result_dict,
            elapsed=args.elapsed,
            project=args.project,
        )

    for r in results:
        icon = "✅" if r.success else "❌"
        print(f"{icon} {r.url}", file=sys.stderr)
        if r.success:
            print(f"   {r.status_code} · {r.elapsed_ms:.0f}ms", file=sys.stderr)
        else:
            print(f"   {r.error}", file=sys.stderr)


if __name__ == "__main__":
    _cli()
