---
title: Toonflow README 归档
date: 2026-03-27
tags:
  - Toonflow
  - 归档
---

# Toonflow README 归档

> 原始来源：https://github.com/HBAI-Ltd/Toonflow-app/blob/main/README.md

---

## 主要功能

- ✅ **角色生成**：自动分析小说文本，生成角色设定（外貌/性格/身份）
- ✅ **剧本生成**：基于选定事件和章节，自动生成结构化剧本
- ✅ **分镜制作**：智能生成分镜提示词与画面设计
- ✅ **视频合成**：集成 AI 图像与视频技术

---

## 安装方式

### 桌面客户端（Windows）

| 操作系统 | 下载地址 |
| :------: | :------: |
| Windows | [GitHub Release](https://github.com/HBAI-Ltd/Toonflow-app/releases) / [夸克网盘](https://pan.quark.cn/s/94ef07509df0) |
| macOS | 即将支持 |
| Linux | 即将支持 |

> 首次登录：账号 `admin`，密码 `admin123`

---

## Docker 部署

### 在线部署（推荐）

```bash
docker-compose -f docker/docker-compose.yml up -d --build
```

**构建参数：**

| 参数 | 说明 | 示例 |
|------|------|------|
| `GIT` | 代码源 | `github` / `gitee`（国内推荐）|
| `TAG` | 版本标签 | `v1.0.6` |
| `BRANCH` | 分支 | `main` / `dev` |

```bash
# 使用 Gitee（国内更快）
GIT=gitee docker-compose -f docker/docker-compose.yml up -d --build

# 指定版本
TAG=v1.0.6 docker-compose -f docker/docker-compose.yml up -d --build
```

### 本地构建

```bash
git clone https://github.com/HBAI-Ltd/Toonflow-app.git
cd Toonflow-app
docker-compose -f docker/docker-compose.local.yml up -d --build
```

**端口说明：**

| 端口 | 用途 | 在线部署 | 本地构建 |
|------|------|----------|----------|
| `80` | 前端页面 | 随机端口 | `8080:80` |
| `60000` | 后端 API | `60000:60000` | `60000:60000` |

---

## 云服务器部署（PM2）

```bash
# 1. 安装环境
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
source ~/.bashrc
nvm install 24
npm install -g yarn pm2

# 2. 克隆项目
git clone https://github.com/HBAI-Ltd/Toonflow-app.git
cd Toonflow-app
yarn install
yarn build

# 3. 配置 PM2
# 创建 pm2.json

# 4. 启动
pm2 start pm2.json
pm2 startup
pm2 save
```

> 首次登录：账号 `admin`，密码 `admin123`

---

## 开发指南

```bash
# 仅启动后端 API（端口 60000）
yarn dev

# 启动 Electron 桌面客户端（推荐完整体验）
yarn dev:gui

# 构建
yarn build

# 打包 Windows
yarn dist:win

# 代码检查
yarn lint
```

**前置条件**：Node.js 23.11.1+

---

## 相关仓库

| 仓库 | 说明 |
|------|------|
| [Toonflow-app](https://github.com/HBAI-Ltd/Toonflow-app) | 完整客户端（推荐）|
| [Toonflow-web](https://github.com/HBAI-Ltd/Toonflow-web) | 前端源码（供二次开发）|

---

## 开发计划

- 🧩 提示词润色生成 Agent（多镜头智能融合）
- 📄 多格式文本支持（剧本/漫画脚本/游戏对话）
- 👗 角色服化道管理（多剧集关联记忆）
- 📦 批量处理/任务队列
- 🎭 多风格模板库
- ⏱️ 智能节奏分析（情绪曲线/高潮点建议）
