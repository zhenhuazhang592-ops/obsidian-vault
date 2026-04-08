/**
 * image-provider.ts
 * =============================================================
 * 从 Claw Code rust/crates/api/src/providers/mod.rs 迁移
 * 用途：为图像生成 API（DashScope / Doubao-Seedream 等）建立统一抽象
 *
 * 核心设计（复刻 Claw Code Provider 模式）：
 *   - Provider 接口（trait 等效）
 *   - Model 注册表（MODEL_REGISTRY）
 *   - detect_provider_kind() 自动探测
 *   - resolve_model_alias() 别名解析
 *   - ProviderClient 统一入口
 *
 * 使用方式：
 *   import { generateImage } from ".claude/scripts/image-provider";
 *   const result = await generateImage({ prompt, model: "flux", provider: "auto" });
 * =============================================================
 */

// ─── Provider 类型 ──────────────────────────────────────────────────

export type ImageProviderKind = "dashscope" | "doubao" | "openai" | "local";

export interface ProviderMetadata {
  provider: ImageProviderKind;
  /** API Key 环境变量名 */
  authEnv: string;
  /** Base URL 环境变量名（可选） */
  baseUrlEnv?: string;
  /** 默认 base URL */
  defaultBaseUrl: string;
}

// ─── 模型注册表 ────────────────────────────────────────────────────

interface ModelEntry {
  metadata: ProviderMetadata;
  aliases: string[];
  defaultSize?: string;
  maxSteps?: number;
}

const IMAGE_MODEL_REGISTRY: ModelEntry[] = [
  // ── DashScope ──────────────────────────────────────────────────
  {
    metadata: {
      provider: "dashscope",
      authEnv: "DASHSCOPE_API_KEY",
      baseUrlEnv: "DASHSCOPE_BASE_URL",
      defaultBaseUrl: "https://dashscope.aliyuncs.com/api/v1",
    },
    aliases: [
      // Flux
      "flux",
      "flux-pro",
      "flux-dev",
      "flux-schnell",
      "flux-ultra",
      "flux-realism",
      // Wanx（阿里系图像模型）
      "wanx",
      "wanx-plus",
      "wanx-pro",
      "wanx-ours",
      "wanx-default",
      "wanx-motion",
    ],
    defaultSize: "1024x1024",
    maxSteps: 30,
  },
  // ── Doubao-Seedream ────────────────────────────────────────────
  {
    metadata: {
      provider: "doubao",
      authEnv: "ARK_API_KEY",
      baseUrlEnv: "ARK_BASE_URL",
      defaultBaseUrl: "https://ark.cn-beijing.volces.com/api/v3",
    },
    aliases: [
      "doubao-seedream",
      "doubao-seedream-3.0",
      "doubao-seedream-3.1",
      "doubao-seedream-4",
      "doubao-seedream-4.5",
      "seedream",
      "seedream-3.0",
      "seedream-3.1",
      "seedream-4",
      "seedream-4.5",
      "doubao-i2v",
      "doubao-i2v-720p",
      "doubao-i2v-2k",
    ],
    defaultSize: "1024x1024",
    maxSteps: 25,
  },
  // ── OpenAI DALL-E ──────────────────────────────────────────────
  {
    metadata: {
      provider: "openai",
      authEnv: "OPENAI_API_KEY",
      baseUrlEnv: "OPENAI_BASE_URL",
      defaultBaseUrl: "https://api.openai.com/v1",
    },
    aliases: ["dalle", "dalle-2", "dalle-3", "dall-e-3", "dall-e-2"],
    defaultSize: "1024x1024",
    maxSteps: undefined,
  },
  // ── 本地（Future）───────────────────────────────────────────────
  {
    metadata: {
      provider: "local",
      authEnv: "",
      defaultBaseUrl: "http://localhost:7860",
    },
    aliases: [
      "local-sd",
      "stable-diffusion",
      "sd-xl",
      "comfyui",
      "flux-local",
    ],
    defaultSize: "512x512",
    maxSteps: 50,
  },
];

// ─── 别名解析 ───────────────────────────────────────────────────────

/**
 * 将用户友好的模型别名解析为规范名称
 * 例: "flux" → "flux-pro", "seedream-3.0" → "doubao-seedream-3.0"
 */
export function resolveModelAlias(model: string): string {
  const lower = model.trim().toLowerCase();

  for (const entry of IMAGE_MODEL_REGISTRY) {
    if (entry.aliases.includes(lower)) {
      return entry.aliases[0]; // 返回第一个别名作为规范名
    }
  }

  return model.trim(); // 未知模型，原样返回
}

/**
 * 获取模型的 Provider 元信息
 */
export function metadataForModel(model: string): ProviderMetadata | null {
  const canonical = resolveModelAlias(model).toLowerCase();

  for (const entry of IMAGE_MODEL_REGISTRY) {
    if (entry.aliases.includes(canonical)) {
      return entry.metadata;
    }
  }

  return null;
}

// ─── Provider 探测 ─────────────────────────────────────────────────

/**
 * 自动探测应该使用哪个 Provider
 * 优先级：模型名匹配 > 环境变量存在性
 */
export function detectProviderKind(
  model: string,
  explicitProvider?: ImageProviderKind,
): ImageProviderKind {
  if (explicitProvider) return explicitProvider;

  const fromModel = metadataForModel(model);
  if (fromModel) return fromModel.provider;

  // 回退：按环境变量存在性探测
  if (process.env["DASHSCOPE_API_KEY"]) return "dashscope";
  if (process.env["ARK_API_KEY"]) return "doubao";
  if (process.env["OPENAI_API_KEY"]) return "openai";

  return "dashscope"; // 默认 DashScope
}

// ─── ProviderClient 统一入口 ────────────────────────────────────────

export interface GenerateOptions {
  prompt: string;
  model?: string;
  provider?: ImageProviderKind | "auto";
  size?: string;
  quality?: "standard" | "hd";
  style?: string;
  steps?: number;
  seed?: number;
  n?: number;
  outputPath?: string;  // 保存到本地路径
  mimeType?: "image/png" | "image/jpeg" | "image/webp";
}

export interface GenerationResult {
  imageUrl?: string;        // HTTP URL（如果有）
  base64?: string;         // base64 编码的图像
  localPath?: string;      // 本地保存路径
  model: string;
  provider: ImageProviderKind;
  tokens?: number;
  elapsedMs: number;
}

export interface Provider {
  generate(options: {
    prompt: string;
    model: string;
    size?: string;
    quality?: string;
    style?: string;
    steps?: number;
    seed?: number;
    n?: number;
    outputPath?: string;
    mimeType?: string;
  }): Promise<GenerationResult>;
}

// ─── Provider 实现 ──────────────────────────────────────────────────

import * as fs from "fs";
import * as path from "path";
import https from "https";
import http from "http";
import { pipeline } from "stream";
import { promisify } from "util";

const pipelineAsync = promisify(pipeline);

/**
 * DashScope Provider
 * API: https://help.aliyun.com/zh/dashscope/
 */
class DashScopeProvider implements Provider {
  constructor(private apiKey: string, private baseUrl?: string) {}

  async generate(opts: {
    prompt: string;
    model: string;
    size?: string;
    quality?: string;
    style?: string;
    steps?: number;
    seed?: number;
    n?: number;
    outputPath?: string;
    mimeType?: string;
  }): Promise<GenerationResult> {
    const start = Date.now();
    const modelMeta = metadataForModel(opts.model);
    const size = opts.size ?? modelMeta?.defaultSize ?? "1024*1024";

    // wanx 系列用 /text2image-stream，flux 系列用 /images/generations
    const isWanx = opts.model.startsWith("wanx");
    const endpoint = isWanx
      ? "/services/aigc/text2image-stream"
      : "/services/aigc/flux";
    const url = `${this.baseUrl ?? "https://dashscope.aliyuncs.com/api/v1"}${endpoint}`;

    const body: Record<string, unknown> = {
      model: opts.model,
      input: { prompt: opts.prompt },
      parameters: {
        size,
        n: opts.n ?? 1,
      },
    };

    if (opts.seed !== undefined) {
      (body.parameters as Record<string, unknown>)["seed"] = opts.seed;
    }
    if (opts.steps !== undefined && modelMeta?.maxSteps) {
      (body.parameters as Record<string, unknown>)["steps"] = Math.min(
        opts.steps,
        modelMeta.maxSteps,
      );
    }
    if (opts.style) {
      (body.parameters as Record<string, unknown>)["style"] = opts.style;
    }

    const response = await this.httpRequest(url, body);
    const data = JSON.parse(response);

    // wanx 返回 { output.images[], output.task_id, ... }
    // flux 返回 { output.image_urls[] }
    const imageUrls: string[] =
      data.output?.images?.map((img: { url?: string; b64_image?: string }) =>
        img.url ?? (img.b64_image ? `data:image/png;base64,${img.b64_image}` : null),
      ).filter(Boolean) ??
      data.output?.image_urls ?? [];

    let localPath: string | undefined;
    if (opts.outputPath && imageUrls[0]) {
      await downloadFile(imageUrls[0], opts.outputPath);
      localPath = opts.outputPath;
    }

    return {
      imageUrl: imageUrls[0],
      base64: imageUrls[0]?.startsWith("data:"),
      localPath,
      model: opts.model,
      provider: "dashscope",
      elapsedMs: Date.now() - start,
    };
  }

  private httpRequest(url: string, body: unknown): Promise<string> {
    return new Promise((resolve, reject) => {
      const urlObj = new URL(url);
      const postData = JSON.stringify(body);

      const options: http.RequestOptions = {
        hostname: urlObj.hostname,
        path: urlObj.pathname + urlObj.search,
        method: "POST",
        headers: {
          Authorization: `Bearer ${this.apiKey}`,
          "Content-Type": "application/json",
          "Content-Length": Buffer.byteLength(postData),
        },
      };

      const req = (urlObj.protocol === "https:" ? https : http).request(
        options,
        (res) => {
          let data = "";
          res.on("data", (chunk) => (data += chunk));
          res.on("end", () => {
            if (res.statusCode && res.statusCode >= 400) {
              reject(new Error(`DashScope API error ${res.statusCode}: ${data}`));
            } else {
              resolve(data);
            }
          });
        },
      );

      req.on("error", reject);
      req.write(postData);
      req.end();
    });
  }
}

/**
 * Doubao-Seedream Provider
 * API: https://www.volcengine.com/docs/82379/1399008
 */
class DoubaoProvider implements Provider {
  constructor(private apiKey: string, private baseUrl?: string) {
    if (!this.baseUrl) {
      this.baseUrl = "https://ark.cn-beijing.volces.com/api/v3";
    }
  }

  async generate(opts: {
    prompt: string;
    model: string;
    size?: string;
    quality?: string;
    n?: number;
    seed?: number;
    outputPath?: string;
    mimeType?: string;
  }): Promise<GenerationResult> {
    const start = Date.now();
    const size = opts.size ?? "1024*1024";
    const isI2v = opts.model.includes("i2v");

    const url = `${this.baseUrl}/images/generations`;

    const body: Record<string, unknown> = {
      model: opts.model,
      prompt: opts.prompt,
      size: size.replace("*", "x"),
      n: opts.n ?? 1,
    };

    if (opts.seed !== undefined) {
      body["seed"] = opts.seed;
    }

    const response = await this.httpRequest(url, body);
    const data = JSON.parse(response);

    const imageUrls: string[] =
      data.data?.map(
        (item: { url?: string; b64_image?: string }) =>
          item.url ?? (item.b64_image ? `data:image/png;base64,${item.b64_image}` : null),
      ).filter(Boolean) ?? [];

    let localPath: string | undefined;
    if (opts.outputPath && imageUrls[0]) {
      await downloadFile(imageUrls[0], opts.outputPath);
      localPath = opts.outputPath;
    }

    return {
      imageUrl: imageUrls[0],
      base64: imageUrls[0]?.startsWith("data:"),
      localPath,
      model: opts.model,
      provider: "doubao",
      elapsedMs: Date.now() - start,
    };
  }

  private httpRequest(url: string, body: unknown): Promise<string> {
    return new Promise((resolve, reject) => {
      const urlObj = new URL(url);
      const postData = JSON.stringify(body);

      const options: http.RequestOptions = {
        hostname: urlObj.hostname,
        path: urlObj.pathname + urlObj.search,
        method: "POST",
        headers: {
          Authorization: `Bearer ${this.apiKey}`,
          "Content-Type": "application/json",
          "Content-Length": Buffer.byteLength(postData),
        },
      };

      const req = (urlObj.protocol === "https:" ? https : http).request(
        options,
        (res) => {
          let data = "";
          res.on("data", (chunk) => (data += chunk));
          res.on("end", () => {
            if (res.statusCode && res.statusCode >= 400) {
              reject(new Error(`Doubao API error ${res.statusCode}: ${data}`));
            } else {
              resolve(data);
            }
          });
        },
      );

      req.on("error", reject);
      req.write(postData);
      req.end();
    });
  }
}

/**
 * OpenAI DALL-E Provider
 */
class OpenAIProvider implements Provider {
  constructor(private apiKey: string, private baseUrl?: string) {}

  async generate(opts: {
    prompt: string;
    model: string;
    size?: string;
    quality?: string;
    style?: string;
    n?: number;
    outputPath?: string;
  }): Promise<GenerationResult> {
    const start = Date.now();
    const size = opts.size ?? "1024x1024";
    const model = opts.model === "dalle-2" ? "dall-e-2" : "dall-e-3";
    const quality = opts.quality ?? (model === "dall-e-3" ? "hd" : "standard");

    const url = `${this.baseUrl ?? "https://api.openai.com/v1"}/images/generations`;

    const body: Record<string, unknown> = {
      model,
      prompt: opts.prompt,
      n: opts.n ?? 1,
      quality,
      response_format: opts.outputPath ? "b64_json" : "url",
    };

    if (opts.size) {
      body["size"] = size;
    }
    if (opts.style && model === "dall-e-3") {
      body["style"] = opts.style;
    }

    const response = await this.httpRequest(url, body);
    const data = JSON.parse(response);

    const images: { url?: string; b64_json?: string }[] = data.data ?? [];

    let localPath: string | undefined;
    if (opts.outputPath && images[0]) {
      const base64 = images[0].b64_json;
      if (base64) {
        fs.mkdirSync(path.dirname(opts.outputPath), { recursive: true });
        fs.writeFileSync(opts.outputPath, Buffer.from(base64, "base64"));
        localPath = opts.outputPath;
      }
    }

    return {
      imageUrl: images[0]?.url,
      base64: images[0]?.b64_json ?? undefined,
      localPath,
      model,
      provider: "openai",
      elapsedMs: Date.now() - start,
    };
  }

  private httpRequest(url: string, body: unknown): Promise<string> {
    return new Promise((resolve, reject) => {
      const urlObj = new URL(url);
      const postData = JSON.stringify(body);

      const options: http.RequestOptions = {
        hostname: urlObj.hostname,
        path: urlObj.pathname + urlObj.search,
        method: "POST",
        headers: {
          Authorization: `Bearer ${this.apiKey}`,
          "Content-Type": "application/json",
          "Content-Length": Buffer.byteLength(postData),
        },
      };

      const req = https.request(options, (res) => {
        let data = "";
        res.on("data", (chunk) => (data += chunk));
        res.on("end", () => {
          if (res.statusCode && res.statusCode >= 400) {
            reject(new Error(`OpenAI API error ${res.statusCode}: ${data}`));
          } else {
            resolve(data);
          }
        });
      });

      req.on("error", reject);
      req.write(postData);
      req.end();
    });
  }
}

// ─── ProviderClient ────────────────────────────────────────────────

/**
 * 工厂函数：从模型名创建对应的 Provider 实例
 */
export function createProvider(
  providerKind: ImageProviderKind,
): Provider | null {
  switch (providerKind) {
    case "dashscope": {
      const key = process.env["DASHSCOPE_API_KEY"];
      if (!key) return null;
      return new DashScopeProvider(key, process.env["DASHSCOPE_BASE_URL"]);
    }
    case "doubao": {
      const key = process.env["ARK_API_KEY"];
      if (!key) return null;
      return new DoubaoProvider(key, process.env["ARK_BASE_URL"]);
    }
    case "openai": {
      const key = process.env["OPENAI_API_KEY"];
      if (!key) return null;
      return new OpenAIProvider(key, process.env["OPENAI_BASE_URL"]);
    }
    case "local":
      // TODO: 本地 SD 集成
      return null;
    default:
      return null;
  }
}

// ─── 统一生成入口 ──────────────────────────────────────────────────

/**
 * 统一图像生成 API
 *
 * @example
 * const result = await generateImage({
 *   prompt: "A cute cat",
 *   model: "flux",           // 自动探测 provider = dashscope
 *   size: "1024x1024",
 *   outputPath: "output.png"
 * });
 */
export async function generateImage(
  options: GenerateOptions,
): Promise<GenerationResult> {
  const model = resolveModelAlias(options.model ?? "flux");
  const providerKind = detectProviderKind(
    model,
    options.provider === "auto" ? undefined : options.provider,
  );

  const provider = createProvider(providerKind);
  if (!provider) {
    throw new Error(
      `No provider available for ${providerKind}. ` +
        `Check that the corresponding API key is set in environment variables.`,
    );
  }

  return provider.generate({
    prompt: options.prompt,
    model,
    size: options.size,
    quality: options.quality,
    style: options.style,
    steps: options.steps,
    seed: options.seed,
    n: options.n,
    outputPath: options.outputPath,
    mimeType: options.mimeType,
  });
}

// ─── 工具函数 ───────────────────────────────────────────────────────

/**
 * 下载文件（支持 data: URI 和 HTTP URL）
 */
async function downloadFile(url: string, destPath: string): Promise<void> {
  fs.mkdirSync(path.dirname(destPath), { recursive: true });

  if (url.startsWith("data:")) {
    const base64 = url.replace(/^data:[^;]+;base64,/, "");
    fs.writeFileSync(destPath, Buffer.from(base64, "base64"));
    return;
  }

  return new Promise((resolve, reject) => {
    const urlObj = new URL(url);
    const protocol = urlObj.protocol === "https:" ? https : http;

    const req = protocol.get(urlObj, (res) => {
      if (res.statusCode && [301, 302, 303, 307, 308].includes(res.statusCode)) {
        const redirectUrl = res.headers.location;
        if (redirectUrl) {
          downloadFile(redirectUrl, destPath).then(resolve).catch(reject);
        } else {
          reject(new Error("Redirect without Location header"));
        }
        return;
      }

      const writer = fs.createWriteStream(destPath);
      pipelineAsync(res, writer).then(() => resolve()).catch(reject);
    });

    req.on("error", reject);
  });
}

/**
 * 列出所有可用模型及其 Provider
 */
export function listModels(): ModelEntry[] {
  return IMAGE_MODEL_REGISTRY;
}

/**
 * 获取 Provider 统计（哪些 API Key 已配置）
 */
export function providerStatus(): Record<ImageProviderKind, boolean> {
  return {
    dashscope: !!process.env["DASHSCOPE_API_KEY"],
    doubao: !!process.env["ARK_API_KEY"],
    openai: !!process.env["OPENAI_API_KEY"],
    local: false, // 本地需手动配置
  };
}

// ─── CLI ──────────────────────────────────────────────────────────

async function main() {
  const args = process.argv.slice(2);

  if (args[0] === "--list" || args[0] === "-l") {
    console.log("=== Available Image Providers ===");
    const status = providerStatus();
    for (const entry of IMAGE_MODEL_REGISTRY) {
      const p = entry.metadata.provider;
      const configured = status[p];
      const aliasList = entry.aliases.join(", ");
      console.log(`[${configured ? "✓" : "✗"}] ${entry.metadata.provider} — ${aliasList}`);
    }
    return;
  }

  if (args[0] === "--status" || args[0] === "-s") {
    const status = providerStatus();
    console.log("=== Provider Status ===");
    for (const [provider, ready] of Object.entries(status)) {
      console.log(`  ${ready ? "✓" : "✗"} ${provider}`);
    }
    return;
  }

  // 默认：生成图像
  const prompt = args.join(" ") || "A beautiful sunset over the ocean";
  const model = process.env["DEFAULT_IMAGE_MODEL"] ?? "flux";

  console.log(`Generating: "${prompt}" with ${model}...`);

  try {
    const result = await generateImage({
      prompt,
      model,
      outputPath: `/tmp/generated-${Date.now()}.png`,
    });
    console.log(`Done! Saved to: ${result.localPath}`);
    console.log(`Provider: ${result.provider}, Model: ${result.model}`);
    console.log(`Elapsed: ${result.elapsedMs}ms`);
  } catch (err) {
    console.error("Generation failed:", err);
    process.exit(1);
  }
}

if (require.main === module) {
  main().catch(console.error);
}
