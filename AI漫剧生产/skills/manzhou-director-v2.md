# 漫舟·导演版 — 从LibTV Agent完整执行层脱胎

> 版本: 2.4.0
> 日期: 2026-03-26
> 定位: 漫舟 + LibTV 一体化Agent
> 核心: 复用LibTV Agent执行层 + 漫舟创作理解能力 = 比LibTV Agent更强的导演级Agent

---

## 一、能力定位

### 与LibTV Agent的对比

| 能力模块 | LibTV Agent | 漫舟·导演版 |
|---------|-------------|------------|
| **执行层（API调用）** | ✅ 完整 | ✅ 完整复用 |
| **轮询+下载** | ✅ 完整 | ✅ 完整复用 |
| **上传参考图** | ✅ 完整 | ✅ 完整复用 |
| **小说理解** | ❌ | ✅ |
| **IP解析** | ❌ | ✅ |
| **剧本生成** | ❌ | ✅ |
| **导演控制塔** | ❌ | ✅ |
| **角色DNA** | ❌ | ✅ |
| **分镜编排** | ❌ | ✅ |
| **运镜意图传递** | ❌ | ✅ |
| **爆款算法** | ❌ | ✅ |
| **短剧化改编** | ❌ | ✅ |
| **忠实转录** | ❌ | ✅ |
| **Canvas双审核（LibTV聊天界面）** | ❌ | ✅ v2.3.0 |

### 核心差异

```
LibTV Agent = "传话筒"
  └─ 接收自然语言 → 直接发API → 无法理解创作意图

漫舟·导演版 = "总导演"
  └─ 理解小说 → 生成剧本 → 导演分析 → 分镜脚本 → Canvas双审核 → 轮询拉回 → 成片

v2.3.0 执行原理：
  └─ Canvas = AI聊天界面（不是节点编辑器）
  └─ create_session发消息 → AI处理 → query_session轮询URL
  └─ 用户只负责审核质量，Agent负责发消息+拉结果
```

---

## 二、用户输入场景

### 场景1：小说 → 完整漫剧

```
用户：请帮我把这个小说做成AI漫剧

[粘贴小说文本]

漫舟·导演版执行：
  ✅ 短剧化改编（剃刀法则）
  ✅ IP解析
  ✅ 剧本生成（忠实转录）
  ✅ 导演控制塔
  ✅ 分镜脚本
  ✅ LibTV执行
  ✅ 视频产出
```

### 场景2：已有项目 → 生成视频

```
用户：帮我把格子间女人的第1集生成视频

漫舟·导演版执行：
  ✅ 读取已有分镜脚本
  ✅ 生成LibTV指令
  ✅ 上传角色参考图
  ✅ 逐镜发送到LibTV
  ✅ 轮询+下载
  ✅ 视频产出
```

### 场景3：指定分镜 → 单镜生成

```
用户：生成第3集第5镜的视频

漫舟·导演版执行：
  ✅ 读取指定分镜
  ✅ 生成LibTV指令
  ✅ 执行单镜
  ✅ 返回结果
```

---

## 三、执行流程（Step by Step）

### Step 0: 环境检查

```bash
# 检查LibTV Access Key
echo $LIBTV_ACCESS_KEY

# 检查脚本路径
ls $LIBTV_DIR/scripts/

# 必要环境变量
export LIBTV_ACCESS_KEY="your-access-key"
export LIBTV_DIR="/path/to/libtv-skills-main/skills/libtv-skill"
```

### Step 1: 小说输入 → 短剧化改编

```
输入：小说原文

处理：
  ├─ 剃刀法则（30:1压缩）
  ├─ 开场5秒抓人（撞破/打脸/揭穿/威胁）
  ├─ 台词≤15字
  ├─ 情绪过山车（每45秒一个爽点）
  └─ 视觉外化（内心→动作/表情）

输出：短剧化改编脚本
```

### Step 2: IP解析

```
输入：短剧化改编脚本

处理：
  ├─ 提取角色 → char_01, char_02...
  ├─ 提取场景 → loc_01, loc_02...
  ├─ 提取道具 → item_01, item_02...
  └─ 生成IP档案.yaml

输出：01-IP档案/IP档案.yaml
```

### Step 3: 剧本生成（忠实转录）

```
输入：IP档案 + 短剧化改编脚本

处理：
  ├─ 镜头拆分（每动作=1镜）
  ├─ 多角色对话拆分（每人1镜）
  ├─ 景别匹配
  ├─ 视听翻译（文学→镜头语言）
  └─ 情绪/SFX标注

输出：02-剧本/第XX集-剧本.md
```

### Step 4: 导演控制塔

```
输入：剧本

处理：
  ├─ 应用救猫咪15节拍表
  ├─ 输出场景节拍表（6种功能）
  ├─ 输出运镜意图指令
  ├─ 180度轴线约束
  └─ 节拍追踪（情绪L1-L5）

输出：03-导演分析/第XX集-导演控制塔.md
```

### Step 5: 分镜脚本

```
输入：剧本 + 导演控制塔

处理：
  ├─ 每镜8字段输出
  │   ├─ shot_id
  │   ├─ durationSec
  │   ├─ locationId
  │   ├─ characterIds
  │   ├─ script
  │   ├─ dialogue
  │   ├─ imagePrompt
  │   └─ videoPrompt
  ├─ 引用导演控制塔约束
  ├─ 角色DNA嵌入
  └─ Audio Layer注入

输出：03-分镜/第XX集-分镜.md
```

### Step 6: 角色资产（LibTV执行前置）

```
输入：IP档案 + 角色DNA

处理：
  ├─ 生成角色参考图
  ├─ 上传到OSS（upload_file.py）
  ├─ 缓存OSS URL
  └─ 关联characterId → oss_url

输出：角色参考图OSS URL映射表
```

### Step 7: LibTV Canvas执行（双审核模式）

> **设计原则**：Canvas = AI聊天界面，Agent发消息，AI处理结果，用户审核，Agent拉回
> - **不是操作节点**，Canvas 本质是聊天：发消息 → AI生成 → 结果在会话里
> - Agent负责：发消息、轮询、拉回结果
> - 用户负责：审核图片质量、审核视频质量
> - 零脚本操作Canvas，纯API交互

```
输入：分镜脚本 + 导演控制塔 + 角色OSS映射

核心原理：
  create_session.py 发消息 → Canvas会话显示 → AI处理 → query_session.py 轮询拉URL

执行流程：
  ① Agent调用 create_session.py → Canvas会话自动创建，Prompt出现在聊天中
  ② 用户在Canvas聊天中查看Prompt → 补充/调整 → 点击执行
  ③ AI在会话中返回图片 → 用户审核 → 确认"生图OK"
  ④ Agent发送视频Prompt → AI在会话中返回视频 → 用户审核 → 确认"生视频OK"
  ⑤ 重复直到全部镜完成
  ⑥ 用户说"完成了" → Agent轮询拉回所有结果URL → download_results.py下载
```

#### 7.1 创建会话

```
Agent操作：
  1. 检查 LIBTV_ACCESS_KEY 环境变量
  2. 调用 create_session.py（不附带message，仅创建会话）
  3. 获取 sessionId + projectUuid + projectUrl

bash命令：
  cd $LIBTV_DIR/scripts
  python3 create_session.py "" 2>&1

返回示例：
  {
    "projectUuid": "aa3ba04c5044477cb7a00a9e5bf3b4d0",
    "sessionId": "90f05e0c-xxx",
    "projectUrl": "https://www.liblib.tv/canvas?projectId=aa3ba04c5044477cb7a00a9e5bf3b4d0"
  }

Agent保存：sessionId、projectId，后续所有命令都依赖这两个值。
```

**输出卡片：**

```
═══════════════════════════════════════
🎬 漫舟导演 · Canvas会话已创建

🔗 点击打开Canvas（保持打开状态）：
   https://www.liblib.tv/canvas?projectId=aa3ba04c5044477cb7a00a9e5bf3b4d0

📋 本集任务：第01集 · 15镜 · 8秒/镜 = 120秒
   - 角色参考图：3张（已上传OSS）
   - 图片生成：15次
   - 视频生成：15次

📝 操作说明：
   1. Canvas保持打开
   2. 我发送Prompt → 你在Canvas中查看并执行
   3. 图片/视频生成后 → 你审核质量
   4. 满意后告诉我「生图OK」或「生视频OK」
   5. 全部完成后告诉我「完成了」

⏳ 开始第P01镜的生图...
═══════════════════════════════════════
```

---

#### 7.2 发送生图Prompt

```
Agent操作：
  1. 根据分镜脚本 + 导演控制塔生成 image_prompt（见第四章模板）
  2. 拼接角色参考URL
  3. 调用 create_session.py --session-id <ID> 发送生图指令

bash命令：
  python3 create_session.py "【第P01镜 · 生图】..." --session-id 90f05e0c-xxx

等待返回：
  {"projectUuid": "...", "sessionId": "...", "projectUrl": "..."}
  （注意：sessionId不变，projectId可能变化）
```

**输出卡片：**

```
═══════════════════════════════════════
📸 第P01镜 · 生图Prompt已发送

【发送给Canvas的内容】：

【角色】
林凤（char_01）
- 外观：黑色短发，深蓝色职业套装，白色衬衫
- 表情风格：冷静克制，眼中有隐忍
- 参考图：https://libtv-res.liblib.art/.../char_linfeng.png

【场景】
位置：MPL大厦深夜办公室
氛围：冷蓝月光 + 台灯暖黄对比
光线：台灯侧光，阴影浓重

【画面内容】
深夜，空旷的MPL办公室只有林凤一人，台灯亮着。
她独自坐在格子间工位，敲击键盘的手突然停下。
眼神凝视屏幕，手悬停在键盘上方，表情凝固。

【运镜要求】
建立镜头（WS）→ 中景缓慢推进 → 面部特写
镜头要稳，不能晃动

【禁止项】
❌ 禁止美颜滤镜
❌ 禁止卡通化
❌ 禁止角色外观变化

⏳ 华哥，请在Canvas中：
   1. 查看我发送的消息，确认Prompt内容正确
   2. 确认角色参考图已关联
   3. 如需调整，修改后点击「执行」
   4. 图片生成完成后，告诉我「生图OK」
═══════════════════════════════════════
```

---

#### 7.3 轮询图片结果（用户确认后）

```
用户输入："生图OK"

Agent操作：
  1. 调用 query_session.py 轮询会话
  2. 从返回的 messages 中提取图片URL
  3. 确认图片URL有效后，继续下一阶段

bash命令：
  python3 query_session.py 90f05e0c-xxx --after-seq 0

返回结构：
  {
    "messages": [
      {"role": "assistant", "content": "生成的图片：https://libtv-res.liblib.art/...png"},
      ...
    ]
  }

轮询逻辑（详细）：
  - 间隔：每8秒一次
  - 超时：连续60秒无图片URL → 提示用户去Canvas检查
  - 完成判断：messages中出现 assistant 消息且含 https://libtv-res...*.png
  - last_seq：每次轮询后记录最大seq，下次用 --after-seq <last_seq>

URL提取正则：
  https://libtv-res\.liblib\.art/[^\s]+\.png
  https://libtv-res\.liblib\.art/[^\s]+\.jpg

保存：image_url_<shot_id> = <提取到的URL>
```

---

#### 7.4 发送视频Prompt

```
Agent操作：
  1. 根据分镜脚本 + 导演控制塔生成 video_prompt（见第四章模板）
  2. 引用上一镜生成的图片URL作为首帧参考
  3. 调用 create_session.py --session-id <ID> 发送视频指令

bash命令：
  python3 create_session.py "【第P01镜 · 视频】..." --session-id 90f05e0c-xxx

Prompt模板（video_prompt）：
  【第P01镜 · 图生视频 · 8秒】

  【首帧参考】
  图片URL：<上一镜生成的图片>

  【角色】
  林凤（char_01）— 参考图：https://libtv-res.liblib.art/.../char_linfeng.png

  【运镜要求】
  - 景别：中景缓慢推进到面部特写
  - 节奏：缓慢推进，镜头稳
  - 动作：手悬停在键盘上方 → 缓缓落下 → 眼神从迷茫到坚定
  - 情绪：L3隐忍，眼神凝聚

  【禁止项】
  ❌ 禁止美颜滤镜
  ❌ 禁止卡通化
  ❌ 禁止角色外观变化
```

**输出卡片：**

```
═══════════════════════════════════════
🎬 第P01镜 · 视频Prompt已发送

【首帧参考】
已使用上一步生成的图片作为首帧

【运镜要求】
- 景别：中景推进到特写
- 节奏：缓慢推进，镜头稳
- 情绪：L3隐忍

【禁止项】
❌ 禁止美颜滤镜
❌ 禁止卡通化
❌ 禁止角色外观变化

⏳ 华哥，请在Canvas中：
   1. 查看视频生成结果
   2. 检查运镜是否符合意图
   3. 检查角色一致性
   4. 视频满意后，告诉我「生视频OK」
═══════════════════════════════════════
```

---

#### 7.5 轮询视频结果 + 批量执行

```
用户输入："生视频OK"

Agent操作：
  1. query_session.py 轮询会话 → 提取视频URL
  2. 保存 video_url_<shot_id>
  3. 判断：还有未生成的镜？ → 继续7.2（下一镜）
  4. 全部完成 → 进入7.6

轮询完成判断：
  - messages中出现 assistant 消息且含 https://libtv-res...*.mp4
  - 视频状态：非 queued / 非 generating（LibTV新返回格式）
  - 多个URL：只取最新一条（last_seq最大）

超时兜底：
  - 60秒无结果：提示用户"Canvas中是否在生成中？"
  - 180秒无结果：记录失败，继续下一镜

批量推进：
  每完成一镜（图片+视频），Agent自动：
    - 记录 shot_id → image_url + video_url
    - 推进到下一镜（自动发生图Prompt）
    - 用户只需审核 + 确认「生图OK」「生视频OK」
```

---

#### 7.6 结果拉回（全部完成后）

```
用户输入："完成了" 或 "全部完成了"

Agent操作：
  1. 检查所有镜的 image_url + video_url 是否完整
  2. 调用 download_results.py 下载所有视频片段

bash命令：
  python3 download_results.py 90f05e0c-xxx \
    --output-dir ./output/格子间女人/EP01 \
    --prefix "shot"

返回结构：
  {
    "output_dir": "./output/格子间女人/EP01",
    "downloaded": ["shot_01.mp4", "shot_02.mp4", ...],
    "total": 15,
    "errors": []
  }

质量报告生成：
  - 每镜：shot_id / image_url / video_url / local_path / status
  - 成功率：success_count / total_count
  - 失败镜：reroll_needed列表
```

**输出卡片：**

```
═══════════════════════════════════════
✅ 漫舟导演 · 第01集生成完成

📁 下载目录：./output/格子间女人/EP01/
   shot_01.mp4  ✅ [image: ✅ video: ✅]
   shot_02.mp4  ✅ [image: ✅ video: ✅]
   shot_03.mp4  ✅ [image: ✅ video: ✅]
   ...
   shot_15.mp4  ✅ [image: ✅ video: ✅]

📊 统计：
   总镜数：15
   成功：15
   失败：0
   成功率：100%

📋 视频URL存档（用于后续拼接）：
   [保存到 08-视频产出/EP01/urls.md]

⏳ 下一集？告诉我"继续第02集"即可。
═══════════════════════════════════════
```

---

#### 7.7 全流程示例（完整交互）

```
用户：请帮我把格子间女人第1集生成视频

Agent：Step 7.1 — 创建Canvas会话
  bash: python3 create_session.py ""
  → 获得 sessionId=abc, projectId=xyz, projectUrl=https://...

Agent：📋 Canvas会话已创建
  🔗 https://www.liblib.tv/canvas?projectId=xyz
  ⏳ 开始第P01镜...

Agent：Step 7.2 — 发送生图Prompt（P01）
  bash: python3 create_session.py "【第P01镜·生图】..." --session-id abc
  → 消息已发送到Canvas

Agent：📸 第P01镜 · 生图Prompt已发送
  [等待用户审核]

用户：[在Canvas中查看消息，点击执行，等待图片生成]
用户：生图OK

Agent：Step 7.3 — 轮询图片URL
  bash: python3 query_session.py abc --after-seq 0
  → 提取URL：https://libtv-res.../shot_01.png

Agent：Step 7.4 — 发送视频Prompt（P01）
  bash: python3 create_session.py "【第P01镜·视频】..." --session-id abc
  → 消息已发送到Canvas

Agent：🎬 第P01镜 · 视频Prompt已发送
  [等待用户审核]

用户：[在Canvas中查看视频，点击执行，等待视频生成]
用户：生视频OK

Agent：Step 7.5 — 轮询视频URL + 推进到P02
  bash: python3 query_session.py abc --after-seq 5
  → 提取URL：https://libtv-res.../shot_01.mp4
  ✅ P01完成 → 继续P02...

[Agent自动重复7.2-7.5，直到P15完成]

用户：完成了

Agent：Step 7.6 — 批量下载
  bash: python3 download_results.py abc --output-dir ./output/... --prefix shot

Agent：✅ 第01集生成完成
  📊 成功率：15/15（100%）
  📁 ./output/格子间女人/EP01/
```

### Step 8: 结果拉回（→ 见 Step 7.6）

> Step 7.6 已完整覆盖结果拉回逻辑（轮询 + 下载 + 质量报告）。
> 此步骤保留用于目录对齐，无新增内容。
>
> 完整流程见 Step 7.6。

### Step 9: 视频拼接（FFmpeg）

> 15个视频片段拼接为完整Episode，使用FFmpeg concat demuxer

```
输入：15个视频片段（./output/格子间女人/EP01/shot_*.mp4）

前置准备：生成文件列表
  for i in $(seq -w 1 15); do
    echo "file 'shot_$i.mp4'" >> concat_list.txt
  done

执行拼接：
  ffmpeg -f concat -safe 0 -i concat_list.txt \
    -c copy ./output/格子间女人/EP01/EP01_完整版.mp4

或单命令（无需文件列表）：
  ffmpeg -i "concat:shot_01.mp4|shot_02.mp4|...|shot_15.mp4" \
    -c copy ./output/格子间女人/EP01/EP01_完整版.mp4

参数说明：
  -f concat          # concat封装器
  -safe 0            # 允许相对路径
  -c copy            # 直接复制流，不重新编码（速度快）
  如需重新编码：去掉 -c copy，换用 -c:v libx264 -crf 23 -preset fast

输出：EP01_完整版.mp4（约120秒）
```

---

## 四、LibTV指令生成（核心能力）

### 漫舟 → LibTV 翻译引擎

```python
def generate_libtv_instruction(shot, director_notes, character_cache):
    """
    漫舟的专业能力在这里体现：
    把结构化的分镜脚本 + 导演意图
    翻译成LibTV能理解但更有创作意图的自然语言

    比LibTV Agent的"直接传话"强100倍
    """

    # 1. 场景功能标注
    scene_function = director_notes.scene_function  # TENSION/MOOD/REVEAL/ACTION/...
    function_desc = {
        "TENSION": "【张力场景】",
        "MOOD": "【氛围场景】",
        "REVEAL": "【揭示场景】",
        "ACTION": "【动作场景】",
        "CLIFFHANGER": "【悬念场景】"
    }

    # 2. 角色描述（内嵌，不依赖外部绑定）
    char_parts = []
    for char_id in shot.characterIds:
        dna = character_cache[char_id]
        char_parts.append(f"""
角色：{dna.name}
- 身份：{dna.identity}
- 外貌：{dna.appearance}
- 服装：{dna.outfit}
- 表情风格：{dna.expression_style}
- 关键特征：{dna.key_features}
        """)

    # 3. 运镜描述（来自导演控制塔）
    camera_action = director_notes.camera_action  # "中景缓慢推进到特写"
    camera_forbidden = director_notes.forbidden_actions  # ["禁止正面特写"]

    # 4. 情绪氛围（来自节拍追踪）
    emotion_level = director_notes.emotion_level  # L3
    emotion_desc = director_notes.emotion_description  # "压抑/紧张"

    # 5. 拼接LibTV友好指令
    instruction = f"""
{function_desc.get(scene_function, '')}

【第{shot.shot_id}镜 · {shot.durationSec}秒】

【角色】
{''.join(char_parts)}

【场景】
位置：{shot.locationId}
氛围：{director_notes.scene_mood}
光线：{director_notes.lighting}

【画面内容】
{shot.script}

【运镜要求】
{camera_action}
注意：{shot.camera_notes}

【情绪氛围】
情绪等级：{emotion_level}级 - {emotion_desc}
节奏：{director_notes.beat_position}

【参考】
角色图：{character_cache[shot.characterIds[0]].oss_url}

【禁止项】
{', '.join(camera_forbidden)}
    """

    return instruction.strip()
```

### 指令生成模板

```markdown
【第P01镜 · TENSION张力场景 · 8秒】

【角色】
林凤（职场女性）
- 身份：MPL大中国区销售部经理
- 外貌：30岁，黑色短发，精致干练
- 服装：深蓝色职业套装，白色衬衫
- 表情风格：冷静克制，眼中有隐忍
- 关键特征：修长手指，说话时微微抬眉

【场景】
位置：MPL大厦深夜办公室
氛围：紧张压抑，城市灯火为背景
光线：台灯侧光，阴影浓重

【画面内容】
林凤坐在格子间工位，深夜空旷的办公室只有她一人，台灯亮着。她正在敲击键盘，突然停下手，瞟一眼屏幕，眼神凝固。

【运镜要求】
从中景缓慢推进到面部特写，最后定格在眼神
镜头要稳，不能晃动
注意：不要出现其他角色

【情绪氛围】
情绪等级：L4级 - 震惊/压抑
节奏：节拍#6，冲突爆发点

【参考】
角色图：https://libtv-res.liblib.art/xxx/char_linfeng.png

【禁止项】
禁止美颜滤镜，禁止过度美化，禁止卡通化
```

---

## 五、LibTV执行层（复用libtv-skills）

### 5.1 环境准备

```bash
# 设置环境变量
export LIBTV_ACCESS_KEY="your-access-key"
export LIBTV_DIR="/path/to/libtv-skills-main/skills/libtv-skill"

# 初始化会话（只创建，不发消息）
python3 $LIBTV_DIR/scripts/create_session.py ""

# 返回：{"projectUuid": "...", "sessionId": "...", "projectUrl": "..."}
```

### 5.2 上传参考图

```bash
# 上传角色参考图
python3 $LIBTV_DIR/scripts/upload_file.py "/path/to/linfeng_ref.png"

# 返回：{"url": "https://libtv-res.liblib.art/..."}
```

### 5.3 发送执行指令

```bash
# 发送LibTV指令
python3 $LIBTV_DIR/scripts/create_session.py \
    "【第P01镜 · 8秒】角色：林凤，职场女性...场景：深夜办公室..." \
    --session-id "your-session-id"

# 返回：{"projectUuid": "...", "sessionId": "...", "projectUrl": "..."}
```

### 5.4 轮询结果

```bash
# 轮询（间隔8秒）
python3 $LIBTV_DIR/scripts/query_session.py "your-session-id" --after-seq 0

# 检查返回
# - 如果有 assistant 消息且包含结果 → 完成
# - 否则继续轮询
# - 超时（180秒）后继续下一镜
```

### 5.5 下载结果

```bash
# 下载所有结果
python3 $LIBTV_DIR/scripts/download_results.py "your-session-id" \
    --output-dir "./output/EP01" \
    --prefix "shot"

# 返回：{"output_dir": "...", "downloaded": [...], "total": N}
```

---

## 六、轮询策略

### 6.1 标准轮询函数

```python
import time
import json
import re
from _common import query_session

def poll_for_result(session_id, last_seq=0, max_wait=180, interval=8):
    """
    LibTV标准轮询策略：
    - 间隔：8秒（LibTV处理通常需要10-30秒）
    - 超时：180秒（约3分钟，超过则记录失败继续下一镜）
    - 增量拉取：每次传入上次最大seq，避免重复拉取
    """
    start_time = time.time()
    retries = 0
    extracted_urls = []

    while time.time() - start_time < max_wait:
        try:
            result = query_session(session_id, after_seq=last_seq)
            messages = result.get("messages", [])
            new_messages = [m for m in messages if m.get("seq", 0) > last_seq]

            if new_messages:
                # 更新 last_seq（用于下次增量拉取）
                last_seq = max(m.get("seq", 0) for m in new_messages)

                # 从所有消息中提取URL
                for msg in new_messages:
                    urls = extract_urls_from_message(msg)
                    extracted_urls.extend(urls)
                    if urls:
                        # 一旦找到URL，说明已生成
                        return {
                            "status": "complete",
                            "urls": extracted_urls,
                            "last_seq": last_seq
                        }

        except Exception as e:
            retries += 1
            if retries >= 3:
                return {"status": "error", "error": str(e), "urls": extracted_urls}

        time.sleep(interval)

    # 超时：有URL则返回，无URL则记录失败
    return {
        "status": "timeout" if not extracted_urls else "partial",
        "urls": extracted_urls,
        "last_seq": last_seq
    }


def extract_urls_from_message(msg):
    """从消息中提取所有 libtv-res 图片/视频URL"""
    urls = []
    content = msg.get("content", "")

    # 1. 从 assistant 文本消息中提取URL
    found = re.findall(r'https://libtv-res\.liblib\.art/[^\s"\']+\.(?:mp4|png|jpg|webp)', content)
    urls.extend(found)

    # 2. 从 tool 消息中解析 task_result JSON
    if msg.get("role") == "tool":
        try:
            data = json.loads(content)
            task_result = data.get("task_result", {})
            # images 列表
            for img in task_result.get("images", []):
                if isinstance(img, str):
                    urls.append(img)
                elif isinstance(img, dict):
                    urls.append(img.get("url", ""))
            # videos 列表
            for vid in task_result.get("videos", []):
                if isinstance(vid, str):
                    urls.append(vid)
                elif isinstance(vid, dict):
                    urls.append(vid.get("url", ""))
        except (json.JSONDecodeError, ValueError):
            pass

    # 3. 去重
    return list(dict.fromkeys(urls))
```

### 6.2 状态判断

```python
def interpret_generation_status(session_id, after_seq=0):
    """
    查询当前生成状态（不等待，用于检查Canvas中的状态）
    返回：generating / queued / completed / failed / no_result
    """
    result = query_session(session_id, after_seq=after_seq)
    messages = result.get("messages", [])
    latest_msg = messages[-1] if messages else {}

    content = latest_msg.get("content", "")

    # 优先检查 tool 消息中的状态
    if latest_msg.get("role") == "tool":
        try:
            data = json.loads(content)
            task_result = data.get("task_result", {})
            videos = task_result.get("videos", [])
            images = task_result.get("images", [])
            if videos or images:
                return "completed"
        except:
            pass

    # 检查文本中是否含URL
    if "libtv-res" in content and any(ext in content for ext in [".mp4", ".png", ".jpg"]):
        return "completed"

    # 检查是否在生成中（关键词判断）
    if any(kw in content for kw in ["生成中", "处理", "稍等", "loading", "generating"]):
        return "generating"

    if "排队" in content or "queue" in content.lower():
        return "queued"

    return "no_result"
```

### 6.3 批量镜次轮询

```python
def poll_all_shots(session_id, shot_count=15, url_map=None):
    """
    批量轮询所有镜次的URL
    每发送一次 create_session（一次生图+一次视频），轮询一次
    返回：{shot_id: {image_url, video_url}}
    """
    if url_map is None:
        url_map = {}

    last_seq = 0
    pending_shots = list(range(1, shot_count + 1))

    for shot_id in pending_shots:
        # 生图轮询（用户确认"生图OK"后）
        result = poll_for_result(session_id, last_seq=last_seq, max_wait=60)
        if result["urls"]:
            url_map[shot_id] = {"image_url": result["urls"][-1]}
            last_seq = result["last_seq"]
        else:
            url_map[shot_id] = {"image_url": None}  # 记录失败

        # 发送视频Prompt（在Step 7.4中由Agent调用create_session）

        # 视频轮询（用户确认"生视频OK"后）
        result = poll_for_result(session_id, last_seq=last_seq, max_wait=120)
        if result["urls"]:
            url_map[shot_id]["video_url"] = result["urls"][-1]
            last_seq = result["last_seq"]
        else:
            url_map[shot_id]["video_url"] = None  # 记录失败

    return url_map
```

---

## 七、完整执行示例

### 7.1 双审核模式流程

```
用户：请帮我把格子间女人第1集生成视频

漫舟·导演版执行：
  ✅ Step 1-5  [纯本地执行，瞬时完成]
  ✅ Step 6   [生成参考图 + 上传OSS]

  📍 Step 7: Canvas双审核模式
    ├─ 创建画布会话 → 获取 projectUrl
    ├─ 告知用户画布地址
    │
    ├─ 📸 P01镜：生图Prompt已填写 → ⏸ 等待用户"生图OK"
    ├─ 📸 P01镜：视频Prompt已填写 → ⏸ 等待用户"生视频OK"
    ├─ 📸 P02镜：生图Prompt已填写 → ⏸ 等待用户"生图OK"
    ├─ 📸 P02镜：视频Prompt已填写 → ⏸ 等待用户"生视频OK"
    │  ...（自动逐镜推进，用户只需审核）
    └─ 📸 P15镜：视频审核完成

用户：完成了

  📍 Step 8: 结果拉回
    ├─ 轮询 session → 收集 15 个视频 URL
    ├─ 下载到 ./output/格子间女人/EP01/
    └─ 成功率统计

  ✅ 漫舟·导演版执行完成！
```

### 7.2 审核卡片示例（Agent输出）

```
═══════════════════════════════════════
📸 第P01镜 · 生图Prompt已填写

【角色】
林凤（char_01）
- 外观：黑色短发，深蓝色职业套装
- 参考图：已关联

【场景】
MPL大厦深夜办公室
- 氛围：冷蓝月光 + 台灯暖黄对比

【画面内容】
林凤独自坐在格子间，深夜空旷办公室，台灯亮着。
眼神凝视屏幕，手悬停在键盘上方。

【运镜意图】
建立镜头 → 中景缓慢推进 → 面部特写

⏳ 华哥，请在Canvas中：
   1. 检查角色外观是否正确
   2. 检查场景氛围是否符合
   3. 点击「执行」生成图片
   4. 图片满意后，对我说「生图OK」
═══════════════════════════════════════
```

---

## 八、错误处理

### 8.1 错误类型与处理（Step 7执行层）

| 错误类型 | 表现 | 处理方式 | 继续执行？ |
|---------|------|---------|-----------|
| `LIBTV_ACCESS_KEY` 未设置 | `sys.exit(1)` | 退出，报错，提示设置环境变量 | ❌ |
| Canvas会话创建失败 | HTTP 401/403 | 退出，检查Key是否有效 | ❌ |
| 参考图上传失败 | HTTP error | 重试3次，间隔5s | ⚠️ |
| `create_session` 发送失败 | 网络错误 | 重试3次，间隔5s | ⚠️ |
| `query_session` 轮询失败 | 网络错误 | 重试3次 | ⚠️ |
| 轮询超时（图片60s/视频120s）| 无URL返回 | 记录，跳到下一镜，告知用户 | ✅ |
| `download_results` 下载失败 | HTTP 502/503 | 重试3次，间隔10s | ⚠️ |
| 视频质量差（用户不确认）| 用户拒绝 | 记录，尝试调整Prompt重试 | ⚠️ |

### 8.2 失败恢复机制

```python
def execute_shot_with_recovery(shot, session_id, retry_count=3):
    """单镜执行 + 失败恢复"""

    # 1. 发送生图Prompt
    for attempt in range(retry_count):
        try:
            resp = create_session_with_retry(session_id, build_image_prompt(shot))
            if resp.get("sessionId"):
                break  # 成功，跳出重试循环
        except Exception as e:
            if attempt == retry_count - 1:
                return {"shot_id": shot.shot_id, "stage": "image", "status": "failed", "error": str(e)}
            time.sleep(5)

    # 2. 轮询图片结果
    result = poll_for_result(session_id, last_seq=0, max_wait=60)
    if not result["urls"]:
        return {"shot_id": shot.shot_id, "stage": "image", "status": "timeout", "error": "60s无图片URL"}
    image_url = result["urls"][-1]

    # 3. 发送视频Prompt
    ...

    # 4. 轮询视频结果
    result = poll_for_result(session_id, last_seq=result["last_seq"], max_wait=120)
    if not result["urls"]:
        return {"shot_id": shot.shot_id, "stage": "video", "status": "timeout", "error": "120s无视频URL"}
    video_url = result["urls"][-1]

    return {
        "shot_id": shot.shot_id,
        "status": "success",
        "image_url": image_url,
        "video_url": video_url
    }


def create_session_with_retry(session_id, message, retries=3):
    """带重试的create_session"""
    import time
    for i in range(retries):
        try:
            return create_session(message, session_id=session_id)
        except Exception as e:
            if i == retries - 1:
                raise
            time.sleep(5)
```

---

## 九、目录结构

```
AI漫剧生产/
├── skills/
│   ├── manzhou-director-v2.md    ← 本文件（核心）
│   ├── manzhou-master.md         ← 主控（调用本文件）
│   ├── manzhou-novel-adapter.md  ← Step 1
│   ├── manzhou-ip-parser.md      ← Step 2
│   ├── manzhou-script.md         ← Step 3
│   ├── manzhou-director-control.md ← Step 4
│   ├── manzhou-shot-script.md    ← Step 5
│   └── ...
├── libtv-skills-main/            ← LibTV执行层（A级，可执行）
│   └── skills/libtv-skill/
│       └── scripts/
│           ├── _common.py          ← API公共模块（鉴权/POST/GET/会话）
│           ├── create_session.py    ← 创建会话+发消息 ✅
│           ├── query_session.py     ← 轮询会话+提取URL ✅
│           ├── upload_file.py       ← 上传参考图到OSS ✅
│           ├── download_results.py  ← 批量下载结果 ✅
│           └── change_project.py    ← 切换项目 ✅
│                                      注意：无Canvas节点操作脚本
│                                      Canvas=聊天界面，操作节点非必须
└── [项目名]/
    ├── 01-IP档案/
    ├── 02-剧本/
    ├── 03-导演分析/
    ├── 03-分镜/
    └── 08-视频产出/              ← 新增
```

---

## 十、调用方式

### 从manzhou-master调用

```markdown
### Step 7: LibTV执行（漫舟·导演版）

```
↓ 调用 manzhou-director-v2
- 输入：分镜脚本 + 导演控制塔 + 角色参考图
- 执行：逐镜生成LibTV指令
- 发送：create_session
- 轮询：query_session
- 收集：download_results
→ 输出：视频片段列表 + 项目画布链接
```
```

---

## 十一、质量门控集成 + Step对应表

### 11.1 编排总控Step对应表

本文档覆盖 **Step 7~Step 9**（LibTV执行层），完整Step对应关系：

| 编排总控Step | 负责文档/Skill | 执行主体 |
|------------|--------------|---------|
| Step 0~6 | manzhou-master.md | 漫舟主控Agent调用子Agent |
| **Step 7 Canvas** | **manzhou-director-v2.md §7** | 漫舟·导演版（Canvas双审核） |
| **Step 8 结果拉回** | **manzhou-director-v2.md §8** | 漫舟·导演版（轮询+下载） |
| **Step 9 视频拼接** | **manzhou-director-v2.md §9** | 漫舟·导演版（FFmpeg） |
| Step 10 风控 | manzhou-safety.md | 风控官Agent |
| Step 11 发布 | manzhou-master.md | 主控Agent |

> manzhou-director-v2.md 是 **Step 7~9 的唯一执行文档**，Step 7~9 不走子Agent调用，直接由本文件执行。

---

### 11.2 质量门控集成（Step 7执行层）

> 引用来源：`AI漫剧知识库/07-执行层/漫舟编排管道/质量门控规范.md`

#### 触发时机

```
每镜视频生成完成（用户确认"生视频OK"后）
    ↓
立即计算五维评分
    ↓
综合评分 ≥ 0.70？──是──→ 记录通过，继续下一镜
    ↓ 否
综合评分 < 0.60？──是──→ 🔴 立即停止，报警
    ↓ 否（0.60-0.69）
记录失败原因 → 自动调整参数重试（最多2次）
    ↓
仍不达标 → 触发 E3 人工介入
```

#### 五维评分规则（来源：质量门控规范.md）

| 维度 | 名称 | 权重 | 阈值 |
|------|------|------|------|
| D1 | 完整性 | 0.20 | ≥ 0.70 |
| D2 | 一致性（角色/场景） | 0.25 | ≥ 0.80 |
| D3 | 指令合规（运镜/情绪） | 0.25 | ≥ 0.80 |
| D4 | 生成质量 | 0.20 | ≥ 0.70 |
| D5 | 用户满意度 | 0.10 | 行为数据回传后生效 |

**综合评分公式**：
```
综合评分 = D1×0.2 + D2×0.25 + D3×0.25 + D4×0.2 + D5×0.1
```

#### 质量门控代码（逐镜嵌入）

```python
def check_shot_quality(video_url, shot_metadata, director_notes):
    """
    每镜生成后立即触发质量门控检查
    来源：质量门控规范.md §Step 8视频生成阈值
    """
    scores = {
        "D1_完整性": score_completeness(shot_metadata),      # 字段非空
        "D2_一致性": score_consistency(video_url, shot_metadata),  # 角色/场景
        "D3_指令合规": score_instruction_compliance(video_url, director_notes),  # 运镜/情绪
        "D4_生成质量": score_generation_quality(video_url),  # 画面质量
        "D5_满意度": 0.8  # Step 8暂用默认值，上线后行为数据替换
    }

    composite = (
        scores["D1_完整性"] * 0.2 +
        scores["D2_一致性"] * 0.25 +
        scores["D3_指令合规"] * 0.25 +
        scores["D4_生成质量"] * 0.2 +
        scores["D5_满意度"] * 0.1
    )

    # 最低红线
    if any(v < 0.50 for v in scores.values()):
        abort(f"🔴 质量红线触发！shot_id={shot_metadata['shot_id']}，某维度<0.50，立即停止")

    # 强制人工介入
    if composite < 0.60:
        trigger_e3_human_intervention(shot_id=shot_metadata["shot_id"], scores=scores)

    # 可自动重试
    if 0.60 <= composite < 0.70:
        retry_count = get_retry_count(shot_metadata["shot_id"])
        if retry_count < 2:
            return {"action": "auto_retry", "scores": scores, "composite": composite}
        else:
            trigger_e3_human_intervention(shot_id=shot_metadata["shot_id"], scores=scores)

    # 通过
    return {"action": "pass", "scores": scores, "composite": composite}
```

#### E3人工介入触发条件（Step 7执行层）

| 条件 | 触发动作 |
|------|---------|
| 任何维度 < 0.50 | 🔴 立即停止，报警 |
| 综合评分 < 0.60 | 强制人工介入，不重试 |
| 综合评分 0.60-0.69，连续2次重试仍不达标 | 触发人工介入 |
| 违禁内容检测 | 零容忍，立即停止 |

#### 人工介入输出格式（Step 7专用）

```
⏸ 质量门控触发 E3 人工介入

【当前Step】：Step 7.5（视频生成 → 质量门控）
【镜头】：shot_07（P07，第56-64秒）
【综合评分】：0.63（未达标）

【各维度评分】：
  D1 完整性：0.85 ✅
  D2 一致性：0.72 ✅
  D3 指令合规：0.58 🔴（运镜未执行，推进→拉远）
  D4 生成质量：0.65 ✅
  D5 满意度：0.80（默认）

【失败原因】：运镜指令"缓慢推进"执行成了"拉远"

❓ 请确认：
[A] 调整Prompt后重试（补充：禁止拉远镜头）
[B] 跳过此镜头，继续其他镜头
[C] 终止执行
```

---

### 11.3 与质量门控规范.md的引用关系

| 质量门控规范章节 | 在director-v2中的对应位置 |
|----------------|------------------------|
| §2 Step 8 视频生成阈值 | §11.2 五维评分规则 |
| §3 自动触发机制 | §11.2 触发时机 |
| §3 重试策略 | §11.2 质量门控代码 |
| §4 人工介入触发条件 | §11.2 E3人工介入触发条件 |
| §4 人工介入输出格式 | §11.2 人工介入输出格式 |

---

### 11.4 执行层质量仪表盘（每日生成）

```markdown
## Step 7 执行质量看板

| 指标 | 数值 | 状态 |
|------|------|------|
| 今日生成镜头数 | 45 | ✅ |
| 今日通过率 | 91.1% (41/45) | ✅ |
| 今日平均综合评分 | 0.78 | 🟡 |
| E3人工介入次数 | 2 | 🟡 |
| 最低分镜头 | EP01-P12 (0.62) | 🔴 |

【质量趋势】
EP01: 0.82 → EP02: 0.79 → EP03: 0.76 → EP04: 0.74 ⚠️（连续下降）
→ 触发橙牌预警，建议检查EP05的Prompt参数
```

---

## 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| 2.0.0 | 2026-03-26 | 首发 - 从LibTV Agent脱胎，完整执行层+漫舟逻辑能力 |
| 2.1.0 | 2026-03-26 | Step 7从"自动执行"改为"规划模式" — Agent填写Canvas Prompt、连接管道，用户手动执行后拉回结果 |
| **2.2.0** | **2026-03-26** | **极简升级**：删除全部Canvas操作脚本，改为"打开画布 + 双审核点"模式 |
| **2.4.0** | **2026-03-26** | **质量门控集成**：新增§11质量门控集成章节（Step对应表 + 五维评分 + E3触发 + 仪表盘），引用质量门控规范.md，填补执行层→质量层的连接空白 |
