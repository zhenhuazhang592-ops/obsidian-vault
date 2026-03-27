# 提示词工程研究报告

> 研究时间：2026-03-25
> 来源：prompts.chat + awesome-seedance + seedance-prompt-skill

---

## 目录

- [01-prompts-chat全局研究.md](01-prompts-chat全局研究.md)
- [02-awesome-seedance详细研究.md](02-awesome-seedance详细研究.md)
- [03-seedance-prompt-skill研究.md](03-seedance-prompt-skill研究.md)
- [04-漫舟借鉴与升级建议.md](04-漫舟借鉴与升级建议.md)
- [README.md](README.md)（本文件）

---

## 一、三个项目概览

| 项目 | 类型 | 规模 | 核心价值 |
|------|------|------|---------|
| **prompts.chat** | 开源提示词库平台 | 143k+ GitHub stars，91054条提示词 | 提示词聚合+质量管控+社区运营 |
| **awesome-seedance** | Seedance 2.0提示词精选 | CC BY 4.0许可 | 电影级分镜+商用场景模板 |
| **seedance-prompt-skill** | Claude Code Skill | 单文件SM单SKILL.md | 自动化Seedance提示词生成 |

## 二、核心发现

### prompts.chat — 提示词平台的工程标杆
- **质量管控**：AI质量检查（confidence≥0.85才下架）+ 基础长度过滤
- **社区机制**：提交→审核→版本控制（Change Requests）+ 打分投票
- **MCP集成**：作为MCP服务器，Claude可直接调用提示词搜索
- **多语言支持**：18种语言国际化

### awesome-seedance — 视频提示词的设计模式
- **时间轴结构化**：`[00:00-00:05]` 精确到秒的分镜控制
- **风格定义前置**：`【风格】` 开头声明导演/时代/情感基调
- **口型字幕双轨**：`口型与字幕逐字完全一致`
- **王家卫/维伦纽瓦等导演风格模板**

### seedance-prompt-skill — 提示词自动化生成
- **十大能力**：纯文本/一致性控制/运镜复刻/剧情创作/视频延长/声音控制/一镜到底/视频编辑/音乐卡点
- **四步工作流**：描述创意→确认参数→生成提示词→微调优化
- **多模态引用**：`@图片1`-`@图片9` / `@视频1`-`@视频3` / `@音频1`-`@音频3`

## 三、对漫舟最有价值的借鉴

### P0优先级
1. **Seedance时间轴格式** → 升级 manzhou-shot-script.md v6.3
2. **王家卫风格模板** → 漫舟情感戏分镜质量提升
3. **Seedance Skill的多模态引用** → 漫舟CDP资产引用规范

### P1优先级
4. **口型字幕双轨制** → 强化Lip-sync标注
5. **情感映射注入** → 每个镜头情感状态描述
6. **prompts.chat质量检查机制** → 漫舟效果追踪体系

## 四、升级路线图

```
v6.2（当前）
  ↓
v6.3（1-2天）
  - manzhou-shot-script.md：引入时间轴格式（P01格式）
  - manzhou-tts-voice.md：口型字幕双轨制
  - manzhou-master.md：风格定义前置规范
  ↓
v6.4（3-5天）
  - 情感映射注入
  - 导演风格库扩充
  - CDP @引用规范对齐Seedance语法
```
