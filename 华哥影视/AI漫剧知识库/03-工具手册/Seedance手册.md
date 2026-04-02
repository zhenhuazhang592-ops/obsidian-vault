---
title: Seedance手册
tags:
  - 工具
  - 工具手册
  - Seedance
  - 评级A级
rating: A
aliases:
  - Seedance
  - 生图
  - 图生视频
---

# Seedance 工具手册

> [!abstract] 评级：A级 | 角色一致性优秀
> **核心优势**：角色一致性极强，适合漫剧制作
> **适用场景**：角色图生成 > 场景图生成

---

## 基本信息

| 项目 | 说明 |
|------|------|
| 官网 | seedance.com |
| 主要功能 | 文生图、图生视频 |
| 角色一致性 | ⭐⭐⭐⭐⭐ 极强 |
| 运镜控制 | ⭐⭐⭐⭐ 强 |
| 场景真实感 | ⭐⭐⭐⭐ 良好 |
| 竖屏支持 | ✅ 支持9:16 |
| 成本 | ¥2-3/张图，¥10-15/5秒视频 |

---

## 功能模块

### 1. 文生图

**适用**：生成角色九宫格基础图、场景氛围图

**Prompt写法规范**：

```markdown
# 基础结构
[主体描述], [场景], [光线], [色调], [风格], 高质量

# 必须禁止项
(worst quality:1.4), (low quality:1.4), watermark, text, logo, signature

# 竖屏必须声明
9:16 vertical format, portrait mode
```

### 2. 图生视频

**适用**：角色视频片段生成

**关键操作**：
1. 上传角色参考图
2. 选择"图生视频"模式
3. 填写 video_prompt
4. 设置运镜参数

**运镜参数写法**：
```markdown
camera movement: dolly in        # 推进
camera movement: dolly out      # 拉远
camera movement: pan left        # 左摇
camera movement: pan right       # 右摇
camera movement: static          # 固定
camera movement: tracking shot    # 跟随
```

### 3. 角色一致性保障

**核心技巧**：
1. **首帧上传**：上传角色DNA九宫格基础图作为首帧
2. **Prompt引用**：Prompt中包含角色DNA外貌关键词
3. **风格标签**：保持与角色设定一致的服装/妆容描述

---

## Prompt模板库

### 角色生图模板

```markdown
[年龄段] [性别], [职业],
[面部特征], [发型发色], [标志性特征],
[服装描述],
[场景/背景],
[光线], [色调],
[风格预设],
(worst quality:1.4), (low quality:1.4),
高质量, 电影感, 8K, 详细, 9:16
```

### 九宫格分镜模板

```markdown
anime style, 3x3 grid storyboard layout,
9 panels in 3 rows × 3 columns,
each panel has upper-right corner shot label,
no text subtitles watermarks,
character [ID] in [服装], consistency,
[场景], [光线], [色调],
[风格预设], high contrast, 4K.
```

---

## 评级与定位

| 维度 | 评级 | 说明 |
|------|------|------|
| 角色一致性 | ⭐⭐⭐⭐⭐ | 业界最强，漫剧首选 |
| 运镜控制 | ⭐⭐⭐⭐ | 指令执行准确 |
| 场景质量 | ⭐⭐⭐⭐ | 良好，需配合氛围词 |
| 速度 | ⭐⭐⭐ | 中等，1-3分钟/片段 |
| 成本 | ⭐⭐⭐ | 中等可接受 |

**定位**：漫剧制作**首选工具**，尤其是角色戏份重的场景

---

## 常见问题

> [!warning] 角色脸型变了
> **原因**：没有上传角色参考图作为首帧
> **解决**：必须上传角色九宫格基础图，并确保Prompt包含DNA外貌关键词

> [!warning] 服装颜色变了
> **原因**：服装描述不够具体
> **解决**：服装描述需包含具体颜色词（藏青色西装，而非"深色衣服"）

> [!warning] 场景氛围不对
> **原因**：缺少光线和色调标签
> **解决**：补充光线描述（冷蓝月光）和色调标签（high contrast）
