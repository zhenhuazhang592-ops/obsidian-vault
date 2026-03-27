"""ai-drama-studio/backend/main.py"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from api.routes import router as lapian_router
from config import config

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时创建目录
    for d in [config.UPLOAD_DIR, config.FRAME_DIR, config.STANDARDIZED_DIR]:
        os.makedirs(d, exist_ok=True)
    yield

app = FastAPI(
    title="漫舟一键拉片 API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件（用于提供帧图片）
app.mount("/frames", StaticFiles(directory=config.FRAME_DIR), name="frames")

app.include_router(lapian_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
