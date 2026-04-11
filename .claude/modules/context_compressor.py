# .claude/modules/context_compressor.py
"""上下文自动压缩：head+tail 保护策略"""

import tiktoken
from dataclasses import dataclass
from typing import Callable

# 默认阈值：60K tokens
DEFAULT_THRESHOLD = 60_000
# 尾部保护 token 预算：20K
TAIL_TOKEN_BUDGET = 20_000


@dataclass
class CompressionResult:
    original_count: int
    compressed_count: int
    summary: str
    kept_messages: list[dict]


class ContextCompressor:
    def __init__(self, model: str = "cl100k_base", threshold: int = DEFAULT_THRESHOLD):
        self.encoding = tiktoken.get_encoding(model)
        self.threshold = threshold

    def should_compress(self, messages: list[dict]) -> bool:
        """判断是否需要压缩"""
        total = self._count_tokens(messages)
        return total > self.threshold

    def compress(self, messages: list[dict],
                 summarize_fn: Callable[[list[dict]], str]) -> CompressionResult:
        """
        head+tail 保护压缩策略。

        - 保护头部：system prompt + 第一轮交互（index 0 ~ 2）
        - 保护尾部：最近 20K tokens
        - 压缩中间：LLM 摘要

        Args:
            messages: 原始消息列表
            summarize_fn: 接收中间段消息列表，返回摘要字符串的函数（由调用方注入 LLM）

        Returns:
            CompressionResult with summary and new message list
        """
        total_tokens = self._count_tokens(messages)
        if total_tokens <= self.threshold:
            return CompressionResult(total_tokens, total_tokens, "", messages)

        # 1. 保护头部：system + first exchange (up to index 2)
        head_end = min(3, len(messages))
        head = messages[:head_end]
        head_tokens = self._count_tokens(head)

        # 2. 保护尾部：最近的 20K tokens
        tail = self._protect_tail(messages, TAIL_TOKEN_BUDGET)
        tail_tokens = self._count_tokens(tail)

        # 3. 中间部分
        middle = messages[head_end:-len(tail)] if len(tail) > 0 else messages[head_end:]

        # 4. 压缩中间（LLM 摘要）
        summary_tokens = 0
        if middle:
            summary = summarize_fn(middle)
            summary_tokens = len(self.encoding.encode(summary))
            middle_compressed = [{
                "role": "system",
                "content": f"[先前会话摘要] {summary}",
                "_is_summary": True
            }]
        else:
            summary = ""
            middle_compressed = []

        # 5. 估算压缩后总量
        compressed_tokens = head_tokens + summary_tokens + tail_tokens

        # 6. 如果仍然超限，进一步压缩尾部
        final_messages = head + middle_compressed + tail
        while self._count_tokens(final_messages) > self.threshold and len(tail) > 2:
            # 逐步减少尾部
            tail = tail[:-2]
            final_messages = head + middle_compressed + tail

        return CompressionResult(
            original_count=total_tokens,
            compressed_count=self._count_tokens(final_messages),
            summary=summary,
            kept_messages=final_messages
        )

    def _protect_tail(self, messages: list[dict], token_budget: int) -> list[dict]:
        """从尾部取消息，直到 token 预算用完"""
        result = []
        total = 0
        for msg in reversed(messages):
            msg_tokens = self._count_tokens([msg])
            if total + msg_tokens <= token_budget:
                result.insert(0, msg)
                total += msg_tokens
            else:
                break
        return result

    def _count_tokens(self, messages: list[dict]) -> int:
        """计算消息列表的 token 总数"""
        if not messages:
            return 0
        text = "\n".join(
            f"{m.get('role', '')}: {m.get('content', '')}"
            for m in messages
        )
        return len(self.encoding.encode(text))