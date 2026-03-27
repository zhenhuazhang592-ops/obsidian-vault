"""Schema 校验引擎 — 跨步一致性校验，D1-D3 可编程评分"""

import re
from dataclasses import dataclass
from typing import Optional
from .schema import ShotScript, IPProfile, Step45Output, ShotScriptMeta
from .constants import (
    SHOT_TYPES, CAMERA_ACTIONS, EMOTION_LEVELS,
    PROHIBITED_KEYWORDS, is_emotion_jump_allowed
)


@dataclass
class ValidationError:
    shot_id: str
    field:   str
    expected: str
    actual:  str
    severity: str  # "BLOCK" | "WARN"


@dataclass
class ValidationResult:
    shot_id:      str
    errors:       list[ValidationError]
    warnings:     list[str]
    d1_score:     float  # 0.0-1.0
    d2_score:     float
    d3_score:     float
    is_passed:    bool
    blocked_reason: str = ""


class SchemaValidator:
    """
    Schema 校验引擎

    校验维度：
    D1 完整性：必填字段是否完整，Prompt 是否为空
    D2 一致性：char_id/loc_id 是否在 IP档案 中存在，情绪值是否在 L1-L5 范围内
    D3 指令合规：景别/运镜是否来自导演塔，情绪跳转是否合法，禁止词是否出现
    """

    def __init__(self, ip_profile: IPProfile, step45_output: Step45Output):
        self.ip_profile = ip_profile
        self.step45 = step45_output

    # ------------------------------------------------------------------ D1 完整性

    def _validate_D1(self, shot: ShotScript) -> tuple[float, list[ValidationError], list[str]]:
        errors = []
        warnings = []

        # 必填字段检查
        required_str_fields = [
            ("script", "分场内容"),
            ("image_prompt", "Image Prompt"),
            ("video_prompt", "Video Prompt"),
        ]
        for field, label in required_str_fields:
            val = getattr(shot, field, None)
            if not val or not val.strip():
                errors.append(ValidationError(
                    shot_id=shot.shot_id, field=field,
                    expected=f"{label}非空",
                    actual="空字符串",
                    severity="BLOCK"
                ))

        # 必填枚举字段
        if shot.emotion_level not in EMOTION_LEVELS:
            errors.append(ValidationError(
                shot_id=shot.shot_id, field="emotion_level",
                expected="L1-L5",
                actual=shot.emotion_level,
                severity="BLOCK"
            ))

        if shot.shot_type not in SHOT_TYPES:
            warnings.append(f"景别 {shot.shot_type} 不在标准景别列表中")

        if shot.camera_action not in CAMERA_ACTIONS:
            warnings.append(f"运镜 {shot.camera_action} 不在标准运镜列表中")

        # Prompt 字数下限检查（防止敷衍生成）
        for field, label in [("image_prompt", "Image"), ("video_prompt", "Video")]:
            val = getattr(shot, field, "")
            if val and len(val.strip()) < 30:
                warnings.append(f"{label} Prompt 少于30字，可能生成质量不足")

        score = 1.0 - (len(errors) * 0.3) - (len(warnings) * 0.05)
        score = max(0.0, min(1.0, score))
        return score, errors, warnings

    # ------------------------------------------------------------------ D2 一致性

    def _validate_D2(self, shot: ShotScript) -> tuple[float, list[ValidationError], list[str]]:
        errors = []
        warnings = []

        # char_id 在 IP档案 中
        known_chars = set(self.ip_profile.characters.keys())
        for char_id in shot.character_ids:
            if char_id not in known_chars:
                errors.append(ValidationError(
                    shot_id=shot.shot_id, field=f"character_ids.{char_id}",
                    expected=f"在IP档案.characters中: {known_chars}",
                    actual=f"未找到 {char_id}",
                    severity="BLOCK"
                ))

        # loc_id 在 IP档案 中
        known_locs = set(self.ip_profile.locations.keys())
        if shot.location_id not in known_locs:
            errors.append(ValidationError(
                shot_id=shot.shot_id, field="location_id",
                expected=f"在IP档案.locations中: {known_locs}",
                actual=f"未找到 {shot.location_id}",
                severity="BLOCK"
            ))

        # meta 中声明的 char_ids_source 必须全部在 IP档案
        if shot.meta and shot.meta.char_ids_source:
            for cid in shot.meta.char_ids_source:
                if cid not in known_chars:
                    errors.append(ValidationError(
                        shot_id=shot.shot_id, field="meta.char_ids_source",
                        expected=cid,
                        actual="不在IP档案中",
                        severity="BLOCK"
                    ))

        score = 1.0 - (len(errors) * 0.4)
        score = max(0.0, min(1.0, score))
        return score, errors, warnings

    # ------------------------------------------------------------------ D3 指令合规

    def _validate_D3(self, shot: ShotScript) -> tuple[float, list[ValidationError], list[str]]:
        errors = []
        warnings = []

        # 1. 禁止词检查（全局 + 风格）
        prohibited = set(self.step45.prohibited_keywords)
        style_preset = getattr(shot, 'style_preset', 'real')
        if style_preset in PROHIBITED_KEYWORDS:
            prohibited |= set(PROHIBITED_KEYWORDS[style_preset])
        prohibited |= set(PROHIBITED_KEYWORDS.get("global", []))

        all_text = " ".join([
            getattr(shot, 'script', ''),
            getattr(shot, 'image_prompt', ''),
            getattr(shot, 'video_prompt', ''),
        ])

        # 预处理：标记所有在"否定前缀+列举"结构中的禁止词位置
        negation_chars = {'无', '去', '不', '消', '避', '免', '排'}
        sep_chars = {'、', '或', '和', '与', ',', '，', ' ', '，', '/', '>', '：', ':'}
        # 标记所有被否定的关键词范围：[start, end) 列表
        negated_ranges = []
        for i, c in enumerate(all_text):
            if c in negation_chars:
                # 从这个否定前缀开始，向右扫描
                j = i + 1
                while j < len(all_text):
                    nc = all_text[j]
                    # 如果遇到下一个否定词、分隔符、空格，继续扫描
                    # 如果遇到汉字（非关键词的一部分），停止
                    if nc in negation_chars:
                        break
                    if nc == '，' or nc == '。' or nc == '\n':
                        break
                    if nc in sep_chars:
                        j += 1
                        continue
                    # 遇到汉字词（2+char词）
                    j += 1
                negated_ranges.append((i, j))

        for word in prohibited:
            # 找到关键词位置
            idx = all_text.find(word)
            if idx == -1:
                continue
            # 检查是否在某个否定范围内
            skipped = False
            for n_start, n_end in negated_ranges:
                if n_start <= idx < n_end:
                    skipped = True
                    break
            if skipped:
                continue
            errors.append(ValidationError(
                shot_id=shot.shot_id, field="prohibited_keyword",
                expected=f"禁止词 '{word}' 不应出现",
                actual=f"在 Prompt 中发现",
                severity="BLOCK"
            ))

        # 2. 情绪值必须来自 D3 beat_tracking
        expected_emotion = self.step45.shot_emotion_map.get(shot.shot_id, "")
        if expected_emotion and shot.emotion_level != expected_emotion:
            errors.append(ValidationError(
                shot_id=shot.shot_id, field="emotion_level",
                expected=f"来自D3: {expected_emotion}",
                actual=shot.emotion_level,
                severity="WARN"  # WARN 不阻断，仅提醒
            ))

        # 3. 景别必须来自 D4 camera_intent
        shot_constraints = self.step45.get_shot_constraints(shot.shot_id)
        expected_shot_type = shot_constraints.get("shot_type", "")
        if expected_shot_type and shot.shot_type != expected_shot_type:
            errors.append(ValidationError(
                shot_id=shot.shot_id, field="shot_type",
                expected=f"来自D4: {expected_shot_type}",
                actual=shot.shot_type,
                severity="WARN"
            ))

        # 4. 运镜必须来自 D4 camera_intent
        expected_camera = shot_constraints.get("camera_action", "")
        if expected_camera and shot.camera_action != expected_camera:
            errors.append(ValidationError(
                shot_id=shot.shot_id, field="camera_action",
                expected=f"来自D4: {expected_camera}",
                actual=shot.camera_action,
                severity="WARN"
            ))

        score = 1.0 - (len([e for e in errors if e.severity == "BLOCK"]) * 0.3)
        score = max(0.0, min(1.0, score))
        return score, errors, warnings

    # ------------------------------------------------------------------ 主校验入口

    def validate_shot(self, shot: ShotScript) -> ValidationResult:
        """校验单个镜头，返回评分 + 错误列表"""
        d1, d1_errors, d1_warnings = self._validate_D1(shot)
        d2, d2_errors, d2_warnings = self._validate_D2(shot)
        d3, d3_errors, d3_warnings = self._validate_D3(shot)

        all_errors = d1_errors + d2_errors + d3_errors
        all_warnings = d1_warnings + d2_warnings + d3_warnings

        # BLOCK 错误超过 2 个 → 不通过
        block_count = sum(1 for e in all_errors if e.severity == "BLOCK")
        is_passed = block_count == 0

        return ValidationResult(
            shot_id=shot.shot_id,
            errors=all_errors,
            warnings=all_warnings,
            d1_score=round(d1, 3),
            d2_score=round(d2, 3),
            d3_score=round(d3, 3),
            is_passed=is_passed,
            blocked_reason=f"{block_count}个BLOCK错误" if block_count > 0 else "",
        )

    def validate_episode(self, shots: list[ShotScript]) -> dict:
        """批量校验整集"""
        results = [self.validate_shot(s) for s in shots]
        passed = sum(1 for r in results if r.is_passed)
        failed = [r for r in results if not r.is_passed]

        composite_scores = [(r.d1_score * 0.35 + r.d2_score * 0.35 + r.d3_score * 0.30) for r in results]
        avg_composite = sum(composite_scores) / len(composite_scores) if composite_scores else 0

        return {
            "total_shots":   len(shots),
            "passed":        passed,
            "failed":        len(failed),
            "avg_composite": round(avg_composite, 3),
            "grade":         "优秀" if avg_composite >= 0.80 else "合格" if avg_composite >= 0.70 else "一般",
            "is_passed":     len(failed) == 0,
            "failed_shots":  [{"shot_id": r.shot_id, "reason": r.blocked_reason, "errors": [
                {"field": e.field, "severity": e.severity, "msg": f"{e.expected}，实际：{e.actual}"}
                for e in r.errors
            ]} for r in failed],
            "warnings_all":  [w for r in results for w in r.warnings],
        }

    # ------------------------------------------------------------------ 报告打印

    def print_validation_report(self, result: dict) -> None:
        """打印校验报告"""
        print("\n" + "=" * 60)
        print(f"🎯 Schema 校验报告（{result['total_shots']}镜）")
        print("=" * 60)
        print(f"  通过: {result['passed']}镜  失败: {result['failed']}镜")
        print(f"  综合分: {result['avg_composite']:.3f}  等级: 【{result['grade']}】")
        print("-" * 60)
        if result['failed_shots']:
            print(f"  ❌ 失败镜头:")
            for fs in result['failed_shots']:
                print(f"    {fs['shot_id']}: {fs['reason']}")
                for e in fs['errors'][:3]:  # 只显示前3条
                    print(f"      - [{e['severity']}] {e['field']}: {e['msg']}")
        if result.get('warnings_all'):
            print(f"  ⚠️  警告 ({len(result['warnings_all'])}条):")
            for w in result['warnings_all'][:5]:  # 只显示前5条
                print(f"      - {w}")
        print("=" * 60 + "\n")
