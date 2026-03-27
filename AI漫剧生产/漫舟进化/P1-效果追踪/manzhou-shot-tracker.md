# 漫舟镜头级效果埋点规范

> **版本**: 1.0.0
> **文件名**: `manzhou-shot-tracker.md`
> **角色**: 为每个镜头生成建立可追踪的效果数据档案
> **维护者**: 漫舟 Agent

---

## 1. 埋点数据结构

```json
{
  "shot_id": "P01",
  "project": "{{项目名}}",
  "episode": 1,
  "shot_sequence": 1,
  "timestamp": "{{ISO时间}}",
  "image_prompt": "{{原始imagePrompt}}",
  "video_prompt": "{{原始videoPrompt}}",
  "generated_video_url": "{{视频URL或本地路径}}",
  "platform_metrics": {
    "play_count": 0,
    "completion_rate": 0.0,
    "like_count": 0,
    "comment_count": 0,
    "share_count": 0
  },
  "manual_rating": null,
  "ai_rating": null,
  "effect_score": 0.0,
  "tags": ["{{爆款标签}}"],
  "srl_position": "Pressure|Release|Vacuum",
  "status": "generated|published|scored"
}
```

---

## 2. 埋点时机

| 时机 | 触发条件 | 写入字段 |
|------|---------|---------|
| **生成时** | 视频生成完成 | `generated_video_url`, `image_prompt`, `video_prompt`, `timestamp` |
| **发布后** | 发布到抖音/快手等平台 | `platform_metrics`（定期更新） |
| **评分时** | 用户评分或AI评分完成 | `manual_rating` / `ai_rating`, `effect_score` |
| **打标签时** | 人工或AI打标签 | `tags` |

---

## 3. 与 SRL 情绪模型的联动

每个镜头的 `srl_position` 字段标记其在 SRL 模型中的位置：

| SRL阶段 | 说明 | 典型得分特征 |
|---------|------|------------|
| **Pressure** | 压点（冲突/困境） | 完播率高（用户好奇结局） |
| **Release** | 释放点（解决/揭露） | 分享率高（用户想转发） |
| **Vacuum** | 真空点（平静/过渡） | 得分偏低（正常现象） |

**统计价值**: 追踪哪种 SRL 位置得分最高 → 反哺剧本节奏规则

---

## 4. 数据写入规范

### 生成时写入（自动）

```python
def log_shot_generated(shot_id: str, project: str, episode: int,
                       image_prompt: str, video_prompt: str,
                       video_url: str) -> dict:
    """镜头生成时调用，向效果日志追加记录"""
    record = {
        "shot_id": shot_id,
        "project": project,
        "episode": episode,
        "shot_sequence": extract_sequence(shot_id),
        "timestamp": datetime.now().isoformat(),
        "image_prompt": image_prompt,
        "video_prompt": video_prompt,
        "generated_video_url": video_url,
        "platform_metrics": {
            "play_count": 0, "completion_rate": 0.0,
            "like_count": 0, "comment_count": 0, "share_count": 0
        },
        "manual_rating": None,
        "ai_rating": None,
        "effect_score": 0.0,
        "tags": [],
        "srl_position": infer_srl_position(shot_id),
        "status": "generated"
    }
    append_to_effect_log(project, record)
    return record
```

### 评分时更新（手动或定时）

```python
def update_shot_score(shot_id: str, manual_rating: float = None,
                     ai_rating: float = None, tags: list = None) -> None:
    """更新镜头评分和标签"""
    record = find_in_effect_log(shot_id)
    if manual_rating is not None:
        record["manual_rating"] = manual_rating
    if ai_rating is not None:
        record["ai_rating"] = ai_rating
    if tags:
        record["tags"] = tags
    # 计算综合评分
    record["effect_score"] = compute_effect_score(record)
    record["status"] = "scored"
    save_effect_log()
```

---

## 5. 效果日志文件路径

```
P1-效果追踪/效果数据/{{项目名}}-效果日志.json
```

**格式**: JSON Lines（每行一条记录，便于追加）

---

## 6. 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `shot_id` | string | 镜头ID，如 `P01`, `ep01_sh01` |
| `project` | string | 项目名，如 `格子间女人` |
| `episode` | number | 集号 |
| `shot_sequence` | number | 镜头序号（集内） |
| `timestamp` | string | ISO 8601 时间戳 |
| `image_prompt` | string | AI生图Prompt原文 |
| `video_prompt` | string | AI生视频Prompt原文 |
| `generated_video_url` | string | 生成视频的URL或本地路径 |
| `play_count` | number | 播放次数（平台API获取） |
| `completion_rate` | float | 完播率（0.0-1.0） |
| `like_count` | number | 点赞数 |
| `comment_count` | number | 评论数 |
| `share_count` | number | 分享数 |
| `manual_rating` | float | 人工评分（1-5），null表示未评分 |
| `ai_rating` | float | AI评分（1-5），null表示未评分 |
| `effect_score` | float | 综合效果评分（0.0-1.0） |
| `tags` | string[] | 爆款标签，如 `["职场", "悬疑", "女性成长"]` |
| `srl_position` | string | SRL情绪模型位置 |
| `status` | string | `generated` / `published` / `scored` |
