"""agent-im OpenAPI 公共模块：创建会话、查询会话（鉴权为 Authorization: Bearer <access_key>）"""

import json
import os
import sys
import urllib.request
import urllib.error

# 默认 im 环境
IM_BASE = os.environ.get("OPENAPI_IM_BASE", os.environ.get("IM_BASE_URL", "https://im.liblib.tv"))
ACCESS_KEY = os.environ.get("LIBTV_ACCESS_KEY", "")

# 项目画布地址前缀，拼上 projectId 即项目地址
PROJECT_CANVAS_BASE = "https://www.liblib.tv/canvas?projectId="


def build_project_url(project_id: str) -> str:
    """根据 projectId（即 projectUuid）拼接项目画布地址"""
    if not project_id:
        return ""
    return PROJECT_CANVAS_BASE + project_id.strip()

if not ACCESS_KEY:
    print("错误：请设置 LIBTV_ACCESS_KEY 环境变量", file=sys.stderr)
    sys.exit(1)


def _headers():
    return {
        "Authorization": f"Bearer {ACCESS_KEY}",
        "Content-Type": "application/json",
    }


def api_post(path: str, body: dict) -> dict:
    """POST 请求 agent-im OpenAPI"""
    url = f"{IM_BASE.rstrip('/')}{path}"
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST", headers=_headers())
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8") if e.fp else ""
        print(f"API 错误 {e.code}: {err_body}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"网络错误: {e.reason}", file=sys.stderr)
        sys.exit(1)


def api_get(path: str) -> dict:
    """GET 请求 agent-im OpenAPI"""
    url = f"{IM_BASE.rstrip('/')}{path}"
    req = urllib.request.Request(url, method="GET", headers=_headers())
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8") if e.fp else ""
        print(f"API 错误 {e.code}: {err_body}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"网络错误: {e.reason}", file=sys.stderr)
        sys.exit(1)


def create_session(session_id: str = "", message: str = "") -> dict:
    body = {}
    if session_id:
        body["sessionId"] = session_id
    if message:
        body["message"] = message
    resp = api_post("/openapi/session", body)
    return resp.get("data", {})


def query_session(session_id: str, after_seq: int = 0) -> dict:
    path = f"/openapi/session/{session_id}"
    if after_seq > 0:
        path += f"?afterSeq={after_seq}"
    resp = api_get(path)
    return resp.get("data", {})


def change_project() -> dict:
    resp = api_post("/openapi/session/change-project", {})
    return resp.get("data", {})


# ══════════════════════════════════════════════════════════════════════════════
# 结构化消息生成器 · 两阶段资产创建
#
# 生图模型：nanobanana（固定）
#
# 阶段一（锚点建立）：
#   character_front_view → 角色正面白底图 → 拿到 element_id
#   scene_establishing  → 场景全景图     → 拿到 element_id
#
# 阶段二（一致性多角度）：
#   character_sheet     → 基于 element_id，生成多角度 Character Sheet
#   scene_sheet         → 基于 element_id，生成多角度 Scene Sheet
#
# 其他任务类型：
#   storyboard_image_batch  分镜批量出图
#   storyboard_video_batch  分镜批量视频
#   image_to_video         图生视频
# ══════════════════════════════════════════════════════════════════════════════

# nanobanana 生图固定锚点标签
NANOBANANA_TAIL = "masterpiece, best quality, highly detailed, sharp focus"


def generate_structured_message(spec: dict) -> str:
    """把 JSON spec 转成 LibTV 后端可解析的结构化自然语言消息。"""
    task_type = spec.get("task_type", "unknown")
    dispatch = {
        "character_front_view": _gen_character_front_view,
        "character_sheet":      _gen_character_sheet,
        "scene_establishing":   _gen_scene_establishing,
        "scene_sheet":          _gen_scene_sheet,
        "storyboard_image_batch": _gen_storyboard_image,
        "storyboard_video_batch": _gen_storyboard_video,
        "image_to_video":        _gen_image_to_video,
    }
    fn = dispatch.get(task_type)
    if fn:
        return fn(spec)
    return f"【任务类型】{task_type}\n【项目】{spec.get('project', {}).get('name', '')}"


# ─────────────────────────────────────────────────────────────────────────────
# Phase 1：角色正面图（锚点）
# ─────────────────────────────────────────────────────────────────────────────

def _gen_character_front_view(spec: dict) -> str:
    lines = [
        "【任务类型】角色正面图 · 主体锚点建立",
        f"【项目名称】{spec['project']['name']}",
        "【生图模型】nanobanana（固定）",
        "",
    ]
    for char in spec.get("characters", []):
        lines += [
            f"【角色】{char['id']} {char['name']}",
            "nanobanana style, anime illustration, flat shading, clean lineart,",
            f"{char['description']},",
            "front view, full body, neutral expression, standing upright,",
            "simple white background,",
            "masterpiece, best quality, highly detailed, sharp focus",
            "",
            "⚠️ 必出：正面全身无表情图，作为后续多角度 Character Sheet 的主体锚点",
            "⚠️ 重要：此图人物为后续所有变体的唯一基准，禁止改变脸型/发型/服装",
            "",
        ]
    if spec.get("notes"):
        lines.append(f"【备注】{spec['notes']}")
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# Phase 2：角色多角度一致性大图（Character Sheet）
# ─────────────────────────────────────────────────────────────────────────────

def _gen_character_sheet(spec: dict) -> str:
    lines = [
        "【任务类型】角色多角度一致性图 · Character Sheet",
        f"【项目名称】{spec['project']['name']}",
        "【生图模型】nanobanana（固定）",
        "【核心原则】②③部分固定不变，只改④变量；所有子图必须与正面锚点人物完全一致",
        "【锚点使用】使用角色正面锚点图（element_id: 见各角色标注）保持脸型/发型/服装一致",
        "【重要提示】可加 LoRA 权重进一步锁定脸型",
        "",
    ]
    for char in spec.get("characters", []):
        anchor_eid = char.get("element_id", "待填入（Phase1完成后填入）")
        views = char.get("views", [])

        lines += [
            f"── 角色 {char['id']} {char['name']} ──",
            f"【锚点 element_id】{anchor_eid}",
            "",
            "① 风格锚点（固定）：",
            "nanobanana style, anime illustration, flat shading, clean lineart,",
            "",
            "② 人物核心外貌（固定不变）：",
        ]
        for tag in char.get("appearance_tags", []):
            lines.append(f"  {tag},")
        lines.append("  same face, consistent character design,")
        lines.append("")
        lines.append("③ 服装装备（固定不变）：")
        for tag in char.get("outfit_tags", []):
            lines.append(f"  {tag},")
        lines.append("  same outfit,")
        lines.append("")
        lines.append("④ 镜头变量（每个子图只改这里）：")
        for v in views:
            lines += [
                "",
                f"  ── {v['view_id']}: {v['label']} ──",
                f"    view_angle: {v['view_angle']}",
                f"    shot_type: {v['shot_type']}",
                f"    expression: {v['expression']}",
                f"    pose: {v['pose']}",
                f"    background: {v.get('background', 'simple white background')}",
                f"    合成完整提示词：",
                f"      nanobanana style, anime illustration, flat shading, clean lineart,",
            ]
            for tag in char.get("appearance_tags", []):
                lines.append(f"      {tag},")
            for tag in char.get("outfit_tags", []):
                lines.append(f"      {tag},")
            lines.append("      same face, same outfit,")
            lines.append(
                f"      {v['view_angle']}, {v['shot_type']}, {v['expression']}, {v['pose']},"
            )
            lines.append(f"      {v.get('background', 'simple white background')},")
            lines.append("      masterpiece, best quality, highly detailed, sharp focus")
        lines.append("")
        lines.append("⚠️ 重要：所有子图必须保持人物脸型、服装、发型完全一致")
        lines.append("")
    if spec.get("notes"):
        lines.append(f"【备注】{spec['notes']}")
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# Phase 1：场景全景图（锚点）
# ─────────────────────────────────────────────────────────────────────────────

def _gen_scene_establishing(spec: dict) -> str:
    lines = [
        "【任务类型】场景全景图 · 主体锚点建立",
        f"【项目名称】{spec['project']['name']}",
        "【生图模型】nanobanana（固定）",
        "",
    ]
    for scene in spec.get("scenes", []):
        lines += [
            f"【场景】{scene['id']} {scene['name']}",
            "nanobanana style, anime illustration,",
            f"{scene['description']},",
            "wide establishing shot, eye-level,",
            f"{scene.get('lighting', '')},",
            "no characters,",
            "masterpiece, best quality, highly detailed, sharp focus",
            "",
            "⚠️ 必出：全景图，作为后续多角度 Scene Sheet 的场景锚点",
            "⚠️ 重要：此图为后续所有子图的唯一基准，禁止改变场景布局/色调/道具陈设",
            "",
        ]
    if spec.get("notes"):
        lines.append(f"【备注】{spec['notes']}")
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# Phase 2：场景多角度一致性大图（Scene Sheet）
# ─────────────────────────────────────────────────────────────────────────────

def _gen_scene_sheet(spec: dict) -> str:
    lines = [
        "【任务类型】场景多角度一致性图 · Scene Sheet",
        f"【项目名称】{spec['project']['name']}",
        "【生图模型】nanobanana（固定）",
        "【核心原则】②③部分固定不变，只改④⑤变量；所有子图必须与全景锚点场景完全一致",
        "【锚点使用】使用场景全景锚点图（element_id: 见各场景标注）保持布局/色调/道具一致",
        "",
    ]
    for scene in spec.get("scenes", []):
        anchor_eid = scene.get("element_id", "待填入（Phase1完成后填入）")
        views = scene.get("views", [])

        lines += [
            f"── 场景 {scene['id']} {scene['name']} ──",
            f"【锚点 element_id】{anchor_eid}",
            "",
            "① 风格锚点（固定）：",
            "nanobanana style, cinematic illustration, detailed interior, atmospheric lighting,",
            "",
            "② 场景类型定义（固定不变）：",
        ]
        for tag in scene.get("scene_type_tags", []):
            lines.append(f"  {tag},")
        lines.append("  consistent environment, same room, same layout,")
        lines.append("")
        lines.append("③ 固定道具与陈设（固定不变）：")
        for tag in scene.get("props_tags", []):
            lines.append(f"  {tag},")
        lines.append("  same props, same furniture arrangement,")
        lines.append("")
        lines.append("④ 镜头变量（每个子图只改这里）：")
        for v in views:
            lines += [
                "",
                f"  ── {v['view_id']}: {v['label']} ──",
                f"    shot_type: {v['shot_type']}",
                f"    camera_angle: {v['camera_angle']}",
                f"    focus_subject: {v.get('focus_subject', 'the scene')}",
                f"    lighting: {v['lighting']}",
                f"    time_of_day: {v['time_of_day']}",
                f"    atmosphere: {v.get('atmosphere', 'dramatic shadows, volumetric light rays')}",
                f"    character_handling: {v.get('character_handling', 'no characters')}",
                f"    合成完整提示词：",
                f"      nanobanana style, cinematic illustration, detailed interior, atmospheric lighting,",
            ]
            for tag in scene.get("scene_type_tags", []):
                lines.append(f"      {tag},")
            for tag in scene.get("props_tags", []):
                lines.append(f"      {tag},")
            lines.append("      same props, same furniture arrangement,")
            lines.append(
                f"      {v['shot_type']}, {v['camera_angle']}, "
                f"focusing on {v.get('focus_subject', 'the scene')},"
            )
            lines.append(
                f"      {v['lighting']}, {v['time_of_day']}, "
                f"{v.get('atmosphere', 'dramatic shadows, volumetric light rays')},"
            )
            lines.append(f"      {v.get('character_handling', 'no characters')},")
            lines.append("      masterpiece, best quality, highly detailed, sharp focus, rich textures")
        lines.append("")
        lines.append("⚠️ 重要：所有子图必须保持场景布局、道具陈设、光线色调完全一致")
        lines.append("")
    if spec.get("notes"):
        lines.append(f"【备注】{spec['notes']}")
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# 分镜批量出图
# ─────────────────────────────────────────────────────────────────────────────

def _gen_storyboard_image(spec: dict) -> str:
    lines = ["【任务类型】分镜批量出图"]
    p = spec.get("project", {})
    if p.get("name"):
        lines.append(f"【项目名称】{p['name']}")
    if spec.get("visual_style"):
        lines.append(f"【视觉风格】{spec['visual_style']}")
    cfg = spec.get("video_config", {})
    if cfg.get("aspect_ratio"):
        lines.append(f"【画面比例】{cfg['aspect_ratio']}")

    chars = spec.get("characters", [])
    if chars:
        lines.append("")
        lines.append("【角色主体库】")
        for c in chars:
            eid = f"（element_id: {c['element_id']}）" if c.get("element_id") else ""
            lines.append(f"  {c['id']} {c['name']}{eid}")

    scenes = spec.get("scenes", [])
    if scenes:
        lines.append("")
        lines.append("【场景参考库】")
        for s in scenes:
            eid = f"（element_id: {s['element_id']}）" if s.get("element_id") else ""
            lines.append(f"  {s['id']} {s['name']}{eid}")

    shots = spec.get("shots", [])
    if shots:
        lines.append("")
        lines.append("【分镜列表】")
        for shot in shots:
            cr = f" | 主体：{shot['character']}" if shot.get("character") else ""
            sr = f" | 场景：{shot['scene']}" if shot.get("scene") else ""
            lines.append(
                f"  镜头{shot['number']:02d} | {shot.get('shot_type', '')} | "
                f"{shot.get('camera_movement', '')} | {shot.get('duration', '')}s | "
                f"{shot.get('description', '')}{cr}{sr}"
            )
            if shot.get("dialogue"):
                lines.append(f"    台词：{shot['dialogue']}")
    if spec.get("notes"):
        lines.append(f"【备注】{spec['notes']}")
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# 分镜批量视频生成
# ─────────────────────────────────────────────────────────────────────────────

def _gen_storyboard_video(spec: dict) -> str:
    lines = ["【任务类型】分镜批量视频生成"]
    p = spec.get("project", {})
    if p.get("name"):
        lines.append(f"【项目名称】{p['name']}")
        lines.append(f"【总时长】约{p.get('total_duration', '')}秒")
    cfg = spec.get("video_config", {})
    lines.append(f"【视频模型】{cfg.get('model', 'Kling O1')}")
    lines.append(f"【画面比例】{cfg.get('aspect_ratio', '16:9')}")
    lines.append(f"【单镜头时长】{cfg.get('shot_duration_range', [3, 5])}秒")

    chars = spec.get("characters", [])
    if chars:
        lines.append("")
        lines.append("【角色主体库】")
        for c in chars:
            vr = f"（变体：{', '.join(c['variants'])}）" if c.get("variants") else ""
            lines.append(
                f"  {c['id']} {c['name']} | element_id: {c.get('element_id', '')}{vr}"
            )

    scenes = spec.get("scenes", [])
    if scenes:
        lines.append("")
        lines.append("【场景参考库】")
        for s in scenes:
            lines.append(f"  {s['id']} {s['name']} | element_id: {s.get('element_id', '')}")

    shots = spec.get("shots", [])
    if shots:
        lines.append("")
        lines.append("【分镜脚本（逐镜头视频生成）】")
        for shot in shots:
            cr = f" | 主体：{shot['character']}" if shot.get("character") else ""
            sr = f" | 场景：{shot['scene']}" if shot.get("scene") else ""
            lines += [
                "",
                f"  镜头{shot['number']:02d}（{shot.get('timecode', '')}）",
                f"  | {shot.get('shot_type', '')} | {shot.get('camera_movement', '')}",
                f"  | 时长：{shot.get('duration', '')}s",
                f"    画面：{shot.get('description', '')}",
            ]
            if shot.get("dialogue"):
                lines.append(f"    台词：{shot['dialogue']}")
            if shot.get("sound_effect"):
                lines.append(f"    音效：{shot['sound_effect']}")

    ts = spec.get("transitions", [])
    if ts:
        lines.append("")
        lines.append("【转场说明】")
        for t in ts:
            lines.append(f"  {t.get('after_shot', '')} → {t.get('effect', '')}")
    if spec.get("notes"):
        lines.append(f"【备注】{spec['notes']}")
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# 图生视频
# ─────────────────────────────────────────────────────────────────────────────

def _gen_image_to_video(spec: dict) -> str:
    lines = ["【任务类型】图生视频"]
    for shot in spec.get("shots", []):
        lines += [
            "",
            f"  镜头{shot['number']:02d}（{shot.get('timecode', '')}）| 时长：{shot.get('duration', '')}s",
            f"    运镜：{shot.get('camera_movement', '')}",
            f"    画面：{shot.get('description', '')}",
        ]
        if shot.get("reference_image_url"):
            lines.append(f"    参考图：{shot['reference_image_url']}")
    return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════════════
# JSON Schema 参考（供 huage888 生成器使用）
# ══════════════════════════════════════════════════════════════════════════════

JSON_SCHEMA = """
# LibTV 结构化任务 JSON Schema v3（两阶段资产创建 + nanobanana）

═══════════════════════════════════════════════════════════════════════════════
task_type 总览
═══════════════════════════════════════════════════════════════════════════════
character_front_view  Phase1：角色正面白底图（建立主体 element_id）
character_sheet       Phase2：基于正面锚点，生成多角度 Character Sheet
scene_establishing    Phase1：场景全景图（建立场景 element_id）
scene_sheet           Phase2：基于全景锚点，生成多角度 Scene Sheet
storyboard_image_batch  分镜批量出图
storyboard_video_batch  分镜批量视频
image_to_video          图生视频

═══════════════════════════════════════════════════════════════════════════════
Phase 1 → Phase 2 流水线（必须按顺序执行）
═══════════════════════════════════════════════════════════════════════════════
  Step 1: character_front_view → 返回 element_id → 填入 character_sheet
  Step 2: character_sheet（引用 element_id）→ 多角度参考图

  Step 3: scene_establishing   → 返回 element_id → 填入 scene_sheet
  Step 4: scene_sheet（引用 element_id）→ 多角度参考图

═══════════════════════════════════════════════════════════════════════════════
character_sheet 完整字段
═══════════════════════════════════════════════════════════════════════════════
{
  "task_type": "character_sheet",
  "project": {"name": "漠玫传 S01E01"},
  "characters": [{
    "id": "C001",
    "name": "漠玫",
    "element_id": "elem_momo_front_001",
    "appearance_tags": [
      "乌黑长发盘成现代感道姑髻",
      "鹅蛋脸，清冷古典感",
      "金色瞳孔数据流缓缓游动",
      "细长眉，眉峰柔和"
    ],
    "outfit_tags": [
      "宽松黑色科技丝绒长袍，绣银灰山峦纹样",
      "白色云头绣鞋"
    ],
    "views": [
      {
        "view_id": "正-3/4侧",
        "label": "3/4侧脸无表情",
        "view_angle": "3/4 view",
        "shot_type": "full body",
        "expression": "neutral expression",
        "pose": "standing upright",
        "background": "simple white background"
      },
      {
        "view_id": "正-侧面",
        "label": "纯侧面无表情",
        "view_angle": "side view",
        "shot_type": "full body",
        "expression": "neutral expression",
        "pose": "standing upright",
        "background": "simple white background"
      }
    ]
  }]
}

═══════════════════════════════════════════════════════════════════════════════
scene_sheet 完整字段
═══════════════════════════════════════════════════════════════════════════════
{
  "task_type": "scene_sheet",
  "project": {"name": "漠玫传 S01E01"},
  "scenes": [{
    "id": "S001",
    "name": "数字西湖断桥·雷雨夜",
    "element_id": "elem_scene_s001_001",
    "description": "数字西湖断桥，雷雨夜，霓虹穿透雨幕，断桥积满雨水",
    "lighting": "冷白漫反射",
    "scene_type_tags": [
      "ancient Chinese bridge, digital cyberpunk lake",
      "consistent environment, same scene"
    ],
    "props_tags": [
      "白色石栏杆，青石板桥面",
      "西湖水面，倒映数据塔流光",
      "断桥石拱"
    ],
    "views": [
      {
        "view_id": "全景-俯拍",
        "label": "断桥全景俯拍",
        "shot_type": "wide establishing shot",
        "camera_angle": "high angle",
        "focus_subject": "the full bridge",
        "lighting": "冷白漫反射",
        "time_of_day": "night, rain",
        "atmosphere": "dramatic shadows, volumetric light rays",
        "character_handling": "no characters"
      },
      {
        "view_id": "中景-桥墩",
        "label": "桥墩附近中景",
        "shot_type": "medium shot",
        "camera_angle": "eye-level",
        "focus_subject": "the bridge pier and water",
        "lighting": "冷白漫反射",
        "time_of_day": "night, rain",
        "atmosphere": "wet stone reflections",
        "character_handling": "no characters"
      }
    ]
  }]
}
"""
