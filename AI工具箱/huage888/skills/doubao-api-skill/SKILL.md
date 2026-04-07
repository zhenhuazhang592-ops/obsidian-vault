---
name: doubao-api-skill
description: Doubao/即梦视频/图片生成 API 调用 Skill。触发场景：huage888 需要自动化生成视频片段或角色图时。
---

# doubao-api-skill — Doubao API 视频/图片生成

> huage888 系统 | 阶段三附 | 自动化视频生成
> 依赖：`config/doubao_pipeline.py`
> 模型：Seedance 2.0（视频）/ Seedream 5.0（图片）

---

## 一、环境配置

```bash
# 必填
export ARK_API_KEY="your_api_key_here"

# 可选（已有默认值）
export ARK_BASE_URL="https://ark.cn-beijing.volces.com/api/v3"

# 测试连接
python3 config/doubao_pipeline.py --test
```

**API Key 获取：** https://console.volcengine.com/ark/region:ark+cn-beijing/apikey

---

## 二、模型速查

| 任务 | 模型 | Model ID |
|------|------|----------|
| 文生视频 | Seedance 2.0 | `doubao-seedance-2-0-260128` |
| 图生视频 | Seedance 2.0 | `doubao-seedance-2-0-260128` |
| 首尾帧视频 | Seedance 2.0 | `doubao-seedance-2-0-260128` |
| 文生图片 | Seedream 5.0 | `doubao-seedream-5-0-260128` |
| 图片参考 | Seedream 5.0 | `doubao-seedream-5-0-260128` |

---

## 三、API 调用方式

### 3.1 视频生成（推荐）

```bash
python3 config/doubao_pipeline.py \
  --video \
  --prompt "古风少女在赛博竹林中缓缓睁眼，金色瞳孔中数据流流动 --wm true --dur 5" \
  --output /tmp/video_001.mp4
```

### 3.2 图片生成

```bash
python3 config/doubao_pipeline.py \
  --image \
  --prompt "古风少女，黑色道姑髻，发簪为流动墨滴形状，金色瞳孔带数据流光晕，超写实，电影级，8K" \
  --output /tmp/character_001.png
```

### 3.3 首尾帧视频

```bash
python3 config/doubao_pipeline.py \
  --video \
  --prompt "小女孩长大了，戴上了眼镜" \
  --img1 /path/to/first_frame.png \
  --img2 /path/to/last_frame.png \
  --output /tmp/video_transition.mp4
```

### 3.4 批量视频（分镜脚本）

```bash
# 从分镜脚本批量生成
python3 config/doubao_pipeline.py \
  --batch \
  --shots-file outputs/02-storyboard-script.md \
  --shots-column libtvPrompt \
  --output-dir outputs/videos/
```

---

## 四、角色一致性 Prompt 模板（赛博墨韵风格）

> 用于分镜脚本中，为每个镜头生成符合漠玫 IP 的视频 Prompt

### 4.1 主体描述模板

```
[角色名] · [场景] · [动作]

▸ 主体：[C001 漠玫] 在 [S001 赛博竹林] 中 [睁眼，数据流从指尖蔓延]
▸ 服装：道袍，丝绸与电路板纹理混合，金色滚边
▸ 光效：青蓝色数据粒子漂浮，轮廓发光感
▸ 表情：平静中带着一丝忧伤，眼神深邃
▸ 画风：超写实，电影级质感，8K，景深效果
```

### 4.2 运镜描述模板

```
镜头[运动方式]至[景别]，
[主体动作描述]，
[光影特效]，
[情绪氛围]

例：镜头缓缓推进至特写，
漠玫右手抬起，指尖发出青蓝色光芒，
数据流从指尖蔓延至全身，衣袖随风飘动，
营造神秘高冷氛围。
```

### 4.3 完整视频 Prompt 示例

**输入分镜：**
```
镜头号：03 | 景别：近景 | 运镜：缓慢推镜头 | 时长：5s
漠玫在赛博竹林中睁眼，金色瞳孔数据流闪烁，
指尖发光，青蓝色粒子漂浮
```

**输出 Doubao Prompt：**
```
古风少女在赛博竹林中缓缓睁眼，
金色瞳孔中数据流闪烁流动，
右手抬起，指尖发出青蓝色光芒，
数据流从指尖蔓延至全身，衣袖随风飘动，
背景竹竿嵌有微型电路，竹叶间漂浮发光粒子，
光影：青蓝色冷调，轮廓发光感，
氛围：神秘高冷，电影级质感
--wm true --dur 5
```

---

## 五、运镜 Prompt 库

> 分镜脚本中的运镜方式 → Doubao 视频 Prompt 映射

| 运镜方式 | Doubao Prompt 写法 |
|---------|-----------------|
| 固定 | 镜头固定，主体动作，[环境描述] |
| 推镜头 | 镜头缓缓推向[主体/面部]，主体[动作/表情变化] |
| 拉镜头 | 镜头缓缓拉远，[主体]从[特写/近景]变为[中景/全景]，环境展开 |
| 横移 | 镜头平移，[主体]从左至右[动作]，背景[变化] |
| 摇镜头 | 镜头围绕[主体]旋转，[主体]保持[动作/表情] |
| 升降 | 镜头从低处升起（或高处降下），[主体]逐渐进入画面，[场景]展开 |
| 跟拍 | 镜头跟随[主体]移动，[主体]在[场景]中[动作]，视角同步 |
| 甩镜头 | 镜头快速甩至[主体/场景]，动感转场，[原主体]虚化 |
| 缓慢推 | 镜头缓慢推向[主体/面部]，营造[情绪/氛围]感 |
| 缓慢拉远 | 镜头缓慢拉远，[主体/场景]逐渐展开，[情绪]释放 |

---

## 六、光影 Prompt 库

> 分镜脚本中的光影描述 → Doubao 视频 Prompt 映射

### 6.1 光源类型

| 光源 | Doubao Prompt 写法 |
|------|-----------------|
| 自然月光 | 月光从[方向]洒下，光线[强度] |
| 霓虹光 | 青色/蓝色霓虹光，光影流动 |
| 轮廓光 | 主体轮廓发出[颜色]光芒，[效果] |
| 粒子光 | 数据粒子漂浮，发光粒子飘落 |
| 混合光 | [光源A] + [光源B] 混合，[效果] |

### 6.2 色温关键词

| 色温 | Doubao Prompt 关键词 |
|------|-------------------|
| 冷调 | 青蓝色，冷调，神秘，禁欲 |
| 暖调 | 金黄色，暖光，柔和，舒适 |
| 中性 | 自然光，平衡，真实 |

### 6.3 赛博墨韵光影模板

```
光源：顶部（数据粒子雨光）+ 地面青色反射
色温：冷青（#00FFD4）
强度：低（神秘感）
特效：
  - 竹竿嵌有微型电路，发出青蓝色微光
  - 竹叶间漂浮发光粒子（数据流可视化）
  - 漠玫轮廓有淡淡青色发光感（仙气）
  - 地面水墨山水纹理反射
```

---

## 七、角色六层 Prompt 模板（直接生成用）

### 漠玫（C001）— 角色一致性描述

```
古风少女，黑色道姑髻，发簪为流动墨滴形状，
金色瞳孔带数据流光晕，青蓝色水墨眼线，
道袍材质为丝绸与电路板纹理混合，金色滚边，
腰间悬挂发光玉佩，刻有电路纹理，
背景为赛博竹林，竹竿嵌有微型电路，
竹叶间漂浮青蓝色发光粒子，
光影：冷青色调，轮廓发光感，
画风：超写实，电影级，8K，景深效果
```

### 大圣三变体 — 角色一致性描述

**C002a — 狼狈相：**
```
大圣初见漠玫，被其禅意震慑，
毛发凌乱，道袍破损，金箍暗淡，
眼神从傲慢转为困惑，
光影：暗色调，红蓝光效，
画风：超写实，电影级，8K
```

**C002b — 爆发相：**
```
大圣爆发，金箍发出耀眼光芒，
火眼金睛全开，法天象地气势，
毛发竖立，战意腾腾，
光影：金色爆发光，暖色调，高对比度，
画风：超写实，电影级，8K
```

**C002c — 巅峰相：**
```
大圣巅峰形态，平视漠玫，
眼神中多了几分敬佩，
金箍光芒内敛，气势沉稳，
光影：中性色调，轮廓发光感，
画风：超写实，电影级，8K
```

---

## 八、API 参数详解

### 8.1 视频生成参数

```python
client.content_generation.tasks.create(
    model="doubao-seedance-2-0-260128",
    content=[{
        "type": "text",
        "text": "[完整视频 Prompt] --wm true --dur [秒数]"
    }]
)
```

| 参数 | 说明 |
|------|------|
| `--wm true` | 无水印（商业使用必须） |
| `--dur 5` | 时长（5秒，Seedance 2.0 支持 5-10s） |

### 8.2 图片生成参数

```python
client.images.generate(
    model="doubao-seedream-5-0-260128",
    prompt="[完整图片 Prompt]",
    size="2K",
    extra_body={"watermark": False}
)
```

---

## 九、任务状态轮询

```python
import time

task_id = result.id
while True:
    task = client.content_generation.tasks.get(task_id=task_id)
    status = task.status

    if status == "succeeded":
        video_url = task.content.video_url
        print(f"完成：{video_url}")
        break
    elif status == "failed":
        print(f"失败：{task.error}")
        break
    else:
        print(f"状态：{status}，3秒后重试...")
        time.sleep(3)
```

**状态枚举：** `pending` → `processing` → `succeeded` / `failed`

---

## 十、错误处理

| 错误 | 原因 | 解决 |
|------|------|------|
| `401 Unauthorized` | ARK_API_KEY 无效 | 检查环境变量 |
| `403 Forbidden` | 模型未开通 | 开通 Seedance 2.0 |
| `429 Rate Limited` | RPM 超出 | 降低请求频率 |
| `failed` | 内容违规 | 修改 Prompt，去除敏感词 |
| 超时（>120s） | 任务过长 | 减少 prompt 长度或降低分辨率 |
