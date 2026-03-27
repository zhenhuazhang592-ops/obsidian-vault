---
title: AI Video Creation with Claude and Remotion
date: 2026-03-18
tags:
  - notebooklm
  - AI
  - Claude
  - Remotion
  - 视频制作
category: AI 工具
source: NotebookLM
---

# AI Video Creation with Claude and Remotion

> [!abstract] 概述
> 介绍如何使用 Claude 的 Remotion 技能来自动化创建视频内容。

---

## 核心理念

将 Claude 比作厨师，**Remotion** 就是制作视频的"技能"。

即使没有技术背景，用户也只需通过对话即可完成操作。

---

## 三个阶段

### 第一阶段：基础设置

> [!note] 准备工作

1. 下载安装 **Claude Desktop**（Mac/Windows）
2. 进入 **Co-work** 或 **Code** 模式
3. 添加视频制作技能：
   ```bash
   npx skills add remotion dev skills
   ```

4. 首个视频：指定文件夹存放视频资源
   - 可根据网站文案、颜色、图片自动生成动态产品演示视频

---

### 第二阶段：技能堆叠

> [!tip] 进阶技巧

- **Claude Code**：可运行服务器并生成视频链接

- **个性化定制**：通过对话修改 Logo 或组件位置

- **服务集成**：
  | 服务 | 用途 |
  |------|------|
  | 11 Labs | AI 配音 |
  | Nano Banana Pro | 图像生成 |
  | Wavespeed | API 整合平台 |

- **记忆功能**：创建 `claude.md` 文件记录指令偏好和风格要求

---

### 第三阶段：视频链制作长视频

> [!warning] 长视频制作流程

1. 编写大纲或脚本
2. 为每个部分制作独立短视频
3. 录制主视频
4. Claude 担任"编排者"缝合所有片段

---

## 应用场景

- 产品演示
- 动态图形
- 自动化营销视频
- 品牌内容创作
