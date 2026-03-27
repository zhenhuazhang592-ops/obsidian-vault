"""ai-drama-studio/backend/api/routes.py"""
import os
import uuid
import json
import asyncio
import tempfile
from typing import Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Form
from fastapi.responses import StreamingResponse
from pipeline.ffmpeg_preprocess import FFmpegPreprocessor
from pipeline.scene_detect import SceneDetector
from pipeline.frame_extract import FrameExtractor
from pipeline.ai_analyzer import AIAnalyzer
from config import config
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/lapian", tags=["一键拉片"])


# ────────────────────────────────────────────────────────────────
# Step 1: 上传视频（同步保存，写入 job 状态文件）
# ────────────────────────────────────────────────────────────────

@router.post("/upload")
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    shot_context: Optional[str] = Form(""),
):
    """
    上传视频，保存到 uploads/{job_id}/，写入初始 job 状态文件。
    返回 job_id，前端据此建立 SSE 连接。
    实际流水线在后台运行。
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="未提供文件")

    job_id = uuid.uuid4().hex
    upload_dir = os.path.join(config.UPLOAD_DIR, job_id)
    os.makedirs(upload_dir, exist_ok=True)

    # 同步保存文件（文件小时足够快）
    input_path = os.path.join(upload_dir, file.filename)
    content = await file.read()
    with open(input_path, "wb") as f:
        f.write(content)

    # 立即写入 job 状态文件（这样 SSE 能立刻读到）
    pipeline_state = {
        "status": "uploading",        # 新状态：文件上传中
        "phase": "preprocessing",
        "phase_desc": "视频上传完成，准备分析...",
        "progress": 5,                # 刚完成上传，给5%
        "shots": [],
        "total_shots": 0,
        "current_shot": 0,
        "error": None,
        "file_size": len(content),
        "file_name": file.filename,
    }
    _save_job_state(job_id, pipeline_state)

    # 后台运行流水线（文件已保存，只做分析）
    background_tasks.add_task(run_pipeline, job_id, input_path, shot_context or "")

    return {"job_id": job_id, "file_name": file.filename, "file_size": len(content)}


# ────────────────────────────────────────────────────────────────
# Step 2: 流水线执行（后台）
# ────────────────────────────────────────────────────────────────

async def run_pipeline(job_id: str, input_path: str, shot_context: str):
    """后台运行完整流水线，结果写入 job 文件供 SSE 轮询。"""

    try:
        # ── Phase 1: FFmpeg 标准化 ──
        _update_job(job_id, status="running", phase="preprocessing",
                     phase_desc="视频标准化中...", progress=10)

        preprocessor = FFmpegPreprocessor()
        std_path, metadata = preprocessor.standardize(input_path)

        _update_job(job_id, progress=20, metadata=metadata)

        # ── Phase 2: 镜头边界检测 ──
        _update_job(job_id, phase="scene_detection",
                     phase_desc="检测镜头边界...", progress=30)

        detector = SceneDetector()
        shots = detector.detect(std_path)

        _update_job(job_id, total_shots=len(shots), progress=40)

        # ── Phase 3: 动态抽帧 ──
        _update_job(job_id, phase="frame_extraction",
                     phase_desc="提取关键帧...", progress=50)

        frame_dir = os.path.join(config.FRAME_DIR, job_id)
        extractor = FrameExtractor()
        frame_results = extractor.extract_shot_frames(
            video_path=std_path,
            fps=metadata["fps"],
            shots=shots,
            output_dir=frame_dir,
            job_id=job_id,
        )

        _update_job(job_id, progress=60)

        # ── Phase 4: AI 分镜分析 ──
        _update_job(job_id, phase="ai_analysis",
                     phase_desc="AI分镜分析中...", progress=60)

        analyzer = AIAnalyzer()
        analyzed_shots = []

        for i, (shot, frame_result) in enumerate(zip(shots, frame_results)):
            frame_paths = frame_result["frames"]

            result = await analyzer.analyze_shot_sync(
                shot_id=shot["shot_id"],
                start_time=shot["start_time"],
                end_time=shot["end_time"],
                duration=shot["duration_sec"],
                frame_paths=frame_paths,
                job_id=job_id,
                shot_context=shot_context,
            )

            result["extracted_frames"] = frame_result["frames"]
            result["start_time"] = shot["start_time"]
            result["end_time"] = shot["end_time"]
            result["duration"] = shot["duration_sec"]
            analyzed_shots.append(result)

            # 进度：60% ~ 98%，每个镜头完成后立即写入 job 文件
            prog = 60 + int(38 * (i + 1) / len(shots))
            _update_job(job_id, current_shot=shot["shot_id"],
                         shots=list(analyzed_shots),  # 实时写入，前端可逐个渲染
                         phase_desc=f"AI分析镜头 {i+1}/{len(shots)}...", progress=prog)

        _update_job(job_id, status="completed", phase="done",
                     phase_desc="分析完成！", progress=100)

    except Exception as e:
        logger.error(f"Pipeline error: {e}")
        import traceback; traceback.print_exc()
        _update_job(job_id, status="error", phase_desc=f"发生错误: {e}", error=str(e))


def _update_job(job_id: str, **kwargs):
    """原子更新 job 状态文件（合并而非覆盖）。"""
    state = _load_job_state(job_id) or {}
    state.update(kwargs)
    _save_job_state(job_id, state)


# ────────────────────────────────────────────────────────────────
# SSE: 流式推送（/stream/{job_id}）
# ────────────────────────────────────────────────────────────────

@router.get("/stream/{job_id}")
async def stream_lapian(job_id: str):
    """
    SSE 流式推送流水线状态和镜头结果。
    - 实时推送每个完成的镜头（支持中途连接补发）
    - 定期推送状态（progress / phase）
    """
    async def event_generator():
        seen_shot_count = 0  # 已发送的镜头数（避免重复推送）
        consecutive_not_found = 0
        last_phase_desc = ""

        while True:
            state = _load_job_state(job_id)

            if state is None:
                consecutive_not_found += 1
                if consecutive_not_found >= 3:
                    yield f"event: error\ndata: {json.dumps({'type': 'error', 'code': 'JOB_NOT_FOUND', 'message': '任务不存在，请重新上传'})}\n\n"
                    break
                yield f"event: status\ndata: {json.dumps({'type': 'status', 'status': 'initializing', 'phase_desc': '连接中...', 'progress': 0})}\n\n"
                await asyncio.sleep(2)
                continue

            consecutive_not_found = 0
            job_status = state.get("status", "unknown")
            current_shots = state.get("shots", [])
            phase_desc = state.get("phase_desc", "")

            # ── 推送新完成的镜头（增量推送）─
            while seen_shot_count < len(current_shots):
                shot = current_shots[seen_shot_count]
                yield f"event: shot_complete\ndata: {json.dumps({'type': 'shot_complete', 'shot': shot, 'total_shots': state.get('total_shots', 0), 'current_shot': shot.get('shot_id', seen_shot_count+1)})}\n\n"
                seen_shot_count += 1
                await asyncio.sleep(0.05)

            # ── 状态推送（每个循环都发，确保进度条实时更新）─
            status_payload = {
                'type': 'status',
                'status': job_status,
                'phase': state.get('phase', ''),
                'progress': state.get('progress', 0),
                'phase_desc': phase_desc,
                'total_shots': state.get('total_shots', 0),
                'current_shot': state.get('current_shot', 0),
            }
            yield f"event: status\ndata: {json.dumps(status_payload)}\n\n"

            if job_status == "completed":
                yield f"event: done\ndata: {json.dumps({'type': 'done', 'total_shots': len(current_shots)})}\n\n"
                break

            if job_status == "error":
                yield f"event: error\ndata: {json.dumps({'type': 'error', 'code': 'PIPELINE_ERROR', 'message': state.get('error', '未知错误')})}\n\n"
                break

            await asyncio.sleep(1.0)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/status/{job_id}")
async def get_status(job_id: str):
    """轮询获取流水线状态"""
    state = _load_job_state(job_id)
    if state is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    return state


# ────────────────────────────────────────────────────────────────
# 工具函数
# ────────────────────────────────────────────────────────────────

def _get_job_file(job_id: str) -> str:
    return os.path.join(tempfile.gettempdir(), f"lapian_job_{job_id}.json")

def _save_job_state(job_id: str, state: dict):
    with open(_get_job_file(job_id), "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def _load_job_state(job_id: str) -> Optional[dict]:
    path = _get_job_file(job_id)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)
