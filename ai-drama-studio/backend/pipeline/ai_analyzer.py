"""ai-drama-studio/backend/pipeline/ai_analyzer.py"""
import json
import base64
import os
from openai import OpenAI
import anthropic
import google.generativeai as genai
from config import config
from prompts.shot_analysis import SHOT_ANALYSIS_SYSTEM_PROMPT
import logging

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# System Prompt 分级：
# - Zhipu（弱）：简化 Schema + response_format=json_object，可靠输出
# - Claude/Gemini（强）：专业 Schema（prompts/shot_analysis.py）
# ─────────────────────────────────────────────────────────────────────────────

ZHIPU_SYSTEM_PROMPT = """你是资深电影分镜分析师。请仔细观看提供的关键帧图片，输出结构化JSON，不要输出任何其他内容。

输出格式（严格JSON，无markdown包裹）：
{
  "scene_description": "【核心输出】一段完整的分镜描述文字，100-200字，用专业场记单风格描述这个镜头的完整画面：包括场景环境、人物站位/走位、人物外观（发型+服饰颜色款式+表情）、镜头运动、画面构图、光影氛围。要求生动具体，让读者仿佛能看到这个镜头。支持后期二次创作。",
  "shot_size": "景别，如：特写/近景/中景/全景/大远景",
  "camera_movement": "运镜，如：固定/推镜/拉镜/摇镜/跟随/航拍",
  "composition_rule": "构图，如：居中/三分线/留白/框架式",
  "angle": "角度，如：平视/俯拍/仰拍/鸟瞰",
  "lighting": "光影，如：自然光/柔光/强光/侧逆光/伦勃朗光",
  "color_palette": "色调，如：暖色/冷色/黑白/高饱和/低饱和",
  "background_style": "背景风格",
  "subject_description": "主体描述（发型+服饰颜色，20字内）",
  "subject_action": "主体动作",
  "prop_details": "道具（如有，否则写\"无\"）",
  "narrative_function": "叙事作用，如：交代环境/情绪铺垫/高潮",
  "visual_hook": "视觉亮点，如：高颜值特写/创意转场/视觉奇观",
  "dialogue": "台词（如有，否则写\"无\"）",
  "vo_emotion": "配音情绪（如有，否则写\"无\"）",
  "sfx": "音效（如有，否则写\"无\"）",
  "bgm_style": "BGM风格（如有，否则写\"无\"）",
  "transition": "转场，如：硬切/淡入淡出/黑场",
  "generation_prompt": "英文AI视频生成Prompt（强调主体特征和视觉风格，60-120词）"
}"""


class AIAnalyzer:
    """
    AI 分镜分析器，支持三种后端：
    - openai: 智谱 GLM-4V（图片 base64）
    - claude: Anthropic Claude（图片 URL）
    - gemini: Google Gemini（图片 base64）
    """

    def __init__(self):
        self.provider = config.AI_PROVIDER
        self._setup_client()

    def _setup_client(self):
        if self.provider == "openai":
            self.client = OpenAI(
                api_key=config.ZHIPU_API_KEY,
                base_url=config.ZHIPU_BASE_URL,
            )
        elif self.provider == "claude":
            self.client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        elif self.provider == "gemini":
            genai.configure(api_key=config.GOOGLE_API_KEY)
            self.client = genai.GenerativeModel(config.GEMINI_MODEL)

    # ─────────────────────────────────────────────────────────────────────────
    # 同步分析入口
    # ─────────────────────────────────────────────────────────────────────────

    async def analyze_shot_sync(
        self,
        shot_id: int,
        start_time: float,
        end_time: float,
        duration: float,
        frame_paths: list[dict],
        job_id: str,
        shot_context: str = "",
    ) -> dict:
        """统一入口，内部路由到各 provider 实现"""
        if self.provider == "openai":
            return await self._zhipu_analyze(
                shot_id, start_time, end_time, duration,
                frame_paths, job_id, shot_context,
            )
        elif self.provider == "claude":
            return await self._claude_analyze(
                shot_id, start_time, end_time, duration,
                frame_paths, job_id, shot_context,
            )
        elif self.provider == "gemini":
            return await self._gemini_analyze(
                shot_id, start_time, end_time, duration,
                frame_paths, job_id, shot_context,
            )
        else:
            raise ValueError(f"Unknown provider: {self.provider}")

    # ─────────────────────────────────────────────────────────────────────────
    # 智谱 GLM-4V（简化 Schema + response_format，图片 base64）
    # ─────────────────────────────────────────────────────────────────────────

    async def _zhipu_analyze(
        self,
        shot_id: int,
        start_time: float,
        end_time: float,
        duration: float,
        frame_paths: list[dict],
        job_id: str,
        shot_context: str,
    ) -> dict:
        content_parts = []
        for f in frame_paths:
            full_path = os.path.join(config.FRAME_DIR, job_id, f["filename"])
            with open(full_path, "rb") as img_file:
                img_b64 = base64.b64encode(img_file.read()).decode("utf-8")
            content_parts.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}
            })

        user_prompt = (
            f"**镜头信息**：镜号{shot_id}，{start_time:.1f}s - {end_time:.1f}s（{duration:.1f}s）\n"
            f"**补充**：{shot_context}\n"
            f"请仔细分析帧图片，严格按上方JSON格式输出。"
        )
        content_parts.append({"type": "text", "text": user_prompt})

        try:
            response = self.client.chat.completions.create(
                model=config.ZHIPU_MODEL,
                messages=[
                    {"role": "system",  "content": ZHIPU_SYSTEM_PROMPT},
                    {"role": "user",    "content": content_parts},
                ],
                max_tokens=1500,
                response_format={"type": "json_object"},
            )
            text = response.choices[0].message.content.strip()
            data = self._parse_json_response(text)
            if data is None:
                raise ValueError(f"无法解析 AI 响应为 JSON: {text[:200]}")
            return self._normalize_schema(data, shot_id, start_time, end_time, duration)
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Zhipu parse error: {e}, raw: {text[:300]}")
            raise

    # ─────────────────────────────────────────────────────────────────────────
    # Claude（专业 Schema，图片 URL）
    # ─────────────────────────────────────────────────────────────────────────

    async def _claude_analyze(
        self,
        shot_id: int,
        start_time: float,
        end_time: float,
        duration: float,
        frame_paths: list[dict],
        job_id: str,
        shot_context: str,
    ) -> dict:
        image_contents = []
        for f in frame_paths:
            image_contents.append({
                "type": "image",
                "source": {
                    "type": "url",
                    "url": f"http://localhost:8000{f['url']}",
                    "media_type": "image/jpeg",
                }
            })

        user_prompt = (
            f"**镜头信息**：镜号{shot_id}，{start_time:.1f}s - {end_time:.1f}s（{duration:.1f}s）\n"
            f"**补充**：{shot_context}\n"
            f"请仔细分析帧图片，严格按上方JSON格式输出。"
        )
        image_contents.append({"type": "text", "text": user_prompt})

        try:
            response = self.client.messages.create(
                model=config.CLAUDE_MODEL,
                system=SHOT_ANALYSIS_SYSTEM_PROMPT,
                max_tokens=4096,
                messages=[{"role": "user", "content": image_contents}],
            )
            text = response.content[0].text.strip()
            data = self._parse_json_response(text)
            if data is None:
                raise ValueError(f"无法解析 Claude 响应为 JSON: {text[:200]}")
            return self._normalize_schema(data, shot_id, start_time, end_time, duration)
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Claude parse error: {e}, raw: {text[:300]}")
            raise

    # ─────────────────────────────────────────────────────────────────────────
    # Gemini（专业 Schema，图片 base64）
    # ─────────────────────────────────────────────────────────────────────────

    async def _gemini_analyze(
        self,
        shot_id: int,
        start_time: float,
        end_time: float,
        duration: float,
        frame_paths: list[dict],
        job_id: str,
        shot_context: str,
    ) -> dict:
        import httpx
        image_parts = []
        for f in frame_paths:
            url = f"http://localhost:8000{f['url']}"
            async with httpx.AsyncClient() as http:
                resp = await http.get(url)
                img_b64 = base64.b64encode(resp.content).decode("utf-8")
            image_parts.append({
                "inline_data": {"mime_type": "image/jpeg", "data": img_b64}
            })

        user_prompt = (
            f"**镜头信息**：镜号{shot_id}，{start_time:.1f}s - {end_time:.1f}s（{duration:.1f}s）\n"
            f"**补充**：{shot_context}\n"
            f"请仔细分析帧图片，严格按上方JSON格式输出。"
        )

        response = self.client.generate_content(
            contents=[{"parts": image_parts + [{"text": user_prompt}]}],
            generation_config={"system_instruction": SHOT_ANALYSIS_SYSTEM_PROMPT},
        )
        text = response.text.strip()
        data = self._parse_json_response(text)
        if data is None:
            raise ValueError(f"无法解析 Gemini 响应为 JSON: {text[:200]}")
        return self._normalize_schema(data, shot_id, start_time, end_time, duration)

    # ─────────────────────────────────────────────────────────────────────────
    # Schema 标准化：统一映射到前端 LapianShot 格式
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _normalize_schema(
        data: dict,
        shot_id: int = 1,
        start_time: float = 0,
        end_time: float = 0,
        duration: float = 0,
    ) -> dict:
        """
        将不同模型的输出映射为统一的 LapianShot 格式。

        扁平 Schema（Zhipu）：shot_size / movement / lighting / color / ...
        嵌套 Schema（Claude/Gemini）：camera_and_composition / visual_aesthetics / ...

        使用 truthy 检查优先取嵌套字段（Claude），空则降级到扁平字段（Zhipu）。
        """
        def _v(nested_val, flat_key, alt_key=""):
            """优先返回嵌套值（truthy），否则返回扁平 alt_key。"""
            return nested_val if nested_val else (data.get(flat_key) or data.get(alt_key) or "")

        # ── 相机与构图 ──
        cc_n = data.get("camera_and_composition", {})
        cc_n = cc_n if isinstance(cc_n, dict) else {}
        cc = {
            "shot_size":        _v(cc_n.get("shot_size"),        "shot_size",   "shot"),
            "camera_movement":  _v(cc_n.get("camera_movement"), "camera_movement", "movement"),
            "composition_rule": _v(cc_n.get("composition_rule"), "composition_rule", "composition"),
            "angle":            _v(cc_n.get("angle"),            "angle",         ""),
        }

        # ── 视觉美学 ──
        va_n = data.get("visual_aesthetics", {})
        va_n = va_n if isinstance(va_n, dict) else {}
        va = {
            "lighting":         _v(va_n.get("lighting"),      "lighting",      ""),
            "color_palette":    _v(va_n.get("color_palette"), "color_palette", "color"),
            "background_style": _v(va_n.get("background_style"), "background_style", "background"),
        }

        # ── 角色与动作 ──
        ca_n = data.get("character_and_action", {})
        ca_n = ca_n if isinstance(ca_n, dict) else {}
        ca = {
            "subject_description": _v(ca_n.get("subject_description"), "subject_description", "subject"),
            "subject_action":       _v(ca_n.get("subject_action"),     "subject_action",      "action"),
            "prop_details":         _v(ca_n.get("prop_details"),       "prop_details",        "props"),
        }

        # ── 叙事与钩子 ──
        nh_n = data.get("narrative_and_hook", {})
        nh_n = nh_n if isinstance(nh_n, dict) else {}
        nh = {
            "narrative_function": _v(nh_n.get("narrative_function"), "narrative_function", "narrative"),
            "visual_hook":        _v(nh_n.get("visual_hook"),        "visual_hook",        "hook"),
        }

        # ── 对白与音频 ──
        da_n = data.get("dialogue_and_audio", {})
        if isinstance(da_n, str):
            da_n = {"dialogue": da_n}
        da_n = da_n if isinstance(da_n, dict) else {}
        da = {
            "has_dialogue": bool(data.get("dialogue") or da_n.get("dialogue")),
            "dialogue":     data.get("dialogue") or da_n.get("dialogue") or "无",
            "vo_emotion":   data.get("vo_emotion") or da_n.get("vo_emotion") or "无",
            "sfx":          data.get("sfx") or da_n.get("sfx") or "无",
            "bgm_style":   (data.get("bgm") or da_n.get("bgm_style") or "无"),
        }

        return {
            "shot_id":                   int(str(shot_id).strip('"')) if shot_id else 1,
            "start_time":                data.get("start_time", start_time),
            "end_time":                  data.get("end_time",   end_time),
            "duration":                  data.get("duration",   duration),
            "scene_description":         data.get("scene_description") or "",
            "camera_and_composition":    cc,
            "visual_aesthetics":         va,
            "character_and_action":     ca,
            "narrative_and_hook":       nh,
            "dialogue_and_audio":       da,
            "transition":               data.get("transition", "硬切"),
            "generation_prompt":        data.get("generation_prompt") or data.get("prompt", ""),
            "extracted_frames":         data.get("extracted_frames", []),
        }

    @staticmethod
    def _parse_json_response(text: str) -> dict | None:
        """
        ZJT三层JSON解析（v2.0 P0强制）：
        Layer 1: 清理 markdown 包裹（```json 等）
        Layer 2: 标准解析
        Layer 3: 截断修复（LLM输出被截断时自动修复）
        """
        if not text or not text.strip():
            return None

        # ── Layer 1: 清理 markdown 包裹 ─────────────────────────────────────
        cleaned = AIAnalyzer._strip_code_fence(text)

        # ── Layer 2: 标准解析 ───────────────────────────────────────────────
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        # ── Layer 2b: 括号匹配找第一个完整 JSON 对象 ─────────────────────
        brace_count, start = 0, -1
        for i, ch in enumerate(cleaned):
            if ch == '{':
                if start == -1:
                    start = i
                brace_count += 1
            elif ch == '}':
                brace_count -= 1
                if brace_count == 0 and start != -1:
                    candidate = cleaned[start:i+1]
                    try:
                        return json.loads(candidate)
                    except json.JSONDecodeError:
                        pass
                    start = -1

        # ── Layer 3: 截断修复（ZJT核心机制）───────────────────────────────
        # 检测：cleaned 不是以 } 结尾（JSON被截断）
        if not cleaned.rstrip().endswith('}'):
            repaired = AIAnalyzer._repair_truncated_json(cleaned)
            if repaired is not None:
                logger.info(f"[JSON修复] 截断修复成功，原始末尾: {cleaned[-80:]}")
                return repaired

        return None

    @staticmethod
    def _repair_truncated_json(content: str) -> dict | None:
        """
        ZJT三层截断修复（Layer 3）：
        当LLM输出被截断时，智能关闭JSON结构。

        修复策略：
        1. 找到最后一个完整的顶层键值对
        2. 关闭所有未闭合的数组和对象
        3. 尝试解析，失败则返回 None
        """
        content = content.rstrip()

        # 策略A：找最后一个完整的 "key": "value" 或 "key": number 并截断其后
        # 匹配模式：完整的字符串值 "..." 或数字
        patterns = [
            r'(?:"[^"\\]*(?:\\.[^"\\]*)*"\s*:\s*"(?:[^"\\]*(?:\\.[^"\\]*)*)"\s*,?\s*})',
            r'(?:"[^"\\]*(?:\\.[^"\\]*)*"\s*:\s*-?\d+\.?\d*\s*,?\s*})',
            r'(?:"[^"\\]*(?:\\.[^"\\]*)*"\s*:\s*\[)',
            r'(?:"[^"\\]*(?:\\.[^"\\]*)*"\s*:\s*\{)',
            r'(?:"[^"\\]*(?:\\.[^"\\]*)*"\s*:\s*true\s*,?\s*})',
            r'(?:"[^"\\]*(?:\\.[^"\\]*)*"\s*:\s*false\s*,?\s*})',
            r'(?:"[^"\\]*(?:\\.[^"\\]*)*"\s*:\s*null\s*,?\s*})',
        ]

        # 找到最后一个逗号或右大括号的位置
        last_valid_end = -1

        # 策略：找最后一个逗号分隔的完整键值对
        # 从后往前扫描，找 "key": value, 或 } 结尾
        brace_depth = 0
        in_string = False
        escape_next = False

        for i in range(len(content) - 1, -1, -1):
            ch = content[i]

            if escape_next:
                escape_next = False
                continue

            if ch == '\\' and in_string:
                escape_next = True
                continue

            if ch == '"' and not escape_next:
                in_string = not in_string
                continue

            if in_string:
                continue

            if ch == '}':
                brace_depth += 1
            elif ch == '{':
                brace_depth -= 1
            elif ch == '[':
                pass
            elif ch == ']':
                pass
            elif ch == ',' and brace_depth == 1:
                # 找到了最后一个顶层键值对的结尾逗号
                last_valid_end = i
                break

        if last_valid_end == -1:
            # 没有找到逗号，尝试找最后一个 }
            last_close = content.rfind('}')
            if last_close > 0:
                last_valid_end = last_close

        if last_valid_end > 0:
            # 截断内容并补全 JSON 结构
            truncated = content[:last_valid_end]
            # 找最后一个逗号后面的字符，确保没有未闭合的数组
            # 补上 } 闭合
            repaired = truncated.rstrip().rstrip(',') + '}'
            try:
                result = json.loads(repaired)
                logger.warning(f"[JSON截断修复] 修复成功，补全了JSON结构")
                return result
            except json.JSONDecodeError:
                pass

        # 策略B：直接找最后一个 } 并截断
        last_close = content.rfind('}')
        if last_close > 10:
            candidate = content[:last_close+1]
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                pass

        return None

    @staticmethod
    def _strip_code_fence(text: str) -> str:
        """去掉 ```json ``` 包裹"""
        lines = text.split("\n", 1)
        if len(lines) > 1 and lines[0].strip().startswith("```"):
            text = lines[1]
        if text.strip().endswith("```"):
            text = text.strip()[:-3]
        return text.strip()

    # ─────────────────────────────────────────────────────────────────────────
    # TapNow 14列标准化（新增，供 manzhou_lapian 调用）
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def normalize_tapnow(data: dict) -> "ShotAnalysis":
        """
        将 AI 输出的原始 JSON 标准化为 ShotAnalysis 对象。
        支持两种格式：
        - TapNow 14列（完整嵌套）
        - 扁平 Schema（Zhipu 降级输出）
        """
        from manzhou_lapian.types import ShotAnalysis, AudioLayer

        # ── Audio Layer ──
        raw_al = data.get("audio_layer", {})
        if isinstance(raw_al, dict):
            al = AudioLayer(
                music=raw_al.get("MUSIC", "无"),
                sfx_ambient=raw_al.get("SFX_AMBIENT", "无"),
                sfx_narrative=raw_al.get("SFX_NARRATIVE", "无"),
                sfx_emotion=raw_al.get("SFX_EMOTION", "无"),
            )
        elif isinstance(raw_al, str) and raw_al != "无":
            # 扁平格式降级
            al = AudioLayer(music=raw_al)
        else:
            al = AudioLayer()

        return ShotAnalysis(
            shot_number=data.get("shot_number", 1),
            start_time=data.get("start_time", 0.0),
            end_time=data.get("end_time", 0.0),
            duration=data.get("duration", 0.0),
            shot_size=data.get("shot_size", ""),
            camera_angle=data.get("camera_angle", ""),
            camera_movement=data.get("camera_movement", data.get("movement", "")),
            yaw=data.get("yaw", 0),
            pitch=data.get("pitch", 0),
            dolly=data.get("dolly", "z"),
            lighting_style=data.get("lighting_style", data.get("lighting", "")),
            color_temperature=data.get("color_temperature",
                                       data.get("color_temp", 0)),
            depth_of_field=data.get("depth_of_field", ""),
            description=data.get("description",
                                data.get("scene_description", "")),
            visual_description=data.get("visual_description", ""),
            dialogue=data.get("dialogue", "无"),
            viseme=data.get("viseme", "无"),
            audio_layer=al,
            keyframe_times=data.get("keyframe_times", []),
            extracted_frames=data.get("extracted_frames", []),
            transition=data.get("transition", "硬切"),
            narrative_function=data.get("narrative_function", ""),
            visual_hook=data.get("visual_hook", ""),
            props=data.get("props", "无"),
            imagePrompt=data.get("imagePrompt",
                                 data.get("generation_prompt", "")),
            videoPrompt=data.get("videoPrompt", ""),
        )
