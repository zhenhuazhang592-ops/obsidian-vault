"""
ai-drama-studio/backend/pipeline/shot_validator.py

分镜脚本强制执行引擎
版本: 1.0.0
依据: manzhou-shot-script.md v6.2 (2026-03-25)
职责: 对分镜脚本进行5类强制校验，输出ValidationResult
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

# ─────────────────────────────────────────────────────────────────────────────
# 数据结构：校验结果
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class ValidationWarning:
    """可修复的警告（不影响通过，但建议修正）"""
    shot_id: str
    code: str                       # 如 "AUTO_FIXED"
    message: str


@dataclass
class ValidationError:
    """不可自动修复的错误（需要人工/LLM修正）"""
    shot_id: str
    code: str                       # 如 "SHOT_AXIS_VIOLATION"
    message: str
    severity: str = "error"         # error | critical


@dataclass
class ValidationResult:
    """
    校验结果聚合
    valid: True 当且仅当 errors 列表为空
    auto_fixes: (shot_id, description) 元组列表，记录所有自动修复
    """
    valid: bool
    warnings: list[ValidationWarning] = field(default_factory=list)
    errors: list[ValidationError] = field(default_factory=list)
    auto_fixes: list[tuple[str, str]] = field(default_factory=list)

    def summary(self) -> str:
        if self.valid:
            lines = [f"✅ 校验通过 ({len(self.warnings)} 个警告)"]
        else:
            lines = [f"❌ 校验失败 ({len(self.errors)} 个错误, {len(self.warnings)} 个警告)"]
        for e in self.errors:
            lines.append(f"  [{e.shot_id}] {e.code}: {e.message}")
        for w in self.warnings:
            lines.append(f"  ⚠ [{w.shot_id}] {w.code}: {w.message}")
        for shot_id, desc in self.auto_fixes:
            lines.append(f"  🔧 [{shot_id}] 已自动修复: {desc}")
        return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# 错误类型定义
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class ShotAxisError(ValidationError):
    """
    180度轴线违规
    相邻对话镜头不得跨越180度轴线。
    A→B→A切换时，必须用OTS/WS过渡，禁止直接切正反打。
    """
    code: str = ""                      # override: no-default → with default
    message: str = ""                   # override: no-default → with default
    expected_yaw_range: tuple[float, float] = (0.0, 180.0)
    actual_yaw: float = 0.0

    def __post_init__(self):
        if not self.code:
            self.code = "SHOT_AXIS_VIOLATION"
        self.severity = "critical"


@dataclass
class DialogueShotError(ValidationError):
    """
    对话镜头类型违规（force_medium_shot）
    对话镜头只允许: MCU / MS / OTS
    禁止: WS / ECU / 2S
    """
    code: str = ""
    message: str = ""
    actual_type: str = ""
    allowed_types: tuple = ("MCU", "MS", "OTS")

    def __post_init__(self):
        if not self.code:
            self.code = "DIALOGUE_SHOT_TYPE_VIOLATION"
        self.severity = "error"


@dataclass
class ShotDurationError(ValidationError):
    """
    镜头时长超限
    校验各景别类型的时长区间。
    """
    code: str = ""
    message: str = ""
    actual_duration: float = 0.0
    min_duration: float = 0.0
    max_duration: float = 0.0

    def __post_init__(self):
        if not self.code:
            self.code = "SHOT_DURATION_OUT_OF_RANGE"
        self.severity = "error"


@dataclass
class LipSyncGradeError(ValidationError):
    """
    Lip-sync质量分级不达标
    S级: ≤8字, slow语速, 正面, 无遮挡
    A级: ≤15字, slow/normal语速, 正面或±15°侧脸
    B级: 15-20字, normal语速, 轻微遮挡
    C级: >20字 或 侧面/遮挡 → 强制 [voice-over]
    """
    code: str = ""
    message: str = ""
    grade: str = "C"
    issue: str = ""

    def __post_init__(self):
        if not self.code:
            self.code = "LIPSYNC_QUALITY_INSUFFICIENT"
        self.severity = "warning"


@dataclass
class CharacterMarkerError(ValidationError):
    """
    【【】】角色标记违规
    - 每个镜头最多1个【【】】标记（避免多角色同一镜头）
    - 每个镜头必须出现【【】】标记
    """
    code: str = ""
    message: str = ""
    marker_count: int = 0
    issue: str = ""                  # "missing" | "multiple"

    def __post_init__(self):
        if not self.code:
            self.code = "CHARACTER_MARKER_VIOLATION"
        self.severity = "warning"


# ─────────────────────────────────────────────────────────────────────────────
# 常量定义
# ─────────────────────────────────────────────────────────────────────────────

# 景别类型集合
SHOT_TYPES = frozenset({"ECU", "CU", "MCU", "MS", "WS", "OTS", "2S", "POV", "EMPTY"})

# 允许的对话镜头景别
ALLOWED_DIALOGUE_SHOT_TYPES = frozenset({"MCU", "MS", "OTS"})

# 禁止用于对话的景别
FORBIDDEN_DIALOGUE_SHOT_TYPES = frozenset({"WS", "ECU", "2S"})

# 镜头时长区间表 (min, standard, max)
DURATION_RANGES: dict[str, tuple[float, float, float]] = {
    "ECU":   (2.0, 3.0, 5.0),
    "CU":    (2.0, 4.0, 6.0),
    "MCU":   (3.0, 5.0, 8.0),
    "MS":    (4.0, 6.0, 12.0),
    "WS":    (5.0, 8.0, 12.0),
    "OTS":   (3.0, 6.0, 10.0),
    "POV":   (2.0, 4.0, 8.0),
    "EMPTY": (2.0, 3.0, 5.0),
    "2S":    (4.0, 6.0, 10.0),
}

# Lip-sync质量分级阈值
LIPSYNC_THRESHOLDS = {
    "S": {"max_chars": 8,  "speeds": ("slow",),     "max_angle": 0,  "obstruction": False},
    "A": {"max_chars": 15, "speeds": ("slow", "normal"), "max_angle": 15, "obstruction": False},
    "B": {"max_chars": 20, "speeds": ("slow", "normal", "fast"), "max_angle": 30, "obstruction": True},
}

# 【【】】标记正则
CHARACTER_MARKER_PATTERN = re.compile(r"【【([^】]+)】】")


# ─────────────────────────────────────────────────────────────────────────────
# 工具函数
# ─────────────────────────────────────────────────────────────────────────────

def _is_dialogue_shot(shot: dict) -> bool:
    """
    判断镜头是否为对话场景。
    标准：台词非空（str非空 或 dialogue列表非空）OR is_dialogue_scene=True
    """
    if shot.get("is_dialogue_scene") is True:
        return True
    dialogue = shot.get("dialogue", "")
    if isinstance(dialogue, str):
        return bool(dialogue.strip())
    if isinstance(dialogue, list):
        return any(_dialogue_item_nonempty(item) for item in dialogue)
    return False


def _dialogue_item_nonempty(item) -> bool:
    """判断单个dialogue项是否非空"""
    if isinstance(item, dict):
        return bool(str(item.get("text", "")).strip())
    return bool(str(item).strip())


def _get_dialogue_text(shot: dict) -> str:
    """提取台词文本（合并所有说话者）"""
    dialogue = shot.get("dialogue", "")
    if isinstance(dialogue, str):
        return dialogue.strip()
    if isinstance(dialogue, list):
        parts = []
        for item in dialogue:
            if isinstance(item, dict):
                t = str(item.get("text", "")).strip()
            else:
                t = str(item).strip()
            if t:
                parts.append(t)
        return "".join(parts)
    return ""


def _count_chars(dialogue_text: str) -> int:
    """计算台词字符数（中文+英文+数字，空格不计入）"""
    return len(re.sub(r"\s+", "", dialogue_text))


def _get_speakers(shot: dict) -> list[str]:
    """从dialogue字段提取所有speaker ID"""
    dialogue = shot.get("dialogue", [])
    if isinstance(dialogue, str):
        return []
    if isinstance(dialogue, list):
        speakers = []
        for item in dialogue:
            if isinstance(item, dict):
                s = item.get("speaker", "").strip()
            else:
                s = str(item).strip() if isinstance(item, str) else ""
            if s:
                speakers.append(s)
        return speakers
    return []


def _extract_character_markers(text: str) -> list[str]:
    """从文本中提取所有【【角色名】】标记"""
    return CHARACTER_MARKER_PATTERN.findall(text)


def _extract_markers_from_shot(shot: dict) -> list[str]:
    """
    从镜头各文本字段提取【【】】标记。
    检查字段：script / dialogue / imagePrompt / videoPrompt / character_markers
    """
    markers: set[str] = set()

    for field_name in ("script", "dialogue", "imagePrompt", "videoPrompt"):
        val = shot.get(field_name, "")
        if isinstance(val, str):
            markers.update(_extract_character_markers(val))
        elif isinstance(val, list):
            for item in val:
                if isinstance(item, dict):
                    t = str(item.get("text", "")).strip()
                    if t:
                        markers.update(_extract_character_markers(t))
                else:
                    markers.update(_extract_character_markers(str(item)))

    # character_markers 字段（直接列表）
    direct = shot.get("character_markers", [])
    if isinstance(direct, list):
        for m in direct:
            # 提取 【【xxx】】 中的内容
            extracted = _extract_character_markers(str(m))
            if extracted:
                markers.update(extracted)
            else:
                # 直接是角色名（无标记包裹）
                markers.add(str(m).strip())

    return list(markers)


def _yaw_side(yaw: float) -> int:
    """
    返回yaw所在的轴线侧。
    0°-180° (含) → 返回 1（轴线一侧）
    180°-360° → 返回 -1（轴线另一侧）
    """
    normalized = yaw % 360.0
    return 1 if normalized <= 180.0 else -1


def _calc_lipsync_grade(shot: dict) -> tuple[str, str]:
    """
    计算Lip-sync质量等级。
    返回 (grade, issue)
    """
    dialogue_text = _get_dialogue_text(shot)
    char_count = _count_chars(dialogue_text)

    if char_count == 0:
        return "S", "无台词，无需Lip-sync"

    speed = str(shot.get("speed", "normal")).lower()
    yaw = shot.get("yaw", 0.0)
    abs_angle = abs(yaw) % 360.0
    if abs_angle > 180.0:
        abs_angle = 360.0 - abs_angle  # 取最近侧的角度
    has_obstruction = shot.get("has_obstruction", False)

    # 判断等级
    s = LIPSYNC_THRESHOLDS["S"]
    a = LIPSYNC_THRESHOLDS["A"]
    b = LIPSYNC_THRESHOLDS["B"]

    if (char_count <= s["max_chars"]
            and speed in s["speeds"]
            and abs_angle <= s["max_angle"]
            and not has_obstruction):
        return "S", "达标"

    if (char_count <= a["max_chars"]
            and speed in a["speeds"]
            and abs_angle <= a["max_angle"]
            and not has_obstruction):
        return "A", "达标"

    if (char_count <= b["max_chars"]
            and abs_angle <= b["max_angle"]
            and has_obstruction is False):
        return "B", "轻微遮挡或语速较快"

    # C级
    issues = []
    if char_count > 20:
        issues.append(f"台词过长({char_count}字)")
    if abs_angle > 30:
        issues.append(f"机位侧偏({abs_angle}°)")
    if has_obstruction:
        issues.append("存在遮挡")
    if speed == "fast":
        issues.append("语速fast")

    return "C", "; ".join(issues) if issues else "综合质量不足"


# ─────────────────────────────────────────────────────────────────────────────
# 核心校验函数（批量）
# ─────────────────────────────────────────────────────────────────────────────


def check_180_axis(shots: list[dict]) -> list[ShotAxisError]:
    """
    180度轴线批量校验。
    规则：
    1. 相邻对话镜头若在轴线两侧（yaw侧异号），判定越轴
    2. 连续A→B→A正反打，中间无OTS/WS过渡 → 越轴
    两人对话中，正反打（OTS-A / OTS-B / OTS-A）若直接切换无过渡也视为越轴。
    """
    errors: list[ShotAxisError] = []

    # 收集所有对话镜头索引
    dialogue_indices = [
        (i, shots[i]) for i in range(len(shots))
        if _is_dialogue_shot(shots[i]) and "yaw" in shots[i]
    ]

    for idx, (i, shot_i) in enumerate(dialogue_indices[:-1]):
        j, shot_j = dialogue_indices[idx + 1]
        yaw_i = shot_i.get("yaw", 0.0)
        yaw_j = shot_j.get("yaw", 0.0)

        side_i = _yaw_side(yaw_i)
        side_j = _yaw_side(yaw_j)

        if side_i != side_j:
            # 跨轴：检查中间是否有过渡镜头
            between = shots[i + 1:j]  # 可能为空
            has_transition = any(
                _shot_type_allows_axis_transition(shots[k])
                for k in range(i + 1, j)
            )
            if not has_transition:
                shot_id = shot_j.get("shot_id", f"shot_{j}")
                err = ShotAxisError(
                    shot_id=shot_id,
                    message=(
                        f"越轴：镜头 {shot_i.get('shot_id', f'shot_{i}')} yaw={yaw_i}° "
                        f"与 {shot_id} yaw={yaw_j}° 跨越180度轴线。"
                        f"请插入WS全景或OTS过肩过渡。"
                    ),
                    expected_yaw_range=(0.0, 180.0) if side_i == 1 else (180.0, 360.0),
                    actual_yaw=yaw_j,
                )
                errors.append(err)

        # 检查 A→B→A 直接正反打（中间无过渡）
        if idx >= 1:
            prev_idx, prev_shot = dialogue_indices[idx - 1]
            chars_i = set(shot_i.get("characters", []))
            chars_j = set(shot_j.get("characters", []))
            chars_prev = set(prev_shot.get("characters", []))

            # 三镜头同一组角色，且类型是OTS，直接切回A
            if chars_i == chars_prev and chars_i == chars_j:
                shot_type_j = str(shot_j.get("shot_type", "")).upper()
                if shot_type_j in ("OTS", "MCU", "MS"):
                    # 中间镜头 j 紧跟 prev 直接切回，视为越轴
                    between_count = j - prev_idx - 1
                    if between_count == 0:
                        shot_id = shot_j.get("shot_id", f"shot_{j}")
                        err = ShotAxisError(
                            shot_id=shot_id,
                            message=(
                                f"A→B→A正反打越轴：{prev_shot.get('shot_id','?')} → "
                                f"{shot_i.get('shot_id','?')} → {shot_id}。"
                                f"中间需插入WS全景或POV过渡镜头。"
                            ),
                            expected_yaw_range=(0.0, 180.0),
                            actual_yaw=yaw_j,
                        )
                        errors.append(err)

    return errors


def _shot_type_allows_axis_transition(shot: dict) -> bool:
    """判断镜头类型是否可作为越轴过渡"""
    t = str(shot.get("shot_type", "")).upper()
    return t in ("WS", "OTS", "POV", "EMPTY", "MV")


def check_dialogue_shots(shots: list[dict]) -> list[DialogueShotError]:
    """
    对话镜头类型校验（force_medium_shot）。
    对话场景只允许: MCU / MS / OTS
    禁止: WS / ECU / 2S
    ECU可用于情绪特写（非对话场景）。
    """
    errors: list[DialogueShotError] = []

    for i, shot in enumerate(shots):
        if not _is_dialogue_shot(shot):
            continue
        shot_type = str(shot.get("shot_type", "")).upper()
        if shot_type in FORBIDDEN_DIALOGUE_SHOT_TYPES:
            shot_id = shot.get("shot_id", f"shot_{i}")
            err = DialogueShotError(
                shot_id=shot_id,
                message=(
                    f"对话镜头类型违规：{shot_id} 使用了 {shot_type}。"
                    f"对话镜头只允许: {', '.join(sorted(ALLOWED_DIALOGUE_SHOT_TYPES))}。"
                    f"禁止: {', '.join(sorted(FORBIDDEN_DIALOGUE_SHOT_TYPES))}。"
                    f"（{shot_type}只允许用于非对话场景：情绪特写/全景交代/双人同框）"
                ),
                actual_type=shot_type,
                allowed_types=tuple(sorted(ALLOWED_DIALOGUE_SHOT_TYPES)),
            )
            errors.append(err)

    return errors


def check_durations(shots: list[dict]) -> list[ShotDurationError]:
    """
    镜头时长校验。
    超时: WARNING（可自动降级为voice-over）
    严重超时(>max*1.5): ERROR（不可自动修复）
    """
    errors: list[ShotDurationError] = []

    for i, shot in enumerate(shots):
        shot_type = str(shot.get("shot_type", "")).upper()
        duration = float(shot.get("duration_sec", 0.0))

        if shot_type not in DURATION_RANGES:
            continue  # 未知景别，跳过

        dmin, dstandard, dmax = DURATION_RANGES[shot_type]
        shot_id = shot.get("shot_id", f"shot_{i}")

        if duration < dmin:
            err = ShotDurationError(
                shot_id=shot_id,
                message=(
                    f"镜头时长过短：{shot_id}({shot_type}) 时长={duration}s，"
                    f"最短时长={dmin}s"
                ),
                actual_duration=duration,
                min_duration=dmin,
                max_duration=dmax,
            )
            err.severity = "warning"
            errors.append(err)

        elif duration > dmax:
            severe = duration > dmax * 1.5
            err = ShotDurationError(
                shot_id=shot_id,
                message=(
                    f"镜头时长超限：{shot_id}({shot_type}) 时长={duration}s，"
                    f"建议时长={dmin}-{dmax}s"
                    + ("（严重超时，需拆分）" if severe else "（建议拆分）")
                ),
                actual_duration=duration,
                min_duration=dmin,
                max_duration=dmax,
            )
            err.severity = "critical" if severe else "error"
            errors.append(err)

    return errors


def check_lipsync_quality(shots: list[dict]) -> list[LipSyncGradeError]:
    """
    Lip-sync质量分级校验。
    C级 → 强制添加 [voice-over] 标签（自动修复）
    S/A/B级 → 通过
    无台词 → 通过（S级）
    """
    errors: list[LipSyncGradeError] = []

    for i, shot in enumerate(shots):
        dialogue_text = _get_dialogue_text(shot)
        if not dialogue_text:
            continue  # 无台词，跳过

        shot_id = shot.get("shot_id", f"shot_{i}")
        grade, issue = _calc_lipsync_grade(shot)

        if grade == "C":
            err = LipSyncGradeError(
                shot_id=shot_id,
                message=(
                    f"Lip-sync质量不达标(C级)：{shot_id}。"
                    f"原因：{issue}。"
                    f"建议：添加 [voice-over] 标签，或缩短台词/调整机位/移除遮挡。"
                ),
                grade=grade,
                issue=issue,
            )
            errors.append(err)

    return errors


def check_character_markers(shots: list[dict]) -> list[CharacterMarkerError]:
    """
    【【】】角色标记强制化校验。
    1. 每个镜头最多1个标记（避免多角色同一镜头）
    2. 每个镜头必须出现标记
    """
    errors: list[CharacterMarkerError] = []

    for i, shot in enumerate(shots):
        shot_id = shot.get("shot_id", f"shot_{i}")
        markers = _extract_markers_from_shot(shot)
        count = len(markers)

        if count == 0:
            err = CharacterMarkerError(
                shot_id=shot_id,
                message=(
                    f"【【】】角色标记缺失：{shot_id}。"
                    f"所有角色引用必须使用【【角色名】】格式。"
                ),
                marker_count=0,
                issue="missing",
            )
            errors.append(err)

        elif count > 1:
            err = CharacterMarkerError(
                shot_id=shot_id,
                message=(
                    f"【【】】角色标记过多：{shot_id} 包含 {count} 个标记 "
                    f"({', '.join(markers)})。"
                    f"同一镜头最多1个【【】】标记（多角色对话需拆分为独立镜头）。"
                ),
                marker_count=count,
                issue="multiple",
            )
            errors.append(err)

    return errors


# ─────────────────────────────────────────────────────────────────────────────
# 自动修复
# ─────────────────────────────────────────────────────────────────────────────

def auto_fix(shot: dict) -> tuple[dict, list[str]]:
    """
    对单镜头进行自动修复。
    返回 (fixed_shot, list[fix_descriptions])
    当前支持：
    - 补充缺失的【【】】标记（从speaker推断）
    - 降级Lip-sync等级标签（C级→添加[voice-over]）
    注意：轴线违规、时长严重超标不自动修复
    """
    fixed = dict(shot)  # 深拷贝
    fixes: list[str] = []

    # 1. 补充【【】】标记
    markers = _extract_markers_from_shot(fixed)
    if len(markers) == 0:
        # 从dialogue的speaker推断角色标记
        speakers = _get_speakers(fixed)
        if speakers:
            speaker = speakers[0]  # 取第一个说话者
            # 查找可用的角色名（去除前缀）
            char_name = re.sub(r"^(char_\d+[_]?)?", "", speaker).strip()
            if not char_name:
                char_name = speaker  # 直接用原始ID

            # 注入到script字段（末尾追加）
            script = fixed.get("script", "")
            new_marker = f"【【{char_name}】】"
            fixed["script"] = f"{script} {new_marker}".strip()
            fixed["character_markers"] = [new_marker]
            fixes.append(f"补充缺失的【【】】标记: {new_marker}（来自speaker: {speaker}）")

    # 2. C级Lip-sync → 注入[voice-over]
    if _get_dialogue_text(fixed):
        grade, issue = _calc_lipsync_grade(fixed)
        if grade == "C":
            dialogue = fixed.get("dialogue", "")
            if isinstance(dialogue, str):
                # 注入 voice-over 前缀
                if not dialogue.strip().startswith("[voice-over]"):
                    fixed["dialogue"] = f"[voice-over] {dialogue}"
                    fixes.append(f"Lip-sync C级: 添加[voice-over]标签（原: {issue}）")
            elif isinstance(dialogue, list):
                for item in dialogue:
                    if isinstance(item, dict):
                        t = item.get("text", "")
                        if t and not str(t).startswith("[voice-over]"):
                            item["text"] = f"[voice-over] {t}"
                            fixes.append(f"Lip-sync C级: 添加[voice-over]标签（原: {issue}）")
                            break

    return fixed, fixes


# ─────────────────────────────────────────────────────────────────────────────
# ShotValidator 主类
# ─────────────────────────────────────────────────────────────────────────────


class ShotValidator:
    """
    分镜脚本强制执行引擎

    用法：
        validator = ShotValidator()
        result = validator.validate(shot_script)   # 单镜头dict 或 多镜头list
        print(result.summary())

        # 批量校验（直接调用）
        errors = validator.check_180_axis(shots)
        errors = validator.check_dialogue_shots(shots)
        errors = validator.check_durations(shots)
        errors = validator.check_lipsync_quality(shots)
        errors = validator.check_character_markers(shots)
    """

    def __init__(self):
        pass

    def validate(self, shot_script: dict | list[dict]) -> ValidationResult:
        """
        校验分镜脚本，返回校验结果。

        shot_script: 单镜头dict 或 多镜头list
        Returns: ValidationResult
        """
        # 标准化为列表
        if isinstance(shot_script, dict):
            shots = [shot_script]
        else:
            shots = list(shot_script)

        warnings: list[ValidationWarning] = []
        errors: list[ValidationError] = []
        auto_fixes: list[tuple[str, str]] = []

        # ── 1. 180度轴线校验（需多镜头上下文）───────────────────────────────
        axis_errors = check_180_axis(shots)
        errors.extend(axis_errors)

        # ── 2. 对话镜头类型校验 ──────────────────────────────────────────────
        dialogue_errors = check_dialogue_shots(shots)
        errors.extend(dialogue_errors)

        # ── 3. 镜头时长校验 ─────────────────────────────────────────────────
        duration_errors = check_durations(shots)
        for err in duration_errors:
            if err.severity == "warning":
                warnings.append(ValidationWarning(
                    shot_id=err.shot_id, code=err.code, message=err.message
                ))
            else:
                errors.append(err)

        # ── 4. Lip-sync质量校验 ──────────────────────────────────────────────
        lipsync_errors = check_lipsync_quality(shots)
        for err in lipsync_errors:
            warnings.append(ValidationWarning(
                shot_id=err.shot_id, code=err.code, message=err.message
            ))
        errors.extend(lipsync_errors)

        # ── 5. 【【】】角色标记校验 ───────────────────────────────────────────
        marker_errors = check_character_markers(shots)
        for err in marker_errors:
            if err.issue == "missing":
                # 缺失标记 → 自动修复
                warnings.append(ValidationWarning(
                    shot_id=err.shot_id, code=err.code,
                    message=f"{err.message}（将自动补充）"
                ))
            else:
                errors.append(err)

        # ── 自动修复（仅警告级别的问题）───────────────────────────────────────
        if len(shots) == 1:
            fixed_shot, fix_descriptions = auto_fix(shots[0])
            for desc in fix_descriptions:
                shot_id = fixed_shot.get("shot_id", "shot_0")
                auto_fixes.append((shot_id, desc))
                warnings.append(ValidationWarning(
                    shot_id=shot_id,
                    code="AUTO_FIXED",
                    message=f"已自动修复: {desc}"
                ))

        # valid = 无 blocking error（warning 不影响通过）
        has_blocking_errors = any(
            e.severity in ("error", "critical") for e in errors
        )

        return ValidationResult(
            valid=not has_blocking_errors,
            warnings=warnings,
            errors=[e for e in errors if e.severity in ("error", "critical")],
            auto_fixes=auto_fixes,
        )

    def auto_fix(self, shot_script: dict) -> dict:
        """
        对单镜头进行自动修复，返回修复后的镜头dict。
        """
        fixed, _ = auto_fix(shot_script)
        return fixed

    def check_180_axis(self, shots: list[dict]) -> list[ShotAxisError]:
        """批量校验180度轴线"""
        return check_180_axis(shots)

    def check_dialogue_shots(self, shots: list[dict]) -> list[DialogueShotError]:
        """批量校验对话镜头类型"""
        return check_dialogue_shots(shots)

    def check_durations(self, shots: list[dict]) -> list[ShotDurationError]:
        """批量校验镜头时长"""
        return check_durations(shots)

    def check_lipsync_quality(self, shots: list[dict]) -> list[LipSyncGradeError]:
        """批量校验Lip-sync质量"""
        return check_lipsync_quality(shots)

    def check_character_markers(self, shots: list[dict]) -> list[CharacterMarkerError]:
        """批量校验【【】】标记"""
        return check_character_markers(shots)


# ─────────────────────────────────────────────────────────────────────────────
# 自测代码
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    validator = ShotValidator()

    print("=" * 70)
    print("ShotValidator 自测")
    print("=" * 70)

    # ── Test 1: 180度轴线违规 ──────────────────────────────────────────────
    print("\n[TEST 1] 180度轴线违规")
    shots_axis = [
        {
            "shot_id": "P01",
            "shot_type": "OTS",
            "duration_sec": 5.0,
            "yaw": 30.0,            # 轴线一侧
            "is_dialogue_scene": True,
            "characters": ["char_01"],
            "dialogue": "Ray……离职了？",
        },
        {
            "shot_id": "P02",
            "shot_type": "OTS",
            "duration_sec": 5.0,
            "yaw": 210.0,           # 越轴！轴线另一侧
            "is_dialogue_scene": True,
            "characters": ["char_02"],
            "dialogue": "是。",
        },
    ]
    result = validator.validate(shots_axis)
    print(result.summary())

    # ── Test 2: 对话镜头类型违规 ───────────────────────────────────────────
    print("\n[TEST 2] 对话镜头类型违规（WS/ECU）")
    shots_dialogue = [
        {
            "shot_id": "P03",
            "shot_type": "WS",
            "duration_sec": 6.0,
            "is_dialogue_scene": True,
            "characters": ["char_01"],
            "dialogue": "你怎么不早说？",
        },
        {
            "shot_id": "P04",
            "shot_type": "ECU",
            "duration_sec": 4.0,
            "is_dialogue_scene": True,
            "characters": ["char_01"],
            "dialogue": "来不及了。",
        },
    ]
    result = validator.validate(shots_dialogue)
    print(result.summary())

    # ── Test 3: 镜头时长超限 ───────────────────────────────────────────────
    print("\n[TEST 3] 镜头时长超限")
    shots_duration = [
        {
            "shot_id": "P05",
            "shot_type": "ECU",
            "duration_sec": 8.0,    # ECU最大5s
            "characters": ["char_01"],
            "dialogue": "大特写",
        },
        {
            "shot_id": "P06",
            "shot_type": "WS",
            "duration_sec": 15.0,   # WS最大12s，严重超时
            "characters": [],
            "dialogue": "",
        },
    ]
    result = validator.validate(shots_duration)
    print(result.summary())

    # ── Test 4: Lip-sync质量C级 ────────────────────────────────────────────
    print("\n[TEST 4] Lip-sync质量C级")
    shots_lipsync = [
        {
            "shot_id": "P07",
            "shot_type": "MCU",
            "duration_sec": 5.0,
            "characters": ["char_01"],
            "dialogue": "这个项目终于完成了，我们真的要好好庆祝一下，"
                        "大家辛苦了这么久，现在终于可以放松一下了！",
            "speed": "fast",
            "yaw": 45.0,           # 侧偏>30°
            "has_obstruction": False,
        },
    ]
    result = validator.validate(shots_lipsync)
    print(result.summary())

    # ── Test 5: 【【】】角色标记缺失（自动修复）────────────────────────────
    print("\n[TEST 5] 【【】】角色标记缺失（自动修复）")
    shots_marker = [
        {
            "shot_id": "P08",
            "shot_type": "MCU",
            "duration_sec": 5.0,
            "characters": ["char_01"],
            "dialogue": [{"speaker": "char_01", "text": "你好。"}],
            "script": "潭斌走进办公室。",
        },
    ]
    result = validator.validate(shots_marker)
    print(result.summary())

    # ── Test 6: 完整正常镜头 ───────────────────────────────────────────────
    print("\n[TEST 6] 完整正常镜头（应通过）")
    shots_ok = [
        {
            "shot_id": "P01",
            "shot_type": "WS",
            "duration_sec": 8.0,
            "characters": ["char_01"],
            "dialogue": "",
            "is_dialogue_scene": False,
            "script": "【【潭斌】】独坐办公室，窗外CBD夜景。",
            "yaw": 0.0,
        },
        {
            "shot_id": "P02",
            "shot_type": "OTS",
            "duration_sec": 5.0,
            "characters": ["char_01", "char_02"],
            "dialogue": "Ray……离职了？",
            "is_dialogue_scene": True,
            "script": "【【潭斌】】压低声线告知，【【Tony】】侧耳倾听。",
            "yaw": 30.0,
        },
    ]
    result = validator.validate(shots_ok)
    print(result.summary())

    # ── Test 7: Lip-sync S/A/B级边界 ───────────────────────────────────────
    print("\n[TEST 7] Lip-sync S/A/B级边界测试")
    shots_grade = [
        {
            "shot_id": "P-S",
            "shot_type": "MCU",
            "duration_sec": 4.0,
            "characters": ["char_01"],
            "dialogue": "你还好吗？",
            "speed": "slow",
            "yaw": 0.0,
            "has_obstruction": False,
            "script": "【【潭斌】】关切地看着对方。",
        },
        {
            "shot_id": "P-A",
            "shot_type": "MCU",
            "duration_sec": 5.0,
            "characters": ["char_01"],
            "dialogue": "你真的决定了吗？",
            "speed": "normal",
            "yaw": 10.0,
            "has_obstruction": False,
            "script": "【【潭斌】】眉头微皱。",
        },
        {
            "shot_id": "P-B",
            "shot_type": "MCU",
            "duration_sec": 6.0,
            "characters": ["char_01"],
            "dialogue": "这个项目终于完成了。",
            "speed": "normal",
            "yaw": 20.0,
            "has_obstruction": True,
            "script": "【【潭斌】】轻叹一口气。",
        },
    ]
    result = validator.validate(shots_grade)
    print(result.summary())

    print("\n" + "=" * 70)
    print("自测完成")
    print("=" * 70)
