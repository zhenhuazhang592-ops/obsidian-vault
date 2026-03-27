# 《格子间女人》角色Prompt参考文档

> 项目：格子间女人
> 版本：v6.3.0
> 生成日期：2026-03-26
> 用途：imagePrompt生成分镜图 + videoPrompt注入--cref参考

---

## CDP角色ID映射

| char_id | 角色名 | 英文名 | 昵称 |
|---------|--------|--------|------|
| char_01 | 潭斌 | Cheritang | Cherie |
| char_02 | 余永麟 | Yu Yonglin | Tony |
| char_03 | 曾婵贞 | Zeng ChanZhen | - |
| char_04 | 乔利维 | Qiao Liwei | - |
| char_05 | 方芳 | Fang Fang | - |
| char_06 | 程睿敏 | Cheng Ruimin | Ray |

---

## 角色形象Prompt（分镜图生成用）

### char_01 · 潭斌（Cheritang）

**角色定位**：女主/视角人物，28-32岁，MPL中国公司销售代表

**外貌特征**：
- 干练的职业女性气质
- 职场形象：正装衬衣 + 大披肩
- 便装形象：松绿软缎 + 白色宽腿长裤 + 金色凉鞋
- 冻得涕泪交零时的脆弱感

**情绪变体**：

| 变体 | 表情 | 场景 |
|------|------|------|
| V1-标准 | 中性专注，职业微笑 | 日常办公 |
| V2-震惊 | 瞳孔放大，僵住 | 收到离职邮件 |
| V3-坚定 | 下颌紧锁，目光坚毅 | 面对威胁/做决定 |
| V4-脆弱 | 眼神闪烁，疲惫 | 深夜独处 |

**分镜图Prompt**：
```
anime style, medium close-up portrait, Chinese female office worker in late 20s,
wearing formal business attire (white shirt with oversized shawl drape),
clean professional appearance with subtle weariness,
expression showing controlled professional calm with underlying determination,
Beijing CBD office background,
ShortDrama_Style × WongKarwai_Style,
cinematic lighting, 85mm telephoto lens, shallow depth of field,
no text subtitles logos watermarks
```

**--cref使用格式**：
```
--cref [char_01_潭斌_V1.png] --cw 100  # 标准表情
--cref [char_01_潭斌_V2.png] --cw 80   # 震惊表情（允许微调）
--cref [char_01_潭斌_V3.png] --cw 100  # 坚定表情
--cref [char_01_潭斌_V4.png] --cw 80   # 脆弱表情
```

---

### char_02 · 余永麟（Tony）

**角色定位**：前MPL销售总监/现FSK北方区总监，30-35岁

**外貌特征**：
- 京腔松弛感男声
-精英外表：头发剃得紧贴头皮
- 便装：T恤+短裤
- 像街边小痞子的痞帅感

**情绪变体**：

| 变体 | 表情 | 场景 |
|------|------|------|
| V1-漫不经心 | 松弛，痞气 | 居家/放松 |
| V2-警觉 | 眉头微皱，收敛 | 接电话/听到消息 |
| V3-苦涩 | 笑容僵硬，眼眶发红 | 谈往事/旧情 |
| V4-计算 | 目光锐利，商人感 | 谈交易 |

**分镜图Prompt**：
```
anime style, medium close-up portrait, Chinese male in early 30s,
casual appearance with closely shaved head giving street-smart vibe,
wearing casual T-shirt, relaxed posture with underlying intelligence,
expression showing mix of carelessness and calculation,
modern Beijing apartment or café background,
WongKarwai_Style,
cinematic lighting with teal and amber tones, 85mm telephoto lens,
shallow depth of field, no text subtitles logos watermarks
```

**--cref使用格式**：
```
--cref [char_02_Tony_V1.png] --cw 100  # 漫不经心
--cref [char_02_Tony_V2.png] --cw 100  # 警觉
--cref [char_02_Tony_V3.png] --cw 80   # 苦涩
--cref [char_02_Tony_V4.png] --cw 100  # 计算
```

---

### char_03 · 曾婵贞（ZengCZ）

**角色定位**：MPL高管，女性领导，30-40岁

**外貌特征**：
- 权威女强人形象
- 细高跟，气场全开
- 冷峻审视的目光
- 职业套装

**情绪变体**：

| 变体 | 表情 | 场景 |
|------|------|------|
| V1-审视 | 目光扫视，评估 | 打量潭斌 |
| V2-宣布 | 权威宣布，不容置疑 | 会议发言 |
| V3-压制 | 冷眼，气场压制 | 面对下属 |

**分镜图Prompt**：
```
anime style, medium close-up portrait, Chinese female executive in late 30s,
commanding presence with pointed high heels,
wearing sharp professional business suit,
expression showing cold authoritative assessment,
MPL conference room background,
ShortDrama_Style,
high contrast dramatic lighting, sharp rim light,
85mm telephoto lens, shallow depth of field,
no text subtitles logos watermarks
```

**--cref使用格式**：
```
--cref [char_03_ZengCZ_V1.png] --cw 100  # 审视
--cref [char_03_ZengCZ_V2.png] --cw 100  # 宣布
--cref [char_03_ZengCZ_V3.png] --cw 100  # 压制
```

---

### char_04 · 乔利维（QiaoLW）

**角色定位**：MPL内部晋升候选/竞争对手，28-35岁

**外貌特征**：
- 东北销售明星外表
- 张扬自信
- 溜须拍马的笑
- 阴冷威胁时面目可怖

**情绪变体**：

| 变体 | 表情 | 场景 |
|------|------|------|
| V1-张扬 | 笑容得意，居功自傲 | 晒业绩 |
| V2-阴冷 | 冷笑，威胁感 | 威胁潭斌 |
| V3-尴尬 | 笑容僵硬 | 被质问 |

**分镜图Prompt**：
```
anime style, medium close-up portrait, Chinese male sales star in early 30s,
smug confident expression with northeastern Chinese accent energy,
wearing professional business suit,
expression showing outward arrogance with underlying desperation,
MPL office or conference room background,
ShortDrama_Style × WongKarwai_Style,
high contrast punchy lighting, teal tones,
85mm telephoto lens, shallow depth of field,
no text subtitles logos watermarks
```

**--cref使用格式**：
```
--cref [char_04_QiaoLW_V1.png] --cw 100  # 张扬
--cref [char_04_QiaoLW_V2.png] --cw 100  # 阴冷
--cref [char_04_QiaoLW_V3.png] --cw 80   # 尴尬
```

---

### char_05 · 方芳（FangF）

**角色定位**：潭斌下属/职场盟友，25-28岁

**外貌特征**：
- 粉扑扑的圆脸
- 圆润亲切
- 八卦但不恶意
- 努力做同情状却幸灾乐祸

**情绪变体**：

| 变体 | 表情 | 场景 |
|------|------|------|
| V1-关切 | 关心递茶 | 安慰潭斌 |
| V2-八卦 | 幸灾乐祸 | 传八卦 |

**分镜图Prompt**：
```
anime style, medium close-up portrait, Chinese female colleague in late 20s,
round friendly face with rosy cheeks,
approachable office worker appearance,
expression showing genuine concern mixed with gossip curiosity,
MPL office tea room background,
WongKarwai_Style,
warm amber lighting, cozy atmosphere,
85mm telephoto lens, shallow depth of field,
no text subtitles logos watermarks
```

**--cref使用格式**：
```
--cref [char_05_FangF_V1.png] --cw 100  # 关切
--cref [char_05_FangF_V2.png] --cw 80   # 八卦
```

---

### char_06 · 程睿敏（Ray）

**角色定位**：前MPL销售总经理/神秘男主，35-40岁

**外貌特征**：
- 极修长的手指
- 触手冰凉
- 似一段多年前就冷却的生命
- 深不可测

**情绪变体**：

| 变体 | 表情 | 场景 |
|------|------|------|
| V1-神秘 | 平静如水，不可读 | 日常/观察 |
| V2-揭露 | 冷峻，说出真相 | 揭露Kenny |
| V3-警告 | 严肃，权力感 | 警告潭斌 |

**分镜图Prompt**：
```
anime style, medium close-up portrait, Chinese male mysterious executive in late 30s,
extremely long slender fingers, cold and distant aura,
expression showing unreadable calm with underlying depth,
extremely long slender fingers visible,
Beijing underground parking or night office background,
WongKarwai_Style,
dramatic shadow and light contrast, moonlight rim lighting,
cold teal tones, 85mm telephoto lens, shallow depth of field,
high ISO cinematic grain, romantic melancholy atmosphere,
no text subtitles logos watermarks
```

**--cref使用格式**：
```
--cref [char_06_Ray_V1.png] --cw 100  # 神秘
--cref [char_06_Ray_V2.png] --cw 100  # 揭露
--cref [char_06_Ray_V3.png] --cw 100  # 警告
```

---

## --cref使用规范（v6.3）

### 语法格式
```
【【角色名】】 → --cref [角色ID_情绪变体.png] --cw 权重
```

### 权重规则

| 场景 | --cw 值 | 说明 |
|------|---------|------|
| 同表情变体 | --cw 100 | 完全一致 |
| 换表情（情绪微调） | --cw 80 | 允许轻微表情调整 |
| 换服装/新场景 | --cw 100 | 必须完全一致 |
| 远景/全景（WS/MS） | --cw 80 | 远景对面部要求较低 |
| 动作镜头 | --cw 100 | 服装/外观完全一致 |

### 多人同镜格式
```
【【潭斌】】【【Tony】】in conversation
→ --cref [char_01_潭斌_V3.png] --cw 100
→ --cref [char_02_Tony_V2.png] --cw 100
```

---

## 角色出场场景汇总

| char_id | 角色 | 第1集 | 第2集 | 第3集 |
|---------|------|-------|-------|-------|
| char_01 | 潭斌 | ✅ 全程 | ✅ 全程 | ✅ 全程 |
| char_02 | 余永麟/Tony | 声音出演 | 短信出演 | 5场 |
| char_03 | 曾婵贞 | 3场 | 1场 | - |
| char_04 | 乔利维 | 2场 | 3场 | - |
| char_05 | 方芳 | 1场 | - | - |
| char_06 | 程睿敏 | 文字外提及 | 3场 | 3场 |

---

## 角色互动关系图

```
        [程睿敏/Ray]
           /     \
          /       \
    [潭斌/Cherie] [余永麟/Tony]
         ↑            ↑
         |            |
    [曾婵贞]      [乔利维]
         \            /
          \          /
         [方芳]
```

---

## 情感对手戏组合

| 场景 | 角色A | 角色B | 情感张力 |
|------|-------|-------|---------|
| P02咖啡厅 | 潭斌 | Tony | 旧情人的克制试探 |
| P09质问 | 程睿敏 | 乔利维 | 权力压制 |
| P11停车场 | 程睿敏 | 潭斌 | 神秘警告 |
| P14U盘 | Tony | 潭斌 | 利益vs感情 |
| P18停车 | 程睿敏 | 潭斌 | 权力启蒙 |

---

*角色Prompt参考文档 v6.3.0 · 生成完毕*
