---
title: Step 08 · 视频生成
tags:
  - SOP
  - Step08
  - 视频生成
  - AI视频
rating: A
aliases:
  - 视频
  - AI视频
---

# Step 08 · 视频生成

> [!abstract] 评级：A级
> **目的**：使用AI视频生成工具将分镜脚本转化为视频片段
> **核心**：video_prompt必须遵循导演运镜意图 + 注入Audio Layer标注

---

## 执行时机

**Step 07 视觉生成完成后执行（需要参考图作为首帧）。**

---

## 工具选择

| 工具 | 运镜控制 | 角色一致性 | 真实感 | 成本 | 评级 |
|------|---------|-----------|--------|------|------|
| Seedance 2.0 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ¥10-15/5秒 | A |
| Kling 1.5 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ¥15-20/5秒 | A |
| 即梦 | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ¥5-10/5秒 | B |
| Runway | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ¥0.2/帧 | A |

**推荐**：Seedance为主（角色一致性强）+ Kling备选（真实场景）

---

## Video Prompt 模板

### Seedance 模板

```markdown
[主体描述],
[场景],
[动作],
camera movement: [具体运镜描述],
[画面比例],
高质量电影感, 详细, 8K
```

**示例**：
```
char_01站在CBD落地窗前俯瞰城市夜景, 冷蓝月光, 室内台灯暖黄光,
西装革履, 商务精英形象, 侧脸, 手指夹烟, 烟雾缭绕,
camera movement: 缓慢推进镜头(dolly in),
9:16竖屏, 高质量电影感, 详细, 8K
```

### Kling 模板

```markdown
[主体描述], [场景], [动作],
--camera-front 0 -5 0 -1 0 0 0 0 0,
[宽高比], 高质量电影感
```

**运镜参数说明**：
```
--camera-front X Y Z X2 Y2 Z2 0 0 0
     ↑ 起始位置        ↑ 结束位置
     X: 左右（正=右） Y: 上下（正=上） Z: 前后（正=前）
```

---

## 运镜与Prompt对应表

| 运镜指令（分镜） | Seedance写法 | Kling写法 |
|-----------------|-------------|---------|
| 固定 | camera movement: static | 去掉camera参数 |
| 推(dolly in) | camera movement: dolly in | --camera-front 0 0 0 -1 0 0 ... |
| 拉(dolly out) | camera movement: dolly out | --camera-front 0 0 0 1 0 0 ... |
| 摇(pan left) | camera movement: pan left | --camera-front 0 0 0 0 0 1 ... |
| 移(tracking) | camera movement: tracking shot | --camera-front 0 0 -2 0 0 2 ... |

---

## Audio Layer 注入格式

```markdown
[Video Prompt],
[BGM: 情绪描述, 曲风, BPM],
[SFX: 音效类型]
```

**示例**：
```
char_01站在落地窗前俯瞰城市夜景, 西装革履, 侧脸,
camera movement: 缓慢推进,
[BGM: 悬疑紧张, 低沉弦乐, 60bpm],
[SFX: 窗外城市白噪音]
```

---

## 执行流程

```
Step 07 视觉生成
    ↓
Step 08 视频生成
    ├── 角色参考图上传（Seedance用）
    ├── video_prompt生成（按分镜脚本）
    ├── 运镜参数配置
    ├── Audio Layer标注注入
    └── 生成 + 轮询下载
    ↓
视频片段上传OSS → 记录URL
```

---

## 关键检查项

- [ ] video_prompt遵循分镜脚本的运镜指令
- [ ] 角色引用了正确的参考图（char_XX）
- [ ] 场景引用了正确的氛围图（loc_XX）
- [ ] Audio Layer完整注入（BGM + SFX）
- [ ] 画幅比例正确（9:16竖屏）
- [ ] 视频时长符合分镜要求（3-8秒）
- [ ] 视频片段上传OSS并记录URL

---

## 引用Skill

**工具手册**：
- [[Seedance手册]]（主推，角色一致性优秀）
- [[Kling手册]]（备选，真实场景优秀）

**执行参考**：[[manzhou-director-v2]]（LibTV执行层）

**输入**：分镜脚本 + 角色参考图 + 场景氛围图
**输出**：视频片段MP4（上传OSS）

---

## 常见问题

> [!warning] 角色不一致
> **原因**：没有使用角色参考图
> **解决**：必须上传角色九宫格参考图作为生成起点

> [!warning] 运镜没有执行
> **原因**：运镜参数写法不对
> **解决**：参考运镜对应表，使用正确格式
