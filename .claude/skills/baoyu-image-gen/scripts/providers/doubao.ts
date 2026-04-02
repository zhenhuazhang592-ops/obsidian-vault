import type { CliArgs } from "../types";

export function getDefaultModel(): string {
  return process.env.DOUBAO_IMAGE_MODEL || "doubao-seedream-4-5-251128";
}

function getApiKey(): string {
  const key = process.env.ARK_API_KEY;
  if (!key) throw new Error("ARK_API_KEY is required for Doubao provider. Set ARK_API_KEY in your environment.");
  return key;
}

function getBaseUrl(): string {
  return (process.env.DOUBAO_BASE_URL || "https://ark.cn-beijing.volces.com/api/v3").replace(/\/+$/g, "");
}

function parseAspectRatio(ar: string): { width: number; height: number } | null {
  const match = ar.match(/^(\d+(?:\.\d+)?):(\d+(?:\.\d+)?)$/);
  if (!match) return null;
  const w = parseFloat(match[1]!);
  const h = parseFloat(match[2]!);
  if (w <= 0 || h <= 0) return null;
  return { width: w, height: h };
}

function sizeForAspectRatio(ar: string | null, quality: CliArgs["quality"]): string {
  // Map aspect ratios to supported Doubao image sizes.
  // Doubao Seedream supports: 1024x1024, 1280x720, 720x1280, 1024x768, 768x1024, 2048x2048, etc.
  const parsed = ar ? parseAspectRatio(ar) : null;
  const is2k = quality === "2k";

  if (!parsed) {
    return is2k ? "2048x2048" : "1024x1024";
  }

  const ratio = parsed.width / parsed.height;

  const sizeMap: Array<{ ratio: number; sizes: [string, string] }> = [
    { ratio: 1, sizes: is2k ? ["2048x2048", "1024x1024"] : ["1024x1024", "1024x1024"] }, // 1:1
    { ratio: 16 / 9, sizes: is2k ? ["2048x1152", "1280x720"] : ["1280x720", "1280x720"] }, // 16:9
    { ratio: 9 / 16, sizes: is2k ? ["1152x2048", "720x1280"] : ["720x1280", "720x1280"] }, // 9:16
    { ratio: 4 / 3, sizes: is2k ? ["2048x1536", "1024x768"] : ["1024x768", "1024x768"] }, // 4:3
    { ratio: 3 / 4, sizes: is2k ? ["1536x2048", "768x1024"] : ["768x1024", "768x1024"] }, // 3:4
  ];

  let best = sizeMap[0]!;
  let bestDiff = Math.abs(best.ratio - ratio);
  for (const entry of sizeMap) {
    const diff = Math.abs(entry.ratio - ratio);
    if (diff < bestDiff) {
      bestDiff = diff;
      best = entry;
    }
  }

  return best.sizes[0]!;
}

export async function generateImage(
  prompt: string,
  model: string,
  args: CliArgs
): Promise<Uint8Array> {
  const apiKey = getApiKey();
  const baseUrl = getBaseUrl();
  const imageSize = args.size || sizeForAspectRatio(args.aspectRatio, args.quality);

  const url = `${baseUrl}/images/generations`;

  // Doubao-Seedream does NOT support reference images via /images/generations.
  // Only text-to-image is supported through this endpoint.
  if (args.referenceImages.length > 0) {
    throw new Error(
      "Reference images are not supported with Doubao-Seedream-4.5 provider. " +
        "Use --provider google with a Gemini multimodal model (gemini-3-pro-image-preview) for reference image support."
    );
  }

  const body = {
    model,
    prompt,
    image_size: imageSize,
  };

  console.log(`Generating image with Doubao ARK (${model})...`, { image_size: imageSize });

  const res = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${apiKey}`,
    },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Doubao ARK API error (${res.status}): ${err}`);
  }

  const result = await res.json() as {
    data?: Array<{ url?: string; b64_json?: string }>;
    error?: { message?: string };
  };

  if (result.error) {
    throw new Error(`Doubao ARK error: ${result.error.message}`);
  }

  const imageItem = result.data?.[0];
  if (!imageItem) {
    console.error("Response:", JSON.stringify(result, null, 2));
    throw new Error("No image in Doubao ARK response");
  }

  let imageData: string;

  if (imageItem.url) {
    imageData = imageItem.url;
  } else if (imageItem.b64_json) {
    imageData = imageItem.b64_json;
  } else {
    console.error("Response:", JSON.stringify(result, null, 2));
    throw new Error("No image URL or base64 data in Doubao ARK response");
  }

  // Download image from URL
  if (imageData.startsWith("http://") || imageData.startsWith("https://")) {
    const imgRes = await fetch(imageData);
    if (!imgRes.ok) throw new Error(`Failed to download image: ${imgRes.status}`);
    const buf = await imgRes.arrayBuffer();
    return new Uint8Array(buf);
  }

  // Decode base64
  return Uint8Array.from(Buffer.from(imageData, "base64"));
}
