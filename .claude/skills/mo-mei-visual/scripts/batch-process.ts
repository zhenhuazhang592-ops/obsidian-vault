#!/usr/bin/env bun
/**
 * 漠玫视觉 · 批量处理脚本
 *
 * 一次处理多个 SKU，全流程编排：
 *   manifest.json → 场景合成 → 智能裁切 → 海报合成 → 详情页文案 → HTML
 *
 * 工具检测策略（graceful fallback）：
 *   - baoyu-image-gen  存在 → 实际调用生成场景图
 *   - baoyu-image-gen  不存在 → 用 Sharp 生成占位图 + 打印操作指令
 *   - baoyu-markdown-to-html 不存在 → 生成占位 HTML + 打印操作指令
 */

import sharp from "sharp";
import { spawn } from "child_process";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "fs";
import { resolve, join, basename } from "path";

// ============================================================
// 类型定义
// ============================================================

interface SkuItem {
  slug: string;
  name: string;
  "品类": string;
  "产地": string;
  "核心卖点": string;
  "规格": string;
  "价格": string;
  image: string;
  styles: string[];
}

interface ProcessingReport {
  slug: string;
  status: "success" | "partial" | "failed";
  steps: Record<string, "success" | "skipped" | "failed">;
  outputDir: string;
}

// ============================================================
// 常量
// ============================================================

const VALID_STYLES = ["minimal", "lifestyle", "origin", "daoju"];
const SCENE_PROMPTS_DIR = resolve(import.meta.dir, "../prompts");
const CROP_SPECS = [
  { name: "main-taobao-1:1", width: 800, height: 800 },
  { name: "main-taobao-3:4", width: 800, height: 1066 },
  { name: "main-jd-1:1", width: 800, height: 800 },
  { name: "main-jd-sub", width: 480, height: 480 },
  { name: "main-pdd-1:1", width: 800, height: 800 },
  { name: "main-pdd-3:4", width: 800, height: 1200 },
  { name: "main-douyin-3:4", width: 800, height: 1066 },
  { name: "main-douyin-9:16", width: 1080, height: 1920 },
];

// ============================================================
// 工具检测
// ============================================================

/**
 * 检测命令是否存在
 * @param cmd 命令名（不含参数）
 */
async function checkCommandExists(cmd: string): Promise<boolean> {
  return new Promise((resolve) => {
    const proc = spawn("which", [cmd], { timeout: 5000 });
    let output = "";
    proc.stdout?.on("data", (d) => (output += d.toString()));
    proc.on("close", (code) => resolve(code === 0 && output.trim().length > 0));
    proc.on("error", () => resolve(false));
  });
}

// ============================================================
// Manifest 验证
// ============================================================

const REQUIRED_FIELDS: (keyof SkuItem)[] = [
  "slug",
  "name",
  "品类",
  "产地",
  "核心卖点",
  "规格",
  "价格",
  "image",
  "styles",
];

function validateManifest(raw: unknown): SkuItem[] {
  if (!Array.isArray(raw)) {
    throw new Error("manifest.json 根节点必须为数组");
  }
  const items: SkuItem[] = raw as SkuItem[];
  for (const item of items) {
    for (const field of REQUIRED_FIELDS) {
      if (!(field in item) || item[field] === undefined || item[field] === null) {
        throw new Error(
          `SKU "${item.slug || "(unnamed)"}" 缺少必填字段: ${field}`
        );
      }
    }
    if (typeof item.styles !== "object" || !Array.isArray(item.styles)) {
      throw new Error(`SKU "${item.slug}" 的 styles 字段必须为字符串数组`);
    }
    for (const style of item.styles) {
      if (!VALID_STYLES.includes(style)) {
        throw new Error(
          `SKU "${item.slug}" 的 style "${style}" 不在支持列表内: ${VALID_STYLES.join(", ")}`
        );
      }
    }
  }
  return items;
}

// ============================================================
// 占位图生成（无外部工具时）
// ============================================================

/**
 * 用 Sharp 生成占位产品图（无 baoyu-image-gen 时的 fallback）
 * 创建一个带品牌色的渐变图，尺寸 1920×1080
 */
async function generatePlaceholderImage(
  outputPath: string,
  slug: string,
  style: string
): Promise<void> {
  const W = 1920;
  const H = 1080;

  // 根据风格生成不同色调的渐变背景
  const styleColors: Record<string, [number, number, number]> = {
    minimal: [253, 251, 247],   // 米白
    lifestyle: [245, 240, 230], // 暖米
    origin: [210, 230, 200],    // 绿野
    daoju: [240, 235, 225],     // 象牙
  };
  const [r, g, b] = styleColors[style] ?? [220, 220, 220];

  // SVG 背景（带渐变色块和产品名水印）
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}">
    <defs>
      <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%" stop-color="rgb(${r},${g},${b})"/>
        <stop offset="100%" stop-color="rgb(${Math.max(r - 20, 0)},${Math.max(g - 20, 0)},${Math.max(b - 20, 0)})"/>
      </linearGradient>
    </defs>
    <rect width="${W}" height="${H}" fill="url(#bg)"/>
    <!-- 中心椭圆占位符 -->
    <ellipse cx="${W / 2}" cy="${H / 2 - 40}" rx="280" ry="220"
             fill="rgba(255,255,255,0.6)" stroke="rgba(46,125,50,0.3)" stroke-width="3" stroke-dasharray="12,8"/>
    <!-- 产品名水印 -->
    <text x="${W / 2}" y="${H / 2 + 240}"
          font-family="sans-serif" font-size="52" font-weight="700"
          fill="rgba(46,125,50,0.35)"
          text-anchor="middle" letter-spacing="0.1em">${escapeXml(slug)}</text>
    <!-- 风格标签 -->
    <text x="${W - 40}" y="${H - 30}"
          font-family="sans-serif" font-size="22"
          fill="rgba(46,125,50,0.4)"
          text-anchor="end">${style} · mock</text>
  </svg>`;

  await sharp(Buffer.from(svg))
    .png({ quality: 90 })
    .toFile(outputPath);
}

// ============================================================
// 场景合成（编排层）
// ============================================================

/**
 * 合成 SKU 场景图
 *
 * 有 baoyu-image-gen：实际调用
 * 无 baoyu-image-gen：生成占位图
 *
 * @returns 生成的场景图文件路径数组
 */
async function generateSceneImages(
  sku: SkuItem,
  inputDir: string,
  outputDir: string,
  hasImageGen: boolean
): Promise<string[]> {
  const refImage = resolve(inputDir, sku.image);

  // 验证参考图存在（即使没有 image-gen 也需要占位）
  if (!existsSync(refImage)) {
    // 占位图不依赖 refImage，但流程里跳过生成
    console.warn(`  ⚠️ 参考图不存在: ${refImage}，跳过场景图生成`);
    return [];
  }

  const sceneFiles: string[] = [];

  if (hasImageGen) {
    console.log(`  → 调用 baoyu-image-gen 生成 ${sku.styles.length} 种场景...`);
    for (const style of sku.styles) {
      const outputPath = join(outputDir, `scene-${style}.png`);
      const promptPath = join(SCENE_PROMPTS_DIR, `scene-${style}.md`);

      // 构造 baoyu-image-gen 调用（参考图模式）
      // 注意：实际命令格式以 baoyu-image-gen 接口为准
      const args = [
        "--provider", "doubao",
        "--ref", refImage,
        "--prompt-file", promptPath,
        "--product-name", sku.name,
        "--category", sku["品类"],
        "--output", outputPath,
      ];

      await new Promise<void>((resolve, reject) => {
        const proc = spawn("baoyu-image-gen", args);
        let stderr = "";
        proc.stderr?.on("data", (d) => (stderr += d.toString()));
        proc.on("close", (code) => {
          if (code === 0) {
            console.log(`  ✅ scene-${style}.png`);
            sceneFiles.push(outputPath);
            resolve();
          } else {
            console.warn(`  ⚠️ baoyu-image-gen ${style} 失败: ${stderr.trim()}`);
            resolve(); // 不中断整个流程
          }
        });
        proc.on("error", (err) => {
          console.warn(`  ⚠️ baoyu-image-gen 调用异常: ${err.message}`);
          resolve();
        });
      });
    }
  } else {
    console.log(`  → baoyu-image-gen 未检测到，生成占位图...`);
    for (const style of sku.styles) {
      const outputPath = join(outputDir, `scene-${style}.png`);
      await generatePlaceholderImage(outputPath, sku.slug, style);
      console.log(`  ✅ scene-${style}.png (mock)`);
      sceneFiles.push(outputPath);
    }
    console.log(`  💡 如需真实生成，请安装并配置 baoyu-image-gen`);
  }

  return sceneFiles;
}

// ============================================================
// 智能裁切
// ============================================================

/**
 * 智能裁切（调用 smart-crop.ts 或用 Sharp 直接处理）
 *
 * @param sourceImage 参考场景图路径（用于裁切）
 * @param outputDir 输出目录
 * @returns 生成的裁切图文件路径数组
 */
async function runSmartCrop(
  sourceImage: string,
  outputDir: string
): Promise<string[]> {
  // 优先调用 smart-crop.ts（它依赖 sharp，在 bun 环境可用）
  const cropScript = resolve(import.meta.dir, "smart-crop.ts");

  if (existsSync(cropScript)) {
    const args = [cropScript, sourceImage, outputDir];
    await new Promise<void>((resolve, reject) => {
      const proc = spawn("bun", args);
      let stderr = "";
      proc.stderr?.on("data", (d) => (stderr += d.toString()));
      proc.on("close", (code) => {
        if (code === 0) resolve();
        else reject(new Error(stderr.trim()));
      });
      proc.on("error", reject);
    });
    return CROP_SPECS.map((s) => join(outputDir, `${s.name}.png`));
  }

  // Fallback：直接用 Sharp 裁切
  const results: string[] = [];
  for (const spec of CROP_SPECS) {
    const out = join(outputDir, `${spec.name}.png`);
    try {
      const meta = await sharp(sourceImage).metadata();
      const srcW = meta.width || 1;
      const srcH = meta.height || 1;
      const scaleX = spec.width / srcW;
      const scaleY = spec.height / srcH;
      const scale = Math.max(scaleX, scaleY);
      const rw = Math.round(srcW * scale);
      const rh = Math.round(srcH * scale);
      const left = Math.round((rw - spec.width) / 2);
      const top = Math.round((rh - spec.height) / 2);
      await sharp(sourceImage)
        .resize(rw, rh, { fit: "fill", kernel: "lanczos3" })
        .extract({ left, top, width: spec.width, height: spec.height })
        .png({ quality: 90 })
        .toFile(out);
      results.push(out);
    } catch (e) {
      // ignore single failure
    }
  }
  return results;
}

// ============================================================
// 海报合成
// ============================================================

/**
 * 海报合成（调用 poster-compose.ts 或直接合成）
 */
async function runPosterCompose(
  sourceImage: string,
  sku: SkuItem,
  outputDir: string
): Promise<string[]> {
  const posterScript = resolve(import.meta.dir, "poster-compose.ts");

  if (existsSync(posterScript)) {
    const args = [
      posterScript,
      sourceImage,
      sku.name,
      sku["核心卖点"],
      sku["价格"],
      outputDir,
    ];
    await new Promise<void>((resolve, reject) => {
      const proc = spawn("bun", args);
      let stderr = "";
      proc.stderr?.on("data", (d) => (stderr += d.toString()));
      proc.on("close", (code) => {
        if (code === 0) resolve();
        else reject(new Error(stderr.trim()));
      });
      proc.on("error", reject);
    });
    return ["poster-h.png", "poster-v.png"].map((f) => join(outputDir, f));
  }

  // Fallback: 用 poster-compose.ts 相同的 Sharp+SVG 逻辑内联
  return generatePosterFallback(sourceImage, sku, outputDir);
}

async function generatePosterFallback(
  sourceImage: string,
  sku: SkuItem,
  outputDir: string
): Promise<string[]> {
  const [LANDSCAPE, PORTRAIT] = [
    { width: 1920, height: 800, name: "poster-h.png" },
    { width: 1080, height: 1920, name: "poster-v.png" },
  ];

  const files: string[] = [];
  for (const spec of [LANDSCAPE, PORTRAIT]) {
    const meta = await sharp(sourceImage).metadata();
    const srcW = meta.width || 1;
    const srcH = meta.height || 1;
    const scaleX = spec.width / srcW;
    const scaleY = spec.height / srcH;
    const scale = Math.max(scaleX, scaleY);
    const rw = Math.round(srcW * scale);
    const rh = Math.round(srcH * scale);
    const left = Math.round((rw - spec.width) / 2);
    const top = Math.round((rh - spec.height) / 2);
    const bg = await sharp(sourceImage)
      .resize(rw, rh, { fit: "fill" })
      .extract({ left, top, width: spec.width, height: spec.height })
      .blur(20)
      .composite([{
        input: Buffer.from(`<svg><rect width="${spec.width}" height="${spec.height}" fill="rgba(46,125,50,0.35)"/></svg>`),
        gravity: "center",
      }])
      .png()
      .toBuffer();

    const bgBase64 = bg.toString("base64");
    const svg = buildFallbackSvg(spec.width, spec.height, bgBase64, sku.name, sku["核心卖点"], sku["价格"], spec.name === "poster-h.png");
    const out = join(outputDir, spec.name);
    await sharp(Buffer.from(svg)).png({ quality: 90 }).toFile(out);
    console.log(`  ✅ ${spec.name} (mock)`);
    files.push(out);
  }
  return files;
}

function buildFallbackSvg(w: number, h: number, bgBase64: string, name: string, tagline: string, price: string, isH: boolean): string {
  const barH = isH ? 200 : 160;
  const barY = h - barH;
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}">
  <image href="data:image/png;base64,${bgBase64}" width="${w}" height="${h}" preserveAspectRatio="xMidYMid slice"/>
  <rect x="0" y="${barY}" width="${w}" height="${barH}" fill="#2E7D32" fill-opacity="0.85"/>
  <foreignObject x="0" y="${barY + (isH ? 20 : 30)}" width="${w}" height="${isH ? 90 : 80}">
    <div xmlns="http://www.w3.org/1999/xhtml" style="font-family:serif;font-weight:700;font-size:${isH ? 72 : 70}px;color:#fff;text-align:center;line-height:1.1;text-shadow:0 2px 8px rgba(0,0,0,0.4)">${escapeXml(name)}</div>
  </foreignObject>
  <foreignObject x="0" y="${barY + (isH ? 110 : 110)}" width="${w}" height="50">
    <div xmlns="http://www.w3.org/1999/xhtml" style="font-family:sans-serif;font-size:${isH ? 36 : 32}px;color:#FDFBF7;text-align:center;line-height:1.2">${escapeXml(tagline)}</div>
  </foreignObject>
  ${!isH ? `<foreignObject x="0" y="${h - 90}" width="${w}" height="60">
    <div xmlns="http://www.w3.org/1999/xhtml" style="font-family:sans-serif;font-size:22px;color:#FDFBF7;text-align:center;opacity:0.9">漠玫 MoMei</div>
  </foreignObject>` : `<foreignObject x="${w - 260}" y="${h - 50}" width="240" height="36">
    <div xmlns="http://www.w3.org/1999/xhtml" style="font-family:sans-serif;font-size:20px;color:#FDFBF7;text-align:right;opacity:0.85">© 漠玫 MoMei</div>
  </foreignObject>`}
</svg>`;
}

// ============================================================
// 详情页文案 + HTML
// ============================================================

/**
 * 生成详情页文案（调用 Qwen3-Max 或生成占位文案）
 */
async function generateDetailCopy(sku: SkuItem, outputDir: string): Promise<string> {
  const mdPath = join(outputDir, "detail.md");
  const promptFile = resolve(SCENE_PROMPTS_DIR, "detail-copy.md");

  // 检测是否有 baoyu-markdown-to-html
  const hasHtmlTool = await checkCommandExists("baoyu-markdown-to-html");

  if (existsSync(promptFile)) {
    console.log(`  → 调用 Qwen3-Max 生成详情页文案...`);
    // TODO: 集成 huage-gzh 的 Qwen3-Max 调用
    // 当前生成占位文案（待接入 huage-gzh 的 7 步流程）
    const placeholder = generateDetailPlaceholder(sku);
    writeFileSync(mdPath, placeholder, "utf-8");
    console.log(`  ✅ detail.md (placeholder)`);
  }

  const htmlPath = join(outputDir, "index.html");

  if (hasHtmlTool) {
    await new Promise<void>((resolve, reject) => {
      const proc = spawn("baoyu-markdown-to-html", [mdPath, "--output", htmlPath]);
      proc.on("close", (code) => {
        if (code === 0) {
          console.log(`  ✅ index.html`);
          resolve();
        } else {
          resolve(); // 不中断
        }
      });
      proc.on("error", () => resolve());
    });
  } else {
    // Fallback: 生成基础 HTML
    const mdContent = readFileSync(mdPath, "utf-8");
    const simpleHtml = `<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>${escapeXml(sku.name)} - 漠玫 MoMei</title>
<style>
  body { font-family: 'Noto Serif SC', serif; max-width: 800px; margin: 0 auto; padding: 2rem; background: #FDFBF7; color: #1A1A1A; }
  h1 { color: #2E7D32; border-bottom: 3px solid #8BC34A; padding-bottom: 0.5rem; }
  h2 { color: #2E7D32; margin-top: 2rem; }
  p { line-height: 1.8; font-size: 1.1rem; }
  table { border-collapse: collapse; width: 100%; margin: 1rem 0; }
  td, th { border: 1px solid #D4A853; padding: 0.6rem 1rem; }
  th { background: #2E7D32; color: #fff; }
  .price { background: #D4A853; color: #1A1A1A; padding: 0.4rem 1rem; display: inline-block; border-radius: 6px; font-weight: 700; }
  .cta { margin-top: 3rem; padding: 1.5rem; background: #2E7D32; color: #fff; border-radius: 8px; text-align: center; }
  .mock-badge { background: #eee; color: #999; font-size: 0.8rem; padding: 0.2rem 0.5rem; border-radius: 4px; }
</style>
</head>
<body>
<h1>${escapeXml(sku.name)} <span class="mock-badge">placeholder</span></h1>
<div class="price">${escapeXml(sku["价格"])}</div>

<div style="margin-top:1rem"><strong>品类：</strong>${escapeXml(sku["品类"])}</div>
<div><strong>产地：</strong>${escapeXml(sku["产地"])}</div>
<div><strong>规格：</strong>${escapeXml(sku["规格"])}</div>
<div><strong>核心卖点：</strong>${escapeXml(sku["核心卖点"])}</div>

<hr style="margin:2rem 0;border:none;border-top:1px solid #D4A853">
<div style="white-space:pre-wrap">${escapeXml(mdContent)}</div>

<div class="cta">
  <p style="color:#fff;margin:0">漠玫承诺：源头直采，新鲜直达。</p>
</div>
</body>
</html>`;
    writeFileSync(htmlPath, simpleHtml, "utf-8");
    console.log(`  ✅ index.html (mock)`);
    console.log(`  💡 如需真实 HTML 排版，请配置 baoyu-markdown-to-html`);
  }

  return htmlPath;
}

function generateDetailPlaceholder(sku: SkuItem): string {
  return `# ${sku.name}

## 产地溯源

${sku["产地"]}，优越的自然条件赋予${sku["品类"]}独特的风味。漠玫团队亲赴产地，精选优质果园，源头直采。

---

## 核心卖点

1. **绵密口感**：${sku["核心卖点"].split("，")[0] || sku["核心卖点"]}
2. **严选品质**：每一颗均经过精心筛选
3. **新鲜直达**：冷链配送，保证到手新鲜

---

## 规格选择

- **规格**：${sku["规格"]}
- **价格**：${sku["价格"]}

---

## 营养成分

> 数据来源：公开营养数据库

| 营养素 | 每100g | 参考值% |
|--------|--------|---------|
| 热量 | - | - |
| 蛋白质 | - | - |
| 脂肪 | - | - |

---

## 选购指南

- 如何判断成熟度
- 如何辨别品质优劣

---

## 储存方法

- **未开封**：阴凉干燥处储存
- **已切开**：冰箱冷藏，建议2天内食用

---

## 食用建议

- 直接食用：保留原味
- 料理搭配：沙拉、奶昔、烘焙

> 漠玫承诺：源头直采，新鲜直达。
`;
}

// ============================================================
// 工具函数
// ============================================================

function escapeXml(str: string): string {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&apos;");
}

// ============================================================
// 主处理函数
// ============================================================

async function processSku(
  sku: SkuItem,
  inputDir: string,
  baseDir: string,
  tools: { hasImageGen: boolean; hasHtmlTool: boolean }
): Promise<ProcessingReport> {
  const outputDir = resolve(baseDir, sku.slug);
  mkdirSync(outputDir, { recursive: true });

  const report: ProcessingReport = {
    slug: sku.slug,
    status: "success",
    steps: {},
    outputDir,
  };

  console.log(`\n${"─".repeat(60)}`);
  console.log(`📦 ${sku.slug} — ${sku.name}`);
  console.log(`  品类: ${sku["品类"]} | 产地: ${sku["产地"]} | 风格: ${sku.styles.join(", ")}`);
  console.log(`${"─".repeat(60)}`);

  try {
    // Step 1: 场景图合成
    console.log(`\n[Step 1] 场景合成`);
    const sceneFiles = await generateSceneImages(sku, inputDir, outputDir, tools.hasImageGen);
    report.steps["scene"] = sceneFiles.length > 0 ? "success" : "skipped";

    // Step 2: 智能裁切
    console.log(`\n[Step 2] 智能裁切`);
    const refImage = sceneFiles[0] ?? resolve(inputDir, sku.image);
    if (existsSync(refImage)) {
      await runSmartCrop(refImage, outputDir);
      report.steps["crop"] = "success";
    } else {
      console.log(`  ⚠️ 无参考图，跳过裁切`);
      report.steps["crop"] = "skipped";
    }

    // Step 3: 海报合成
    console.log(`\n[Step 3] 海报合成`);
    if (existsSync(refImage)) {
      await runPosterCompose(refImage, sku, outputDir);
      report.steps["poster"] = "success";
    } else {
      console.log(`  ⚠️ 无参考图，跳过海报合成`);
      report.steps["poster"] = "skipped";
    }

    // Step 4: 详情页
    console.log(`\n[Step 4] 详情页`);
    await generateDetailCopy(sku, outputDir);
    report.steps["detail"] = "success";
  } catch (error) {
    report.status = "partial";
    console.error(`\n  ❌ 处理出错: ${(error as Error).message}`);
  }

  return report;
}

// ============================================================
// 汇总报告
// ============================================================

function printSummary(reports: ProcessingReport[]): void {
  console.log(`\n\n${"=".repeat(60)}`);
  console.log(`📊 批量处理汇总`);
  console.log(`${"=".repeat(60)}`);

  for (const r of reports) {
    const icon = r.status === "success" ? "✅" : r.status === "partial" ? "⚠️" : "❌";
    const steps = Object.entries(r.steps)
      .map(([k, v]) => `   ${v === "success" ? "✅" : v === "skipped" ? "⏭️" : "❌"} ${k}`)
      .join("\n");
    console.log(`\n${icon} ${r.slug} [${r.status}]`);
    console.log(`   📁 ${r.outputDir}/`);
    console.log(steps);
  }

  const total = reports.length;
  const ok = reports.filter((r) => r.status === "success").length;
  const partial = reports.filter((r) => r.status === "partial").length;
  console.log(`\n${"=".repeat(60)}`);
  console.log(`总计: ${total} SKU | ✅ 成功 ${ok} | ⚠️ 部分 ${partial}`);
  console.log(`${"=".repeat(60)}\n`);
}

// ============================================================
// 主程序
// ============================================================

async function main() {
  const args = process.argv.slice(2);

  if (args.length < 3) {
    console.error(`❌ 用法: bun scripts/batch-process.ts <manifest.json> <input-images-dir> <output-base-dir>`);
    console.error(``);
    console.error(`  参数说明：`);
    console.error(`  <manifest.json>       manifest.json 文件路径（见下格式）`);
    console.error(`  <input-images-dir>    输入实拍图目录`);
    console.error(`  <output-base-dir>     输出根目录`);
    console.error(``);
    console.error(`  manifest.json 示例：`);
    console.error(`  [`);
    console.error(`    { "slug": "avocado-hass", "name": "墨西哥哈斯牛油果", "品类": "avocado",`);
    console.error(`      "产地": "墨西哥", "核心卖点": "绵密口感", "规格": "1kg", "价格": "68元",`);
    console.error(`      "image": "avocado.jpg", "styles": ["minimal", "lifestyle"] }`);
    console.error(`  ]`);
    console.error(``);
    console.error(`  支持的 styles: ${VALID_STYLES.join(", ")}`);
    process.exit(1);
  }

  const [manifestPath, inputDir, outputBase] = args.map((a) => resolve(a));

  // 验证 manifest
  if (!existsSync(manifestPath)) {
    console.error(`❌ manifest.json 不存在: ${manifestPath}`);
    process.exit(1);
  }

  if (!existsSync(inputDir)) {
    console.error(`❌ 输入图片目录不存在: ${inputDir}`);
    process.exit(1);
  }

  let rawManifest: unknown;
  try {
    rawManifest = JSON.parse(readFileSync(manifestPath, "utf-8"));
  } catch {
    console.error(`❌ manifest.json 解析失败，请检查 JSON 格式`);
    process.exit(1);
  }

  let skus: SkuItem[];
  try {
    skus = validateManifest(rawManifest);
  } catch (e) {
    console.error(`❌ manifest 验证失败: ${(e as Error).message}`);
    process.exit(1);
  }

  // 检测工具
  console.log(`🔍 检测外部工具...`);
  const [hasImageGen, hasHtmlTool] = await Promise.all([
    checkCommandExists("baoyu-image-gen"),
    checkCommandExists("baoyu-markdown-to-html"),
  ]);
  console.log(`   baoyu-image-gen:        ${hasImageGen ? "✅ 已安装" : "⚠️ 未检测到"}`);
  console.log(`   baoyu-markdown-to-html: ${hasHtmlTool ? "✅ 已安装" : "⚠️ 未检测到"}`);
  if (!hasImageGen || !hasHtmlTool) {
    console.log(`   💡 可用 bun install -g <package> 安装，或使用 mock 模式继续`);
  }

  // 创建输出根目录
  mkdirSync(outputBase, { recursive: true });

  console.log(`\n🚀 开始批量处理 ${skus.length} 个 SKU...`);
  console.log(`📂 manifest: ${manifestPath}`);
  console.log(`📂 输入目录: ${inputDir}`);
  console.log(`📂 输出目录: ${outputBase}`);

  const reports: ProcessingReport[] = [];
  for (const sku of skus) {
    const report = await processSku(sku, inputDir, outputBase, {
      hasImageGen,
      hasHtmlTool,
    });
    reports.push(report);
  }

  printSummary(reports);

  // 如有失败，返回非零退出码
  const hasFailure = reports.some((r) => r.status === "failed");
  process.exit(hasFailure ? 1 : 0);
}

main().catch((error) => {
  console.error(`❌ 未知错误: ${error.message}`);
  process.exit(1);
});
