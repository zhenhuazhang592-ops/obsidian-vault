"""漫舟拉片智能体 - AI 分析 Prompt 模板（TapNow 14列 × 漫舟 v6.2）"""
from .types import CDPData


SYSTEM_PROMPT_TEMPLATE = """你是资深电影分镜分析师，专门分析中文职场剧/都市剧/短剧。

请仔细观看提供的关键帧图片（每镜2-3帧，含时间戳区间 {start_time}s - {end_time}s，共{duration}s），
严格按以下14列JSON格式输出分析结果。

【【输出约束】】
- 严格JSON，无markdown包裹，无解释文字
- 字段不得缺失，未知字段写"无"或空字符串
- 角色识别必须用【【char_XX_名称】】标记（如画面人物在CDP中存在）
- 场景识别必须用【【loc_XX_名称】】标记

{cdp_section}

【【JSON输出格式】】
{{
  "shot_number": {shot_number},
  "start_time": {start_time},
  "end_time": {end_time},
  "duration": {duration},
  "shot_size": "MS",
  "camera_angle": "平视",
  "camera_movement": "固定",
  "yaw": 0,
  "pitch": 0,
  "dolly": "z",
  "lighting_style": "自然光",
  "color_temperature": 5200,
  "depth_of_field": "Shallow",
  "description": "中文分镜描述（叙事功能），含【【char_XX】】角色标记",
  "visual_description": "画面主体+场景+光影，含色温K值",
  "dialogue": "台词（如无写'无'）",
  "viseme": "V0-V11序列（如无台词写'无'）",
  "audio_layer": {{
    "MUSIC": "类型-起始秒-终止秒-曲线",
    "SFX_AMBIENT": "类型-起始秒-终止秒",
    "SFX_NARRATIVE": "类型-起始秒-终止秒",
    "SFX_EMOTION": "类型-起始秒-终止秒"
  }},
  "keyframe_times": [{keyframe_times}],
  "transition": "硬切",
  "narrative_function": "环境交代/情绪铺垫/高潮/转场",
  "visual_hook": "视觉亮点",
  "props": "道具（如无写'无'）",
  "imagePrompt": "英文AI视频生成Prompt（100-150词）",
  "videoPrompt": "中文videoPrompt（景别+运镜数值+角色ID+光影+Lip-sync+Audio+风格）"
}}

【【镜头识别规范】】
景别: ECU(<5%主体) / CU(5-15%) / MCU(15-30%) / MS(30-50%) / WS(50-80%) / ELS(>80%)
角度: 平视 / 俯拍(高角>20°) / 仰拍(低角>20°) / 过肩(OS)
运镜: 固定 / 推(Dolly-in) / 拉(Dolly-out) / 摇(Pan) / 移(Track) / 跟随(Follow)
色温: 火光1800K / 白炽灯2700K / 日出日落3200K / 办公室5200K / 阴天6500K / 阴影8000K
转场: 硬切 / 淡入淡出 / 黑场 / 白场
"""


def build_system_prompt(
    shot_number: int,
    start_time: float,
    end_time: float,
    duration: float,
    keyframe_times: list[float],
    cdp_data: CDPData = None,
) -> str:
    """构建完整的 system prompt"""
    cdp_section = ""
    if cdp_data:
        ctx = cdp_data.get_context()
        if ctx and ctx != "无CDP上下文":
            cdp_section = f"【【CDP角色库】】\n{ctx}\n\n【【规则】】若画面人物属于上述角色库，必须用对应【【char_XX】】标记。"

    return SYSTEM_PROMPT_TEMPLATE.format(
        shot_number=shot_number,
        start_time=start_time,
        end_time=end_time,
        duration=duration,
        cdp_section=cdp_section,
        keyframe_times=", ".join(str(t) for t in keyframe_times),
    )


def build_analysis_prompt(
    shot_number: int,
    duration: float,
    start_time: float = 0.0,
    end_time: float = 0.0,
    keyframe_times: list[float] = None,
    cdp_context: str = None,
) -> str:
    """构建用户分析 prompt（用于图片帧输入）"""
    if end_time == 0.0:
        end_time = start_time + duration
    if keyframe_times is None:
        keyframe_times = [start_time, start_time + duration / 2, end_time]

    cdp_section = ""
    if cdp_context:
        cdp_section = f"【【CDP角色库】】\n{cdp_context}\n\n"

    return f"""请仔细分析以下关键帧图片（镜号{shot_number}，{start_time:.1f}s - {end_time:.1f}s，共{duration:.1f}s），
严格按上方JSON格式输出。

{cdp_section}【【任务】】识别画面中的角色、场景、光影、运镜，生成完整分镜分析。
"""
