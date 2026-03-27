# 漫舟效果评分引擎

> **版本**: 1.0.0
> **文件名**: `manzhou-effect-scorer.md`
> **角色**: 将多维平台指标聚合成单一 effect_score，用于Prompt进化决策
> **维护者**: 漫舟 Agent

---

## 1. 评分公式

```
effect_score = w1×完播率 + w2×点赞率 + w3×评论率 + w4×分享率
```

**权重配置**（默认值，可根据项目调整）:

| 指标 | 权重 | 理由 |
|------|------|------|
| 完播率 (w1) | **0.40** | 最核心指标，反映内容留存能力 |
| 点赞率 (w2) | **0.25** | 简单认可，用户成本低 |
| 评论率 (w3) | **0.20** | 深度互动，暗示内容引发思考 |
| 分享率 (w4) | **0.15** | 主动传播意愿，最强认可 |

### 归一化计算

```python
def normalize_rate(count: int, base: int = 1000) -> float:
    """将原始计数归一化为0-1比率"""
    return min(count / base, 1.0)

def compute_effect_score(metrics: dict) -> float:
    """
    计算综合效果评分
    metrics: {
        "play_count": int,
        "completion_rate": float,  # 0.0-1.0
        "like_count": int,
        "comment_count": int,
        "share_count": int
    }
    """
    w1, w2, w3, w4 = 0.40, 0.25, 0.20, 0.15

    # 评论率和分享率基于播放量计算
    play_count = max(metrics["play_count"], 1)  # 避免除零
    comment_rate = min(metrics["comment_count"] / play_count, 1.0)
    share_rate = min(metrics["share_count"] / play_count, 1.0)

    score = (
        w1 * metrics["completion_rate"] +
        w2 * normalize_rate(metrics["like_count"]) +
        w3 * comment_rate +
        w4 * share_rate
    )
    return round(score, 3)
```

---

## 2. 评分分级

| 等级 | 分数区间 | 标签 | 行动指引 |
|------|---------|------|---------|
| 🔥 **爆款** | `score ≥ 0.80` | 爆款 | 提取成功Prompt特征，加入知识库成功库 |
| ✅ **合格** | `0.60 ≤ score < 0.80` | 合格 | 观察复用，必要时微调 |
| ⚠️ **待优化** | `0.40 ≤ score < 0.60` | 待优化 | 诊断失败原因，修正Prompt |
| ❌ **失败** | `score < 0.40` | 失败 | 记录失败日志，进入失败知识库 |

---

## 3. 人工评分补充

当 `manual_rating` 有值时，加权融合：

```python
def compute_hybrid_score(effect_score: float, manual_rating: float) -> float:
    """
    融合算法评分和人工评分
    manual_rating: 1-5 分
    """
    # 将manual_rating归一化到0-1
    normalized_manual = (manual_rating - 1) / 4
    # 60%算法 + 40%人工
    return round(0.6 * effect_score + 0.4 * normalized_manual, 3)
```

---

## 4. 与SRL模型联动

**统计目标**: 找出哪种SRL位置得分最高

```python
def analyze_srl_performance(effect_log: list) -> dict:
    """
    按SRL位置统计平均得分
    返回: {"Pressure": 0.72, "Release": 0.81, "Vacuum": 0.55}
    """
    from collections import defaultdict
    buckets = defaultdict(list)
    for record in effect_log:
        if record.get("effect_score", 0) > 0:
            buckets[record["srl_position"]].append(record["effect_score"])
    return {
        pos: round(sum(scores)/len(scores), 3)
        for pos, scores in buckets.items()
    }
```

**洞察规则**:
- 若 `Release` 得分显著高于 `Pressure` → 释放点设计可能不足，需要更多悬念
- 若 `Vacuum` 得分过低 → 过渡镜头需精简或增强情绪张力
- 若所有位置得分均低 → 检查整体内容质量或平台匹配问题

---

## 5. AI辅助评分

当缺少真实平台数据时，可用AI对视频/截图打分：

```python
async def ai_rate_shot(video_url: str, criteria: list) -> float:
    """
    AI评分（基于视频内容分析）
    criteria: ["画面构图", "情绪传达", "角色一致性", "场景还原"]
    """
    # 使用Vision模型分析关键帧
    frames = extract_key_frames(video_url, count=3)
    analysis = await vision_model.analyze(
        frames,
        prompt="从以下维度评分（1-5分）：画面构图、情绪传达、角色一致性、场景还原。"
    )
    # 综合计算
    scores = [analysis[c] for c in criteria]
    return round(sum(scores) / (len(scores) * 5), 3)
```

---

## 6. 评分数据流向

```
平台API / 手动录入
        ↓
  metrics 写入效果日志
        ↓
  compute_effect_score()
        ↓
  effect_score + 等级标签
        ↓
  ├─ score ≥ 0.8 → 触发 Prompt 入库流程
  ├─ score < 0.4 → 触发失败日志记录
  └─ 所有数据 → 喂养进化引擎
```
