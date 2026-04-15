"""
Dify Webhook 处理
处理 HITL 确认点回调
"""
import asyncio
import logging
import os
from typing import Literal, Optional
from dataclasses import dataclass
from fastapi import APIRouter, HTTPException, Header

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks/dify", tags=["dify"])


@dataclass
class HITLPayload:
    """HITL 回调载荷"""
    session_id: str
    conversation_id: str
    hitl_type: Literal["strategy", "outline", "final_preview"]
    user_response: str
    context: dict


@dataclass
class HITLResponse:
    """HITL 响应"""
    approved: bool
    updates: dict
    feedback: str


class HITLHandler:
    """
    HITL 处理器

    负责处理 Dify HITL 节点的回调，
    调用 pipeline.deliver_hitl_response() 更新状态
    """

    def __init__(self, pipeline=None):
        self.pipeline = pipeline

    def set_pipeline(self, pipeline):
        """设置 pipeline 实例"""
        self.pipeline = pipeline

    async def handle(
        self,
        hitl_type: Literal["strategy", "outline", "final_preview"],
        payload: dict,
    ) -> HITLResponse:
        """
        处理 HITL 回调

        Args:
            hitl_type: HITL 类型
            payload: 回调载荷

        Returns:
            处理结果
        """
        if not self.pipeline:
            raise RuntimeError("Pipeline not set")

        session_id = payload.get("session_id", "")
        user_response = payload.get("user_response", "")

        logger.info(f"[HITL] {hitl_type} callback: session={session_id}")

        try:
            # 调用 pipeline 的 HITL 响应处理
            context = await self.pipeline.deliver_hitl_response(
                confirm_type=hitl_type,
                human_response=user_response,
            )

            # 解析响应
            last_hitl = context.get("_hitl_last", {})
            approved = last_hitl.get("approved", False)
            feedback = last_hitl.get("feedback", "")

            return HITLResponse(
                approved=approved,
                updates=context,
                feedback=feedback,
            )

        except Exception as e:
            logger.exception(f"[HITL] Error handling {hitl_type}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    def build_confirm_card(self, hitl_type: str, context: dict) -> str:
        """
        构建确认卡片（用于 Dify HITL 节点）

        Args:
            hitl_type: HITL 类型
            context: 数据总线上下文

        Returns:
            确认卡片文本
        """
        if hitl_type == "strategy":
            return self._build_strategy_card(context)
        elif hitl_type == "outline":
            return self._build_outline_card(context)
        elif hitl_type == "final_preview":
            return self._build_final_card(context)
        else:
            return "未知确认类型"

    def _build_strategy_card(self, ctx: dict) -> str:
        return f"""📋 **创作策略确认**

**主题**：{ctx.get('topic', '')}
**发布平台**：{ctx.get('platform', '')}
**写作框架**：{ctx.get('framework', '')}
**排版主题**：{ctx.get('theme', '')}

确认开始创作？回复"开始"继续。"""

    def _build_outline_card(self, ctx: dict) -> str:
        outline = ctx.get("outline", {})
        sections = outline.get("sections", [])
        structure_text = "\n".join(
            f"- {s.get('title', '')}" for s in sections
        ) if sections else "（暂无大纲）"

        return f"""📝 **大纲确认**

**标题**：{outline.get('title', '（未选择）')}
**结构**：
{structure_text}

确认大纲？回复"确认"继续，或指出需要调整的地方。"""

    def _build_final_card(self, ctx: dict) -> str:
        quality_score = ctx.get("quality_score", 0)
        word_count = ctx.get("word_count", 0)
        image_count = len(ctx.get("inline_images", []))

        return f"""🎉 **创作完成！**

**质量评分**：{quality_score}/100
**字数**：约{word_count}字
**配图**：封面×1 + 内文×{image_count}张

已生成完整 HTML 版本，可直接复制到公众号编辑器。

是否需要调整任何内容？"""


# 全局 handler 实例
_handler: Optional[HITLHandler] = None


def get_handler() -> HITLHandler:
    """获取全局 handler"""
    global _handler
    if _handler is None:
        _handler = HITLHandler()
    return _handler


def set_pipeline(pipeline):
    """设置 pipeline 实例"""
    get_handler().set_pipeline(pipeline)


@router.post("/hitl")
async def handle_hitl_callback(
    payload: dict,
    authorization: str = Header(None),
):
    """
    Dify HITL 回调端点

    Dify 的 HITL 节点会在需要人工确认时调用此端点，
    我们返回确认卡片内容让 Dify 展示给用户
    """
    # Bearer token 验证
    expected = os.environ.get("DIFY_WEBHOOK_BEARER_TOKEN", "")
    if expected and authorization != f"Bearer {expected}":
        raise HTTPException(status_code=401, detail="Unauthorized")

    hitl_type = payload.get("hitl_type")
    session_id = payload.get("session_id")

    if not hitl_type:
        raise HTTPException(status_code=400, detail="hitl_type required")

    handler = get_handler()

    if payload.get("action") == "get_card":
        # 获取确认卡片
        context = payload.get("context", {})
        card = handler.build_confirm_card(hitl_type, context)
        return {"card": card}

    # 处理用户响应
    result = await handler.handle(hitl_type, payload)
    return {
        "approved": result.approved,
        "feedback": result.feedback,
        "context": result.updates,
    }


@router.get("/sessions/{session_id}/status")
async def get_session_status(session_id: str):
    """获取会话状态"""
    handler = get_handler()
    if handler.pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline not configured")
    status = await handler.pipeline.get_status(session_id)
    return status


@router.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "service": "dify-webhook"}
