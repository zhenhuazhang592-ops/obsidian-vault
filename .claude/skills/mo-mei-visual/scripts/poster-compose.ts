#!/usr/bin/env bun
/**
 * 海报合成脚本 - 将基础产品图合成为漠玫品牌海报
 *
 * 技术方案：Sharp + SVG 混合渲染
 * - Sharp 处理背景：缩放填满 + 高斯模糊 + 叠加遮罩色
 * - SVG 描述完整画面：背景 + 色块 + 文字（通过 foreignObject）
 * - Sharp 将 SVG 渲染为 PNG
 *
 * 字体策略：
 * - 优先：Google Fonts Noto Serif SC / Noto Sans SC（CDN）
 * - Fallback：serif / sans-serif
 */

import sharp from "sharp";
import { mkdirSync, existsSync } from "fs";
import { resolve, join, basename } from "path";

// ============================================================
// 品牌色彩
// ============================================================
const BRAND = {
  moMeiGreen: "#2E7D32",
  moMeiGreenRgb: "46, 125, 50",
  avocadoGreen: "#8BC34A",
  creamWhite: "#FDFBF7",
  warmGold: "#D4A853",
  inkBlack: "#1A1A1A",
  grayText: "#6B6B6B",
} as const;

// ============================================================
// 尺寸规格
// ============================================================
const LANDSCAPE = { width: 1920, height: 800, name: "poster-h.png" };
const PORTRAIT = { width: 1080, height: 1920, name: "poster-v.png" };

// ============================================================
// Google Fonts CSS（注入到 SVG foreignObject）
// ============================================================
const GOOGLE_FONTS_CSS = `
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@700&family=Noto+Sans+SC:wght@400;700&display=swap');

*, *::before, *::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

html, body {
  width: 100%;
  height: 100%;
  overflow: hidden;
}
`;

// ============================================================
// 通用背景处理
// ============================================================

/**
 * 用 Sharp 生成背景 Buffer
 * - 缩放填满目标尺寸（fit: cover，中心裁切）
 * - 高斯模糊模拟景深
 * - 叠加半透明色模拟虚化氛围
 *
 * @param inputPath 原始图片路径
 * @param width 目标宽度
 * @param height 目标高度
 * @param overlayColor 叠加色（可选，RGBA）
 */
async function buildBackgroundBuffer(
  inputPath: string,
  width: number,
  height: number,
  overlayColor?: string
): Promise<Buffer> {
  const metadata = await sharp(inputPath).metadata();
  const srcW = metadata.width || 1;
  const srcH = metadata.height || 1;

  // 计算填满裁切参数
  const scaleX = width / srcW;
  const scaleY = height / srcH;
  const scale = Math.max(scaleX, scaleY);
  const resizeW = Math.round(srcW * scale);
  const resizeH = Math.round(srcH * scale);
  const left = Math.round((resizeW - width) / 2);
  const top = Math.round((resizeH - height) / 2);

  let pipeline = sharp(inputPath)
    .resize(resizeW, resizeH, { fit: "fill", kernel: "lanczos3" })
    .extract({ left, top, width, height })
    .blur(20); // 高斯模糊模拟景深

  if (overlayColor) {
    pipeline = pipeline
      .composite([
        {
          input: Buffer.from(
            `<svg width="${width}" height="${height}">
              <rect width="${width}" height="${height}" fill="${overlayColor}"/>
            </svg>`
          ),
          gravity: "center",
        },
      ])
      .png();
  }

  return await pipeline.toBuffer();
}

// ============================================================
// SVG 生成器
// ============================================================

/**
 * 生成横版海报 SVG
 *
 * 布局：
 * - 背景：填满的高斯模糊底图 + 透明叠加色
 * - 底部色块：200px 高，漠玫绿 #2E7D32，透明度 85%
 * - 品名：白色，72px，居中，思源宋体 Bold
 * - 副标题：米白，36px，居中，思源黑体
 * - 右下角：© 漠玫 MoMei
 */
function buildLandscapeSvg(
  bgDataUri: string,
  productName: string,
  tagline: string,
  price: string
): string {
  const { width, height } = LANDSCAPE;
  const barHeight = 200;
  const barY = height - barHeight;

  return `<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
  width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">
  <defs>
    <style><![CDATA[${GOOGLE_FONTS_CSS}]]></style>
  </defs>

  <!-- 背景图（已模糊 + 叠加色） -->
  <image href="${bgDataUri}" width="${width}" height="${height}" preserveAspectRatio="xMidYMid slice"/>

  <!-- 底部色块：漠玫绿 85% 透明度 -->
  <rect x="0" y="${barY}" width="${width}" height="${barHeight}"
        fill="${BRAND.moMeiGreen}" fill-opacity="0.85"/>

  <!-- 品名（foreignObject） -->
  <foreignObject x="0" y="${barY + 20}" width="${width}" height="90">
    <div xmlns="http://www.w3.org/1999/xhtml" style="
      font-family: 'Noto Serif SC', 'Source Han Serif SC', 'Source Han Serif CN', serif;
      font-weight: 700;
      font-size: 72px;
      color: #FFFFFF;
      text-align: center;
      line-height: 1.1;
      text-shadow: 0 2px 8px rgba(0,0,0,0.35);
      letter-spacing: 0.05em;
    ">${escapeXml(productName)}</div>
  </foreignObject>

  <!-- 副标题（foreignObject） -->
  <foreignObject x="0" y="${barY + 110}" width="${width}" height="55">
    <div xmlns="http://www.w3.org/1999/xhtml" style="
      font-family: 'Noto Sans SC', 'Source Han Sans SC', 'Source Han Sans CN', sans-serif;
      font-weight: 400;
      font-size: 36px;
      color: ${BRAND.creamWhite};
      text-align: center;
      line-height: 1.2;
      letter-spacing: 0.02em;
    ">${escapeXml(tagline)}</div>
  </foreignObject>

  <!-- 右下角品牌水印 -->
  <foreignObject x="${width - 280}" y="${height - 50}" width="260" height="36">
    <div xmlns="http://www.w3.org/1999/xhtml" style="
      font-family: 'Noto Sans SC', 'Source Han Sans SC', 'Source Han Sans CN', sans-serif;
      font-weight: 400;
      font-size: 20px;
      color: ${BRAND.creamWhite};
      text-align: right;
      line-height: 1;
      opacity: 0.85;
    ">© 漠玫 MoMei</div>
  </foreignObject>

</svg>`;
}

/**
 * 生成竖版海报 SVG
 *
 * 布局：
 * - 背景：全出血基础图
 * - 顶部渐变遮罩：黑色→透明，透明度 40%
 * - 品名：白色，80px，居中偏上，思源宋体 Bold
 * - 副标题：米白，36px，居中
 * - 底部色块：漠玫绿，160px
 * - 价格：暖金底白字，48px
 * - 底部：漠玫 MoMei
 */
function buildPortraitSvg(
  bgDataUri: string,
  productName: string,
  tagline: string,
  price: string
): string {
  const { width, height } = PORTRAIT;
  const bottomBarHeight = 160;
  const bottomBarY = height - bottomBarHeight;
  // 顶部渐变高度 300px
  const topGradientHeight = 300;

  return `<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
  width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">
  <defs>
    <style><![CDATA[${GOOGLE_FONTS_CSS}]]></style>
    <!-- 顶部渐变：透明 → 漠玫绿 85% -->
    <linearGradient id="topGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="rgba(0,0,0,0)"/>
      <stop offset="100%" stop-color="rgba(${BRAND.moMeiGreenRgb},0.85)"/>
    </linearGradient>
    <!-- 底部渐变：透明 → 墨色 80% -->
    <linearGradient id="bottomGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="rgba(26,26,26,0)"/>
      <stop offset="100%" stop-color="rgba(26,26,26,0.8)"/>
    </linearGradient>
  </defs>

  <!-- 背景图（全出血） -->
  <image href="${bgDataUri}" width="${width}" height="${height}" preserveAspectRatio="xMidYMid slice"/>

  <!-- 顶部渐变遮罩 -->
  <rect x="0" y="0" width="${width}" height="${topGradientHeight}" fill="url(#topGrad)"/>

  <!-- 底部渐变遮罩（覆盖文字区域） -->
  <rect x="0" y="${bottomBarY - 520}" width="${width}" height="680" fill="url(#bottomGrad)"/>

  <!-- 底部色块：漠玫绿 -->
  <rect x="0" y="${bottomBarY}" width="${width}" height="${bottomBarHeight}" fill="${BRAND.moMeiGreen}"/>

  <!-- 文字区域容器（居中于底部区域） -->
  <foreignObject x="0" y="${bottomBarY - 440}" width="${width}" height="420">
    <div xmlns="http://www.w3.org/1999/xhtml" style="
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: flex-end;
      height: 100%;
      gap: 0;
    ">
      <!-- 品名 -->
      <div style="
        font-family: 'Noto Serif SC', 'Source Han Serif SC', 'Source Han Serif CN', serif;
        font-weight: 700;
        font-size: 80px;
        color: #FFFFFF;
        text-align: center;
        line-height: 1.1;
        text-shadow: 0 3px 12px rgba(0,0,0,0.5);
        letter-spacing: 0.05em;
        margin-bottom: 24px;
      ">${escapeXml(productName)}</div>

      <!-- 副标题 -->
      <div style="
        font-family: 'Noto Sans SC', 'Source Han Sans SC', 'Source Han Sans CN', sans-serif;
        font-weight: 400;
        font-size: 36px;
        color: ${BRAND.creamWhite};
        text-align: center;
        line-height: 1.2;
        letter-spacing: 0.03em;
        margin-bottom: 32px;
      ">${escapeXml(tagline)}</div>

      <!-- 价格标签：暖金底白字 -->
      <div style="
        display: inline-block;
        background-color: ${BRAND.warmGold};
        color: ${BRAND.inkBlack};
        font-family: 'Noto Sans SC', 'Source Han Sans SC', 'Source Han Sans CN', sans-serif;
        font-weight: 700;
        font-size: 48px;
        padding: 12px 40px;
        border-radius: 10px;
        text-align: center;
        line-height: 1.1;
        letter-spacing: 0.02em;
        margin-bottom: 32px;
      ">${escapeXml(price)}</div>
    </div>
  </foreignObject>

  <!-- 底部品牌水印 -->
  <foreignObject x="0" y="${height - 80}" width="${width}" height="60">
    <div xmlns="http://www.w3.org/1999/xhtml" style="
      font-family: 'Noto Sans SC', 'Source Han Sans SC', 'Source Han Sans CN', sans-serif;
      font-weight: 400;
      font-size: 22px;
      color: ${BRAND.creamWhite};
      text-align: center;
      line-height: 1;
      opacity: 0.9;
    ">漠玫 MoMei</div>
  </foreignObject>

</svg>`;
}

// ============================================================
// 工具函数
// ============================================================

/**
 * 转义 XML 特殊字符（防止 SVG 注入）
 */
function escapeXml(str: string): string {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&apos;");
}

// ============================================================
// 核心合成函数
// ============================================================

/**
 * 生成横版海报
 */
async function composeLandscape(
  bgBuffer: Buffer,
  productName: string,
  tagline: string,
  price: string,
  outputPath: string
): Promise<void> {
  const { width, height } = LANDSCAPE;

  // 构建背景 Data URI
  const bgBase64 = bgBuffer.toString("base64");
  const bgDataUri = `data:image/png;base64,${bgBase64}`;

  // 生成 SVG
  const svg = buildLandscapeSvg(bgDataUri, productName, tagline, price);

  // Sharp 渲染 SVG → PNG
  await sharp(Buffer.from(svg))
    .png({ quality: 100, compressionLevel: 6 })
    .toFile(outputPath);

  console.log(`✅ 已生成: ${basename(outputPath)} (${width}×${height}) [横版海报]`);
}

/**
 * 生成竖版海报
 */
async function composePortrait(
  bgBuffer: Buffer,
  productName: string,
  tagline: string,
  price: string,
  outputPath: string
): Promise<void> {
  const { width, height } = PORTRAIT;

  // 构建背景 Data URI
  const bgBase64 = bgBuffer.toString("base64");
  const bgDataUri = `data:image/png;base64,${bgBase64}`;

  // 生成 SVG
  const svg = buildPortraitSvg(bgDataUri, productName, tagline, price);

  // Sharp 渲染 SVG → PNG
  await sharp(Buffer.from(svg))
    .png({ quality: 100, compressionLevel: 6 })
    .toFile(outputPath);

  console.log(`✅ 已生成: ${basename(outputPath)} (${width}×${height}) [竖版海报]`);
}

// ============================================================
// 主程序
// ============================================================

async function main() {
  const args = process.argv.slice(2);

  if (args.length < 5) {
    console.error("❌ 用法: bun scripts/poster-compose.ts <base-image> <product-name> <tagline> <price> <output-dir>");
    console.error("");
    console.error("   参数说明：");
    console.error("   <base-image>   基础产品图路径（PNG/JPG/WebP）");
    console.error("   <product-name> 品名（如：墨西哥哈斯牛油果）");
    console.error("   <tagline>      核心卖点（如：奶油般绵密口感）");
    console.error("   <price>         价格区间（如：68-128元）");
    console.error("   <output-dir>    输出目录");
    console.error("");
    console.error("   示例：");
    console.error("   bun scripts/poster-compose.ts avocado-main.png \\");
    console.error("     '墨西哥哈斯牛油果' \\");
    console.error("     '奶油般绵密口感' \\");
    console.error("     '68-128元' \\");
    console.error("     output/");
    process.exit(1);
  }

  const [inputPath, productName, tagline, price, outputDir] = args;
  const resolvedInput = resolve(inputPath);
  const resolvedOutput = resolve(outputDir);

  // 验证输入文件
  if (!existsSync(resolvedInput)) {
    console.error(`❌ 输入文件不存在: ${resolvedInput}`);
    process.exit(1);
  }

  // 创建输出目录
  if (!existsSync(resolvedOutput)) {
    mkdirSync(resolvedOutput, { recursive: true });
  }

  console.log(`📂 输入图片: ${resolvedInput}`);
  console.log(`📛 品名: ${productName}`);
  console.log(`📝 副标题: ${tagline}`);
  console.log(`💰 价格: ${price}`);
  console.log(`📂 输出目录: ${resolvedOutput}`);
  console.log("");

  try {
    // 并行生成两种尺寸的背景（横版需叠加色，竖版不需要）
    const [landscapeBg, portraitBg] = await Promise.all([
      // 横版背景：模糊 + 漠玫绿 40% 叠加（模拟虚化感）
      buildBackgroundBuffer(
        resolvedInput,
        LANDSCAPE.width,
        LANDSCAPE.height,
        `rgba(${BRAND.moMeiGreenRgb}, 0.40)`
      ),
      // 竖版背景：模糊 + 黑色 40% 叠加
      buildBackgroundBuffer(
        resolvedInput,
        PORTRAIT.width,
        PORTRAIT.height,
        "rgba(0, 0, 0, 0.40)"
      ),
    ]);

    // 并行合成两张海报
    await Promise.all([
      composeLandscape(
        landscapeBg,
        productName,
        tagline,
        price,
        join(resolvedOutput, LANDSCAPE.name)
      ),
      composePortrait(
        portraitBg,
        productName,
        tagline,
        price,
        join(resolvedOutput, PORTRAIT.name)
      ),
    ]);

    console.log("");
    console.log("🎉 全部完成！");
    console.log(`   横版：${join(resolvedOutput, LANDSCAPE.name)}`);
    console.log(`   竖版：${join(resolvedOutput, PORTRAIT.name)}`);
  } catch (error) {
    console.error(`❌ 合成失败: ${(error as Error).message}`);
    process.exit(1);
  }
}

main().catch((error) => {
  console.error("❌ 未知错误:", error);
  process.exit(1);
});
