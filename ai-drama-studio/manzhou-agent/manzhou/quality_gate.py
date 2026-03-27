"""质量门控 - 五维评分（D1-D5）、自动触发、人工介入"""

import re
from dataclasses import dataclass
from typing import Optional

from .constants import QUALITY_DIMENSIONS, QUALITY_GRADES, QUALITY_REDLINE


# =============================================================================
# 质量评分结果
# =============================================================================

@dataclass
class QualityScore:
    dimension:    str   # D1/D2/D3/D4/D5
    score:        float # 0.0-1.0
    evidence:     str   # 打分依据
    suggestion:   str   # 改进建议


@dataclass
class QualityGateResult:
    scores:         dict[str, QualityScore]   # {D1: QualityScore}
    composite:      float                      # 加权综合分
    grade:          str                        # 优秀/合格/一般/失败
    is_passed:      bool
    redline_hit:    bool                       # 是否触发了最低红线
    action:         str                        # "入库" / "微调" / "优化" / "进化" / "报警"
    auto_proceed:  bool                       # 是否可以自动继续
    suggestions:    list[str]                  # 改进建议列表


# =============================================================================
# 质量门控引擎
# =============================================================================

class QualityGate:
    """
    三维质量门控（简化版，到分镜截止）

    D1 完整性（0.35）：资产/对白/Prompt是否完整
    D2 一致性（0.35）：角色/场景是否前后一致
    D3 指令合规（0.30）：Prompt是否遵循导演控制塔约束
    """

    def __init__(self):
        self.weights = {k: v["weight"] for k, v in QUALITY_DIMENSIONS.items()}
        self.thresholds = {k: v["threshold"] for k, v in QUALITY_DIMENSIONS.items()}

    # ------------------------------------------------------------------ 评分

    def score_D1_completeness(
        self,
        shot_script: dict,
        image_url: Optional[str] = None,
        video_url: Optional[str] = None,
    ) -> QualityScore:
        """D1 完整性评分"""
        score = 0.0
        evidence_parts = []

        # 检查分镜字段完整性
        required_fields = ["shot_id", "duration_sec", "location_id", "script",
                           "dialogue", "image_prompt", "video_prompt"]
        filled = sum(1 for f in required_fields if shot_script.get(f))
        field_ratio = filled / len(required_fields)
        score += field_ratio * 0.6
        evidence_parts.append(f"字段完整率: {field_ratio:.0%}")

        # 检查图片是否生成
        if image_url:
            score += 0.2
            evidence_parts.append("图片已生成")
        else:
            evidence_parts.append("图片未生成")

        # 检查视频是否生成
        if video_url:
            score += 0.2
            evidence_parts.append("视频已生成")
        else:
            evidence_parts.append("视频未生成")

        score = min(score, 1.0)
        return QualityScore(
            dimension="D1",
            score=score,
            evidence=" / ".join(evidence_parts),
            suggestion="补充缺失字段" if field_ratio < 1.0 else "OK"
        )

    def score_D2_consistency(
        self,
        shot_script: dict,
        character_ids: list[str],
        asset_library: dict,
        ref_images: Optional[list[str]] = None,
    ) -> QualityScore:
        """
        D2 一致性评分（已补全）
        1. char_id 是否在 IP档案 中（权重 0.5）
        2. loc_id 是否在 IP档案 中（权重 0.3）
        3. 参考图覆盖率（权重 0.2）
        """
        score = 0.0
        evidence_parts = []

        # 1. char_id 匹配
        known_chars = set(asset_library.get("characters", {}).keys())
        if known_chars:
            matched_chars = [c for c in character_ids if c in known_chars]
            char_ratio = len(matched_chars) / len(character_ids) if character_ids else 0
            score += char_ratio * 0.5
            evidence_parts.append(f"角色匹配率: {len(matched_chars)}/{len(character_ids)}")
        else:
            evidence_parts.append("无角色档案")

        # 2. loc_id 匹配
        known_locs = set(asset_library.get("locations", {}).keys())
        loc_id = shot_script.get("location_id", "")
        if loc_id in known_locs:
            score += 0.3
            evidence_parts.append(f"场景ID匹配: {loc_id}")
        else:
            evidence_parts.append(f"场景ID未匹配: {loc_id}")

        # 3. 参考图覆盖率
        if ref_images:
            ref_count = len(ref_images)
            img_count = shot_script.get("image_url_count", 0)
            ref_ratio = min(img_count / max(ref_count, 1), 1.0)
            score += ref_ratio * 0.2
            evidence_parts.append(f"参考图覆盖: {img_count}/{ref_count}")

        score = min(score, 1.0)
        suggestion = "OK"
        if not known_chars or (character_ids and len(matched_chars) < len(character_ids)):
            suggestion = f"角色ID {set(character_ids) - known_chars if known_chars else set(character_ids)} 不在IP档案中"
        elif not ref_images:
            suggestion = "建议补充参考图提升一致性"

        return QualityScore(
            dimension="D2",
            score=round(score, 3),
            evidence=" / ".join(evidence_parts),
            suggestion=suggestion,
        )

    def score_D3_instruction_compliance(
        self,
        shot_script: dict,
        director_constraints: dict,
    ) -> QualityScore:
        """
        D3 指令合规评分（已补全）
        1. 禁止词检查（权重 0.4）
        2. 情绪跳转合规（权重 0.3）
        3. 景别运镜合规（权重 0.3）
        """
        from .constants import PROHIBITED_KEYWORDS, is_emotion_jump_allowed

        score = 1.0
        evidence_parts = []
        violations = []

        all_text = " ".join([
            shot_script.get("script", ""),
            shot_script.get("image_prompt", ""),
            shot_script.get("video_prompt", ""),
        ])

        # 1. 禁止词检查
        all_prohibited = set(PROHIBITED_KEYWORDS.get("global", []))
        style = shot_script.get("style_preset", "real")
        if style in PROHIBITED_KEYWORDS:
            all_prohibited |= set(PROHIBITED_KEYWORDS[style])

        found_prohibited = [w for w in all_prohibited if w in all_text]
        if found_prohibited:
            violations.append(f"禁止词: {found_prohibited}")
            score -= 0.4
            evidence_parts.append(f"发现禁止词: {len(found_prohibited)}个")

        # 2. 情绪跳转合规
        emotion_curve = director_constraints.get("D3_beat_tracking", [])
        if emotion_curve:
            prev_emotion = None
            for item in emotion_curve:
                cur = item.get("emotion_curve", "")
                # e.g. "L1→L2" → from=L1, to=L2
                if "→" in cur:
                    from_lvl = cur.split("→")[0].strip()
                    to_lvl = cur.split("→")[-1].strip()
                    if prev_emotion is not None:
                        if not is_emotion_jump_allowed(prev_emotion, from_lvl):
                            violations.append(f"情绪跳转违规: {prev_emotion}→{from_lvl}")
                            score -= 0.2
                    prev_emotion = to_lvl

        # 3. 景别运镜合规（与导演塔对比）
        d4_list = director_constraints.get("D4_camera_intent", [])
        shot_id = shot_script.get("shot_id", "")
        d4_match = next((d for d in d4_list if d.get("shot_id") == shot_id), None)
        if d4_match:
            expected_shot = d4_match.get("camera_intent", {}).get("shot_type", "")
            actual_shot = shot_script.get("shot_type", "")
            if expected_shot and actual_shot and actual_shot != expected_shot:
                violations.append(f"景别不符: 期望{expected_shot}，实际{actual_shot}")
                score -= 0.15

        score = max(0.0, min(1.0, score))
        return QualityScore(
            dimension="D3",
            score=round(score, 3),
            evidence=f"违规: {len(violations)}项" if violations else "全部合规",
            suggestion="修正: " + "; ".join(violations) if violations else "OK",
        )

    # ------------------------------------------------------------------ 门控决策

    def evaluate(
        self,
        shot_script: dict,
        director_constraints: dict,
        asset_library: dict,
        image_urls: Optional[list[str]] = None,
    ) -> QualityGateResult:
        """
        综合三维评分 + 决策
        """
        # 计算三个维度
        d1 = self.score_D1_completeness(shot_script, image_urls, None)
        d2 = self.score_D2_consistency(
            shot_script,
            shot_script.get("character_ids", []),
            asset_library,
            ref_images=image_urls
        )
        d3 = self.score_D3_instruction_compliance(shot_script, director_constraints)

        scores = {"D1": d1, "D2": d2, "D3": d3}

        # 计算综合分
        composite = sum(
            s.score * self.weights[k]
            for k, s in scores.items()
        )

        # 等级判定
        grade = self._get_grade(composite)

        # 检查红线
        redline_hit = any(s.score < QUALITY_REDLINE for s in scores.values())

        # 决策动作
        if redline_hit:
            action = "需人工调整"
            auto_proceed = False
        elif composite >= 0.80:
            action = "优秀-可直接使用"
            auto_proceed = True
        elif composite >= 0.70:
            action = "合格-微调后使用"
            auto_proceed = True
        else:
            action = "一般-需人工调整"
            auto_proceed = False

        suggestions = [s.suggestion for s in scores.values() if s.suggestion != "OK"]

        return QualityGateResult(
            scores=scores,
            composite=round(composite, 3),
            grade=grade,
            is_passed=composite >= 0.70 and not redline_hit,
            redline_hit=redline_hit,
            action=action,
            auto_proceed=auto_proceed,
            suggestions=suggestions,
        )

    @staticmethod
    def _get_grade(score: float) -> str:
        for threshold, grade, _ in QUALITY_GRADES:
            if score >= threshold:
                return grade
        return "失败"

    # ------------------------------------------------------------------ 打印报告

    def print_report(self, result: QualityGateResult) -> None:
        """打印质量门控报告"""
        print("\n" + "=" * 50)
        print("🎯 质量门控报告（三维）")
        print("=" * 50)
        for dim_id, qs in result.scores.items():
            dim_info = QUALITY_DIMENSIONS[dim_id]
            bar = "█" * int(qs.score * 10) + "░" * (10 - int(qs.score * 10))
            print(f"  [{dim_id}] {dim_info['name']:<8} {bar} {qs.score:.2f}  | {qs.evidence}")
        print("-" * 50)
        print(f"  📊 综合评分: {result.composite:.3f}  等级: 【{result.grade}】")
        print(f"  🎬 决策动作: {result.action}")
        if result.redline_hit:
            print(f"  ⚠️  最低红线触发，需人工介入！")
        if result.suggestions:
            print(f"  💡 改进建议:")
            for s in result.suggestions:
                print(f"      - {s}")
        print("=" * 50 + "\n")

    # ------------------------------------------------------------------ 批量评分（集级别）

    def evaluate_episode(self, shot_results: list[dict]) -> dict:
        """
        批量评估整集的所有镜头结果
        返回集级别汇总
        """
        if not shot_results:
            return {"composite": 0.0, "grade": "无数据", "is_passed": False}

        scores = [r.get("composite_score", 0.0) for r in shot_results]
        avg = sum(scores) / len(scores)

        return {
            "total_shots":   len(shot_results),
            "avg_composite": round(avg, 3),
            "grade":         self._get_grade(avg),
            "is_passed":    avg >= 0.70,
            "failed_shots":  [r["shot_id"] for r in shot_results if r.get("composite_score", 0) < 0.60],
        }
