---
title: waoowaoo README 归档
date: 2026-03-27
tags:
  - waoowaoo
  - 归档
---

# waoowaoo AI 影视 Studio — README 归档

> 原始来源：https://github.com/saturndec/waoowaoo/blob/main/README.md

---

## 功能特性

- AI 剧本分析 — 自动解析小说，提取角色、场景、剧情
- 角色 & 场景生成 — AI 生成一致性人物和场景图片
- 分镜视频制作 — 自动生成分镜头并合成视频
- AI 配音 — 多角色语音合成
- 多语言支持 — 中文 / 英文界面，右上角一键切换

---

## 快速开始

### 前提条件

安装 [Docker Desktop](https://docs.docker.com/get-docker/)

### 方式一：拉取预构建镜像（最简单）

```bash
# 下载 docker-compose.yml
curl -O https://raw.githubusercontent.com/saturndec/waoowaoo/main/docker-compose.yml

# 启动所有服务
docker compose up -d
```

> 当前为测试版，版本间数据库不兼容。升级请先清除旧数据：

```bash
docker compose down -v
docker rmi ghcr.io/saturndec/waoowaoo:latest
curl -O https://raw.githubusercontent.com/saturndec/waoowaoo/main/docker-compose.yml
docker compose up -d
```

> 启动后请**清空浏览器缓存**并重新登录。

### 方式二：克隆仓库 + Docker 构建

```bash
git clone https://github.com/saturndec/waoowaoo.git
cd waoowaoo
docker compose up -d
```

### 方式三：本地开发模式

```bash
git clone https://github.com/saturndec/waoowaoo.git
cd waoowaoo
cp .env.example .env
# 编辑 .env，填入你的 AI API Key

npm install

# 只启动基础设施
docker compose up mysql redis minio -d

# 初始化数据库
npx prisma db push

# 启动开发服务器
npm run dev
```

> 首次启动会自动完成数据库初始化，无需任何额外配置。

**访问**：http://localhost:13000（方式一、二）或 http://localhost:3000（方式三）

---

## API 配置

启动后进入**设置中心**配置 AI 服务的 API Key，内置配置教程。

---

## 技术栈

- **框架**: Next.js 15 + React 19
- **数据库**: MySQL + Prisma ORM
- **队列**: Redis + BullMQ
- **样式**: Tailwind CSS v4
- **认证**: NextAuth.js
