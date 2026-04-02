#!/usr/bin/env bun
/**
 * 增量追加脚本 - 为已有 SKU 追加新风格主图和海报
 *
 * 用法:
 *   bun scripts/incremental-add.ts <sku-dir> <new-style> [--image <override-image>]
 *
 * 示例:
 *   bun scripts/incremental-add.ts output/avocado-hass lifestyle
 *   bun scripts/incremental-add.ts output/avocado-hass origin --image new-photo.jpg
 *
 * 流程:
 *   1. 检测 SKU 目录是否存在
 *   2. 加载 scene-<style>.md prompt
 *   3. 调用 baoyu-image-gen 生成新风格图
 *   4. 调用 smart-crop.ts 追加尺寸
 *   5. 调用 poster-compose.ts 追加海报
 */

import { existsSync, readFileSync, readdirSync, statSync } from "fs";
import { resolve, join, dirname, basename, extname } from "path";
import { spawn } from "child_process";

// ============================================================
// 配置
// ============================================================
const SKILL_DIR = resolve(__dirname, "..");
const PROMPTS_DIR = join(SKILL_DIR, "prompts");
const BAOYU_IMAGE_GEN = join(SKILL_DIR.replace(/\\/g, "/"), "../baoyu-image-gen/scripts/main.ts");

// 支持的风格列表（与 prompts/scene-*.md 对应）
const VALID_STYLES = [
  "minimal",
  "origin",
  "lifestyle",
  "daoju",
] as const;
type Style = (typeof VALID_STYLES)[number];

// ============================================================
// 工具函数
// ============================================================

/** 转义 shell 特殊字符 */
function escapeShellArg(arg: string): string {
  return `'${arg.replace(/'/g, "'\\''")}'`;
}

/** 打印进度日志 */
function logStep(step: string, msg: string) {
  console.log(`\n[${step}] ${msg}`);
}

/** 执行子进程命令，返回 exit code */
function runCommand(cmd: string, args: string[]): Promise<number> {
  return new Promise((resolve) => {
    const child = spawn(cmd, args, { stdio: "inherit", shell: true });
    child.on("close", (code) => resolve(code ?? 1));
    child.on("error", () => resolve(1));
  });
}

/** 从已有主图中找一张作为参考图 */
function findExistingMainImage(skuDir: string): string | null {
  const candidates = [
    "main-taobao-1:1.png",
    "main-pdd-1:1.png",
    "main-jd-1:1.png",
    "main-douyin-3:4.png",
  ];
  for (const name of candidates) {
    const path = join(skuDir, name);
    if (existsSync(path)) return path;
  }
  // 兜底：取目录下任意 png
  const files = readdirSync(skuDir).filter(
    (f) => extname(f).toLowerCase() === ".png" && !f.startsWith("poster")
  );
  if (files.length > 0) return join(skuDir, files[0]);
  return null;
}

/** 从已有主图中推断品名（取第一张 png 的目录名作为默认值） */
function inferProductName(skuDir: string): string {
  return basename(skuDir)
    .replace(/^output[\\/]/, "")
    .replace(/[_-]/g, " ");
}

/** 加载 scene prompt 内容 */
function loadScenePrompt(style: string): string {
  const promptPath = join(PROMPTS_DIR, `scene-${style}.md`);
  if (!existsSync(promptPath)) {
    console.error(`❌ 场景 prompt 不存在: prompts/scene-${style}.md`);
    console.error(`   可用风格: ${VALID_STYLES.join(", ")}`);
    process.exit(1);
  }
  return readFileSync(promptPath, "utf-8");
}

/** 从 prompt 内容提取正文（跳过标题和 markdown 格式） */
function extractPromptBody(content: string): string {
  return content
    .replace(/^#.+$/gm, "")          // 移除 markdown 一级标题
    .replace(/^#{1,3}\s+.+$/gm, "")  // 移除二/三级标题
    .replace(/^\|.+\|$/gm, "")        // 移除 markdown 表格
    .replace(/^-+$/gm, "")           // 移除分隔线
    .replace(/\n{3,}/g, "\n\n")     // 压缩多余空行
    .trim();
}

// ============================================================
// 主流程
// ============================================================

async function main() {
  const args = process.argv.slice(2);

  // 解析位置参数 + 选项
  let skuDir = "";
  let newStyle = "";
  let overrideImage = "";

  let i = 0;
  while (i < args.length) {
    if (args[i] === "--image" && i + 1 < args.length) {
      overrideImage = args[i + 1];
      i += 2;
    } else if (!skuDir) {
      skuDir = args[i++];
    } else if (!newStyle) {
      newStyle = args[i++];
    } else {
      console.error(`❌ 未知参数: ${args[i]}`);
      process.exit(1);
    }
  }

  if (!skuDir || !newStyle) {
    console.error("❌ 用法: bun scripts/incremental-add.ts <sku-dir> <new-style> [--image <override-image>]");
    console.error("");
    console.error("  <sku-dir>      已有 SKU 目录（如 output/avocado-hass）");
    console.error("  <new-style>    新风格（minimal | origin | lifestyle | daoju）");
    console.error("  --image        可选：指定参考图路径（默认使用 SKU 目录已有主图）");
    console.error("");
    console.error(`  可用风格: ${VALID_STYLES.join(", ")}`);
    console.error("");
    console.error("  示例:");
    console.error("    bun scripts/incremental-add.ts output/avocado-hass lifestyle");
    console.error("    bun scripts/incremental-add.ts output/avocado-hass origin --image new-photo.jpg");
    process.exit(1);
  }

  const resolvedSkuDir = resolve(skuDir);

  // ----- Step 1: 检测目录 -----
  logStep("1/5", `检测目录: ${resolvedSkuDir}`);
  if (!existsSync(resolvedSkuDir)) {
    console.error(`❌ SKU 目录不存在: ${resolvedSkuDir}`);
    console.error("   请先运行完整生成流程，再使用增量追加。");
    process.exit(1);
  }
  const stat = statSync(resolvedSkuDir);
  if (!stat.isDirectory()) {
    console.error(`❌ 不是目录: ${resolvedSkuDir}`);
    process.exit(1);
  }
  console.log(`✅ 目录存在，已包含 ${readdirSync(resolvedSkuDir).length} 个文件`);

  // 列出已有风格（根据已生成的文件判断）
  const existingStyles = readdirSync(resolvedSkuDir)
    .filter((f) => f.startsWith("poster-") && extname(f) === ".png")
    .map((f) => basename(f, ".png").replace("poster-", ""));
  console.log(`📦 已有风格: ${existingStyles.length > 0 ? existingStyles.join(", ") : "（仅主图）"}`);

  // ----- Step 2: 加载 prompt -----
  logStep("2/5", `加载场景 prompt: ${newStyle}`);
  const style = newStyle.toLowerCase() as Style;
  if (!VALID_STYLES.includes(style)) {
    console.error(`❌ 不支持的风格: ${newStyle}`);
    console.error(`   可用风格: ${VALID_STYLES.join(", ")}`);
    process.exit(1);
  }

  const promptContent = loadScenePrompt(style);
  const scenePrompt = extractPromptBody(promptContent);
  console.log(`✅ 已加载 scene-${style}.md（${scenePrompt.length} 字符）`);

  // ----- Step 3: 确定参考图 -----
  logStep("3/5", "确定参考图");
  let refImage = overrideImage ? resolve(overrideImage) : findExistingMainImage(resolvedSkuDir);

  if (!refImage) {
    console.error(`❌ 无法找到参考图:`);
    console.error(`   - 未指定 --image 参数`);
    console.error(`   - SKU 目录中也没有已有的主图文件`);
    console.error(`   请使用 --image 参数指定一张参考图。`);
    process.exit(1);
  }
  console.log(`🖼  参考图: ${refImage}`);

  // ----- Step 4: 调用 baoyu-image-gen -----
  logStep("4/5", `生成新风格图（${style}）`);
  const outputImage = join(resolvedSkuDir, `generated-${style}.png`);
  const baoyuScript = resolve(BAOYU_IMAGE_GEN);

  console.log(`📤 输出: ${outputImage}`);
  console.log(`\n--- 调用 baoyu-image-gen ---`);

  const genCode = await runCommand(
    "npx",
    [
      "-y", "bun",
      baoyuScript,
      "--prompt", scenePrompt,
      "--image", outputImage,
      "--ref", refImage,
      "--provider", "doubao",
    ]
  );

  if (genCode !== 0) {
    console.error(`\n❌ 图片生成失败（exit code: ${genCode}）`);
    console.error("   请检查 API 配置和环境变量。");
    process.exit(1);
  }

  if (!existsSync(outputImage)) {
    console.error(`❌ 生成完成但输出文件不存在: ${outputImage}`);
    process.exit(1);
  }
  console.log(`✅ 图片生成成功: ${basename(outputImage)}`);

  // ----- Step 5a: 调用 smart-crop -----
  logStep("5a/5", "追加尺寸（smart-crop）");
  const cropScript = join(SKILL_DIR, "scripts", "smart-crop.ts");
  const cropCode = await runCommand(
    "npx",
    ["-y", "bun", cropScript, outputImage, resolvedSkuDir]
  );
  if (cropCode !== 0) {
    console.error(`❌ smart-crop 失败（exit code: ${cropCode}）`);
    process.exit(1);
  }
  console.log("✅ 尺寸追加完成");

  // ----- Step 5b: 调用 poster-compose -----
  logStep("5b/5", "追加海报（poster-compose）");
  const composeScript = join(SKILL_DIR, "scripts", "poster-compose.ts");
  const productName = inferProductName(resolvedSkuDir);
  const tagline = "增量追加风格图";
  const price = "¥--";
  const composeCode = await runCommand(
    "npx",
    [
      "-y", "bun", composeScript,
      outputImage,
      productName,
      tagline,
      price,
      resolvedSkuDir,
    ]
  );
  if (composeCode !== 0) {
    console.error(`❌ poster-compose 失败（exit code: ${composeCode}）`);
    process.exit(1);
  }
  console.log("✅ 海报追加完成");

  // ----- 完成汇总 -----
  console.log("\n========================================");
  console.log("🎉 增量追加完成！");
  console.log(`   SKU: ${resolvedSkuDir}`);
  console.log(`   新增风格: ${style}`);
  console.log(`   生成图片: ${basename(outputImage)}`);
  console.log("========================================\n");
}

main().catch((error) => {
  console.error("❌ 未知错误:", error);
  process.exit(1);
});
