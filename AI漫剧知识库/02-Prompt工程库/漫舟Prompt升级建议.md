# 漫舟Prompt升级建议

> 来源：`AI漫剧工具研究/提示词工程研究/04-漫舟借鉴与升级建议.md`
> 制定时间：2026-03-25
> 整合来源：prompts.chat + awesome-seedance + seedance-prompt-skill

---

## 升级路线图

```
v6.2（当前）✅
  ├── manzhou-shot-script.md v6.2（运镜参数量化 + Audio Layer v6.2 + Viseme标注）
  └── manzhou-tts-voice.md v1.1（Viseme音素表 + Lip-sync五级质量）

v6.3（本次升级）🎯
  ├── manzhou-shot-script.md v6.3
  │     + 时间轴格式（P01格式）← 来自Seedance
  │     + 情感映射字段 ← 来自Seedance
  │     + 风格定义前置 ← 来自Seedance
  ├── manzhou-tts-voice.md v1.2
  │     + 台词逐字情绪标注 ← 来自seedance-prompt-skill
  └── manzhou-master.md v6.3

v6.4（下次迭代）
  ├── CDP引用语法对齐Seedance @语法
  ├── 导演风格库扩充（王家卫/维伦纽瓦/诺兰...）
  └── prompts.chat质量检查机制引入
```

---

## 高优先级（P0，立即执行）

### 1. P01时间轴格式 — manzhou-shot-script.md v6.3

**现状**：漫舟有镜号和时长，无精确秒级时间轴。

升级为：
```markdown
[00:00-00:05] 镜头1：极特写（ECU）
【角色】char_01 女主
【动作】抬头，眼神空洞望向远方
【场景】雨覆盖的玻璃窗，霓虹灯光折射
【动因光源】窗边台灯，色温2800K，主光来自左侧
【构图】头顶留白20%，视线方向留白60%
【情绪】char_01内心独白："如果记忆是一个罐头..."
【情感映射】展现"想触碰却收回手"的极致克制与孤独
【Lip-sync】V0-V3-V7-V11（逐字viseme）
【口型/字幕】："如果记忆是一个罐头，我希望它永远不会过期。"
【音效】雨声渐弱，远处传来汽车喇叭

[00:05-00:08] 镜头2：特写（CU）
【运镜】推（dolly_forward: +0.3），聚焦眼神
【情绪】情感升级：克制→隐忍
```

来源：awesome-seedance 时间轴格式

### 2. 口型字幕双轨制 — Lip-sync精度强化

```markdown
【口型/字幕】："如果记忆是一个罐头，我希望它永远不会过期。"
【口型精度】逐字完全一致，字幕即台词本身
```

来源：awesome-seedance「口型与字幕逐字完全一致」

### 3. 王家卫风格模板 — 情感戏分镜质量提升

```markdown
【风格定义】
【风格】90年代香港艺术电影风格
【情感基调】浪漫/忧郁
【色调】暧昧黄绿色调，复古胶片感，高ISO颗粒
【技术参数】抽帧效果，浅景深，偏色

【【】】第01集-分镜脚本-王家卫风格

| 镜号 | 时间轴 | 景别 | 运镜 | 角色 | 动作 | 情感映射 | 口型/字幕 |
|------|--------|------|------|------|------|---------|---------|
| 01 | [00:00-00:04] | ECU | 固定 | char_01 | 紧握听筒，不说话 | 透过玻璃折射，眼神空洞却饱含深情 | （沉默，只有雨声） |
| 02 | [00:04-00:07] | CU | 推 | char_01 | 轻声耳语，嘴唇颤抖 | "想触碰却收回手"的极致克制与孤独 | "我..." |
| 03 | [00:07-00:10] | WS | 拉 | char_01 | 挂断电话，走入雨中 | 抽帧效果+动态模糊，背景车灯光轨 | （背影消失在人群中） |

【音效设计】
SFX-AMBIENT：雨声渐弱
SFX-NARRATIVE：电话挂断的咔哒声
MUSIC：爵士乐，萨克斯风，渐弱
```

来源：awesome-seedance 王家卫雨夜情感戏模板

---

## 中优先级（P1，一周内完成）

### 4. 情感映射注入 — 每镜头情感状态描述

```markdown
【情感映射】展现"想触碰却收回手"的极致克制与孤独
【情感映射】情感升级：从克制→隐忍→即将爆发
【情感映射】高潮点：情绪爆发临界值
```

**情绪五级标注**：

| 级别 | 标注 | 说明 |
|------|------|------|
| 1 | 【平静】 | 正常语速，自然呼吸 |
| 2 | 【克制】 | 压抑情感，轻声细语 |
| 3 | 【隐忍】 | 声音颤抖，强压情绪 |
| 4 | 【爆发】 | 情绪宣泄，语速加快 |
| 5 | 【高潮】 | 极端情绪，声音变形 |

### 5. 风格定义前置 — 分镜脚本头部规范

```markdown
【【】】第01集-分镜脚本-v6.3

【风格定义】
【风格】中文情感短剧 / 好莱坞赛车 / 王家卫雨夜 / 武侠仙侠
【情感基调】浪漫 / 紧张 / 悬疑 / 喜剧 / 史诗
【画面比例】9:16竖屏 / 16:9横屏
【总时长】15秒
【色调】黄绿色调（王家卫）/ 低饱和写实（维伦纽瓦）
【技术参数】颗粒质感 / 浅景深 / 抽帧效果 / 手持晃动

【角色资产】
char_01 女主：[【【】】资产引用规范]
char_02 总裁：[【【】】资产引用规范]
```

### 6. prompts.chat质量检查机制 — 漫舟效果追踪升级

```typescript
const MANZHOU_QUALITY_THRESHOLDS = {
  min_chars: 50,
  min_words: 10,
  min_shot_duration: 2,
  max_shot_duration: 15,
  ai_confidence_threshold: 0.85,
  viseme_match_threshold: 0.9,
};

interface ShotEvent {
  shot_id: string;
  watch_duration: number;
  completion_rate: number;
  like_count: number;
  comment_count: number;
  share_count: number;
  lip_sync_score: number;
  emotion_match_score: number;
}
```

---

## 低优先级（P2，未来迭代）

### 7. CDP @引用语法对齐 — v6.4规划

现状：
```markdown
char_01 女主 / loc_01 格子间 / item_01 咖啡杯
```

对齐Seedance：
```markdown
@char_01 — 女主角色参考
@loc_01 — 格子间场景
@item_01 — 咖啡杯道具
```

过渡策略：v6.3兼容层 → v6.4完全迁移

### 8. 导演风格库扩充 — v6.4迭代

| 风格 | 核心特征 | 来源 |
|------|---------|------|
| 维伦纽瓦 | IMAX 70mm，颗粒写实，史诗规模，低饱和度 | awesome-seedance |
| 诺兰 | 复杂叙事，时间扭曲，手持摄影 | 待开发 |
| 好莱坞赛车 | 运动模糊，雨夜，高风险氛围 | awesome-seedance |

### 9. manzhou-tts-voice.md v1.2 — 台词逐字情绪标注

```markdown
char_01 女主 | 【克制】 | "如...如果记忆..." | V0-V3-V7-V11 | Lip-sync: sync_window[0.0-0.8]
char_01 女主 | 【隐忍/颤抖】 | "我希望它永远不会过期" | V0-AI-V3-BMP-V7-V11 | Lip-sync: sync_window[0.8-2.0]
char_01 女主 | 【克制/坚定】 | "这个吻，我不后悔" | V0-CH-V7-V11 | Lip-sync: sync_window[2.0-3.2]
```

---

## 执行计划

### v6.3升级（1-2天）

| Task | 文件 | 内容 |
|------|------|------|
| Task 1 | manzhou-shot-script.md | P01时间轴格式 + 情感映射字段 + 风格定义前置 |
| Task 2 | manzhou-tts-voice.md v1.2 | 台词逐字情绪标注五级规范 |
| Task 3 | manzhou-master.md v6.3 | 集成v6.3全部变更 |

### v6.4迭代（3-5天）

| Task | 内容 |
|------|------|
| Task 4 | CDP @语法支持 + 兼容层 |
| Task 5 | 王家卫/维伦纽瓦/诺兰风格模板库 |
| Task 6 | prompts.chat式阈值检查 + AI质量评分 |
```
