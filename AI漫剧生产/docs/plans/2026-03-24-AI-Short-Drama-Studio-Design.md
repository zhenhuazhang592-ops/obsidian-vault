---
name: AI Short Drama Studio 系统设计
date: 2026-03-24
status: 设计完成，待实现
三期: 第一期 + 第二期 + 第三期
---

# AI Short Drama Studio — 系统设计文档

> **设计理念**: 树状分发 · Skill驱动 · 三期建设 · 傻瓜式输出

---

## 一、系统定位

**使用方式**: 两者兼顾
- 交互式创作（Claude Code + Skill系统）
- 批量生产（脚本化执行）

**目标**: 将任何小说或IP转化为100%可直接复制执行的"电影级AI漫剧生产资产"

**核心规则**:
1. 绝对禁止使用占位符（`...`、`等`、`以此类推`）
2. 每个镜头输出必须包含完整参数
3. Prompt必须做到精确到帧、直接复制、无需增减一字
4. 情绪与听觉必须绑定

---

## 二、技术架构

### 2.1 Agent树状分发结构

```
用户输入
   │
   ▼
【主控Agent】 manzhou-master.md
   │
   ├──▶ 【IP解析Agent】     manzhou-ip-parser.md
   ├──▶ 【爆款算法Agent】   manzhou-hit-engine.md
   ├──▶ 【剧本Agent】       manzhou-script.md
   ├──▶ 【导演Agent】       manzhou-director.md
   ├──▶ 【视觉Agent】       manzhou-visual-style.md
   ├──▶ 【角色Agent】       manzhou-character-consistency.md
   ├──▶ 【配音Agent】       manzhou-voice.md
   ├──▶ 【BGM Agent】       manzhou-bgm.md
   ├──▶ 【SFX Agent】       manzhou-sfx.md
   └──▶ 【风控Agent】       manzhou-safety.md
```

### 2.2 核心工具链

- **主视频**: Seedance（字节跳动AI视频模型）
- **兼容视频**: Kling（快手可灵）
- **配乐生成**: Suno / Udio
- **配音**: VO标签系统（接入第三方TTS）

### 2.3 角色一致性保障

- **Reference Image + Tag双锁**
- 每个角色预设定妆照（用户上传）
- 强制Tag权重参数包
- 禁止出现的特征清单

### 2.4 内置风控

- 角色名/场景/情绪标签自动检查
- 过滤敏感词
- 符合国内平台规范

---

## 三、三期建设计划

### 第一期（剧本创作系统）

| Engine | 输入 | 输出 |
|--------|------|------|
| IP解析 | 小说文本/简介 | 世界观、人物体系、核心冲突 |
| 剧本生成 | IP档案 + 用户指令 | 分集剧本（每集详细剧情） |
| 分镜输出 | 剧本 + 视觉风格 | 每集完整镜头脚本 + Prompt |
| 风控检查 | 剧本/分镜 | 敏感词/合规审核 |

**交付物**:
- `manzhou-master.md`
- `manzhou-ip-parser.md`
- `manzhou-script.md`
- `manzhou-storyboard.md`
- `manzhou-safety.md`

---

### 第二期（爆款算法 + 视觉系统）

| Engine | 输入 | 输出 |
|--------|------|------|
| 爆款算法 | 剧本/集数 | 爆点密度检测、钩子优化、反转插入、情绪曲线 |
| 视觉风格库 | 剧本情绪 + 类型 | 匹配的电影级视觉风格方案 |
| 角色一致性 | 角色档案 | Reference Image + Tag参数包 |

**交付物**:
- `manzhou-hit-engine.md`
- `manzhou-visual-style.md`
- `manzhou-character-consistency.md`

**爆款算法检测维度**:

| 维度 | 阈值 | 说明 |
|------|------|------|
| 黄金3秒钩子 | >=70分 | 前3秒视觉冲击/悬念 |
| 爆点密度 | >=1.0 | 每3分钟一个高潮点 |
| 反转频率 | >=0.6 | 每5分钟一个反转 |
| 悬念留存 | 必须有 | 结尾钩子设计 |

**视觉风格库**（6种）:

| 风格 | 适用场景 | 代表性后缀 |
|------|----------|------------|
| 极简高级风 | 现代都市/职场/爱情轻甜 | minimalist, muted tones |
| 好莱坞史诗风 | 复仇/逆袭/商战/玄幻 | IMAX 70mm, epic |
| 王家卫情绪风 | 虐恋/离别/孤独/都市情感 | neon-lit, slow motion |
| 短剧爽剧风 | 打脸/逆袭/爽文改编 | high emotional intensity |
| 现实纪录风 | 生活类/温情/写实 | handheld, documentary |
| 赛博朋克风 | 科幻/异能/未来都市 | cyberpunk, neon |

---

### 第三期（音频系统）

| Engine | 输入 | 输出 |
|--------|------|------|
| 配音标签 | 剧本对白 | 情绪标签 + 语速 + 语调参数 |
| BGM生成 | 场景情绪 | Suno/Udio 配乐Prompt |
| SFX音效 | 场景描述 | 关键音效提示词 |

**交付物**:
- `manzhou-voice.md`
- `manzhou-bgm.md`
- `manzhou-sfx.md`
- `manzhou-audio.md`（整合输出）

---

## 四、Obsidian存储结构

```
AI漫剧生产/
└── [项目名]/
    ├── 00-项目信息/
    │   ├── 项目概述.md
    │   └── 创作笔记.md
    ├── 01-IP档案/
    │   ├── IP档案.yaml
    │   ├── 世界观设定.md
    │   └── 人物卡/
    │       ├── protagonist_01.md
    │       ├── protagonist_02.md
    │       └── antagonist_01.md
    ├── 02-剧本/
    │   ├── 第1集-剧本.md
    │   └── ...
    ├── 03-分镜/
    │   ├── 第1集-分镜.md
    │   └── ...
    ├── 04-视觉/
    │   └── 视觉风格方案.md
    ├── 05-SeedancePrompts/
    │   └── 第1集.md
    ├── 06-KlingPrompts/
    │   └── 第1集.md
    └── 07-音频包/
        ├── 配音标签表/
        ├── BGM时间轴/
        └── SFX标注/
```

---

## 五、核心输出标准

### 5.1 镜头输出"四件套"

每个镜头必须输出：

```markdown
### 镜头01

**【AI导演分镜】**
- 运镜: [全景拉开/特写推进/手持跟拍]
- 画面: [具体画面描述]
- 人物: [角色名]
- 动作: [具体动作]
- 情绪: [当前场景情绪]
- 光影: [主光/补光/氛围光]

**【配音】**
VO_Emotion: [愤怒/哽咽/冷笑/...]
语速: [1.0x/1.2x/...]
语调: [具体语调描述]
"【台词】[具体台词]"

**【音效】**
SFX: [雷声/心跳/脚步声/...]

**【Seedance直接可用Prompt】**
```
[完整英文Prompt]
--ar 16:9 --style 4k
```

**【Kling直接可用Prompt】**
```
[适配Kling格式的完整Prompt]
--aspect 16:9
```
```

### 5.2 角色身份证标准

```yaml
角色ID: protagonist_01
Reference Image: [定妆照路径]  # 用户上传
服装Tag:
  - (black formal suit:1.3)
  - (white shirt:1.1)
发型Tag:
  - (messy black hair:1.2)
光影Tag:
  - (cold dramatic rim light:1.2)
禁止Tag:
  - (different hair color) ❌
  - (beard/mustache) ❌
Seedance后缀: --cref [路径] --ar 16:9 --style 4k
```

---

## 六、Skill文件清单

| 序号 | 文件名 | 职责 | 期次 |
|------|--------|------|------|
| 1 | `manzhou-master.md` | 主控Agent，统一调度 | 全部 |
| 2 | `manzhou-ip-parser.md` | IP解析引擎 | 第一期 |
| 3 | `manzhou-script.md` | 剧本生成引擎 | 第一期 |
| 4 | `manzhou-storyboard.md` | 分镜输出引擎 | 第一期 |
| 5 | `manzhou-safety.md` | 风控审核引擎 | 第一期 |
| 6 | `manzhou-hit-engine.md` | 爆款算法引擎 | 第二期 |
| 7 | `manzhou-visual-style.md` | 视觉风格库引擎 | 第二期 |
| 8 | `manzhou-character-consistency.md` | 角色一致性引擎 | 第二期 |
| 9 | `manzhou-voice.md` | 配音标签引擎 | 第三期 |
| 10 | `manzhou-bgm.md` | BGM生成引擎 | 第三期 |
| 11 | `manzhou-sfx.md` | SFX音效引擎 | 第三期 |
| 12 | `manzhou-audio.md` | 音频系统整合 | 第三期 |

---

## 七、关键设计决策

| 决策点 | 选择 | 理由 |
|--------|------|------|
| Agent架构 | 树状分发 | 复杂IP、电影级制作 |
| 角色一致性 | Reference Image + Tag双锁 | 最可靠的一致性保障 |
| 工具链 | Seedance为主 + Kling兼容 | 字节+快手双生态 |
| 输出标准 | 四件套（分镜+配音+SFX+Prompt） | 傻瓜式直接执行 |
| 存储方案 | Obsidian Vault | 与现有笔记系统整合 |
| 风控 | 内置合规检查 | 符合国内平台规范 |

---

## 八、与V5.0对比优化

| V5.0痛点 | 优化方案 |
|----------|----------|
| 角色一致性不足 | Reference Image + Tag双锁 |
| Prompt需要二次补全 | 四件套完整输出 |
| 前3秒设计缺失 | 黄金3秒钩子库 + 爆款算法 |
| 无声音系统 | 第三期音频系统完整覆盖 |

---

## 九、下一步

- [ ] 确认设计文档
- [ ] 进入writing-plans，拆解第一期实现计划
- [ ] 开始实现第一期6个Skill文件
