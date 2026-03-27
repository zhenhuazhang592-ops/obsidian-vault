"""ai-drama-studio/backend/tts/tts_engine.py

漫舟TTS引擎 v1.0
支持后端：豆包(Doubao) / MiniMax / OpenAI-TTS
参考 manzhou-tts-voice.md v1.1 规范

调用示例：
    tts = TTSEngine(provider="doubao")
    result = await tts.generate(
        text="Ray……离职了？",
        emotion="震惊",
        speed="slow",
        pitch="high",
        output_path="./output.wav",
    )
"""

import os
import asyncio
import uuid
import base64
import httpx
from abc import ABC, abstractmethod
from typing import Optional
from config import config
import logging

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# 情绪 → TTS参数映射（来自 manzhou-tts-voice.md v1.1）
# ─────────────────────────────────────────────────────────────────────────────

EMOTION_PARAMS = {
    "震惊":      {"speed": 0.8, "pitch": 1.2, "emotion": "震惊"},
    "愤怒":      {"speed": 1.2, "pitch": 0.8, "emotion": "愤怒"},
    "平静":      {"speed": 1.0, "pitch": 1.0, "emotion": "平静"},
    "悲伤":      {"speed": 0.8, "pitch": 0.8, "emotion": "悲伤"},
    "紧张":      {"speed": 0.8, "pitch": 1.1, "emotion": "紧张"},
    "漫不经心":  {"speed": 1.0, "pitch": 1.0, "emotion": "轻松"},
    "急促":      {"speed": 1.3, "pitch": 1.0, "emotion": "急促"},
    "嘶哑":      {"speed": 0.7, "pitch": 0.7, "emotion": "嘶哑"},
    "疲惫":      {"speed": 0.7, "pitch": 0.9, "emotion": "疲惫"},
    "刻意平静":  {"speed": 0.9, "pitch": 0.95, "emotion": "克制"},
    "审视":      {"speed": 1.0, "pitch": 0.9, "emotion": "审视"},
    "紧绷":      {"speed": 0.8, "pitch": 1.1, "emotion": "紧绷"},
    "中性":      {"speed": 1.0, "pitch": 1.0, "emotion": "中性"},
}

# Lip-sync 质量分级（v1.1）
LIPSYNC_GRADE = {
    "S": {"max_chars": 8,  "speed": "slow",   "yaw": 0,   "obstruction": False},
    "A": {"max_chars": 15, "speed": "slow/normal", "yaw": 15, "obstruction": False},
    "B": {"max_chars": 20, "speed": "normal", "yaw": 30, "obstruction": True},
    "C": {"max_chars": 15, "speed": "normal", "yaw": 45, "obstruction": True},
}


# ─────────────────────────────────────────────────────────────────────────────
# 抽象基类
# ─────────────────────────────────────────────────────────────────────────────

class TTSBackend(ABC):
    """TTS后端抽象接口"""

    @abstractmethod
    async def generate(
        self,
        text: str,
        speed: float = 1.0,
        pitch: float = 1.0,
        emotion: str = "中性",
        output_path: str = "",
    ) -> dict:
        """生成TTS音频文件，返回 {file_path, duration_sec, lip_sync_grade}"""
        ...


# ─────────────────────────────────────────────────────────────────────────────
# 豆包(Doubao) TTS — 字节跳动，API方式，免费额度
# ─────────────────────────────────────────────────────────────────────────────

class DoubaoTTS(TTSBackend):
    """
    豆包TTS后端
    API文档: https://www.volcengine.com/docs/tts/online-restriction/API
    模型: volcengine_tts -> doubao-omni-tts
    """

    def __init__(self, api_key: str = ""):
        self.api_key = api_key or os.getenv("DOUBAO_API_KEY", "")
        self.base_url = "https://openspeech.bytedance.com/api/v3/tts"
        self.voice_id = os.getenv("DOUBAO_VOICE_ID", "BV700_TONE_GAOXIN")

    async def generate(
        self,
        text: str,
        speed: float = 1.0,
        pitch: float = 1.0,
        emotion: str = "中性",
        output_path: str = "",
    ) -> dict:
        if not self.api_key:
            raise RuntimeError("DOUBAO_API_KEY 未设置")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer;{self.api_key}",
        }

        payload = {
            "app": {
                "appid": os.getenv("DOUBAO_APP_ID", ""),
                "token": self.api_key,
                "cluster": "volcengine_tts",
            },
            "user": {"uid": "manzhou"},
            "audio": {
                "voice_type": self.voice_id,
                "encoding": "mp3",
                "speed": int(speed * 100),      # 0-200
                "pitch": int(pitch * 100),       # 0-200
                "emotion": emotion,
            },
            "request": {
                "reqid": uuid.uuid4().hex,
                "text": text,
                "text_type": "plain",
                "operation": "submit",
            },
        }

        output_path = output_path or f"/tmp/manzhou_tts_{uuid.uuid4().hex[:8]}.mp3"

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(self.base_url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()

            # 豆包返回 task_id，需要轮询获取结果
            task_id = data.get("task_id")
            audio_url = await self._poll_task(client, headers, task_id)

            # 下载音频
            audio_resp = await client.get(audio_url)
            audio_resp.raise_for_status()
            os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(audio_resp.content)

        # 获取时长
        duration = await self._get_duration(output_path)

        # Lip-sync 质量评估
        lip_grade = self._eval_lipsync_grade(text)

        return {
            "file_path": output_path,
            "duration_sec": round(duration, 2),
            "lip_sync_grade": lip_grade,
            "chars": len(text),
            "provider": "doubao",
        }

    async def _poll_task(
        self, client: httpx.AsyncClient, headers: dict, task_id: str, max_wait: int = 30
    ) -> str:
        """轮询豆包任务状态，返回音频URL"""
        query_url = f"{self.base_url}/query"
        for _ in range(max_wait):
            await asyncio.sleep(1)
            resp = await client.post(query_url, json={"task_id": task_id}, headers=headers)
            data = resp.json()
            status = data.get("status")
            if status == "success":
                return data["audio_url"]
            elif status == "failed":
                raise RuntimeError(f"TTS任务失败: {data.get('message', 'unknown')}")
        raise RuntimeError(f"TTS任务超时（>{max_wait}s）")

    async def _get_duration(self, path: str) -> float:
        """用 ffprobe 获取音频时长"""
        import subprocess
        try:
            result = subprocess.run(
                [
                    "ffprobe", "-v", "error",
                    "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1", path
                ],
                capture_output=True, text=True, timeout=5,
            )
            return float(result.stdout.strip())
        except Exception:
            # 估算：中文约4字/秒
            return 3.0

    @staticmethod
    def _eval_lipsync_grade(text: str) -> str:
        chars = len(text)
        if chars <= 8:
            return "S"
        elif chars <= 15:
            return "A"
        elif chars <= 20:
            return "B"
        else:
            return "C"


# ─────────────────────────────────────────────────────────────────────────────
# MiniMax TTS — 中文情感TTS，免费额度
# ─────────────────────────────────────────────────────────────────────────────

class MiniMaxTTS(TTSBackend):
    """
    MiniMax TTS后端
    API文档: https://www.minimaxi.com/document
    模型: MiniMax-Speech-01
    """

    def __init__(self, api_key: str = ""):
        self.api_key = api_key or os.getenv("MINIMAX_API_KEY", "")
        self.group_id = os.getenv("MINIMAX_GROUP_ID", "")
        self.base_url = "https://api.minimax.chat/v1"

    async def generate(
        self,
        text: str,
        speed: float = 1.0,
        pitch: float = 1.0,
        emotion: str = "中性",
        output_path: str = "",
    ) -> dict:
        if not self.api_key:
            raise RuntimeError("MINIMAX_API_KEY 未设置")

        # MiniMax情感ID映射
        emotion_id_map = {
            "震惊": 3, "愤怒": 5, "平静": 0, "悲伤": 4,
            "紧张": 2, "轻松": 0, "急促": 1, "嘶哑": 6,
            "疲惫": 4, "克制": 0, "审视": 2, "紧绷": 2,
        }
        emotion_id = emotion_id_map.get(emotion, 0)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": "MiniMax-Speech-01",
            "text": text,
            "stream": False,
            "voice_setting": {
                "voice_id": os.getenv("MINIMAX_VOICE_ID", "male-qn-qingse"),
                "speed": speed,
                "pitch": pitch,
                "volume": 1.0,
                "emotion": emotion_id,
            },
            "audio_setting": {
                "audio_format": "mp3",
                "sample_rate": 16000,
            },
        }

        output_path = output_path or f"/tmp/manzhou_tts_{uuid.uuid4().hex[:8]}.mp3"

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{self.base_url}/t2a_v2",
                json=payload,
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()

            # MiniMax 返回 base64 音频
            audio_b64 = data.get("data", {}).get("audio_file", "")
            if not audio_b64:
                raise RuntimeError(f"MiniMax TTS 返回格式异常: {data}")

            audio_bytes = base64.b64decode(audio_b64)
            os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(audio_bytes)

        duration = await self._get_duration(output_path)
        lip_grade = DoubaoTTS._eval_lipsync_grade(text)

        return {
            "file_path": output_path,
            "duration_sec": round(duration, 2),
            "lip_sync_grade": lip_grade,
            "chars": len(text),
            "provider": "minimax",
        }

    async def _get_duration(self, path: str) -> float:
        import subprocess
        try:
            result = subprocess.run(
                [
                    "ffprobe", "-v", "error",
                    "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1", path
                ],
                capture_output=True, text=True, timeout=5,
            )
            return float(result.stdout.strip())
        except Exception:
            return 3.0


# ─────────────────────────────────────────────────────────────────────────────
# OpenAI TTS — 通用接口（支持任何 OpenAI 兼容 API）
# ─────────────────────────────────────────────────────────────────────────────

class OpenAITTS(TTSBackend):
    """
    OpenAI 兼容 TTS 后端
    支持: OpenAI / 智谱 / 其他兼容 API
    """

    def __init__(self, api_key: str = "", model: str = "tts-1", voice: str = "alloy"):
        self.api_key = api_key or os.getenv("OPENAI_TTS_API_KEY", "")
        self.model = model or os.getenv("TTS_MODEL", "tts-1")
        self.voice = voice or os.getenv("TTS_VOICE", "alloy")
        self.base_url = os.getenv("OPENAI_TTS_BASE_URL", "https://api.openai.com/v1")

    async def generate(
        self,
        text: str,
        speed: float = 1.0,
        pitch: float = 1.0,
        emotion: str = "中性",
        output_path: str = "",
    ) -> dict:
        if not self.api_key:
            raise RuntimeError("OPENAI_TTS_API_KEY 未设置")

        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)

        output_path = output_path or f"/tmp/manzhou_tts_{uuid.uuid4().hex[:8]}.mp3"

        try:
            # OpenAI TTS 不直接支持 speed/pitch，用 model 映射
            response = await client.audio.speech.create(
                model=self.model,
                voice=self.voice,
                input=text,
                response_format="mp3",
            )
            audio_bytes = await response.aread()

            os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(audio_bytes)

        except Exception as e:
            logger.error(f"OpenAI TTS 生成失败: {e}")
            raise

        duration = await self._get_duration(output_path)
        lip_grade = DoubaoTTS._eval_lipsync_grade(text)

        return {
            "file_path": output_path,
            "duration_sec": round(duration, 2),
            "lip_sync_grade": lip_grade,
            "chars": len(text),
            "provider": "openai",
        }

    async def _get_duration(self, path: str) -> float:
        import subprocess
        try:
            result = subprocess.run(
                [
                    "ffprobe", "-v", "error",
                    "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1", path
                ],
                capture_output=True, text=True, timeout=5,
            )
            return float(result.stdout.strip())
        except Exception:
            return 3.0


# ─────────────────────────────────────────────────────────────────────────────
# TTSEngine 工厂（统一入口）
# ─────────────────────────────────────────────────────────────────────────────

PROVIDER_MAP = {
    "doubao":  DoubaoTTS,
    "minimax": MiniMaxTTS,
    "openai":  OpenAITTS,
}


class TTSEngine:
    """
    漫舟TTS统一引擎
    支持后端: doubao / minimax / openai

    用法:
        tts = TTSEngine(provider="doubao")
        result = await tts.generate(
            text="Ray……离职了？",
            emotion="震惊",
        )
    """

    def __init__(self, provider: str = ""):
        self.provider = provider or os.getenv("TTS_PROVIDER", "doubao")
        self._client = None

    def _get_backend(self) -> TTSBackend:
        cls = PROVIDER_MAP.get(self.provider)
        if not cls:
            raise ValueError(f"不支持的TTS后端: {self.provider}，可用: {list(PROVIDER_MAP.keys())}")
        return cls()

    async def generate(
        self,
        text: str,
        emotion: str = "中性",
        speed: str = "normal",
        pitch: str = "normal",
        output_path: str = "",
        lip_sync: bool = True,
    ) -> dict:
        """
        生成TTS音频。

        Args:
            text:       台词文本
            emotion:    情绪（来自 EMOTION_PARAMS 映射）
            speed:       语速 slow/normal/fast 或 float
            pitch:       音调 low/normal/high 或 float
            output_path: 保存路径，默认 /tmp/manzhou_tts_{uuid}.mp3
            lip_sync:    是否评估 Lip-sync 质量

        Returns:
            {
                "file_path": str,       # 音频文件路径
                "duration_sec": float,   # 音频时长（秒）
                "lip_sync_grade": str,  # S/A/B/C
                "chars": int,            # 字数
                "provider": str,        # 供应商
                "lip_sync_detail": {   # v1.1 Lip-sync质量评估
                    "grade": str,
                    "max_chars": int,
                    "recommended_speed": str,
                    "camera_yaw": int,
                    "obstruction_risk": bool,
                    "visemes": str,       # 简化的Viseme序列
                }
            }
        """
        params = EMOTION_PARAMS.get(emotion, EMOTION_PARAMS["中性"])
        speed_val = float(speed) if isinstance(speed, (int, float)) else (0.8 if speed == "slow" else 1.2 if speed == "fast" else params["speed"])
        pitch_val = float(pitch) if isinstance(pitch, (int, float)) else (0.8 if pitch == "low" else 1.2 if pitch == "high" else params["pitch"])

        backend = self._get_backend()
        result = await backend.generate(
            text=text,
            speed=speed_val,
            pitch=pitch_val,
            emotion=emotion,
            output_path=output_path,
        )

        # Lip-sync 质量评估
        if lip_sync:
            lip_grade = DoubaoTTS._eval_lipsync_grade(text)
            detail = LIPSYNC_GRADE.get(lip_grade, LIPSYNC_GRADE["A"])
            result["lip_sync_detail"] = {
                "grade": lip_grade,
                "max_chars": detail["max_chars"],
                "recommended_speed": detail["speed"],
                "camera_yaw": detail["yaw"],
                "obstruction_risk": detail["obstruction"],
                "visemes": self._gen_viseme_hint(text),
            }
        else:
            result["lip_sync_detail"] = None

        logger.info(
            f"[TTS] {self.provider} | {emotion} | {len(text)}字 | "
            f"Lip-sync:{result['lip_sync_grade']} | {result['duration_sec']}s"
        )
        return result

    @staticmethod
    def _gen_viseme_hint(text: str) -> str:
        """生成简化 Viseme 序列提示（v1.1）"""
        # 简化版：按韵母类型生成大致嘴型序列
        # 实际精确Viseme需要音素分析工具
        hints = []
        for ch in text:
            if ch in "aeiou":  # 元音为主 → V2 张嘴
                hints.append("V2")
            elif ch in "iy":   # i → V1 拉伸
                hints.append("V1")
            elif ch in "mn":   # 鼻音 → V0 闭嘴
                hints.append("V0")
            else:
                hints.append("V5")  # 辅音 → V5 抿唇
        # 压缩重复
        compressed = [h for i, h in enumerate(hints) if i == 0 or h != hints[i-1]]
        return "→".join(compressed[:12])  # 最多12个


# ─────────────────────────────────────────────────────────────────────────────
# 批量生成（单集TTS配音表）
# ─────────────────────────────────────────────────────────────────────────────

class TTSBatchGenerator:
    """
    批量生成单集所有TTS配音
    参考 manzhou-tts-voice.md 对白表格模板
    """

    def __init__(self, provider: str = ""):
        self.engine = TTSEngine(provider=provider)
        self.output_dir = os.getenv("TTS_OUTPUT_DIR", "./tts_output")
        os.makedirs(self.output_dir, exist_ok=True)

    async def generate_episode(
        self,
        dialogue_table: list[dict],
        project_name: str = "project",
        episode: int = 1,
    ) -> dict:
        """
        批量生成一集所有TTS配音。

        dialogue_table 格式（来自 manzhou-tts-voice.md 对白表格）:
        [
            {
                "shot_id": "P03",
                "character_id": "char_01",
                "character_name": "潭斌",
                "text": "Ray……离职了？",
                "emotion": "震惊",
                "speed": "slow",
                "pitch": "high",
            },
            ...
        ]

        Returns:
            {
                "episode": int,
                "total_shots": int,
                "total_duration": float,
                "files": [TTSResult, ...],
                "dialogue_table": [带音频路径的对白表, ...],
            }
        """
        results = []
        total_duration = 0.0

        for entry in dialogue_table:
            shot_id = entry["shot_id"]
            text = entry["text"]

            output_path = os.path.join(
                self.output_dir,
                f"{project_name}_EP{episode:02d}_{shot_id}.mp3"
            )

            tts_result = await self.engine.generate(
                text=text,
                emotion=entry.get("emotion", "中性"),
                speed=entry.get("speed", "normal"),
                pitch=entry.get("pitch", "normal"),
                output_path=output_path,
            )

            total_duration += tts_result["duration_sec"]
            results.append({**tts_result, "shot_id": shot_id, **entry})

        # 生成对白表格（含音频路径）
        dialogue_table_out = [
            {
                "shot_id": r["shot_id"],
                "character_id": r["character_id"],
                "character_name": r["character_name"],
                "text": r["text"],
                "chars": r["chars"],
                "emotion": r.get("emotion", "中性"),
                "speed": r.get("speed", "normal"),
                "duration_sec": r["duration_sec"],
                "lip_sync_grade": r["lip_sync_grade"],
                "audio_path": r["file_path"],
                "lip_sync_detail": r.get("lip_sync_detail"),
            }
            for r in results
        ]

        return {
            "episode": episode,
            "total_shots": len(dialogue_table),
            "total_duration": round(total_duration, 2),
            "files": results,
            "dialogue_table": dialogue_table_out,
        }
