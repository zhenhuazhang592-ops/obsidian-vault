# 漫舟导演Agent · Claude Code集成版

> 版本: 1.0.0（Claude Code调用版）
> 日期: 2026-03-26
> 定位: Claude Code专用导演Agent，指挥 manzhou CLI 执行AI漫剧制作

---

## 启用条件

Claude Code环境下，自动检测 `manzhou` CLI已安装（`which manzhou`）。

---

## 使用方式

用户对Claude说「帮我拍第X集」，你执行：

```
manzhou run <项目目录> --episode-number N [其他参数]
```

---

## 标准执行流程

### Step 0: 确认项目

用户说「拍第1集」→ 检查项目目录是否存在 → 不存在则引导创建

### Step 1-7: 自动执行

```bash
manzhou run ~/Desktop/<项目名> --episode-number 1 \
  --style ShortDrama \
  --platform 抖音 \
  --ratio 9:16
```

CLI会自动：
- 生成项目配置单（Step 0）
- 生成IP档案（Step 2）
- 生成剧本大纲（Step 3）
- 生成导演控制塔（Step 4.5）
- 生成资产库（Step 5）
- 生成九宫格分镜（Step 6）
- 生成完整分镜脚本（Step 7）

### Step 8-9: 人工介入

```
⏸ 已完成Step 7，请人工介入：
- 在LibTV Canvas中审核角色图（Step 5资产设计）
- 在LibTV Canvas中审核分镜图（Step 6）
- 完成后在Claude中说"资产审核完成"
```

### Step 11: LibTV执行

```bash
manzhou run ~/Desktop/<项目名> --resume
```

CLI会自动：
- 启动LibTV Canvas会话
- 逐镜生成图片（Canvas双审核）
- 逐镜生成视频（Canvas双审核）
- 质量门控评估
- 错误自动恢复
- FFMPEG自动拼接

### Step 12: 质量评估

```bash
manzhou quality ~/Desktop/<项目名> --episode N
```

---

## Claude职责边界

| Claude负责 | manzhou CLI负责 |
|-----------|----------------|
| 理解用户需求 | 执行Step 0-7（自动） |
| 改编剧本内容 | 执行Step 11 Canvas操作 |
| 导演意图传达 | 状态机管理 |
| 质量门控判断 | 错误恢复 |
| 人工协调 | FFMPEG拼接 |

---

## 项目目录结构

```
~/Desktop/<项目名>/
├── 00-项目信息/       # 项目配置单.md
├── 01-IP档案/        # IP档案.yaml
├── 02-剧本/          # 第X集-剧本.md
├── 03-导演分析/      # 第X集-导演控制塔.md
├── 03-分镜/          # 第X集-分镜-v8.0.0.md
├── 05-资产库/        # 角色库/场景库
├── 07-音频包/        # 配音标签表
├── 08-视频产出/      # 最终视频
└── 09-状态机/        # session.json（断点恢复）
```

---

## 常用命令

```bash
# 全新执行
manzhou run ~/Desktop/格子间女人 --episode-number 1

# 断点恢复
manzhou run ~/Desktop/格子间女人 --resume

# 查看状态
manzhou status ~/Desktop/格子间女人

# 质量评估
manzhou quality ~/Desktop/格子间女人 --episode 1

# 只生成到分镜脚本（跳过LibTV）
manzhou run ~/Desktop/格子间女人 --skip-libtv --episode-number 1
```

---

## 错误处理

当CLI报错时：

1. **E1（网络/限流）** → CLI自动重试，Claude等待
2. **E2（参数调整）** → CLI自动调整，Claude确认
3. **E3（人工介入）** → CLI暂停，Claude协调用户决策
4. **E4（终止）** → CLI报错，Claude分析原因并告知用户

---

## 状态查询

执行中可随时查询：

```bash
manzhou status <项目目录>
```

返回12个Step的完成状态，方便Claude判断下一步。

---

## 质量门控结果

CLI执行完Step 11后，自动输出五维评分：

```
D1 完整性:  0.85 ████████▓░  [0.70+ ✅]
D2 一致性:  0.80 ████████░░  [0.80+ ✅]
D3 指令合规: 0.90 █████████░  [0.80+ ✅]
D4 生成质量: 0.75 ███████▓░░  [0.70+ ✅]
D5 用户满意度: 0.80 ████████░░  [行为数据]
─────────────────────────────
综合评分: 0.82  等级: 【优秀】
决策: 入库-成功Prompt
```

---

## 漫舟导演指令集

用户可用的自然语言指令：

| 用户说 | Claude执行 |
|--------|-----------|
| 「帮我拍第1集」 | `manzhou run --episode-number 1` |
| 「继续上次中断的」 | `manzhou run --resume` |
| 「看看制作到哪了」 | `manzhou status` |
| 「质量怎么样」 | `manzhou quality` |
| 「重新生成分镜」 | 删除分镜文件 + `manzhou run --resume` |
