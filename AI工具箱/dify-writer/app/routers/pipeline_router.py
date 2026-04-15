# Pipeline router — FastAPI endpoints for the writing pipeline
import asyncio
import logging
from typing import Literal

from fastapi import APIRouter, HTTPException

from app.core.session import SessionState
from app.pipeline.writing_pipeline import WritingPipeline, PipelineConfig

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


@router.post("/run")
async def run_pipeline(
    topic: str,
    platform: str = "wechat",
    style_profile: str = "专业严谨",
    hitl_enabled: bool = True,
    session_id: str | None = None,
):
    """
    Run the full writing pipeline.

    This is a long-running endpoint that orchestrates all 9 agents.
    For HITL-enabled runs, returns HITL card info for each confirm point.
    For fully automated runs (hitl_enabled=False), runs to completion.

    Args:
        topic: Article topic
        platform: wechat | xiaohongshu | both
        style_profile: 亲和力强 | 专业严谨 | 幽默风趣 | 极简干货
        hitl_enabled: If True, pipeline pauses at each HITL confirm point
        session_id: Optional session ID for state persistence
    """
    if not topic:
        raise HTTPException(status_code=400, detail="topic is required")

    config = PipelineConfig(
        topic=topic,
        platform=platform,
        style_profile=style_profile,
        hitl_enabled=hitl_enabled,
    )
    pipeline = WritingPipeline(config)

    try:
        result = await pipeline.run(
            topic=topic,
            platform=platform,
            style_profile=style_profile,
            hitl_enabled=hitl_enabled,
        )
        return {
            "status": result.get("status", "unknown"),
            "topic": result.get("topic"),
            "framework": result.get("framework"),
            "quality_score": result.get("quality_score", 0),
            "draft_word_count": len(result.get("draft", "")),
            "polished_word_count": len(result.get("polished_draft", "")),
            "html_output_length": len(result.get("html_output", "")),
            "errors": result.get("errors", []),
        }
    except Exception as e:
        logger.exception("Pipeline run failed")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/hitl/respond")
async def hitl_respond(
    confirm_type: Literal["strategy", "outline", "final_preview"],
    human_response: str,
    session_id: str | None = None,
):
    """
    Deliver human response to a HITL confirmation card.

    Used by Dify chatflow to relay human feedback back to the pipeline.
    """
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required")

    try:
        session = SessionState.load(session_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    pipeline = WritingPipeline()
    pipeline._data_bus = session.state.get("_pipeline_data", {})

    updated = await pipeline.deliver_hitl_response(confirm_type, human_response)

    # Persist updated data_bus back to session
    session.update(_pipeline_data=updated)
    session.write_checkpoint()

    return {
        "confirm_type": confirm_type,
        "approved": updated.get("_hitl_last", {}).get("approved", False),
        "feedback": human_response,
    }
