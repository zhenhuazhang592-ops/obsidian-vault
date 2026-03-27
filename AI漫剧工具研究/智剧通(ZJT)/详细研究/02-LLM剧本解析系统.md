# ZJT（智剧通）· LLM剧本解析系统详细研究报告

## 一、系统概述

ZJT（智剧通）的剧本解析系统是整个AI短剧制作平台的核心引擎，负责将**文字剧本**转换为**结构化分镜数据**。该系统设计精巧，包含约1100行Python代码，分为多个模块协同工作。

### 1.1 文件架构

```
llm/
├── script_parser.py       # 核心解析引擎（约1100行）
├── gemini_client.py       # Gemini API 封装
├── qwen.py               # 通义千问 API 封装
├── baidu.py              # 百度千帆 VL API 封装
└── json_example/
    ├── script_parser_prompt.txt    # Prompt 示例文本
    └── script_parser_example.json   # JSON 结构示例
```

### 1.2 核心入口函数

```python
async def parse_script_to_shots(
    script_content: str,
    max_group_duration: int = 15,
    world_id: Optional[int] = None,
    model: Optional[str] = None,
    temperature: float = 0.7,
    force_medium_shot: bool = False,
    no_bg_music: bool = False,
    split_multi_dialogue: bool = False,
    narration_as_dialogue: bool = False,
) -> Dict[str, Any]
```

---

## 二、SCRIPT_PARSER_SYSTEM_PROMPT 系统提示词深度分析

### 2.1 13条核心规则

| 规则 | 内容 | 借鉴价值 |
|------|------|---------|
| 1 | 严格按JSON格式输出 | ★★★ |
| 2 | 分镜组默认15秒 | ★★ |
| 3 | 人物信息完整 | ★★ |
| **4** | **【严禁外貌描写】分镜描述中不写外貌，外貌由角色库管理** | ★★★★★ |
| **5** | **场景嵌套层级**（parent_id + level） | ★★★★ |
| **6** | **location_db_id 数据库关联** | ★★★★★ |
| **7** | **props_db_id 数据库关联** | ★★★★★ |
| 8 | props_present 分镜道具关联 | ★★★★ |
| 9 | 分镜详细字段（类型/运动/对话/动作） | ★★ |
| **10** | **opening_frame_description 是最关键字段** | ★★★★★ |
| 11 | ID引用关系正确性 | ★★★ |
| **12** | **【【】】角色标记系统** | ★★★★★ |
| 13 | ID格式规范 | ★★ |

### 2.2 规则4详解：严禁外貌描写

```
在分镜描述中严禁描写人物外貌特征：系统的角色库中已有完整的外貌信息，
在所有分镜相关字段中，只需要提及角色名称（用【【角色名】】格式），
不要描述角色的外貌、服装、发型、身材等任何外观特征
```

**设计动机**：解决AI生成图像时"外貌漂移"痛点。角色的外貌一致性由角色库（CDP）统一管理，分镜脚本只负责引用。

### 2.3 规则12详解：【【】】角色标记系统

**标记语法**：`【【角色名】】`

**使用场景**：
- 所有shot节点的文本字段（description、opening_frame_description、scene_detail、action）
- dialogue中的character_name字段

**系统处理流程**：
```
1. LLM生成JSON时，在角色名两侧添加【【】】标记
2. 后处理系统提取所有【【】】包裹的文本
3. 与角色库（CDP）中的角色名进行匹配
4. 生成参考图时，确保角色一致性
```

**禁止使用【【】】的场景**：场景名称、地点名称、物品名称、道具名称

---

## 三、四大特殊参数深度解析

### 3.1 force_medium_shot（强制中景）

**触发条件**：`force_medium_shot=True`

**核心规则**：
- 所有包含对话的镜头，shot_type禁止使用"全景"或"远景"
- 对话镜头应该使用"近景"或"中景"
- opening_frame_description必须在开头明确标注"近景："或"中景："

**设计动机**：Sora等视频生成模型在全景对话场景中效果较差（多人面部难以生成清晰），强制使用近景/中景可确保质量。

### 3.2 no_bg_music（禁用背景音乐）

```
所有shot节点的background_music字段必须设置为null或空字符串
不要生成任何背景音乐描述
这是为了方便后期调音处理
```

### 3.3 split_multi_dialogue（多人对话拆分）【核心亮点】

**核心规则**：
```
当一个镜头中有多个角色对话时，必须将该镜头拆分为多个单人对话镜头
【关键】每个拆分后的镜头只能包含一个角色的对话
```

#### 180度轴线原则

```
假设两个角色A和B对话，建立一条虚拟的轴线连接两人
摄像机必须始终保持在轴线的同一侧拍摄
正确示例：角色A在画面左侧面向右，角色B在画面右侧面向左（正反打）
错误示例：角色A和B都面向同一方向，或者位置关系突然颠倒
```

#### 拆分示例

**原镜头（错误）**：
```json
{
  "description": "【【A】】和【【B】】在咖啡厅对话",
  "opening_frame_description": "中景：【【A】】和【【B】】坐在咖啡厅...",
  "dialogue": [
    {"character_id": "A", "text": "你好吗？"},
    {"character_id": "B", "text": "我很好，谢谢"}
  ]
}
```

**拆分后（正确）**：
```json
// 镜头1：只有A说话
{
  "description": "【【A】】说话",
  "opening_frame_description": "中景：【【A】】坐在咖啡厅的座位上，身体微微前倾，双手放在桌上，面带微笑，眼神看向画面右侧（镜头外），嘴唇微动正在说话",
  "characters_present": ["char_001"],
  "dialogue": [{"character_id": "A", "text": "你好吗？"}]
}

// 镜头2：只有B回应
{
  "description": "【【B】】回应",
  "opening_frame_description": "中景：【【B】】坐在咖啡厅的另一侧座位，身体放松靠在椅背上，双手交叉放在胸前，面带笑容，眼神看向画面左侧（镜头外），点头回应",
  "characters_present": ["char_002"],
  "dialogue": [{"character_id": "B", "text": "我很好，谢谢"}]
}
```

### 3.4 narration_as_dialogue（旁白视为对话）

**注入的Prompt规则**：
```python
- 在characters数组中自动创建特殊角色：
  * id: "char_narrator"
  * name: "旁白"
  * role: "旁白"
- dialogue格式：{"character_id": "char_narrator", "character_name": "【【旁白】】", "text": "旁白内容"}
```

---

## 四、reorganize_shot_groups() 重组算法

### 4.1 核心策略：贪心算法

```
1. 提取所有shots并按shot_number排序（保持全局顺序）

2. 按顺序遍历shots，根据时长限制进行分组：
   - 如果 current_group_duration + shot_duration > max_group_duration
     → 创建新组
   - 否则
     → 加入当前组

3. 每个分镜组的总时长尽可能接近但不超过 max_group_duration
```

### 4.2 时长限制硬规则

```
【硬性规则】每个shot_group内所有shots的duration总和绝对不能超过{max_group_duration}秒

【强制分组规则】相同地点(location_id相同)的连续镜头，
只要总时长不超过{max_group_duration}秒，必须强制放在同一个shot_group中，禁止拆分

【成本优化要求】每个shot_group的总时长应该尽可能接近{max_group_duration}秒（建议≥12秒），避免浪费
```

**正确示例**：
- 镜头1(地点A, 8秒) + 镜头2(地点A, 7秒) = 15秒 → 必须放在同一个shot_group中 ✓

**错误示例**：
- 镜头1(地点A, 8秒)单独一组，镜头2(地点A, 7秒)单独一组 → 违反规则，浪费成本 ✗

### 4.3 镜头时长合理性要求

| 镜头类型 | 建议时长 |
|---------|---------|
| 特写/近景 | 2-5秒 |
| 中景/全景 | 3-8秒 |
| 远景 | 5-10秒 |
| 对话镜头 | 3-8秒（根据台词） |
| 动作镜头 | 5-12秒 |

---

## 五、convert_script_to_narration() 旁白解说剧转换

### 5.1 功能说明

将包含角色对话的剧本转换为**纯旁白解说格式**的剧本。

### 5.2 输出格式要求

```
每个场景包含两部分：
- 【画面描述】：详细描述该场景中的画面内容
- 【旁白台本】：用第三人称旁白的方式叙述故事
```

### 5.3 转换示例

**原始剧本**：
```
角色A：今天天气真好啊！
角色B：是啊，我们去郊游吧。
```

**转换后**：
```
【画面描述】
阳光明媚的周末早晨，A站在窗前伸了个懒腰，脸上洋溢着愉悦的笑容。B从厨房走出来，手里端着两杯咖啡。

【旁白台本】
"A看了看窗外，感叹道天气宜人。B提议不如去郊外踏青，享受这难得的悠闲时光。"
```

---

## 六、opening_frame_description 写法规范

### 6.1 ZJT 的规范要求

```
必须详细描述镜头开始时的静态画面
必须包含：人物位置、姿态、表情、服装
必须包含：场景布局、物品摆放，光线方向和强度
必须包含：构图信息（如三分法、景深、视角等）
描述要具体到能让AI准确还原画面
涉及角色名称时必须用【【角色名】】格式包裹
```

### 6.2 ZJT 示例

```json
{
  "opening_frame_description": "客厅中景，【【小李】】坐在沙发上，身体微微后靠，
双手捧着咖啡杯。落地窗在背景中，晨光勾勒出他的轮廓。茶几上放着一本书。"
}
```

---

## 七、数据库关联机制

### 7.1 location_db_id 匹配逻辑

```python
# 加载数据库场景
db_locations = LocationModel.get_tree_by_world(world_id=world_id, limit=20)

# 格式化为提示词
db_locations_text = """
**【数据库已有场景列表】**
- ID: 123, 名称: 现代办公室, 描述: 写字楼内的开放式办公区
- ID: 124, 名称: 咖啡厅, 描述: 温馨的咖啡厅，有落地窗

**【重要警告】关于location_db_id字段：**
- 只能使用上面列表中显示的ID，不能使用其他任何数字
- 严禁编造或随意填写不存在的location_db_id！
"""
```

### 7.2 props_db_id 匹配逻辑

```python
# 加载数据库道具
props_result = PropsModel.list_by_world(world_id=world_id, page=1, page_size=50)

# 格式化为提示词
db_props_text = """
**【数据库已有道具列表】**
- ID: 456, 名称: 智能手机, 描述: 黑色iPhone手机
- ID: 457, 名称: 咖啡杯, 描述: 白色陶瓷咖啡杯

**【重要警告】关于props_db_id字段：**
- 只能使用上面列表中显示的ID，不能使用其他任何数字
- 严禁编造或随意填写不存在的props_db_id！
"""
```

---

## 八、JSON 解析失败修复策略

### 8.1 三层修复机制

```python
# 第一层：清理 markdown 标记
if cleaned_content.startswith("```json"):
    cleaned_content = cleaned_content[7:]
if cleaned_content.startswith("```"):
    cleaned_content = cleaned_content[3:]
if cleaned_content.endswith("```"):
    cleaned_content = cleaned_content[:-3]

# 第二层：尝试解析
try:
    parsed_data = json.loads(cleaned_content)

# 第三层：截断修复（如果JSON被截断）
except json.JSONDecodeError as e:
    if not cleaned_content.endswith('}'):
        last_bracket = cleaned_content.rfind(']')
        if last_bracket > 0:
            fixed_content = cleaned_content[:last_bracket+1] + '\n}'
            parsed_data = json.loads(fixed_content)
```

---

## 九、日志保存系统

```python
ENABLE_SCRIPT_PARSER_LOGGING = True  # 设置为 True 启用详细日志
```

| 文件名 | 内容 |
|--------|------|
| `{timestamp}_00_SUMMARY.txt` | 解析总结 |
| `{timestamp}_01_system_prompt.txt` | 系统提示词 |
| `{timestamp}_02_user_prompt.txt` | 用户提示词 |
| `{timestamp}_03_input_script.txt` | 原始剧本 |
| `{timestamp}_04_raw_response.txt` | LLM原始响应 |
| `{timestamp}_05_cleaned_content.txt` | 清理后内容 |
| `{timestamp}_06_parsed_success.json` | 解析成功JSON |
| `{timestamp}_07_reorganize_info.txt` | 分镜组重组信息 |
| `{timestamp}_ERROR_parse_failed.txt` | 解析失败错误信息 |

---

## 十、与漫舟 manzhou-shot-script.md 对比分析

| 维度 | ZJT | 漫舟 |
|------|-----|------|
| 剧本解析入口 | `parse_script_to_shots()` | `manzhou-shot-script.md` |
| 分镜格式 | JSON结构 | Markdown + 双Prompt |
| 镜头分组 | `shot_groups` 数组 | 九宫格分镜表 |
| 时长控制 | `max_group_duration` 参数 | 固定 15s/镜 |
| 角色引用 | 【【角色名】】 | `[ID: TanBin_V1]` |
| 场景嵌套 | parent_id + level | 扁平场景 |
| 道具关联 | props_db_id | 无 |

### ZJT 独有的核心设计

1. **数据库关联机制**（location_db_id / props_db_id）
2. **多人对话拆分 + 180度轴线规则**
3. **解说剧模式**（narration_as_dialogue）
4. **强制中景对话**（force_medium_shot）
5. **JSON截断自动修复**
6. **完整日志系统**

### 漫舟独有的核心设计

1. **双Prompt分离**（imagePrompt + videoPrompt）
2. **九宫格分镜图生成**
3. **--cref 参考图引用**
4. **Lip-sync 唇形同步标注**
5. **风格后缀参数块**（16种）
6. **时长达标公式**（120秒目标）

---

## 十一、推荐借鉴的设计

### 高优先级（可立即落地）

| 设计 | 借鉴价值 | 落地文件 |
|------|---------|---------|
| 180度轴线 + 多人对话拆分 | ★★★★★ | manzhou-shot-script.md |
| 数据库关联机制 | ★★★★ | manzhou-master.md |
| 【【】】角色标记系统 | ★★★★ | manzhou-character-design.md |
| JSON截断自动修复 | ★★★★★ | ai-drama-studio AI解析模块 |
| 完整日志系统 | ★★★ | ai-drama-studio |

### 中优先级（需要改造）

| 设计 | 借鉴价值 | 落地文件 |
|------|---------|---------|
| 分镜组时长重组算法 | ★★★ | manzhou-shot-script.md |
| 场景嵌套层级 | ★★★ | manzhou-master.md |
| 强制中景对话 | ★★★ | manzhou-shot-script.md |
