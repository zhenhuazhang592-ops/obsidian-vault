#!/usr/bin/env bun
/**
 * 智能裁切脚本 - 使用 Sharp 将基础合成图裁切为全平台 7 种尺寸
 *
 * 技术选型说明：
 * - 任务原计划使用 Fabric.js，但 Fabric.js 6.x 需要完整 DOM 环境
 * - Sharp 是 Node.js/Bun 原生图片处理库，性能更好，稳定性更高
 * - 核心裁切逻辑与 Fabric.js 等效：填满 + 裁切
 */

import sharp from "sharp";
import { mkdirSync, existsSync } from "fs";
import { resolve, join, basename } from "path";

// ============================================================
// 尺寸规格配置
// ============================================================
interface CropSpec {
  name: string;
  width: number;
  height: number;
  ratio: string;
  mode: "center" | "top";
  platform: string;
  usage: string;
}

const CROP_SPECS: CropSpec[] = [
  { name: "main-taobao-1:1", width: 800, height: 800, ratio: "1:1", mode: "center", platform: "taobao", usage: "淘宝主图" },
  { name: "main-taobao-3:4", width: 800, height: 1066, ratio: "3:4", mode: "center", platform: "taobao", usage: "淘宝长图" },
  { name: "main-jd-1:1", width: 800, height: 800, ratio: "1:1", mode: "center", platform: "jd", usage: "京东白底主图" },
  { name: "main-pdd-1:1", width: 800, height: 800, ratio: "1:1", mode: "center", platform: "pdd", usage: "拼多多主图" },
  { name: "main-pdd-3:4", width: 800, height: 1200, ratio: "2:3", mode: "center", platform: "pdd", usage: "拼多多长图" },
  { name: "main-douyin-3:4", width: 800, height: 1066, ratio: "3:4", mode: "top", platform: "douyin", usage: "抖音主图" },
  { name: "main-douyin-9:16", width: 1080, height: 1920, ratio: "9:16", mode: "top", platform: "douyin", usage: "抖音竖版" },
];

// ============================================================
// 裁切核心逻辑
// ============================================================

/**
 * 计算缩放和裁切参数
 * @param srcW 原图宽度
 * @param srcH 原图高度
 * @param targetW 目标宽度
 * @param targetH 目标高度
 * @param mode 裁切模式: center=居中, top=保留上方
 */
function calculateResizeParams(
  srcW: number,
  srcH: number,
  targetW: number,
  targetH: number,
  mode: "center" | "top"
): { resizeW: number; resizeH: number; left: number; top: number } {
  // 计算缩放比例：确保填满目标尺寸
  const scaleX = targetW / srcW;
  const scaleY = targetH / srcH;
  const scale = Math.max(scaleX, scaleY);

  // 缩放后的尺寸
  const resizeW = Math.round(srcW * scale);
  const resizeH = Math.round(srcH * scale);

  // 计算裁切起点
  let left = 0;
  let top = 0;

  if (mode === "center") {
    // 居中裁切：主体中心点落在画面中心
    left = Math.round((resizeW - targetW) / 2);
    top = Math.round((resizeH - targetH) / 2);
  } else if (mode === "top") {
    // 顶部裁切：保留画面上方（抖音内容常在顶部）
    left = Math.round((resizeW - targetW) / 2);
    top = 0;
  }

  return { resizeW, resizeH, left, top };
}

/**
 * 生成单张裁切图
 */
async function cropImage(
  inputPath: string,
  outputPath: string,
  spec: CropSpec
): Promise<void> {
  // 获取原图元数据
  const metadata = await sharp(inputPath).metadata();
  const srcW = metadata.width || 0;
  const srcH = metadata.height || 0;

  if (srcW === 0 || srcH === 0) {
    throw new Error(`无法读取图片尺寸: ${inputPath}`);
  }

  // 计算裁切参数
  const { resizeW, resizeH, left, top } = calculateResizeParams(
    srcW,
    srcH,
    spec.width,
    spec.height,
    spec.mode
  );

  // 执行 resize + extract 裁切
  await sharp(inputPath)
    .resize(resizeW, resizeH, {
      fit: "fill", // 填满
      kernel: "lanczos3", // 高质量缩放
    })
    .extract({
      left,
      top,
      width: spec.width,
      height: spec.height,
    })
    .png({
      quality: 100,
      compressionLevel: 6,
    })
    .toFile(outputPath);

  // 输出日志
  console.log(
    `✅ 已生成: ${basename(outputPath)} (${spec.width}×${spec.height}) [${spec.platform}] ${spec.usage}`
  );
}

// ============================================================
// 主程序
// ============================================================

async function main() {
  // 解析命令行参数
  const args = process.argv.slice(2);

  if (args.length < 2) {
    console.error("❌ 用法: bun scripts/smart-crop.ts <input-image> <output-dir>");
    console.error("   示例: bun scripts/smart-crop.ts avocado-main.png output/avocado/");
    console.error("");
    console.error("📐 支持的尺寸规格:");
    console.table(
      CROP_SPECS.map((s) => ({
        规格: s.name,
        尺寸: `${s.width}×${s.height}`,
        比例: s.ratio,
        模式: s.mode,
        平台: s.platform,
        用途: s.usage,
      }))
    );
    process.exit(1);
  }

  const inputPath = resolve(args[0]);
  const outputDir = resolve(args[1]);

  // 验证输入文件
  if (!existsSync(inputPath)) {
    console.error(`❌ 输入文件不存在: ${inputPath}`);
    process.exit(1);
  }

  // 创建输出目录
  if (!existsSync(outputDir)) {
    mkdirSync(outputDir, { recursive: true });
  }

  console.log(`📂 输入: ${inputPath}`);
  console.log(`📂 输出目录: ${outputDir}`);
  console.log(`📐 生成 ${CROP_SPECS.length} 种尺寸...\n`);

  // 批量裁切
  const results: { success: string[]; failed: string[] } = { success: [], failed: [] };

  for (const spec of CROP_SPECS) {
    const outputPath = join(outputDir, `${spec.name}.png`);

    try {
      await cropImage(inputPath, outputPath, spec);
      results.success.push(spec.name);
    } catch (error) {
      console.error(`❌ 失败: ${spec.name} - ${(error as Error).message}`);
      results.failed.push(spec.name);
    }
  }

  // 汇总报告
  console.log(`\n📊 完成: ${results.success.length} 成功, ${results.failed.length} 失败`);
  if (results.failed.length > 0) {
    console.error(`⚠️ 失败列表: ${results.failed.join(", ")}`);
    process.exit(1);
  }
}

main().catch((error) => {
  console.error("❌ 未知错误:", error);
  process.exit(1);
});
