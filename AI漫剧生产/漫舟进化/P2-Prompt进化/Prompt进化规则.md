# 漫舟 Prompt 进化规则

> **版本**: 1.0.0
> **文件名**: `Prompt进化规则.md`
> **角色**: 定义 Prompt 如何从历史数据中自动学习和优化
> **维护者**: 漫舟 Agent

---

## 1. 进化触发条件

```
触发条件: 同一场景类型累计 ≥ 5 个镜头有评分数据
         且 success_rate 有统计意义（至少2个成功案例）
```

**场景类型定义**:
- 按 `tags[场景标签]` 聚合（如"都市职场"、"古风国潮"）
- 或按 `subcategory` 聚合（如"MS中景-对话"）

---

## 2. 进化算法（5步闭环）

### Step 1: 聚类分析

```python
def cluster_shots(effect_log: list, scene_tag: str) -> list[list[dict]]:
    """
    将相似镜头聚类
    scene_tag: "都市职场" / "古风国潮" 等
    """
    target_shots = [s for s in effect_log if scene_tag in s.get("tags", [])]
    # 按 SRL 位置分组（Pressure/Release/Vacuum）
    clusters = {}
    for shot in target_shots:
        pos = shot.get("srl_position", "Unknown")
        clusters.setdefault(pos, []).append(shot)
    return clusters
```

### Step 2: 词频提取

```python
def extract_high_value_keywords(prompt_list: list[str],
                                 score_threshold: float = 0.7) -> dict:
    """
    提取高评分Prompt的共有关键词
    返回: {"关键词": 权重分数}
    """
    from collections import Counter
    # 分离高分组和低分组
    high_group = [p for p in prompt_list if p["score"] >= score_threshold]
    low_group = [p for p in prompt_list if p["score"] < score_threshold]

    high_words = Counter(tokenize(" ".join([p["text"] for p in high_group])))
    low_words = Counter(tokenize(" ".join([p["text"] for p in low_group])))

    # 计算每个词的权重分数 = 高分频率 - 低分频率
    result = {}
    for word, count in high_words.items():
        result[word] = (count / len(high_group)) - (low_words.get(word, 0) / max(len(low_group), 1))
    return {k: v for k, v in sorted(result.items(), key=lambda x: -x[1]) if v > 0}
```

### Step 3: 权重提升

```python
def boost_keywords(new_prompt: str, high_value_keywords: dict) -> str:
    """
    将高权重关键词注入Prompt
    策略: 关键词放在Prompt前部（权重更高）
    """
    prompt_words = new_prompt.split()
    boosted = []
    for word in prompt_words:
        if word in high_value_keywords:
            # 高权重词重复一次，增强权重
            boosted.extend([word, word])
        else:
            boosted.append(word)
    return " ".join(boosted)
```

### Step 4: 模板生成

```python
def generate_prompt_template(high_value_keywords: dict,
                              scene_tag: str,
                              shot_type: str) -> PromptTemplate:
    """
    生成新的标准Prompt模板
    """
    # 取权重最高的前10个关键词
    top_keywords = list(high_value_keywords.keys())[:10]

    # 构建模板骨架
    template = {
        "id": f"tpl_{scene_tag}_{shot_type}_{uuid4()[:6]}",
        "scene_tag": scene_tag,
        "shot_type": shot_type,
        "template": f"{' '.join(top_keywords)}, {shot_type}, {scene_tag}, cinematic, high quality",
        "keywords": top_keywords,
        "created_by": "evolution_engine",
        "version": 1
    }
    return template
```

### Step 5: 入库验证

**新模板入库规则**:
```
入库 → 测试使用 ≥ 3 次 → 验证 success_rate ≥ 0.7 → 升级为"已验证模板"
```

```python
def validate_template(template: PromptTemplate, min_trials: int = 3) -> bool:
    """
    验证新模板是否值得入库
    """
    trials = get_template_trials(template["id"])
    if len(trials) < min_trials:
        return False
    success_count = sum(1 for t in trials if t["effect_score"] >= 0.6)
    success_rate = success_count / len(trials)
    return success_rate >= 0.7
```

---

## 3. 进化决策树

```
累计 ≥ 5 个同类镜头数据？
    │
    ├── 否 → 继续累积数据，不触发进化
    │
    └── 是 → 执行进化算法
              │
              ├── 高分组关键词提取成功？
              │   ├── 否 → 数据不足，需更多样本
              │   │
              │   └── 是 → 生成新模板
              │            │
              │            ├── 验证通过（≥3次，success_rate≥0.7）
              │            │   → 入库为"已验证模板"
              │            │   → 通知漫舟Agent优先使用
              │            │
              │            └── 验证失败
              │                → 记录失败原因
              │                → 调整关键词权重，重新测试
```

---

## 4. 与 P0/P1 的数据闭环

```
P1 效果追踪 → 产出 effect_score + tags
        ↓
P2 进化引擎 → 聚类分析 + 词频提取 + 模板生成
        ↓
验证通过 → Prompt 入库成功库
        ↓
漫舟Agent → 新镜头复用验证通过模板
        ↓
复用数据 → 补充 P1 效果日志
        ↓
再次触发进化 → 形成正向飞轮
```

---

## 5. 进化安全护栏

**禁止事项**:
- 进化过程中不得删除原始成功Prompt（保留回滚能力）
- 新模板首次使用需人工确认（不得全自动发布）
- 发现生成内容违反安全规则 → 立即停止进化流程

**回滚机制**:
- 每个新模板有 `parent_prompt_id` 可追溯
- 若新模板连续3次失败 → 自动回退到父模板
