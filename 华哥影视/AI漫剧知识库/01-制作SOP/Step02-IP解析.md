---
title: Step 02 · IP解析
tags:
  - SOP
  - Step02
  - IP解析
  - 角色档案
rating: A
aliases:
  - IP档案
  - 角色解析
---

# Step 02 · IP解析

> [!abstract] 评级：A级 | 多次验证
> **目的**：从改编稿中提取角色、场景、道具世界观资产，建立标准化IP档案
> **核心价值**：角色/场景/道具用ID引用（char_01/loc_01/item_01），为后续AI生成提供一致引用机制

---

## 执行时机

**Step 01 短剧改编完成后执行。**

---

## 三类资产解析

### 1. 角色档案（必须项）

每集出场角色均需建立档案，结构如下：

```yaml
char_XX:
  id: char_XX                    # 角色ID，AI生成时引用
  name: [中文名]                  # 角色名称
  role_type: [主角/反派/配角/工具人]  # 角色类型
  age_range: [数字]               # 年龄范围
  aliases: [别名/英文名/昵称]     # 检索用

  appearance:                    # 第一层：外貌锁
    face: [脸型/眉形/眼形/鼻形/嘴形/肤色]
    body: [身高/体型/仪态]
    distinguishing: [标志性特征，如：左眉有疤/眼角痣]
    hair: [发型/发色]

  clothing:                      # 第二层：风格锁
    daily: [日常服装描述]
    work: [职场服装描述]
    special: [特殊场合服装]

  personality:                   # 第三层：行为锁
    traits: [性格关键词：3-5个]
    speech: [语言风格：强势/柔和/幽默/冷淡]
    habits: [习惯性动作/表情]
    conflict_style: [冲突处理方式]

  voice:                         # 声音特征
    timbre: [音色：低沉/清脆/沙哑]
    speed: [语速：快/中/慢]
    accent: [口音/方言]

  relationships:                 # 关系网
    - target: char_XX
      type: [恋人/上司/闺蜜/对手]
      tension: [核心矛盾点]
```

### 2. 场景档案（必须项）

```yaml
loc_XX:
  id: loc_XX
  name: [场景名称]

  type: [室内/室外/虚拟]
  time: [白天/夜晚/清晨/黄昏]
  weather: [晴天/雨天/雪天/室内无天气]

  atmosphere: [氛围关键词：冷/暖/压抑/明快/神秘]
  color_temp: [冷色/暖色/中性]
  lighting: [自然光/人工光/混合光]

  key_elements:                  # 场景核心道具
    - [物品1]
    - [物品2]

  visual_tags:                   # AI生成用标签
    - [风格标签1]
    - [风格标签2]
```

### 3. 道具档案（按需项）

```yaml
item_XX:
  id: item_XX
  name: [道具名称]

  type: [重要道具/背景道具/功能道具]
  owner: char_XX                 # 所属角色

  appearance: [外观描述]

  symbolic: [象征意义：剧情符号]

  key_scenes:                    # 出场场景
    - loc_XX
    - loc_XX
```

---

## 执行Prompt模板

```markdown
你是IP分析师。请从以下改编稿中提取角色、场景、道具资产，生成标准化IP档案。

要求：
1. 角色使用ID引用：char_01, char_02...
2. 场景使用ID引用：loc_01, loc_02...
3. 道具使用ID引用：item_01, item_02...
4. 每角色必须有外貌锁+风格锁+行为锁
5. 每场景必须有氛围标签+光效标签
6. 道具需标注象征意义和关键出场场景

---
[改编稿粘贴]
---
```

---

## 关键检查项

- [ ] 所有角色有唯一ID（char_XX格式）
- [ ] 所有场景有唯一ID（loc_XX格式）
- [ ] 角色外貌描述具体可生成
- [ ] 场景氛围标签与剧情情绪匹配
- [ ] 重要道具标注了象征意义
- [ ] 角色关系网完整（含核心矛盾）

---

## 引用Skill

**执行参考**：[[manzhou-ip-parser]]

**输入**：改编稿
**输出**：`01-IP档案/IP档案.yaml`

---

## 案例参考

- [[格子间女人-IP档案]] → 3个核心角色完整档案 + 6个场景档案
- [[许三观-IP档案]] → 完整角色+场景系统
