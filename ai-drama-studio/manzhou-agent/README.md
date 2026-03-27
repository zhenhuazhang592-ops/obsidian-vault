# 漫舟导演Agent v10.1.0

> 机器可验证的AI漫剧分镜脚本生成工具，到分镜截止
> 全局Schema强制约束 + Qwen3-Max 自动化生成

---

## 安装

```bash
cd manzhou-agent
pip install -e .
```

## 快速开始

```bash
# 全新执行（到分镜脚本截止）
manzhou run ./活着-v9 --episode-number 1

# 断点恢复
manzhou run ./活着-v9 --resume

# 查看状态
manzhou status ./活着-v9
```

---

## 架构概览

```
漫舟 v10.0.0 = v9.0.0（CLI状态机）+ v10.0.0（Schema强制层）

Step 0 ──► Step 1 ──► Step 2 ──► Step 3 ──► Step 4.5 ──► Step 7
  项目配置    短剧改编    IP档案     剧本大纲    导演控制塔     分镜脚本
                                                    ↓
                                        SchemaValidator 校验
                                        PromptBuilder 构建
```

**v9.0.0** = 简化版CLI，到分镜脚本（Step 7）截止，后续AI生成由人工执行
**v10.0.0** = 新增Schema强制层（见下方）

---

## Qwen3-Max API 集成

### 环境变量

```bash
export DASHSCOPE_API_KEY="sk-..."
```

### 使用

```python
from manzhou.qwen_client import QwenClient
from manzhou.schema import ShotScript
from manzhou.prompt_builder import PromptBuilder

qwen = QwenClient(api_key="sk-...", model="qwen-max")

# 单镜生成
system = prompt_builder.build_shot_system_prompt("EP01")
result = qwen.generate_shot_prompts(system, shot_context)
print(result["image_prompt"])   # AI生图Prompt
print(result["video_prompt"])   # AI视频Prompt

# 整集批量生成（自动 Schema 校验）
results = qwen.batch_generate_episode_prompts(shots, prompt_builder)
for r in results:
    print(f"{r['shot_id']}: 通过={r['validation']['is_passed']}")
```

### 禁止词豁免规则

Qwen 生成的 Prompt 中，"无美颜、滤镜、特效" 等否定列举格式会被正确识别为合规：
- 单字否定：`无美颜` / `去滤镜` / `不卡通`
- 列举否定：`无美颜、滤镜、特效处理`（整段豁免）
- 直接出现：`使用了美颜滤镜` → **BLOCK**

---

## 文件结构

```
manzhou/
├── cli.py                   # CLI入口（v9.0.0）
├── state_machine.py         # 状态机引擎（v10.0.0 约束传递）
├── schema.py                # 12个Step数据Schema（v10.0.0）
├── schema_validator.py      # Schema校验引擎（D1/D2/D3 + 否定豁免）
├── prompt_builder.py        # Prompt构建器
├── qwen_client.py          # Qwen3-Max API客户端（v10.1.0 NEW）
├── quality_gate.py          # 三维质量门控
├── constants.py             # 枚举/常量（禁止词/情绪矩阵）
└── tests/
    └── test_schema_validator.py  # 12个单元测试
```

---

## v10.0.0 Schema强制架构（三层）

### Layer 1 — Schema契约（schema.py）

每步输出携带显式元数据，保证跨步引用不丢失：

```python
@datum
class ShotScriptMeta:
    char_ids_source:   list[str]   # 必须在 IP档案 中存在
    loc_id_source:     str         # 必须在 IP档案 中存在
    emotion_from_d3:   str         # 必须来自 D3 beat_tracking
    shot_type_from_d4: str         # 必须来自 D4 camera_intent
    prohibited_check:  list[str]   # 必须来自 导演控制塔.prohibited
    style_anchor:      str         # 必须来自项目配置

@datum
class Step45Output:
    shot_emotion_map: dict[str, str]   # {"P01": "L1", "P02": "L2"}
    shot_camera_map:  dict[str, dict]  # {"P01": {"shot_type":"LS","camera_action":"固定"}}
    prohibited_keywords: list[str]
    def get_shot_constraints(shot_id): ...
    def validate_emotion_curve(): ...
```

### Layer 2 — SchemaValidator（schema_validator.py）

D1/D2/D3 可编程评分，BLOCK错误阻断，WARN不阻断：

| 维度 | 权重 | 校验内容 | 阻断 |
|------|------|---------|------|
| D1 完整性 | 0.35 | 必填字段非空、Prompt≥30字 | BLOCK |
| D2 一致性 | 0.35 | char_id/loc_id在IP档案、emotion_level∈L1-L5 | BLOCK |
| D3 指令合规 | 0.30 | 禁止词、情绪跳转矩阵、景别运镜对齐 | BLOCK |

**禁止词策略**：
- 全局禁止词：`美颜、滤镜、卡通化、过度煽情、特效、AI感`
- 风格禁止词（写实）：`唯美滤镜、柔光、磨皮、过度明亮、动漫感`
- **否定式不算违规**：`无美颜、去滤镜` 不触发BLOCK（因为意图是避免该效果）

**情绪跳转矩阵**：

| 从/到 | L1 | L2 | L3 | L4 | L5 |
|-------|----|----|----|----|----|
| L1 | — | ✅ | ✅ | ❌ | ❌ |
| L2 | ✅ | — | ✅ | ✅ | ❌ |
| L3 | ❌ | ✅ | — | ✅ | ❌ |
| L4 | ❌ | ❌ | ✅ | — | ✅ |
| L5 | ❌ | ❌ | ❌ | ✅ | — |

### Layer 3 — 状态机约束传递（state_machine.py）

跨步约束通过 `ProjectSession.constraints` 字典传递：

```python
# Step 7 执行前 → 从 IP档案 和 导演控制塔 加载约束
session.set_step_constraints(StepID.S7, {
    "required_fields": ["shots"],
    "char_id_pool": list(ip_profile.characters.keys()),
    "loc_id_pool": list(ip_profile.locations.keys()),
})

# Step执行前校验
is_valid, error_msg = sm.validate_step_input(step_id, input_data)
```

---

## 使用示例

```python
from manzhou.schema_validator import SchemaValidator
from manzhou.schema import ShotScript, IPProfile, Step45Output

# 初始化校验引擎
validator = SchemaValidator(ip_profile, step45_output)

# 单镜校验
result = validator.validate_shot(shot)
print(f"D1={result.d1_score} D2={result.d2_score} D3={result.d3_score}")
print(f"通过: {result.is_passed}")
for e in result.errors:
    print(f"  [{e.severity}] {e.field}: {e.expected}")

# 整集批量校验
episode_result = validator.validate_episode(shots)
print(f"通过: {episode_result['passed']}/{episode_result['total_shots']}")
print(f"综合分: {episode_result['avg_composite']:.3f}")
validator.print_validation_report(episode_result)
```

---

## PromptBuilder

基于Schema约束构建合规的AI生图/生视频Prompt：

```python
from manzhou.prompt_builder import PromptBuilder

builder = PromptBuilder(
    ip_profile, step45_output,
    style_preset="real",
    aspect_ratio="9:16"
)

# 构建符合导演塔约束的Prompt
img_prompt = builder.build_image_prompt(shot)
vid_prompt = builder.build_video_prompt(shot)

# 生成LLM系统Prompt（带所有约束上下文）
system_prompt = builder.build_shot_system_prompt(episode_shots)
```

---

## 单元测试

```bash
cd manzhou-agent
python3 -m pytest manzhou/tests/test_schema_validator.py -v
```

测试覆盖：

| 测试 | 内容 |
|------|------|
| test_D1_pass | 所有必填字段完整 → 应通过 |
| test_D1_missing_prompt | image_prompt为空 → BLOCK |
| test_D2_char_id_valid | char_id在IP档案 → D2=1.0 |
| test_D2_char_id_invalid | char_id不在IP档案 → BLOCK |
| test_D2_loc_id_invalid | loc_id不在IP档案 → BLOCK |
| test_D3_prohibited_keyword_found | Prompt含禁止词 → BLOCK |
| test_D3_emotion_mismatch_warn | 情绪不符 → WARN（不阻断） |
| test_emotion_jump_allowed | 跳转矩阵边界测试 |
| test_validate_episode_all_pass | 整集无违规 → 优秀 |
| test_validate_episode_one_fails | 一镜含禁止词 → 报告失败镜 |
| test_step45_get_shot_constraints | get_shot_constraints 返回正确约束 |
| test_step45_validate_emotion_curve_pass | 合法曲线 → 0违规 |

---

## 与v8.0.0的核心区别

| 维度 | v8.0.0 | v9.0.0/v10.0.0 |
|------|---------|----------------|
| 流程 | Step 0-11 完整 | Step 0-7 简化（AI生成由人工） |
| 校验 | 文档约定 | 机器可验证Schema |
| Prompt构建 | 大模型自由发挥 | PromptBuilder受约束生成 |
| 禁止词 | 无 | 全局+风格禁止词+否定式豁免 |
| 情绪跳转 | 无 | EMOTION_TRANSITION_MATRIX强制 |
| 测试 | 无 | 12个单元测试 |

---

## Schema版本约定

| 版本 | 说明 |
|------|------|
| v9 | 简化版CLI，到分镜脚本截止 |
| v10 | 新增Schema强制层（当前版本） |
