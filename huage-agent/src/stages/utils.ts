/**
 * Stage 执行器通用工具
 */

import { z } from 'zod';

/**
 * 将复杂对象 stringify 后注入模板
 * 用于 {{VAR}} 占位符——所有对象在 render 前必须 stringify
 */
export function stringifyForTemplate(obj: unknown): string {
  if (typeof obj === 'string') return obj;
  return JSON.stringify(obj, null, 2);
}

/**
 * 解析 LLM JSON 响应
 * 优先从 markdown code fence 提取，fallback 到直接 parse
 */
export function parseJsonResponse<T>(text: string, schema: z.ZodSchema<T>): T | null {
  const jsonMatch = text.match(/```json\s*([\s\S]*?)\s*```/);
  const raw = jsonMatch ? jsonMatch[1].trim() : text.trim();
  try {
    return schema.parse(JSON.parse(raw));
  } catch {
    return null;
  }
}
