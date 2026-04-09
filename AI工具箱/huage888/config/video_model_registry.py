#!/usr/bin/env python3
"""
video_model_registry.py — 视频模型能力矩阵（Python 版）

对标 config/video-model-registry.md，提供：
- 结构化 VideoModel / ImageModel 数据类
- 模型查询：按需求自动选最优模型
- Pipeline 集成：video_pipeline.py / doubao_pipeline.py 直接引用

用法：

  from config.video_model_registry import (
      VIDEO_MODELS, IMAGE_MODELS, select_video_model, select_image_model
  )

  # 自动选型（竖屏短剧，有声，5s）
  model = select_video_model(
      has_audio=True,
      duration=5,
      aspect_ratio="9:16",
      mode="T2V",          # T2V / I2V / both
  )
  print(model.model_id)    # doubao-seedance-2-0-260128

  # 按厂商选型
  model = select_video_model(manufacturer="kling", has_audio=False)
"""

from dataclasses import dataclass, field
from typing import Literal

# ─────────────────────────────────────────────────────────────────────────────
# 数据模型
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class VideoModel:
    """视频模型参数"""
    model_id: str
    manufacturer: str                  # volcengine / kling / wan / vidu / gemini / runninghub
    name: str                          # 显示名
    mode: str                          # T2V / I2V / T2V+I2V
    audio: bool                        # 是否有声
    duration_range: tuple[int, int]     # (min, max) 秒
    resolutions: list[str]             # e.g. ["720p", "1080p"]
    aspect_ratios: list[str]           # e.g. ["16:9", "9:16"]
    generation_type: list[str]         # text / singleImage / startEndRequired / endFrameOptional / reference
    i2v_type: str | None               # startEndRequired / endFrameOptional / singleImage / reference
    recommend_for: str                 # 推荐场景
    caveat: str = ""                   # 注意事项
    priority: int = 50                  # 默认优先级（0-100）

    @property
    def supports_audio(self) -> bool:
        return self.audio

    def supports_duration(self, seconds: int) -> bool:
        lo, hi = self.duration_range
        return lo <= seconds <= hi

    def supports_resolution(self, res: str) -> bool:
        return res in self.resolutions

    def supports_aspect_ratio(self, ar: str) -> bool:
        return ar in self.aspect_ratios

    def supports_mode(self, mode: str) -> bool:
        if mode == "both":
            return "T2V" in self.mode and "I2V" in self.mode
        return mode in self.mode


@dataclass
class ImageModel:
    """图片模型参数"""
    model_id: str
    manufacturer: str
    name: str
    mode: str = "img2img"             # img2img / t2i
    sizes: list[str] = field(default_factory=lambda: ["1K", "2K"])
    aspect_ratios: list[str] = field(default_factory=lambda: ["16:9", "9:16", "1:1", "4:3"])
    recommend_for: str = ""
    caveat: str = ""
    watermark_flag: str = "--wm false"  # 水印关闭参数


# ─────────────────────────────────────────────────────────────────────────────
# 模型注册表（与 video-model-registry.md 同步）
# ─────────────────────────────────────────────────────────────────────────────

VIDEO_MODELS: dict[str, VideoModel] = {

    # ── 火山引擎 / 豆包 ───────────────────────────────────────────────────
    "doubao-seedance-2-0-260128": VideoModel(
        model_id="doubao-seedance-2-0-260128",
        manufacturer="volcengine",
        name="Doubao Seedance 2.0 ⭐",
        mode="T2V+I2V",
        audio=True,
        duration_range=(5, 10),
        resolutions=["720p", "1080p"],
        aspect_ratios=["16:9", "9:16", "1:1", "4:3"],
        generation_type=["text", "endFrameOptional"],
        i2v_type="endFrameOptional",
        recommend_for="旗舰首选，T2V+I2V+有声全支持，竖屏短剧最新最强",
        caveat="",
        priority=95,
    ),
    "doubao-seedance-1-5-pro-251215": VideoModel(
        model_id="doubao-seedance-1-5-pro-251215",
        manufacturer="volcengine",
        name="Doubao Seedance 1.5-pro",
        mode="T2V+I2V",
        audio=True,
        duration_range=(4, 12),
        resolutions=["480p", "720p", "1080p"],
        aspect_ratios=["16:9", "4:3", "1:1", "3:4", "9:16", "21:9"],
        generation_type=["text", "endFrameOptional"],
        i2v_type="endFrameOptional",
        recommend_for="高质量有声短剧",
        caveat="",
        priority=80,
    ),
    "doubao-seedance-1-0-pro-250528": VideoModel(
        model_id="doubao-seedance-1-0-pro-250528",
        manufacturer="volcengine",
        name="Doubao Seedance 1.0-pro",
        mode="T2V+I2V",
        audio=False,
        duration_range=(2, 12),
        resolutions=["480p", "720p", "1080p"],
        aspect_ratios=["16:9", "4:3", "1:1", "3:4", "9:16", "21:9"],
        generation_type=["text", "endFrameOptional"],
        i2v_type="endFrameOptional",
        recommend_for="标准短剧，T2V 主力",
        caveat="质量略低于 2.0",
        priority=65,
    ),
    "doubao-seedance-1-0-lite-i2v-250428": VideoModel(
        model_id="doubao-seedance-1-0-lite-i2v-250428",
        manufacturer="volcengine",
        name="Doubao 1.0-lite-i2v",
        mode="I2V",
        audio=False,
        duration_range=(2, 12),
        resolutions=["480p", "720p", "1080p"],
        aspect_ratios=[],   # 继承参考图
        generation_type=["endFrameOptional", "reference"],
        i2v_type="reference",
        recommend_for="写实人物图生视频",
        caveat="仅支持图生视频",
        priority=50,
    ),
    "doubao-seedance-1-0-lite-t2v-250428": VideoModel(
        model_id="doubao-seedance-1-0-lite-t2v-250428",
        manufacturer="volcengine",
        name="Doubao 1.0-lite-t2v",
        mode="T2V",
        audio=False,
        duration_range=(2, 12),
        resolutions=["480p", "720p", "1080p"],
        aspect_ratios=["16:9", "4:3", "1:1", "3:4", "9:16", "21:9"],
        generation_type=["text"],
        i2v_type=None,
        recommend_for="快速 T2V 预览",
        caveat="质量偏低，调试用",
        priority=30,
    ),

    # ── 可灵（Kling）───────────────────────────────────────────────────────
    "kling-v1-std-5s": VideoModel(
        model_id="kling-v1(STD)",
        manufacturer="kling",
        name="Kling O1 STD 5s",
        mode="T2V",
        audio=False,
        duration_range=(5, 5),
        resolutions=["720p"],
        aspect_ratios=["16:9", "1:1", "9:16"],
        generation_type=["text"],
        i2v_type="startEndRequired",
        recommend_for="竖屏短剧日常镜头",
        caveat="",
        priority=70,
    ),
    "kling-v1-std-10s": VideoModel(
        model_id="kling-v1(STD)",
        manufacturer="kling",
        name="Kling O1 STD 10s",
        mode="T2V",
        audio=False,
        duration_range=(10, 10),
        resolutions=["720p"],
        aspect_ratios=["16:9", "1:1", "9:16"],
        generation_type=["text"],
        i2v_type="startEndRequired",
        recommend_for="竖屏短剧长镜头",
        caveat="",
        priority=72,
    ),
    "kling-v1-pro-5s": VideoModel(
        model_id="kling-v1(PRO)",
        manufacturer="kling",
        name="Kling O1 PRO 5s",
        mode="T2V",
        audio=False,
        duration_range=(5, 5),
        resolutions=["1080p"],
        aspect_ratios=["16:9", "1:1", "9:16"],
        generation_type=["text"],
        i2v_type="startEndRequired",
        recommend_for="高质量竖屏精品",
        caveat="",
        priority=82,
    ),
    "kling-v1-pro-10s": VideoModel(
        model_id="kling-v1(PRO)",
        manufacturer="kling",
        name="Kling O1 PRO 10s",
        mode="T2V",
        audio=False,
        duration_range=(10, 10),
        resolutions=["1080p"],
        aspect_ratios=["16:9", "1:1", "9:16"],
        generation_type=["text"],
        i2v_type="startEndRequired",
        recommend_for="高质量竖屏长镜头",
        caveat="",
        priority=85,
    ),
    "kling-v2-6-pro": VideoModel(
        model_id="kling-v2-6(PRO)",
        manufacturer="kling",
        name="Kling v2.6-turbo PRO",
        mode="T2V",
        audio=False,
        duration_range=(5, 10),
        resolutions=["1080p"],
        aspect_ratios=["16:9", "1:1", "9:16"],
        generation_type=["text"],
        i2v_type="startEndRequired",
        recommend_for="v2 最新款，质量最优",
        caveat="成本最高",
        priority=88,
    ),

    # ── 万象（Wan）─────────────────────────────────────────────────────────
    "wan2.6-t2v": VideoModel(
        model_id="wan2.6-t2v",
        manufacturer="wan",
        name="Wan 2.6-t2v",
        mode="T2V",
        audio=True,
        duration_range=(2, 15),
        resolutions=["720p", "1080p"],
        aspect_ratios=["16:9", "9:16", "1:1", "4:3", "3:4"],
        generation_type=["text"],
        i2v_type=None,
        recommend_for="有声短剧首选",
        caveat="",
        priority=78,
    ),
    "wan2.6-i2v-flash": VideoModel(
        model_id="wan2.6-i2v-flash",
        manufacturer="wan",
        name="Wan 2.6-i2v-flash",
        mode="I2V",
        audio=True,
        duration_range=(2, 15),
        resolutions=["720p", "1080p"],
        aspect_ratios=[],   # 继承参考图
        generation_type=["singleImage"],
        i2v_type="singleImage",
        recommend_for="快速图生视频",
        caveat="质量偏低",
        priority=40,
    ),
    "wan2.6-i2v": VideoModel(
        model_id="wan2.6-i2v",
        manufacturer="wan",
        name="Wan 2.6-i2v",
        mode="I2V",
        audio=True,
        duration_range=(2, 15),
        resolutions=["720p", "1080p"],
        aspect_ratios=[],   # 继承参考图
        generation_type=["singleImage"],
        i2v_type="singleImage",
        recommend_for="高质量图生视频",
        caveat="",
        priority=75,
    ),
    "wan2.5-t2v-preview": VideoModel(
        model_id="wan2.5-t2v-preview",
        manufacturer="wan",
        name="Wan 2.5-t2v-preview",
        mode="T2V",
        audio=True,
        duration_range=(5, 10),
        resolutions=["480p", "720p", "1080p"],
        aspect_ratios=["16:9", "9:16", "1:1", "4:3", "3:4"],
        generation_type=["text"],
        i2v_type=None,
        recommend_for="有声预览",
        caveat="较 2.6 旧",
        priority=35,
    ),

    # ── Vidu / Gemini Veo / Sora ────────────────────────────────────────────
    "viduq3-pro": VideoModel(
        model_id="viduq3-pro",
        manufacturer="vidu",
        name="Vidu Q3-pro",
        mode="I2V",
        audio=True,
        duration_range=(1, 16),
        resolutions=["540p", "720p", "1080p"],
        aspect_ratios=[],
        generation_type=["singleImage"],
        i2v_type="singleImage",
        recommend_for="长时长图生视频",
        caveat="仅图生",
        priority=65,
    ),
    "vidu2.0": VideoModel(
        model_id="vidu2.0",
        manufacturer="vidu",
        name="Vidu 2.0",
        mode="I2V",
        audio=False,
        duration_range=(4, 8),
        resolutions=["360p", "720p", "1080p"],
        aspect_ratios=[],
        generation_type=["singleImage", "reference"],
        i2v_type="reference",
        recommend_for="多分辨率兼容",
        caveat="",
        priority=55,
    ),
    "veo-3.1-generate-preview": VideoModel(
        model_id="veo-3.1-generate-preview",
        manufacturer="gemini",
        name="Gemini Veo 3.1",
        mode="T2V+I2V",
        audio=True,
        duration_range=(4, 8),
        resolutions=["720p", "1080p"],
        aspect_ratios=["16:9", "9:16"],
        generation_type=["text", "singleImage", "startEndRequired", "endFrameOptional", "reference"],
        i2v_type="endFrameOptional",
        recommend_for="写实人物，多类型生成",
        caveat="Preview 阶段",
        priority=70,
    ),
    "veo-3.0-generate-preview": VideoModel(
        model_id="veo-3.0-generate-preview",
        manufacturer="gemini",
        name="Gemini Veo 3",
        mode="T2V+I2V",
        audio=True,
        duration_range=(4, 8),
        resolutions=["720p", "1080p"],
        aspect_ratios=["16:9", "9:16"],
        generation_type=["text", "singleImage"],
        i2v_type=None,
        recommend_for="写实人物高质量",
        caveat="质量最高",
        priority=68,
    ),
    "sora-2-pro": VideoModel(
        model_id="sora-2-pro",
        manufacturer="runninghub",
        name="Sora 2 Pro",
        mode="T2V+I2V",
        audio=False,
        duration_range=(15, 25),
        resolutions=[],
        aspect_ratios=["16:9", "9:16"],
        generation_type=["singleImage", "text"],
        i2v_type=None,
        recommend_for="超长镜头",
        caveat="需 RunningHub",
        priority=60,
    ),
}

IMAGE_MODELS: dict[str, ImageModel] = {
    "doubao-seedream-5-0-260128": ImageModel(
        model_id="doubao-seedream-5-0-260128",
        manufacturer="volcengine",
        name="Doubao Seedream 5.0",
        mode="img2img+t2i",
        sizes=["1K", "2K"],
        aspect_ratios=["16:9", "9:16", "1:1", "4:3"],
        recommend_for="资产参考图（角色/场景/道具），主力模型",
        caveat="",
        watermark_flag="--wm false",
    ),
    "doubao-seedream-5-0-lite-260128": ImageModel(
        model_id="doubao-seedream-5-0-lite-260128",
        manufacturer="volcengine",
        name="Doubao Seedream 5.0 Lite",
        mode="img2img+t2i",
        sizes=["1K", "2K"],
        aspect_ratios=["16:9", "9:16", "1:1", "4:3"],
        recommend_for="草稿预览，调试用",
        caveat="质量低于 5.0 正式版",
        watermark_flag="--wm false",
    ),
}


# ─────────────────────────────────────────────────────────────────────────────
# 自动选型
# ─────────────────────────────────────────────────────────────────────────────

def select_video_model(
    has_audio: bool | None = None,
    duration: int | None = None,
    aspect_ratio: str | None = None,
    mode: str = "T2V",
    manufacturer: str | None = None,
    min_duration: int = 1,
    max_duration: int = 30,
    preferred_resolution: str = "1080p",
) -> VideoModel | None:
    """
    根据需求自动选最优视频模型。

    Args:
        has_audio: 是否需要音频
        duration: 目标时长（秒）
        aspect_ratio: 画面比例（16:9 / 9:16 / 1:1）
        mode: T2V / I2V / both
        manufacturer: 指定厂商（volcengine/kling/wan/vidu/gemini/runninghub）
        min_duration: 最小时长
        max_duration: 最大时长
        preferred_resolution: 优先分辨率

    Returns:
        最匹配的 VideoModel 或 None
    """
    candidates = []

    for model in VIDEO_MODELS.values():
        score = 0

        # 厂商过滤
        if manufacturer and model.manufacturer != manufacturer:
            continue

        # 音频过滤
        if has_audio is True and not model.audio:
            continue
        elif has_audio is False and model.audio:
            score -= 20  # 有声但不需要，可以接受但不优先

        # 模式过滤
        if not model.supports_mode(mode) and mode != "both":
            continue

        # 时长过滤
        if duration is not None:
            if not model.supports_duration(duration):
                # 允许±1s 容差
                lo, hi = model.duration_range
                if not (lo - 1 <= duration <= hi + 1):
                    continue
        else:
            lo, hi = model.duration_range
            if hi < min_duration or lo > max_duration:
                continue

        # 画面比例过滤
        if aspect_ratio and not model.supports_aspect_ratio(aspect_ratio):
            continue

        # 基础分：priority
        score += model.priority

        # 加分：精确匹配时长
        if duration is not None:
            lo, hi = model.duration_range
            if lo <= duration <= hi:
                score += 10
            elif abs(duration - lo) <= 1 or abs(duration - hi) <= 1:
                score += 5

        # 加分：支持首选分辨率
        if preferred_resolution in model.resolutions:
            score += 5

        # 加分：需要音频时，有声优先
        if has_audio and model.audio:
            score += 15

        # 扣分：caveat
        if model.caveat:
            score -= 5

        candidates.append((score, model))

    if not candidates:
        return None

    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]


def select_image_model(
    manufacturer: str = "volcengine",
    use_lite: bool = False,
) -> ImageModel:
    """选图片模型"""
    if manufacturer == "volcengine":
        key = "doubao-seedream-5-0-lite-260128" if use_lite else "doubao-seedream-5-0-260128"
        return IMAGE_MODELS[key]
    return IMAGE_MODELS["doubao-seedream-5-0-260128"]


# ─────────────────────────────────────────────────────────────────────────────
# 速查表（快速参考）
# ─────────────────────────────────────────────────────────────────────────────

RECOMMENDATIONS = {
    "竖屏短剧_有声": "doubao-seedance-2-0-260128",
    "竖屏短剧_无声_高质量": "kling-v1-pro-10s",
    "竖屏短剧_无声_标准": "kling-v2-6-pro",
    "人物特写_写实": "veo-3.1-generate-preview",
    "产品特写": "doubao-seedance-2-0-260128",
    "快速预览": "doubao-seedance-1-0-lite-t2v-250428",
    "超长镜头_15s+": "sora-2-pro",
    "横屏短剧_B站": "doubao-seedance-2-0-260128",
}


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def _cli():
    import argparse
    parser = argparse.ArgumentParser(description="视频模型注册表")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # list
    p_list = sub.add_parser("list", help="列出所有模型")
    p_list.add_argument("--type", choices=["video", "image"], default="video")
    p_list.add_argument("--manufacturer", help="按厂商过滤")

    # select
    p_sel = sub.add_parser("select", help="自动选型")
    p_sel.add_argument("--audio", action="store_true", help="需要音频")
    p_sel.add_argument("--no-audio", dest="audio", action="store_false", help="无声")
    p_sel.add_argument("--duration", type=int, help="时长（秒）")
    p_sel.add_argument("--aspect", default="9:16", help="画面比例")
    p_sel.add_argument("--mode", default="T2V", help="T2V / I2V / both")
    p_sel.add_argument("--manufacturer", help="指定厂商")

    # recommend
    p_rec = sub.add_parser("recommend", help="速查表推荐")
    p_rec.add_argument("scenario", nargs="?", choices=list(RECOMMENDATIONS.keys()))

    args = parser.parse_args()

    if args.cmd == "list":
        models = VIDEO_MODELS if args.type == "video" else IMAGE_MODELS
        for m in models.values():
            if args.manufacturer and m.manufacturer != args.manufacturer:
                continue
            audio_str = "🔊" if m.audio else "🔇" if hasattr(m, 'audio') else ""
            print(f"[{m.manufacturer}] {m.model_id} | {m.name} | {audio_str}")
            print(f"  推荐：{m.recommend_for}")
            if m.caveat:
                print(f"  注意：{m.caveat}")
            print()

    elif args.cmd == "select":
        model = select_video_model(
            has_audio=args.audio if "audio" in args else None,
            duration=args.duration,
            aspect_ratio=args.aspect,
            mode=args.mode,
            manufacturer=args.manufacturer,
        )
        if model:
            print(f"✅ 推荐：{model.name}")
            print(f"   model_id:   {model.model_id}")
            print(f"   manufacturer: {model.manufacturer}")
            print(f"   理由：{model.recommend_for}")
            if model.caveat:
                print(f"   注意：{model.caveat}")
        else:
            print("❌ 未找到匹配模型")

    elif args.cmd == "recommend":
        if args.scenario:
            key = RECOMMENDATIONS[args.scenario]
            model = VIDEO_MODELS.get(key)
            print(f"场景：{args.scenario}")
            print(f"推荐：{model.name if model else key}")
        else:
            print("可用场景：")
            for scene, mid in RECOMMENDATIONS.items():
                print(f"  {scene} → {mid}")


if __name__ == "__main__":
    _cli()
