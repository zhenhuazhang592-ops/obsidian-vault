# 漫舟失败 Prompt 追踪规范

> **版本**: 1.0.0
> **文件名**: `manzhou-failure-log.md`
> **角色**: 积累"什么不该做"的反面知识，防止重复踩坑
> **维护者**: 漫舟 Agent

---

## 1. 失败分类体系

| 类型 | 代码 | 说明 | 典型表现 |
|------|------|------|---------|
| **生成失败** | `GENERATION_FAILED` | 模型无法生成（Prompt冲突/越界） | 画面崩坏、肢体扭曲 |
| **质量低分** | `LOW_QUALITY` | `effect_score < 0.4` | 各项指标均差 |
| **角色崩坏** | `CHARACTER_BREAK` | 与DNA手册不一致 | 角色外观/行为与档案不符 |
| **场景穿帮** | `SCENE_GLITCH` | 逻辑不合理或穿帮 | 物品悬浮/光照不一致 |
| **风格漂移** | `STYLE_DRIFT` | 与整体视觉风格不一致 | 色调/画风突变 |

---

## 2. 失败记录格式

```json
{
  "id": "fail_001",
  "shot_id": "P07",
  "project": "格子间女人",
  "failure_type": "CHARACTER_BREAK",
  "failure_timestamp": "2026-03-25T14:30:00+08:00",
  "original_prompt": "完整原始Prompt原文",
  "failure_reason": "角色服装描述与DNA手册不一致：Prompt写了'红色连衣裙'，但char_01的clothing应为'白衬衫+黑色铅笔裙'",
  "corrected_prompt": "修正后Prompt原文",
  "correction_effect": "修正后在测试中效果_score提升至0.72",
  "related_char_id": "char_01",
  "date": "2026-03-25"
}
```

---

## 3. 失败记录触发时机

| 时机 | 触发条件 | 操作 |
|------|---------|------|
| 生成完成时 | 视频画面明显崩坏 | 记录 `GENERATION_FAILED` |
| 效果评分时 | `effect_score < 0.4` | 记录 `LOW_QUALITY` |
| 发布审核时 | 用户/编辑发现角色问题 | 记录 `CHARACTER_BREAK` |
| 质量抽检时 | AI自动检测到穿帮 | 记录 `SCENE_GLITCH` |
| 风格审查时 | 与整体风格不一致 | 记录 `STYLE_DRIFT` |

---

## 4. 修正流程

```
发现失败记录
    ↓
Step 1: 分析 failure_reason
        - 提取关键词（如"服装颜色错误"）
        - 定位根因（Prompt问题/模型问题/资产问题）
    ↓
Step 2: 生成 corrected_prompt
        - 修正 Prompt 中的具体问题
        - 保持其他有效部分不变
    ↓
Step 3: 记录 correction_effect
        - 重新测试或等待下次评分
        - 更新 effect_score
    ↓
Step 4: 更新防重检查
        - 检查是否有相似失败模式
        - 如有共性 → 提取规则 → 写入 manzhou-safety.md
```

---

## 5. 防重复机制

**触发**: 失败记录入库时，自动检查相似模式

```python
def check_failure_pattern(failure_reason: str) -> bool:
    """
    检查是否命中已知失败模式
    返回 True 表示命中黑名单 → 阻止执行
    """
    patterns = load_safety_blacklist()
    for pattern in patterns:
        if fuzzy_match(failure_reason, pattern["description"]):
            return True
    return False

def extract_common_rule(failure_record: dict) -> dict:
    """
    从失败记录中提取共性规则
    """
    # 提取失败关键词
    keywords = extract_keywords(failure_record["failure_reason"])
    # 检查是否已有相似规则
    existing = find_similar_rule(keywords)
    if existing:
        # 更新规则的触发计数
        existing["trigger_count"] += 1
        existing["example_shots"].append(failure_record["shot_id"])
    else:
        # 创建新规则
        return {
            "rule_id": generate_rule_id(),
            "keywords": keywords,
            "description": summarize_failure(failure_record),
            "trigger_count": 1,
            "example_shots": [failure_record["shot_id"]],
            "created_from": failure_record["id"]
        }
```

---

## 6. 黑名单规则示例

```
# manzhou-safety.md（自动生成，内容摘要）

## CHARACTER_BREAK 黑名单
- ❌ 服装颜色与DNA手册不一致 → 必须引用 asset.clothing
- ❌ 角色身高比例异常 → 添加"realistic proportions"约束

## SCENE_GLITCH 黑名单
- ❌ 室内场景出现自然阴影 → 添加"consistent indoor lighting"
- ❌ 镜面反射内容错误 → 添加"accurate mirror reflection"

## STYLE_DRIFT 黑名单
- ❌ 写实风格场景混入卡通元素 → 添加"maintain consistent style: realistic"
- ❌ 冷色调场景突然出现暖色光源 → 统一光影风格
```

---

## 7. 失败日志文件路径

```
P2-Prompt进化/prompt库/失败/{{项目名}}-失败日志.json
```

**格式**: JSON Lines（每行一条失败记录）
