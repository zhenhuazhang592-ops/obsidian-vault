# 漠玫 Mo Mei · 独立站实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal：**上线一个漠玫品牌独立站（13个页面，20篇内容），支持 SEO + 私域导流，托管于 Vercel。

**Architecture：**Next.js 14 + App Router + MDX 内容管理，无后端无数据库，静态生成+ISR，适合内容主导的品品牌站。前端全栈由外包方负责，内容由运营方提供。

**Tech Stack：**Next.js 14 · TailwindCSS · Framer Motion · Contentlayer · Vercel · MDX

---

## 阶段总览

| 阶段 | 时长 | 主要工作 |
|------|------|---------|
| Phase 0 | Week 0 | 项目准备与环境搭建 |
| Phase 1 | Week 1-2 | 品牌设计与 UI |
| Phase 2 | Week 3-4 | 核心开发 |
| Phase 3 | Week 5 | 内容填充 |
| Phase 4 | Week 6 | 测试上线 |

---

## Phase 0 · 项目准备（第0周）

### Task 0: 项目初始化

**Files：**
- 创建: `PROJECT_ROOT/`（项目根目录，假设 `~/projects/momo-website/`）
- 创建: `PROJECT_ROOT/README.md`
- 创建: `PROJECT_ROOT/.env.example`

**Step 1: 创建项目目录并初始化 Next.js**

```bash
mkdir -p ~/projects/momo-website
cd ~/projects/momo-website
npx create-next-app@latest . \
  --typescript \
  --tailwind \
  --eslint \
  --app \
  --src-dir=false \
  --import-alias="@/*"
```

**Step 2: 安装核心依赖**

```bash
npm install framer-motion contentlayer @next/mdx @mdx-js/react gray-matter
npm install -D @tailwindcss/typography
```

**Step 3: 创建 .env.example**

```bash
# 企微客服二维码图片URL（可选）
NEXT_PUBLIC_WECHAT_QR_URL=/images/wechat-qr.png
# 公众号二维码图片URL
NEXT_PUBLIC_GZH_QR_URL=/images/gzh-qr.png
```

**Step 4: 配置 Tailwind typography 插件**

```js
// tailwind.config.ts
import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./content/**/*.{md,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        "momo-green": "#2E7D32",
        "momo-light": "#8BC34A",
        "momo-cream": "#FDFBF7",
        "momo-gold": "#D4A853",
        "momo-black": "#1A1A1A",
        "momo-gray": "#6B6B6B",
      },
      fontFamily: {
        serif: ["Noto Serif SC", "serif"],
        sans: ["Noto Sans SC", "sans-serif"],
        display: ["Playfair Display", "serif"],
      },
    },
  },
  plugins: [require("@tailwindcss/typography")],
};
export default config;
```

**Step 5: 提交**

```bash
git init
git add README.md .env.example package.json next.config.ts tailwind.config.ts
git commit -m "chore: init Next.js 14 project with TypeScript and Tailwind"
```

---

## Phase 1 · 品牌设计与 UI（第1-2周）

> ⚠️ 此阶段由设计师负责，外包方 Design Team 输出。

### Task 1: 品牌 Logo 设计

**交付物：**
- 3套 Logo 方案（见下方）
- 每套包含：全彩版 / 单色版 / 深色版 / 透明背景 PNG + SVG

**Logo 方案要求：**

方案A：字母组合（推荐）
```
M M          # 抽象线条构成 "M" 形，融入水果自然曲线
  ╰─╯
```

方案B：中英文组合
```
漠 玫
Mo Mei      # 中文书法感 + 英文无衬线组合
```

方案C：抽象图形
```
◯ 🌿         # 圆形（代表水果）+ 叶片（代表自然）
```

**确认节点：** 设计师提交3方案 → 华哥选择1个 → 微调 → 确认

---

### Task 2: VI 设计规范输出

**Files：**
- 创建: `PROJECT_ROOT/design/VI-Brand-Guidelines.pdf`
- 创建: `PROJECT_ROOT/design/UI-Style-Guide.fig`

**VI 规范必须包含：**

| 内容 | 说明 |
|------|------|
| 色彩体系 | 主色/辅色/背景/强调色的 Hex + CMYK + Pantone |
| 字体规范 | 标题字体（Noto Serif SC Bold）+ 正文字体（Noto Sans SC）+ 英文装饰（Playfair Display） |
| Logo 使用规范 | 最小尺寸/安全距离/禁止使用场景 |
| 组件规范 | 按钮/卡片/标签/表单的尺寸/圆角/间距 |
| 图片风格 | 产品摄影风格指引、禁止示例 |
| 动效风格 | 参考 Framer Motion 参数范围 |

---

### Task 3: UI 高保真原型（Figma）

**Files：**
- 创建: `PROJECT_ROOT/design/Figma-Prototype.md`（含 Figma 链接）

**必须包含以下页面原型：**

1. 首页（桌面版 + 移动版）
2. 产品列表页
3. 产品详情页（任意一个）
4. 博客首页
5. 文章详情页
6. 品牌故事页
7. 联系我们页
8. 私域导流弹窗（全状态）

**确认节点：** 华哥审阅 Figma 原型 → 确认后进入开发阶段

---

## Phase 2 · 核心开发（第3-4周）

### Task 4: 全局布局组件

**Files：**
- 创建: `app/layout.tsx`
- 创建: `components/layout/Header.tsx`
- 创建: `components/layout/Footer.tsx`
- 创建: `styles/globals.css`

**Step 1: 全局 CSS 变量**

```css
/* styles/globals.css */
:root {
  --color-primary: #2E7D32;
  --color-primary-dark: #1B5E20;
  --color-primary-light: #8BC34A;
  --color-cream: #FDFBF7;
  --color-gold: #D4A853;
  --color-black: #1A1A1A;
  --color-gray: #6B6B6B;
  --radius-base: 8px;
  --shadow-card: 0 2px 12px rgba(0,0,0,0.06);
  --shadow-hover: 0 8px 24px rgba(0,0,0,0.1);
}

body {
  background-color: var(--color-cream);
  color: var(--color-black);
  font-family: "Noto Sans SC", sans-serif;
}
```

**Step 2: Header 组件**

```tsx
// components/layout/Header.tsx
"use client";
import Link from "next/link";
import { useState } from "react";
import { motion } from "framer-motion";

const navLinks = [
  { href: "/brand", label: "品牌" },
  { href: "/products", label: "产品" },
  { href: "/blog", label: "博客" },
  { href: "/contact", label: "联系我们" },
];

export default function Header() {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-[var(--color-cream)]/95 backdrop-blur-sm border-b border-black/5">
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2">
          <span className="font-serif text-2xl font-bold tracking-wide">漠玫</span>
          <span className="font-display text-sm text-[var(--color-gray)]">Mo Mei</span>
        </Link>

        {/* Desktop Nav */}
        <nav className="hidden md:flex items-center gap-8">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="text-sm font-medium text-[var(--color-black)] hover:text-[var(--color-primary)] transition-colors"
            >
              {link.label}
            </Link>
          ))}
        </nav>

        {/* 企微按钮 */}
        <Link
          href="/contact"
          className="hidden md:flex items-center gap-2 px-4 py-2 bg-[var(--color-primary)] text-white text-sm font-semibold rounded-[var(--radius-base)] hover:bg-[var(--color-primary-dark)] transition-colors"
        >
          咨询我们
        </Link>

        {/* Mobile Menu Toggle */}
        <button
          className="md:hidden p-2"
          onClick={() => setMobileOpen(!mobileOpen)}
          aria-label="菜单"
        >
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
            {mobileOpen ? (
              <path d="M6 6l12 12M6 18L18 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            ) : (
              <path d="M4 6h16M4 12h16M4 18h16" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            )}
          </svg>
        </button>
      </div>

      {/* Mobile Menu */}
      {mobileOpen && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="md:hidden bg-white border-t border-black/5 px-6 py-4 space-y-4"
        >
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="block text-base font-medium py-2"
              onClick={() => setMobileOpen(false)}
            >
              {link.label}
            </Link>
          ))}
        </motion.div>
      )}
    </header>
  );
}
```

**Step 3: Footer 组件**

```tsx
// components/layout/Footer.tsx
import Link from "next/link";

export default function Footer() {
  return (
    <footer className="bg-[var(--color-black)] text-white py-12">
      <div className="max-w-7xl mx-auto px-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Brand */}
          <div>
            <p className="font-serif text-2xl font-bold mb-2">漠玫</p>
            <p className="font-display text-sm text-white/60">Mo Mei</p>
            <p className="mt-4 text-sm text-white/70 leading-relaxed">
              精选全球优质产地<br />懂水果的生活家
            </p>
          </div>

          {/* 导航 */}
          <div>
            <p className="font-semibold mb-3">探索</p>
            <ul className="space-y-2 text-sm text-white/70">
              <li><Link href="/brand" className="hover:text-white transition-colors">品牌故事</Link></li>
              <li><Link href="/products" className="hover:text-white transition-colors">产品列表</Link></li>
              <li><Link href="/blog" className="hover:text-white transition-colors">博客文章</Link></li>
              <li><Link href="/contact" className="hover:text-white transition-colors">联系我们</Link></li>
            </ul>
          </div>

          {/* 品类 */}
          <div>
            <p className="font-semibold mb-3">精选品类</p>
            <ul className="space-y-2 text-sm text-white/70">
              <li><Link href="/products/avocado" className="hover:text-white transition-colors">牛油果</Link></li>
              <li><Link href="/products/durian" className="hover:text-white transition-colors">榴莲</Link></li>
              <li><Link href="/products/blueberry" className="hover:text-white transition-colors">蓝莓</Link></li>
            </ul>
          </div>

          {/* 联系 */}
          <div>
            <p className="font-semibold mb-3">关注我们</p>
            <p className="text-sm text-white/70 mb-2">扫码添加客服微信</p>
            {/* 公众号二维码 */}
            <div className="w-20 h-20 bg-white/10 rounded-lg flex items-center justify-center">
              <span className="text-xs text-white/50">二维码</span>
            </div>
          </div>
        </div>

        <div className="border-t border-white/10 mt-8 pt-8 text-center text-xs text-white/40">
          © {new Date().getFullYear()} 漠玫 Mo Mei · 保留所有权利
        </div>
      </div>
    </footer>
  );
}
```

**Step 4: Root Layout**

```tsx
// app/layout.tsx
import type { Metadata } from "next";
import "./styles/globals.css";
import Header from "@/components/layout/Header";
import Footer from "@/components/layout/Footer";
import PrivateTrafficFloat from "@/components/layout/PrivateTrafficFloat";

export const metadata: Metadata = {
  title: {
    default: "漠玫 Mo Mei - 进口高端水果品牌 | 牛油果 榴莲 蓝莓",
    template: "%s - 漠玫 Mo Mei",
  },
  description:
    "漠玫精选全球优质产地，提供牛油果、榴莲、蓝莓等进口高端水果。品牌故事、产地溯源、健康食谱——漠玫，懂水果的生活家。",
  keywords: ["进口水果", "牛油果", "榴莲", "蓝莓", "高端水果", "健康饮食", "漠玫"],
  openGraph: {
    type: "website",
    locale: "zh_CN",
    siteName: "漠玫 Mo Mei",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body className="antialiased">
        <Header />
        <main className="pt-16">{children}</main>
        <Footer />
        <PrivateTrafficFloat />
      </body>
    </html>
  );
}
```

**Step 5: 提交**

```bash
git add app/layout.tsx components/layout/Header.tsx components/layout/Footer.tsx styles/globals.css
git commit -m "feat: add global layout with Header, Footer and CSS variables"
```

---

### Task 5: 企微悬浮按钮 + 私域导流组件

**Files：**
- 创建: `components/layout/PrivateTrafficFloat.tsx`
- 创建: `components/layout/PrivateTrafficModule.tsx`

**Step 1: 企微悬浮按钮**

```tsx
// components/layout/PrivateTrafficFloat.tsx
"use client";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Image from "next/image";

export default function PrivateTrafficFloat() {
  const [open, setOpen] = useState(false);

  return (
    <>
      {/* 悬浮按钮 */}
      <button
        onClick={() => setOpen(true)}
        className="fixed bottom-6 right-6 z-50 w-14 h-14 bg-[var(--color-primary)] rounded-full shadow-lg flex flex-col items-center justify-center text-white hover:bg-[var(--color-primary-dark)] transition-colors cursor-pointer"
        aria-label="联系客服"
      >
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
        </svg>
        <span className="text-[10px] mt-0.5 font-semibold">咨询</span>
      </button>

      {/* 弹窗 */}
      <AnimatePresence>
        {open && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/40 z-50"
              onClick={() => setOpen(false)}
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.9, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.9, y: 20 }}
              transition={{ type: "spring", damping: 25 }}
              className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-50 bg-white rounded-2xl shadow-2xl p-8 w-[360px] max-w-[90vw]"
            >
              <button
                onClick={() => setOpen(false)}
                className="absolute top-4 right-4 text-[var(--color-gray)] hover:text-[var(--color-black)]"
                aria-label="关闭"
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M18 6L6 18M6 6l12 12" strokeLinecap="round"/>
                </svg>
              </button>

              <div className="text-center">
                <p className="font-serif text-xl font-bold text-[var(--color-black)] mb-1">扫码添加客服微信</p>
                <p className="text-sm text-[var(--color-gray)] mb-6">回复「入群」，邀请你进漠玫健康生活福利群</p>

                <div className="w-40 h-40 mx-auto bg-[var(--color-cream)] rounded-xl flex items-center justify-center border border-black/5 mb-4">
                  {/* TODO: 替换为真实企微二维码 */}
                  <span className="text-xs text-[var(--color-gray)]">企微二维码</span>
                </div>

                <p className="text-xs text-[var(--color-gray)]">
                  或搜索微信号：<span className="font-semibold text-[var(--color-black)]">momoeats</span>
                </p>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
}
```

**Step 2: 私域导流模块（底部版）**

```tsx
// components/layout/PrivateTrafficModule.tsx
import Image from "next/image";

export default function PrivateTrafficModule({ variant = "default" }: { variant?: "default" | "hero" }) {
  if (variant === "hero") {
    return (
      <section className="bg-[var(--color-primary)] py-16">
        <div className="max-w-7xl mx-auto px-6 text-center text-white">
          <h2 className="font-serif text-3xl font-bold mb-2">漠玫 · 你的水果健康生活圈</h2>
          <p className="text-white/80 mb-8">每周一份水果健康指南 · 社群专属价格 · 新品抢先尝</p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-6">
            <div className="w-32 h-32 bg-white rounded-xl flex items-center justify-center">
              <span className="text-xs text-[var(--color-gray)]">公众号二维码</span>
            </div>
            <div className="text-left">
              <p className="font-semibold mb-1">扫码关注公众号</p>
              <p className="text-sm text-white/80">回复「入群」邀请你进福利群</p>
            </div>
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className="bg-[var(--color-cream)] border-t border-black/5 py-12">
      <div className="max-w-4xl mx-auto px-6">
        <div className="text-center mb-8">
          <h2 className="font-serif text-2xl font-bold text-[var(--color-black)] mb-2">
            漠玫 · 你的水果健康生活圈
          </h2>
          <p className="text-sm text-[var(--color-gray)]">
            每周一份水果健康指南 · 社群专属价格 · 新品抢先尝
          </p>
        </div>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-6 bg-white rounded-2xl p-6 shadow-[var(--shadow-card)]">
          <div className="w-28 h-28 bg-[var(--color-cream)] rounded-xl flex items-center justify-center flex-shrink-0">
            <span className="text-xs text-[var(--color-gray)]">公众号二维码</span>
          </div>
          <div>
            <p className="font-semibold text-[var(--color-black)] mb-1">扫码关注公众号</p>
            <p className="text-sm text-[var(--color-gray)] mb-3">回复「入群」，邀请你进漠玫健康生活福利群</p>
            <p className="text-sm text-[var(--color-gray)]">
              或直接添加客服微信：<span className="font-semibold text-[var(--color-black)]">momoeats</span>
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
```

**Step 3: 提交**

```bash
git add components/layout/PrivateTrafficFloat.tsx components/layout/PrivateTrafficModule.tsx
git commit -m "feat: add private traffic float button and CTA module"
```

---

### Task 6: 首页开发

**Files：**
- 创建: `app/page.tsx`
- 创建: `components/sections/Hero.tsx`
- 创建: `components/sections/CategoryShowcase.tsx`
- 创建: `components/sections/BlogPreview.tsx`

**Step 1: Hero 区域**

```tsx
// components/sections/Hero.tsx
"use client";
import { motion } from "framer-motion";
import Link from "next/link";

const containerVariants = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.1 } },
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5, ease: "easeOut" } },
};

export default function Hero() {
  return (
    <section className="relative h-screen min-h-[600px] flex items-center justify-center overflow-hidden">
      {/* 背景图（占位：需替换为真实食材摄影） */}
      <div className="absolute inset-0 bg-[url('/images/hero-bg.jpg')] bg-cover bg-center">
        <div className="absolute inset-0 bg-black/30" />
      </div>

      {/* 内容 */}
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="relative z-10 text-center text-white px-6 max-w-4xl"
      >
        <motion.p variants={itemVariants} className="font-display text-sm tracking-[0.3em] uppercase mb-4 text-white/80">
          Premium Healthy Fresh
        </motion.p>
        <motion.h1 variants={itemVariants} className="font-serif text-5xl md:text-7xl font-bold mb-4 leading-tight">
          Eat Real.<br />Live Better.
        </motion.h1>
        <motion.p variants={itemVariants} className="font-serif text-xl md:text-2xl mb-8 text-white/90">
          漠玫 · 懂水果的生活家
        </motion.p>
        <motion.div variants={itemVariants} className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link
            href="/products"
            className="px-8 py-3 bg-[var(--color-primary)] text-white font-semibold rounded-[var(--radius-base)] hover:bg-[var(--color-primary-dark)] transition-colors"
          >
            探索产品
          </Link>
          <Link
            href="/blog"
            className="px-8 py-3 bg-white/10 backdrop-blur-sm text-white font-semibold rounded-[var(--radius-base)] border border-white/30 hover:bg-white/20 transition-colors"
          >
            阅读文章
          </Link>
        </motion.div>
      </motion.div>
    </section>
  );
}
```

**Step 2: 品类展示**

```tsx
// components/sections/CategoryShowcase.tsx
"use client";
import Link from "next/link";
import Image from "next/image";
import { motion } from "framer-motion";

const categories = [
  {
    name: "牛油果",
    slug: "avocado",
    tagline: "绵密口感，油脂皇后",
    image: "/images/category-avocado.jpg",
    href: "/products/avocado",
  },
  {
    name: "榴莲",
    slug: "durian",
    tagline: "果中之王，浓郁醇厚",
    image: "/images/category-durian.jpg",
    href: "/products/durian",
  },
  {
    name: "蓝莓",
    slug: "blueberry",
    tagline: "护眼小精灵，花青素宝库",
    image: "/images/category-blueberry.jpg",
    href: "/products/blueberry",
  },
];

export default function CategoryShowcase() {
  return (
    <section className="py-16 bg-white">
      <div className="max-w-7xl mx-auto px-6">
        <div className="text-center mb-12">
          <h2 className="font-serif text-3xl font-bold text-[var(--color-black)]">漠玫精选</h2>
          <p className="text-[var(--color-gray)] mt-2">每一颗水果，都经过严格筛选</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {categories.map((cat) => (
            <Link key={cat.slug} href={cat.href}>
              <motion.div
                whileHover={{ y: -4, boxShadow: "var(--shadow-hover)" }}
                transition={{ duration: 0.2 }}
                className="group rounded-2xl overflow-hidden shadow-[var(--shadow-card)] cursor-pointer"
              >
                <div className="relative h-64 bg-[var(--color-cream)]">
                  <Image
                    src={cat.image}
                    alt={cat.name}
                    fill
                    className="object-cover group-hover:scale-105 transition-transform duration-300"
                    sizes="(max-width: 768px) 100vw, 33vw"
                  />
                </div>
                <div className="p-6 bg-white">
                  <h3 className="font-serif text-xl font-bold text-[var(--color-black)]">{cat.name}</h3>
                  <p className="text-sm text-[var(--color-gray)] mt-1">{cat.tagline}</p>
                </div>
              </motion.div>
            </Link>
          ))}
        </div>
      </div>
    </section>
  );
}
```

**Step 3: 最新文章预览**

```tsx
// components/sections/BlogPreview.tsx
import Link from "next/link";
import Image from "next/image";

const recentPosts = [
  {
    slug: "avocado-benefits",
    title: "牛油果的10个健康益处",
    category: "牛油果",
    excerpt: "牛油果不只是健身餐的标配，它的好处远超你想象。",
    image: "/images/blog/avocado-benefits.jpg",
    readingTime: "8分钟",
  },
  {
    slug: "durian-how-to-eat",
    title: "榴莲怎么开完整不浪费",
    category: "榴莲",
    excerpt: "买了一个榴莲却不知道怎么开？这篇教会你。",
    image: "/images/blog/durian-how-to-eat.jpg",
    readingTime: "5分钟",
  },
  {
    slug: "blueberry-benefits",
    title: "蓝莓护眼是真的吗",
    category: "蓝莓",
    excerpt: "从小听到大的说法，到底有没有科学依据？",
    image: "/images/blog/blueberry-benefits.jpg",
    readingTime: "6分钟",
  },
];

export default function BlogPreview() {
  return (
    <section className="py-16 bg-[var(--color-cream)]">
      <div className="max-w-7xl mx-auto px-6">
        <div className="flex items-center justify-between mb-10">
          <div>
            <h2 className="font-serif text-3xl font-bold text-[var(--color-black)]">漠玫生活</h2>
            <p className="text-[var(--color-gray)] mt-1">健康饮食，从认识一颗好水果开始</p>
          </div>
          <Link href="/blog" className="text-[var(--color-primary)] font-semibold hover:underline text-sm">
            查看全部 →
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {recentPosts.map((post) => (
            <Link key={post.slug} href={`/blog/${post.slug}`}>
              <article className="group bg-white rounded-2xl overflow-hidden shadow-[var(--shadow-card)] hover:shadow-[var(--shadow-hover)] transition-shadow cursor-pointer">
                <div className="relative h-48 bg-[var(--color-cream)]">
                  <Image
                    src={post.image}
                    alt={post.title}
                    fill
                    className="object-cover group-hover:scale-105 transition-transform duration-300"
                    sizes="(max-width: 768px) 100vw, 33vw"
                  />
                </div>
                <div className="p-5">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-xs font-semibold text-[var(--color-primary)] bg-[var(--color-primary)]/10 px-2 py-0.5 rounded-full">
                      {post.category}
                    </span>
                    <span className="text-xs text-[var(--color-gray)]">{post.readingTime}</span>
                  </div>
                  <h3 className="font-semibold text-[var(--color-black)] mb-2 group-hover:text-[var(--color-primary)] transition-colors">
                    {post.title}
                  </h3>
                  <p className="text-sm text-[var(--color-gray)] line-clamp-2">{post.excerpt}</p>
                </div>
              </article>
            </Link>
          ))}
        </div>
      </div>
    </section>
  );
}
```

**Step 4: 首页组装**

```tsx
// app/page.tsx
import Hero from "@/components/sections/Hero";
import CategoryShowcase from "@/components/sections/CategoryShowcase";
import BlogPreview from "@/components/sections/BlogPreview";
import PrivateTrafficModule from "@/components/layout/PrivateTrafficModule";

export default function HomePage() {
  return (
    <>
      <Hero />
      <CategoryShowcase />
      <PrivateTrafficModule variant="hero" />
      <BlogPreview />
      <PrivateTrafficModule />
    </>
  );
}
```

**Step 5: 提交**

```bash
git add app/page.tsx components/sections/Hero.tsx components/sections/CategoryShowcase.tsx components/sections/BlogPreview.tsx
git commit -m "feat: build homepage with Hero, CategoryShowcase, BlogPreview and PrivateTraffic"
```

---

### Task 7: 产品列表页

**Files：**
- 创建: `app/products/page.tsx`
- 创建: `components/ui/ProductCard.tsx`
- 创建: `components/ui/CategoryTabs.tsx`

**Step 1: CategoryTabs 组件**

```tsx
// components/ui/CategoryTabs.tsx
"use client";
import { useState } from "react";

const tabs = [
  { value: "all", label: "全部" },
  { value: "avocado", label: "牛油果" },
  { value: "durian", label: "榴莲" },
  { value: "blueberry", label: "蓝莓" },
];

interface CategoryTabsProps {
  active: string;
  onChange: (value: string) => void;
}

export default function CategoryTabs({ active, onChange }: CategoryTabsProps) {
  return (
    <div className="flex gap-2 flex-wrap">
      {tabs.map((tab) => (
        <button
          key={tab.value}
          onClick={() => onChange(tab.value)}
          className={`px-4 py-2 rounded-full text-sm font-medium transition-colors cursor-pointer ${
            active === tab.value
              ? "bg-[var(--color-primary)] text-white"
              : "bg-white text-[var(--color-gray)] hover:bg-[var(--color-cream)]"
          }`}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}
```

**Step 2: 产品卡片**

```tsx
// components/ui/ProductCard.tsx
import Link from "next/link";
import Image from "next/image";

interface Product {
  slug: string;
  name: string;
  category: string;
  origin: string;
  highlight: string;
  coverImage: string;
}

export default function ProductCard({ product }: { product: Product }) {
  const categoryColor: Record<string, string> = {
    avocado: "bg-green-100 text-green-700",
    durian: "bg-amber-100 text-amber-700",
    blueberry: "bg-blue-100 text-blue-700",
  };

  return (
    <Link href={`/products/${product.slug}`}>
      <article className="group bg-white rounded-2xl overflow-hidden shadow-[var(--shadow-card)] hover:shadow-[var(--shadow-hover)] transition-all cursor-pointer">
        <div className="relative h-56 bg-[var(--color-cream)]">
          <Image
            src={product.coverImage}
            alt={product.name}
            fill
            className="object-cover group-hover:scale-105 transition-transform duration-300"
            sizes="(max-width: 768px) 50vw, 25vw"
          />
          <span className={`absolute top-3 left-3 text-xs font-semibold px-2 py-1 rounded-full ${categoryColor[product.category] || "bg-gray-100"}`}>
            {product.category === "avocado" ? "牛油果" : product.category === "durian" ? "榴莲" : "蓝莓"}
          </span>
        </div>
        <div className="p-5">
          <h3 className="font-semibold text-[var(--color-black)] mb-1 group-hover:text-[var(--color-primary)] transition-colors">
            {product.name}
          </h3>
          <p className="text-xs text-[var(--color-gray)] mb-2">产地：{product.origin}</p>
          <p className="text-sm text-[var(--color-gray)] line-clamp-2">{product.highlight}</p>
          <div className="mt-4 flex items-center text-[var(--color-primary)] text-sm font-semibold">
            查看详情
            <svg className="ml-1 w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M5 12h14M12 5l7 7-7 7" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
        </div>
      </article>
    </Link>
  );
}
```

**Step 3: 产品列表页**

```tsx
// app/products/page.tsx
"use client";
import { useState } from "react";
import CategoryTabs from "@/components/ui/CategoryTabs";
import ProductCard from "@/components/ui/ProductCard";
import PrivateTrafficModule from "@/components/layout/PrivateTrafficModule";

const allProducts = [
  {
    slug: "avocado-hass",
    name: "墨西哥哈斯牛油果",
    category: "avocado",
    origin: "墨西哥米却肯州",
    highlight: "奶油般绵密口感，油脂含量高达20%，最适合直接食用或制作酱料",
    coverImage: "/images/products/avocado-hass.jpg",
  },
  {
    slug: "avocado-fuerte",
    name: "秘鲁富尔特牛油果",
    category: "avocado",
    origin: "秘鲁",
    highlight: "果皮光滑，果肉细腻，早熟品种，春季限定",
    coverImage: "/images/products/avocado-fuerte.jpg",
  },
  {
    slug: "durian-monthong",
    name: "泰国金枕榴莲",
    category: "durian",
    origin: "泰国尖竹汶府",
    highlight: "果肉金黄饱满，甜度极高，是国内最受欢迎的榴莲品种",
    coverImage: "/images/products/durian-monthong.jpg",
  },
  {
    slug: "durian-musk",
    name: "猫山王榴莲",
    category: "durian",
    origin: "马来西亚彭亨州",
    highlight: "榴莲之王，苦中带甘，口感绵密，产量稀少",
    coverImage: "/images/products/durian-musk.jpg",
  },
  {
    slug: "blueberry-premium",
    name: "智利进口蓝莓",
    category: "blueberry",
    origin: "智利",
    highlight: "皮薄肉厚，花青素含量高，脆甜口感，自然保鲜",
    coverImage: "/images/products/blueberry-premium.jpg",
  },
  {
    slug: "blueberry-organic",
    name: "云南有机蓝莓",
    category: "blueberry",
    origin: "中国云南",
    highlight: "国产精品，有机认证，即摘即发，新鲜直达",
    coverImage: "/images/products/blueberry-organic.jpg",
  },
];

export default function ProductsPage() {
  const [activeCategory, setActiveCategory] = useState("all");
  const filtered = activeCategory === "all"
    ? allProducts
    : allProducts.filter((p) => p.category === activeCategory);

  return (
    <>
      <section className="py-12 bg-white border-b border-black/5">
        <div className="max-w-7xl mx-auto px-6">
          <h1 className="font-serif text-4xl font-bold text-[var(--color-black)] mb-2">漠玫精选</h1>
          <p className="text-[var(--color-gray)]">每一颗水果，都经过严格筛选</p>
        </div>
      </section>

      <section className="py-12">
        <div className="max-w-7xl mx-auto px-6">
          <div className="mb-8">
            <CategoryTabs active={activeCategory} onChange={setActiveCategory} />
          </div>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
            {filtered.map((product) => (
              <ProductCard key={product.slug} product={product} />
            ))}
          </div>
        </div>
      </section>
      <PrivateTrafficModule />
    </>
  );
}
```

**Step 4: 提交**

```bash
git add app/products/page.tsx components/ui/ProductCard.tsx components/ui/CategoryTabs.tsx
git commit -m "feat: build products listing page with category filter"
```

---

### Task 8: 产品详情页

**Files：**
- 创建: `app/products/[slug]/page.tsx`
- 创建: `components/ui/ProductTabs.tsx`

**Step 1: 产品详情页（静态数据版）**

```tsx
// app/products/[slug]/page.tsx
"use client";
import { useState } from "react";
import Image from "next/image";
import Link from "next/link";
import PrivateTrafficModule from "@/components/layout/PrivateTrafficModule";

// 临时硬编码数据，后续替换为 MDX 读取
const productsData: Record<string, any> = {
  "avocado-hass": {
    name: "墨西哥哈斯牛油果",
    category: "avocado",
    categoryLabel: "牛油果",
    origin: "墨西哥米却肯州",
    highlight: "奶油般绵密口感，油脂含量高达20%",
    price: "38-68",
    unit: "元/个（按规格）",
    coverImage: "/images/products/avocado-hass.jpg",
    gallery: ["/images/products/avocado-hass.jpg"],
    nutrition: [
      { label: "热量", value: "160 kcal/100g" },
      { label: "脂肪", value: "15g/100g" },
      { label: "膳食纤维", value: "7g/100g" },
      { label: "钾", value: "485mg/100g" },
      { label: "维生素E", value: "2.1mg/100g" },
    ],
    story: "墨西哥米却肯州是全球最适合牛油果生长的地区之一，位于火山带，土壤肥沃，气候温和......",
    origin: "米却肯州的农民世代种植牛油果，这里的海拔和湿度为哈斯品种提供了完美的生长条件......",
    buying: "选择表皮深褐色的哈斯牛油果，按压果柄附近有轻微软感即可食用。",
    storage: "未成熟时室温存放，成熟后放冰箱冷藏，可保存3-5天。",
  },
};

const tabList = ["营养价值", "产地故事", "选购指南", "储存方法"];

export default function ProductDetailPage({ params }: { params: { slug: string } }) {
  const [activeTab, setActiveTab] = useState(0);
  const product = productsData[params.slug];

  if (!product) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-[var(--color-gray)]">产品不存在</p>
      </div>
    );
  }

  const tabContent = [
    // 营养价值
    <div key="nutrition" className="space-y-2">
      {product.nutrition.map((item: any) => (
        <div key={item.label} className="flex justify-between py-2 border-b border-black/5">
          <span className="text-[var(--color-gray)]">{item.label}</span>
          <span className="font-semibold text-[var(--color-black)]">{item.value}</span>
        </div>
      ))}
    </div>,
    // 产地故事
    <div key="origin" className="prose prose-gray">
      <p>{product.story}</p>
      <p className="mt-4">{product.origin}</p>
    </div>,
    // 选购指南
    <div key="buying" className="prose prose-gray">
      <p>{product.buying}</p>
    </div>,
    // 储存方法
    <div key="storage" className="prose prose-gray">
      <p>{product.storage}</p>
    </div>,
  ];

  return (
    <>
      <section className="py-8">
        <div className="max-w-7xl mx-auto px-6">
          {/* 面包屑 */}
          <nav className="text-sm text-[var(--color-gray)] mb-8">
            <Link href="/" className="hover:text-[var(--color-primary)]">漠玫首页</Link>
            <span className="mx-2">/</span>
            <Link href="/products" className="hover:text-[var(--color-primary)]">产品</Link>
            <span className="mx-2">/</span>
            <span>{product.name}</span>
          </nav>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 mb-12">
            {/* 图片 */}
            <div className="relative h-[400px] lg:h-[500px] bg-[var(--color-cream)] rounded-2xl overflow-hidden">
              <Image
                src={product.coverImage}
                alt={product.name}
                fill
                className="object-cover"
                sizes="(max-width: 1024px) 100vw, 50vw"
              />
            </div>

            {/* 详情 */}
            <div>
              <span className="text-xs font-semibold text-[var(--color-primary)] bg-[var(--color-primary)]/10 px-3 py-1 rounded-full">
                {product.categoryLabel}
              </span>
              <h1 className="font-serif text-3xl font-bold text-[var(--color-black)] mt-3 mb-2">{product.name}</h1>
              <p className="text-[var(--color-gray)] mb-4">产地：{product.origin}</p>
              <p className="text-lg text-[var(--color-black)] mb-6">{product.highlight}</p>

              <div className="bg-[var(--color-cream)] rounded-xl p-6 mb-6">
                <p className="text-sm text-[var(--color-gray)] mb-1">参考价格</p>
                <p className="text-2xl font-bold text-[var(--color-primary)]">
                  {product.price} <span className="text-base font-normal text-[var(--color-gray)]">{product.unit}</span>
                </p>
              </div>

              <div className="bg-[var(--color-primary)] text-white rounded-xl p-6 text-center">
                <p className="font-semibold mb-2">扫码联系客服，获取最新报价与购买方式</p>
                <p className="text-sm text-white/80">我们提供多种规格，支持社群专属价格</p>
              </div>
            </div>
          </div>

          {/* Tab 区域 */}
          <div className="border-t border-black/5 pt-8">
            <div className="flex gap-1 bg-[var(--color-cream)] rounded-xl p-1 mb-6 overflow-x-auto">
              {tabList.map((tab, i) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(i)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-colors cursor-pointer ${
                    activeTab === i ? "bg-white shadow text-[var(--color-black)]" : "text-[var(--color-gray)] hover:text-[var(--color-black)]"
                  }`}
                >
                  {tab}
                </button>
              ))}
            </div>
            <div className="prose prose-lg max-w-none">{tabContent[activeTab]}</div>
          </div>
        </div>
      </section>
      <PrivateTrafficModule />
    </>
  );
}
```

**Step 2: 品类专区页（牛油果/榴莲/蓝莓）**

```tsx
// app/products/avocado/page.tsx
// 其他品类复制此结构，替换标题和筛选slug即可

import ProductCard from "@/components/ui/ProductCard";
import PrivateTrafficModule from "@/components/layout/PrivateTrafficModule";

const avocadoProducts = [
  {
    slug: "avocado-hass",
    name: "墨西哥哈斯牛油果",
    category: "avocado",
    origin: "墨西哥米却肯州",
    highlight: "奶油般绵密口感，油脂含量高达20%",
    coverImage: "/images/products/avocado-hass.jpg",
  },
];

export default function AvocadoPage() {
  return (
    <>
      <section className="py-12 bg-white border-b border-black/5">
        <div className="max-w-7xl mx-auto px-6">
          <h1 className="font-serif text-4xl font-bold text-[var(--color-black)]">牛油果专区</h1>
          <p className="text-[var(--color-gray)] mt-2">来自全球优质产地的精选牛油果</p>
        </div>
      </section>
      <section className="py-12">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
            {avocadoProducts.map((p) => (
              <ProductCard key={p.slug} product={p} />
            ))}
          </div>
        </div>
      </section>
      <PrivateTrafficModule />
    </>
  );
}
```

**Step 3: 提交**

```bash
git add app/products/\[slug\]/page.tsx app/products/avocado/page.tsx
git commit -m "feat: build product detail page with tabbed info"
```

---

### Task 9: 博客系统

**Files：**
- 创建: `app/blog/page.tsx`
- 创建: `app/blog/[slug]/page.tsx`
- 创建: `components/ui/BlogCard.tsx`
- 创建: `components/ui/CategoryTag.tsx`

**Step 1: MDX 内容工具**

```ts
// lib/blog.ts
// 临时使用静态数据，后续迁移到 MDX 文件读取

export interface Post {
  slug: string;
  title: string;
  category: string;
  tags: string[];
  excerpt: string;
  coverImage: string;
  author: string;
  publishedAt: string;
  readingTime: string;
  content: string;
}

export const posts: Post[] = [
  {
    slug: "avocado-benefits",
    title: "牛油果的10个健康益处",
    category: "牛油果",
    tags: ["牛油果", "健康科普", "营养"],
    excerpt: "牛油果不只是健身餐的标配，它的好处远超你想象。",
    coverImage: "/images/blog/avocado-benefits.jpg",
    author: "漠玫内容团队",
    publishedAt: "2026-03-15",
    readingTime: "8分钟",
    content: `
## 引言

牛油果，这个外表粗糙内心绵软的水果，近几年频繁出现在健身餐、轻食餐厅的菜单上。但它的好处，真的只是"健身人士爱吃"这么简单吗？

## 1. 富含单不饱和脂肪，有益心血管

牛油果的脂肪含量高达15-20%，但其中70%是单不饱和脂肪酸（油酸），这种脂肪有助于降低坏胆固醇（LDL），提升好胆固醇（HDL）。

## 2. 膳食纤维含量极高

一颗中等大小的牛油果含有约13克膳食纤维，占每日推荐摄入量的近一半。充足的膳食纤维有助于肠道健康、血糖稳定。

## 3. 钾含量超过香蕉

很多人不知道，牛油果的钾含量比香蕉高出约40%。钾是维持血压正常的重要矿物质。

## 4. 对眼睛健康有益

牛油果含有叶黄素和玉米黄质，这两种类胡萝卜素对视网膜有保护作用。

## 5. 帮助营养吸收

牛油果中的健康脂肪可以显著提升蔬菜中脂溶性维生素（A、D、E、K）的吸收率。在沙拉里加几片牛油果，比单独吃蔬菜营养价值更高。

## 6. 天然保湿成分

牛油果油被广泛用于护肤品，因为它含有维生素E和卵磷脂，有深层保湿功效。

## 7. 饱腹感强，适合体重管理

牛油果的高纤维+健康脂肪组合，带来强大的饱腹感，可以减少对零食的渴望。

## 8. 适合多种饮食方式

牛油果不含麸质，低碳水，生酮饮食、地中海饮食、DASH饮食都推荐牛油果。

## 9. 改善肠道菌群

牛油果中的膳食纤维是益生菌的"食物"，有助于维护健康的肠道菌群。

## 10. 提升整体饮食质量

研究表明，经常吃牛油果的人，整体饮食质量评分更高。

## 总结

牛油果确实是一种被低估的超级食材。但也要注意：热量不低，每天吃半个到一整个即可。
    `,
  },
  {
    slug: "durian-how-to-eat",
    title: "榴莲怎么开完整不浪费",
    category: "榴莲",
    tags: ["榴莲", "实操教程"],
    excerpt: "买了一个榴莲却不知道怎么开？这篇教会你。",
    coverImage: "/images/blog/durian-how-to-eat.jpg",
    author: "漠玫内容团队",
    publishedAt: "2026-03-18",
    readingTime: "5分钟",
    content: `
## 引言

榴莲被称为"果中之王"，但也让很多人望而却步——不知道怎么开。今天教你三步开榴莲。

## 第一步：判断成熟度

成熟的榴莲有以下特征：
- 闻：有浓郁香味，但不应有酒精味（过熟）
- 捏：两根刺能轻松靠拢，说明成熟
- 摇：有轻微的果肉脱离果壳的声音

## 第二步：找准开壳位置

榴莲的果肉藏在瓣里。从榴莲的"屁股"（底部凸起处）找缝，顺着纹路用刀尖轻轻撬开。

## 第三步：完整取出果肉

沿着缝隙掰开后，用手轻轻取出果肉。不要用勺子挖，会弄破果肉。

## 注意事项

- 未熟的榴莲不要放冰箱，会停止后熟
- 开了的榴莲放冰箱冷藏，48小时内吃完
- 榴莲和酒不宜同食
    `,
  },
];

export function getAllPosts(): Post[] {
  return posts.sort((a, b) => new Date(b.publishedAt).getTime() - new Date(a.publishedAt).getTime());
}

export function getPostBySlug(slug: string): Post | undefined {
  return posts.find((p) => p.slug === slug);
}

export function getPostsByCategory(category: string): Post[] {
  return getAllPosts().filter((p) => p.category === category);
}
```

**Step 2: 博客卡片组件**

```tsx
// components/ui/BlogCard.tsx
import Link from "next/link";
import Image from "next/image";

interface Post {
  slug: string;
  title: string;
  category: string;
  excerpt: string;
  coverImage: string;
  publishedAt: string;
  readingTime: string;
}

export default function BlogCard({ post, featured = false }: { post: Post; featured?: boolean }) {
  if (featured) {
    return (
      <Link href={`/blog/${post.slug}`}>
        <article className="group relative h-80 md:h-96 rounded-2xl overflow-hidden cursor-pointer">
          <Image
            src={post.coverImage}
            alt={post.title}
            fill
            className="object-cover group-hover:scale-105 transition-transform duration-500"
            sizes="100vw"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/20 to-transparent" />
          <div className="absolute bottom-0 left-0 right-0 p-6 text-white">
            <span className="text-xs font-semibold text-[var(--color-gold)] bg-white/10 backdrop-blur-sm px-3 py-1 rounded-full">
              {post.category}
            </span>
            <h2 className="font-serif text-2xl font-bold mt-3 mb-2">{post.title}</h2>
            <p className="text-sm text-white/80 line-clamp-2">{post.excerpt}</p>
          </div>
        </article>
      </Link>
    );
  }

  return (
    <Link href={`/blog/${post.slug}`}>
      <article className="group bg-white rounded-2xl overflow-hidden shadow-[var(--shadow-card)] hover:shadow-[var(--shadow-hover)] transition-shadow cursor-pointer">
        <div className="relative h-44 bg-[var(--color-cream)]">
          <Image
            src={post.coverImage}
            alt={post.title}
            fill
            className="object-cover group-hover:scale-105 transition-transform duration-300"
            sizes="(max-width: 768px) 100vw, 33vw"
          />
        </div>
        <div className="p-5">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xs font-semibold text-[var(--color-primary)] bg-[var(--color-primary)]/10 px-2 py-0.5 rounded-full">
              {post.category}
            </span>
            <span className="text-xs text-[var(--color-gray)]">{post.readingTime}</span>
          </div>
          <h3 className="font-semibold text-[var(--color-black)] mb-2 group-hover:text-[var(--color-primary)] transition-colors">
            {post.title}
          </h3>
          <p className="text-sm text-[var(--color-gray)] line-clamp-2">{post.excerpt}</p>
        </div>
      </article>
    </Link>
  );
}
```

**Step 3: 博客首页**

```tsx
// app/blog/page.tsx
import BlogCard from "@/components/ui/BlogCard";
import { getAllPosts } from "@/lib/blog";
import PrivateTrafficModule from "@/components/layout/PrivateTrafficModule";

const categories = ["全部", "牛油果", "榴莲", "蓝莓", "食谱", "健康科普"];

export default async function BlogPage() {
  const posts = getAllPosts();
  const [featured, ...rest] = posts;

  return (
    <>
      <section className="py-12 bg-white border-b border-black/5">
        <div className="max-w-7xl mx-auto px-6">
          <h1 className="font-serif text-4xl font-bold text-[var(--color-black)]">漠玫生活</h1>
          <p className="text-[var(--color-gray)] mt-2">健康饮食，从认识一颗好水果开始</p>
        </div>
      </section>

      <section className="py-12">
        <div className="max-w-7xl mx-auto px-6 space-y-10">
          {/* 分类标签 */}
          <div className="flex gap-2 flex-wrap">
            {categories.map((cat) => (
              <button
                key={cat}
                className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                  cat === "全部" ? "bg-[var(--color-primary)] text-white" : "bg-white text-[var(--color-gray)] hover:bg-[var(--color-cream)]"
                }`}
              >
                {cat}
              </button>
            ))}
          </div>

          {/* 精选文章 */}
          {featured && (
            <div className="mb-6">
              <BlogCard post={featured} featured />
            </div>
          )}

          {/* 文章网格 */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {rest.map((post) => (
              <BlogCard key={post.slug} post={post} />
            ))}
          </div>
        </div>
      </section>
      <PrivateTrafficModule />
    </>
  );
}
```

**Step 4: 文章详情页**

```tsx
// app/blog/[slug]/page.tsx
import Image from "next/image";
import Link from "next/link";
import { getPostBySlug, getAllPosts } from "@/lib/blog";
import PrivateTrafficModule from "@/components/layout/PrivateTrafficModule";

export async function generateStaticParams() {
  return getAllPosts().map((post) => ({ slug: post.slug }));
}

export default function BlogPostPage({ params }: { params: { slug: string } }) {
  const post = getPostBySlug(params.slug);

  if (!post) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-[var(--color-gray)]">文章不存在</p>
      </div>
    );
  }

  const allPosts = getAllPosts();
  const currentIndex = allPosts.findIndex((p) => p.slug === post.slug);
  const prevPost = currentIndex < allPosts.length - 1 ? allPosts[currentIndex + 1] : null;
  const nextPost = currentIndex > 0 ? allPosts[currentIndex - 1] : null;
  const relatedPosts = allPosts.filter((p) => p.category === post.category && p.slug !== post.slug).slice(0, 3);

  // 简单渲染内容（实际使用 MDX 渲染器）
  const paragraphs = post.content.trim().split("\n## ");

  return (
    <>
      <article className="py-12">
        <div className="max-w-3xl mx-auto px-6">
          {/* 面包屑 */}
          <nav className="text-sm text-[var(--color-gray)] mb-8">
            <Link href="/" className="hover:text-[var(--color-primary)]">漠玫首页</Link>
            <span className="mx-2">/</span>
            <Link href="/blog" className="hover:text-[var(--color-primary)]">博客</Link>
            <span className="mx-2">/</span>
            <span>{post.title}</span>
          </nav>

          {/* 文章头 */}
          <div className="text-center mb-8">
            <div className="flex items-center justify-center gap-3 mb-4">
              <span className="text-xs font-semibold text-[var(--color-primary)] bg-[var(--color-primary)]/10 px-3 py-1 rounded-full">
                {post.category}
              </span>
              <span className="text-xs text-[var(--color-gray)]">{post.publishedAt}</span>
              <span className="text-xs text-[var(--color-gray)]">·</span>
              <span className="text-xs text-[var(--color-gray)]">{post.readingTime}</span>
            </div>
            <h1 className="font-serif text-3xl md:text-4xl font-bold text-[var(--color-black)] leading-snug mb-4">
              {post.title}
            </h1>
            <p className="text-lg text-[var(--color-gray)]">{post.excerpt}</p>
            <p className="text-sm text-[var(--color-gray)] mt-2">文 / {post.author}</p>
          </div>

          {/* 封面图 */}
          <div className="relative h-64 md:h-80 bg-[var(--color-cream)] rounded-2xl overflow-hidden mb-10">
            <Image
              src={post.coverImage}
              alt={post.title}
              fill
              className="object-cover"
              sizes="(max-width: 768px) 100vw, 720px"
              priority
            />
          </div>

          {/* 正文 */}
          <div className="prose prose-lg max-w-none">
            {paragraphs.map((para, i) => (
              <div key={i}>
                {para.startsWith("#") ? (
                  <h2 id={para.split("\n")[0].replace(/^#+\s*/, "").toLowerCase()} className="font-serif text-2xl font-bold text-[var(--color-black)] mt-8 mb-4">
                    {para.split("\n")[0].replace(/^#+\s*/, "")}
                  </h2>
                ) : (
                  <p className="text-[var(--color-black)] leading-relaxed mb-4">{para.trim()}</p>
                )}
              </div>
            ))}
          </div>

          {/* 标签 */}
          <div className="flex gap-2 mt-8 pt-8 border-t border-black/5">
            {post.tags.map((tag) => (
              <span key={tag} className="text-xs bg-[var(--color-cream)] text-[var(--color-gray)] px-3 py-1 rounded-full">
                {tag}
              </span>
            ))}
          </div>

          {/* 上下篇 */}
          <div className="flex gap-4 mt-8">
            {prevPost && (
              <Link href={`/blog/${prevPost.slug}`} className="flex-1 p-4 bg-[var(--color-cream)] rounded-xl hover:bg-[var(--color-primary)]/5 transition-colors">
                <p className="text-xs text-[var(--color-gray)] mb-1">← 上一篇</p>
                <p className="text-sm font-medium text-[var(--color-black)] line-clamp-1">{prevPost.title}</p>
              </Link>
            )}
            {nextPost && (
              <Link href={`/blog/${nextPost.slug}`} className="flex-1 p-4 bg-[var(--color-cream)] rounded-xl hover:bg-[var(--color-primary)]/5 transition-colors text-right">
                <p className="text-xs text-[var(--color-gray)] mb-1">下一篇 →</p>
                <p className="text-sm font-medium text-[var(--color-black)] line-clamp-1">{nextPost.title}</p>
              </Link>
            )}
          </div>
        </div>
      </article>

      {/* 相关文章 */}
      {relatedPosts.length > 0 && (
        <section className="py-12 bg-[var(--color-cream)]">
          <div className="max-w-7xl mx-auto px-6">
            <h2 className="font-serif text-2xl font-bold text-[var(--color-black)] mb-6">相关推荐</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {relatedPosts.map((p) => (
                <Link key={p.slug} href={`/blog/${p.slug}`}>
                  <article className="bg-white rounded-xl overflow-hidden shadow-[var(--shadow-card)] hover:shadow-[var(--shadow-hover)] transition-shadow">
                    <div className="relative h-36 bg-[var(--color-cream)]">
                      <Image src={p.coverImage} alt={p.title} fill className="object-cover" sizes="33vw" />
                    </div>
                    <div className="p-4">
                      <h3 className="text-sm font-semibold text-[var(--color-black)] line-clamp-2">{p.title}</h3>
                    </div>
                  </article>
                </Link>
              ))}
            </div>
          </div>
        </section>
      )}
      <PrivateTrafficModule />
    </>
  );
}
```

**Step 5: 提交**

```bash
git add app/blog/page.tsx app/blog/\[slug\]/page.tsx components/ui/BlogCard.tsx lib/blog.ts
git commit -m "feat: build blog system with listing and detail pages"
```

---

### Task 10: 品牌故事页 & 联系我们页

**Files：**
- 创建: `app/brand/page.tsx`
- 创建: `app/contact/page.tsx`

**Step 1: 品牌故事页**

```tsx
// app/brand/page.tsx
import Image from "next/image";
import Link from "next/link";
import PrivateTrafficModule from "@/components/layout/PrivateTrafficModule";

const origins = [
  {
    name: "墨西哥 · 米却肯州",
    product: "牛油果",
    description: "火山带肥沃土壤，温和气候，世代种植牛油果的农民家族。",
    image: "/images/brand/michoacan.jpg",
  },
  {
    name: "泰国 · 尖竹汶府",
    product: "榴莲",
    description: "泰国榴莲核心产区，得天独厚的热带气候与红土土壤。",
    image: "/images/brand/chanthaburi.jpg",
  },
  {
    name: "智利 · 湖区",
    product: "蓝莓",
    description: "南半球夏季产季，昼夜温差大，果实糖分积累充足。",
    image: "/images/brand/chile-lake.jpg",
  },
];

export default function BrandPage() {
  return (
    <>
      {/* Hero */}
      <section className="relative h-[60vh] min-h-[400px] flex items-center justify-center overflow-hidden">
        <div className="absolute inset-0 bg-[url('/images/brand-hero.jpg')] bg-cover bg-center">
          <div className="absolute inset-0 bg-black/40" />
        </div>
        <div className="relative z-10 text-center text-white px-6">
          <h1 className="font-serif text-4xl md:text-5xl font-bold mb-4">漠玫，好水果的守护者</h1>
          <p className="text-lg text-white/80 max-w-xl mx-auto">精选全球优质产地，让每一颗到达你手中的水果，都值得被认真对待。</p>
        </div>
      </section>

      {/* 品牌理念 */}
      <section className="py-16 bg-white">
        <div className="max-w-5xl mx-auto px-6">
          <h2 className="font-serif text-3xl font-bold text-center mb-12">我们的理念</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              { word: "精选", desc: "只选择各产地最优等级的果园合作，不妥协于次品" },
              { word: "溯源", desc: "每一批次水果都可追溯到具体的农场和采摘时间" },
              { word: "共生", desc: "与产地农民建立长期合作，确保品质稳定" },
            ].map((item) => (
              <div key={item.word} className="text-center">
                <p className="font-serif text-5xl font-bold text-[var(--color-primary)] mb-4">{item.word}</p>
                <p className="text-[var(--color-gray)] leading-relaxed">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 产地溯源 */}
      <section className="py-16 bg-[var(--color-cream)]">
        <div className="max-w-5xl mx-auto px-6">
          <h2 className="font-serif text-3xl font-bold text-center mb-12">产地溯源</h2>
          <div className="space-y-12">
            {origins.map((origin, i) => (
              <div key={origin.name} className={`grid grid-cols-1 md:grid-cols-2 gap-8 items-center ${i % 2 === 1 ? "md:flex-row-reverse" : ""}`}>
                <div className="relative h-64 md:h-72 bg-[var(--color-cream)] rounded-2xl overflow-hidden">
                  <Image src={origin.image} alt={origin.name} fill className="object-cover" sizes="50vw" />
                </div>
                <div>
                  <span className="text-xs font-semibold text-[var(--color-primary)] bg-[var(--color-primary)]/10 px-3 py-1 rounded-full">
                    {origin.product}
                  </span>
                  <h3 className="font-serif text-2xl font-bold text-[var(--color-black)] mt-3 mb-3">{origin.name}</h3>
                  <p className="text-[var(--color-gray)] leading-relaxed">{origin.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <PrivateTrafficModule variant="hero" />
    </>
  );
}
```

**Step 2: 联系我们页**

```tsx
// app/contact/page.tsx
import PrivateTrafficModule from "@/components/layout/PrivateTrafficModule";

export default function ContactPage() {
  return (
    <>
      <section className="py-12 bg-white border-b border-black/5">
        <div className="max-w-7xl mx-auto px-6">
          <h1 className="font-serif text-4xl font-bold text-[var(--color-black)]">联系我们</h1>
          <p className="text-[var(--color-gray)] mt-2">我们在这里等你</p>
        </div>
      </section>

      <section className="py-16">
        <div className="max-w-3xl mx-auto px-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-12">
            {/* 公众号 */}
            <div className="bg-white rounded-2xl p-8 shadow-[var(--shadow-card)] text-center">
              <div className="w-16 h-16 bg-[var(--color-primary)]/10 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--color-primary)" strokeWidth="2">
                  <rect x="2" y="2" width="20" height="20" rx="5"/>
                  <path d="M8 10h8M8 14h4"/>
                </svg>
              </div>
              <h3 className="font-semibold text-[var(--color-black)] mb-2">关注公众号</h3>
              <p className="text-sm text-[var(--color-gray)] mb-4">获取每周食谱与健康指南</p>
              <div className="w-32 h-32 bg-[var(--color-cream)] rounded-xl mx-auto flex items-center justify-center border border-black/5">
                <span className="text-xs text-[var(--color-gray)]">公众号二维码</span>
              </div>
            </div>

            {/* 客服微信 */}
            <div className="bg-white rounded-2xl p-8 shadow-[var(--shadow-card)] text-center">
              <div className="w-16 h-16 bg-[var(--color-primary)]/10 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--color-primary)" strokeWidth="2">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                </svg>
              </div>
              <h3 className="font-semibold text-[var(--color-black)] mb-2">添加客服微信</h3>
              <p className="text-sm text-[var(--color-gray)] mb-4">回复「入群」，邀请你进福利群</p>
              <div className="w-32 h-32 bg-[var(--color-cream)] rounded-xl mx-auto flex items-center justify-center border border-black/5 mb-3">
                <span className="text-xs text-[var(--color-gray)]">企微二维码</span>
              </div>
              <p className="text-sm text-[var(--color-gray)]">微信号：momoeats</p>
            </div>
          </div>

          {/* 合作联系 */}
          <div className="bg-[var(--color-cream)] rounded-2xl p-8 text-center">
            <h3 className="font-serif text-xl font-bold text-[var(--color-black)] mb-2">商务合作</h3>
            <p className="text-[var(--color-gray)] mb-4">品牌合作 · 渠道分销 · 内容共创</p>
            <p className="text-[var(--color-black)]">
              邮箱：<a href="mailto:hello@momoeats.com" className="text-[var(--color-primary)] font-semibold hover:underline">hello@momoeats.com</a>
            </p>
          </div>
        </div>
      </section>

      <PrivateTrafficModule variant="hero" />
    </>
  );
}
```

**Step 3: 提交**

```bash
git add app/brand/page.tsx app/contact/page.tsx
git commit -m "feat: build brand story and contact pages"
```

---

### Task 11: SEO 配置与结构化数据

**Files：**
- 修改: `app/layout.tsx`
- 创建: `lib/seo.ts`

**Step 1: SEO 结构化数据工具**

```ts
// lib/seo.ts
import { Post } from "./blog";

export function generateArticleJsonLd(post: Post) {
  return {
    "@context": "https://schema.org",
    "@type": "Article",
    headline: post.title,
    image: post.coverImage,
    author: {
      "@type": "Organization",
      name: "漠玫内容团队",
    },
    publisher: {
      "@type": "Organization",
      name: "漠玫 Mo Mei",
    },
    datePublished: post.publishedAt,
    description: post.excerpt,
  };
}

export function generateOrgJsonLd() {
  return {
    "@context": "https://schema.org",
    "@type": "Organization",
    name: "漠玫 Mo Mei",
    description: "进口高端水果品牌，精选全球优质产地",
    url: "https://momoeats.com",
    contactPoint: {
      "@type": "ContactPoint",
      email: "hello@momoeats.com",
      contactType: "customer service",
    },
  };
}
```

**Step 2: 提交**

```bash
git add lib/seo.ts
git commit -m "feat: add SEO structured data helpers"
```

---

## Phase 3 · 内容填充（第5周）

> ⚠️ 此阶段由运营方（你）和内容编辑负责。

### Task 12: 首批20篇文章

**内容生产 SOP（由运营方执行）：**

1. 从关键词库（见设计文档第五章）选一个关键词
2. 使用 AI 提示词模板生成文章初稿
3. 人工审核：事实准确性、品牌语气、长度
4. 生成/选配图（2张/篇）
5. 将 MDX 文件放入 `/content/blog/` 目录
6. Vercel 自动触发 ISR 重新生成页面

**文件命名规范：**

```
content/blog/
├── 2026-03-15-avocado-benefits.mdx
├── 2026-03-18-durian-how-to-eat.mdx
├── 2026-03-20-blueberry-benefits.mdx
├── 2026-03-22-avocado-breakfast-recipes.mdx
└── ...
```

**MDX Frontmatter 模板：**

```mdx
---
title: 牛油果的10个健康益处
slug: avocado-benefits
category: 牛油果
tags: [牛油果, 健康科普, 营养]
coverImage: /images/blog/avocado-benefits.jpg
excerpt: 牛油果不只是健身餐的标配，它的好处远超你想象。
author: 漠玫内容团队
publishedAt: 2026-03-15
readingTime: 8分钟
relatedProducts: [avocado-hass]
---

## 引言
...
```

---

## Phase 4 · 测试上线（第6周）

### Task 13: 全端测试

**测试清单（QA 执行）：**

| 检查项 | 标准 |
|--------|------|
| 13个页面全部可访问 | 无404，响应时间<3s |
| 首页 Hero | 背景图正常，文字叠加清晰 |
| 产品列表 | 筛选切换正常，产品卡片点击跳转正确 |
| 产品详情 | Tab切换正常，内容加载正常 |
| 博客首页 | 文章卡片正常，加载<1s |
| 文章详情 | 正文渲染正常，相关文章显示 |
| 私域导流 | 右下角悬浮按钮可见，点击弹窗正常 |
| 响应式 | 375px/768px/1280px 三端正常 |
| 微信内置 | 扫码、二维码、页面加载全部正常 |
| Lighthouse | Performance≥90 |

---

### Task 14: 部署上线

**Step 1: Vercel 部署**

```bash
# 安装 Vercel CLI
npm install -g vercel

# 登录
vercel login

# 部署（生产环境）
vercel --prod
```

**Step 2: 域名解析（可选）**

在华哥域名服务商（阿里云/腾讯云）添加 DNS 记录：
- 类型：A
- 名称：@（或 momo）
- 值：[Vercel 分配的 IP 或 CNAME]

**Step 3: 百度站长验证**

1. 注册百度搜索资源平台 account.baidu.com
2. 添加网站 → 验证网站（推荐 HTML 文件验证）
3. 提交 sitemap.xml：`https://your-domain.com/sitemap.xml`
4. 手动提交首页和重要页面 URL

**Step 4: 微信安全域名配置**

在华哥公众号后台 → 设置与开发 → 公众号设置 → 功能设置：
- JS接口安全域名
- 网页授权域名

---

### Task 15: 运营交接

**交付文档（外包方输出）：**

| 文档 | 内容 |
|------|------|
| 用户手册 | 如何添加文章、如何更新产品信息 |
| 技术文档 | 部署流程、CI/CD 配置说明 |
| 设计源文件 | Figma 链接、Logo 文件包 |

**华哥执行：**
1. 注册企微，生成二维码，替换 `public/images/wechat-qr.png`
2. 注册公众号，生成二维码，替换 `public/images/gzh-qr.png`
3. 配置文章 MDX 文件
4. 上线第一天：手动提交 sitemap 到百度

---

## 实施检查点

| 检查点 | 通过标准 | 负责人 |
|--------|---------|-------|
| C0: 项目初始化 | Next.js 项目跑起来，localhost:3000 正常 | 开发 |
| C1: UI 设计确认 | 华哥在 Figma 上点击确认 | 华哥 |
| C2: 视觉还原验收 | 与 Figma 偏差≤10% | 开发+华哥 |
| C3: 功能完整 | 13个页面全部可访问，私域导流正常 | 开发 |
| C4: 内容填充 | 首批20篇文章上线 | 运营 |
| C5: Lighthouse | 性能≥90，可访问性≥90 | 开发 |
| C6: 百度收录 | site:your-domain.com 能查到首页 | 运营 |

---

*实施计划版本：V1.0 · 2026-03-29*
