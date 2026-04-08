#!/usr/bin/env node
/**
 * compact-vault.ts
 * =============================================================
 * 从 Claw Code rust/crates/runtime/src/compact.rs 迁移
 * 用途：Token 预算压缩 — 将超长会话历史摘要进 MEMORY.md
 *
 * 核心算法：
 *   1. 保留最近 N 条消息（默认 4）
 *   2. 其余消息生成 <summary> 标签块
 *   3. 用系统消息 prepend 会话，开头写：
 *      "This session is being continued from a previous conversation..."
 *   4. 支持链式压缩（多次压缩后合并 summary）
 *
 * 使用方式：
 *   npx ts-node .claude/scripts/compact-vault.ts [session.md] [output.md]
 *   默认：读取 .claude/sessions/current.json，写入 .claude/sessions/compacted.md
 * =============================================================
 */

import * as fs from "fs";
import * as path from "path";
import * as readline from "readline";

// ─── 配置 ───────────────────────────────────────────────────────────

export interface CompactionConfig {
  /** 保留最近的 N 条消息（默认 4） */
  preserve_recent_messages: number;
  /** 触发压缩的 token 阈值（默认 10,000） */
  max_estimated_tokens: number;
  /** summary 块最大字符数（默认 160） */
  summary_truncate_chars: number;
}

export const DEFAULT_CONFIG: CompactionConfig = {
  preserve_recent_messages: 4,
  max_estimated_tokens: 10_000,
  summary_truncate_chars: 160,
};

// ─── 数据类型 ───────────────────────────────────────────────────────

export type MessageRole = "system" | "user" | "assistant" | "tool";

export interface ContentBlock {
  type: "text" | "tool_use" | "tool_result";
  text?: string;
  tool_name?: string;
  tool_input?: string;
  tool_output?: string;
  is_error?: boolean;
}

export interface ConversationMessage {
  role: MessageRole;
  blocks: ContentBlock[];
  usage?: unknown;
}

export interface Session {
  version: number;
  messages: ConversationMessage[];
}

export interface CompactionResult {
  summary: string;
  formatted_summary: string;
  compacted_session: Session;
  removed_message_count: number;
}

// ─── 核心算法 ───────────────────────────────────────────────────────

/**
 * 估算会话总 token 数（粗略：字符数 / 4 + 1）
 */
export function estimateSessionTokens(session: Session): number {
  return session.messages.reduce(
    (sum, msg) => sum + estimateMessageTokens(msg),
    0,
  );
}

/**
 * 是否应该触发压缩
 * 规则：可压缩消息 > preserve_recent_messages 且 token 数 >= 阈值
 */
export function shouldCompact(
  session: Session,
  config: CompactionConfig = DEFAULT_CONFIG,
): boolean {
  const start = compactedSummaryPrefixLen(session);
  const compactable = session.messages.slice(start);
  return (
    compactable.length > config.preserve_recent_messages &&
    compactable.reduce((s, m) => s + estimateMessageTokens(m), 0) >=
      config.max_estimated_tokens
  );
}

/**
 * 压缩会话：
 *   - 早期消息 → <summary> 标签块
 *   - 最近 N 条 → 保持原样
 *   - 插入系统续接消息
 */
export function compactSession(
  session: Session,
  config: CompactionConfig = DEFAULT_CONFIG,
): CompactionResult {
  if (!shouldCompact(session, config)) {
    return {
      summary: "",
      formatted_summary: "",
      compacted_session: session,
      removed_message_count: 0,
    };
  }

  const existingSummary = extractExistingCompactedSummary(session);
  const compactedPrefixLen = existingSummary ? 1 : 0;
  const keepFrom =
    session.messages.length - config.preserve_recent_messages;
  const removed = session.messages.slice(compactedPrefixLen, keepFrom);
  const preserved = session.messages.slice(keepFrom);

  const newSummary = summarizeMessages(removed, config);
  const summary = mergeCompactSummaries(existingSummary, newSummary);
  const formattedSummary = formatCompactSummary(summary);
  const continuation = getCompactContinuationMessage(
    summary,
    true,
    preserved.length > 0,
  );

  const compactedMessages: ConversationMessage[] = [
    {
      role: "system",
      blocks: [{ type: "text", text: continuation }],
      usage: null,
    },
    ...preserved,
  ];

  return {
    summary,
    formatted_summary: formattedSummary,
    compacted_session: {
      version: session.version,
      messages: compactedMessages,
    },
    removed_message_count: removed.length,
  };
}

// ─── 摘要生成 ───────────────────────────────────────────────────────

export function summarizeMessages(
  messages: ConversationMessage[],
  config: CompactionConfig = DEFAULT_CONFIG,
): string {
  const userCount = messages.filter((m) => m.role === "user").length;
  const assistantCount = messages.filter((m) => m.role === "assistant").length;
  const toolCount = messages.filter((m) => m.role === "tool").length;

  // 提取涉及的工具
  const toolNames = [
    ...new Set(
      messages.flatMap((m) =>
        m.blocks.map((b) => {
          if (b.type === "tool_use") return b.tool_name;
          if (b.type === "tool_result") return b.tool_name;
          return null;
        }),
      ).filter(Boolean) as string[],
    ),
  ];

  // 最近 3 条用户请求
  const recentUserRequests = collectRecentRoleSummaries(
    messages,
    "user",
    3,
    config.summary_truncate_chars,
  );

  // 待办事项（从含 next/todo/pending 的消息推断）
  const pendingWork = inferPendingWork(messages, config.summary_truncate_chars);

  // 关键文件（从 tool_use 参数中提取 .md/.ts/.json 等路径）
  const keyFiles = collectKeyFiles(messages);

  // 当前工作（最后一条非空文本）
  const currentWork = inferCurrentWork(messages, config.summary_truncate_chars);

  const lines: string[] = ["<summary>", "Conversation summary:"];

  lines.push(
    `- Scope: ${messages.length} earlier messages compacted (user=${userCount}, assistant=${assistantCount}, tool=${toolCount}).`,
  );

  if (toolNames.length > 0) {
    lines.push(`- Tools mentioned: ${toolNames.join(", ")}.`);
  }

  if (recentUserRequests.length > 0) {
    lines.push("- Recent user requests:");
    recentUserRequests.forEach((r) => lines.push(`  - ${r}`));
  }

  if (pendingWork.length > 0) {
    lines.push("- Pending work:");
    pendingWork.forEach((p) => lines.push(`  - ${p}`));
  }

  if (keyFiles.length > 0) {
    lines.push(`- Key files referenced: ${keyFiles.join(", ")}.`);
  }

  if (currentWork) {
    lines.push(`- Current work: ${currentWork}`);
  }

  lines.push("- Key timeline:");
  messages.forEach((msg) => {
    const content = msg.blocks.map(summarizeBlock).join(" | ");
    lines.push(`  - ${msg.role}: ${content}`);
  });

  lines.push("</summary>");
  return lines.join("\n");
}

// ─── 摘要合并（链式压缩）────────────────────────────────────────────

export function mergeCompactSummaries(
  existing: string | null | undefined,
  newSummary: string,
): string {
  if (!existing) return newSummary;

  const previousHighlights = extractSummaryHighlights(existing);
  const newFormatted = formatCompactSummary(newSummary);
  const newHighlights = extractSummaryHighlights(newFormatted);
  const newTimeline = extractSummaryTimeline(newFormatted);

  const lines: string[] = ["<summary>", "Conversation summary:"];

  if (previousHighlights.length > 0) {
    lines.push("- Previously compacted context:");
    previousHighlights.forEach((l) => lines.push(`  ${l}`));
  }

  if (newHighlights.length > 0) {
    lines.push("- Newly compacted context:");
    newHighlights.forEach((l) => lines.push(`  ${l}`));
  }

  if (newTimeline.length > 0) {
    lines.push("- Key timeline:");
    newTimeline.forEach((l) => lines.push(`  ${l}`));
  }

  lines.push("</summary>");
  return lines.join("\n");
}

// ─── 格式化 ─────────────────────────────────────────────────────────

/**
 * 去掉 <analysis> 标签，保留 <summary> 内容
 * 将 <summary>...</summary> 转换为 "Summary:\n..."
 */
export function formatCompactSummary(summary: string): string {
  const withoutAnalysis = stripTagBlock(summary, "analysis");
  const content = extractTagBlock(withoutAnalysis, "summary");

  let formatted: string;
  if (content) {
    formatted = withoutAnalysis.replace(
      `<summary>${content}</summary>`,
      `Summary:\n${content.trim()}`,
    );
  } else {
    formatted = withoutAnalysis;
  }

  return collapseBlankLines(formatted.trim());
}

/**
 * 续接消息前缀（粘贴到 system prompt 开头）
 */
const COMPACT_CONTINUATION_PREAMBLE =
  "This session is being continued from a previous conversation that ran out of context. The summary below covers the earlier portion of the conversation.\n\n";
const COMPACT_RECENT_MESSAGES_NOTE = "Recent messages are preserved verbatim.";
const COMPACT_DIRECT_RESUME_INSTRUCTION =
  "Continue the conversation from where it left off without asking the user any further questions. Resume directly — do not acknowledge the summary, do not recap what was happening, and do not preface with continuation text.";

export function getCompactContinuationMessage(
  summary: string,
  suppressFollowUpQuestions: boolean,
  recentMessagesPreserved: boolean,
): string {
  let base =
    COMPACT_CONTINUATION_PREAMBLE + formatCompactSummary(summary);

  if (recentMessagesPreserved) {
    base += "\n\n" + COMPACT_RECENT_MESSAGES_NOTE;
  }

  if (suppressFollowUpQuestions) {
    base += "\n" + COMPACT_DIRECT_RESUME_INSTRUCTION;
  }

  return base;
}

// ─── 辅助函数 ───────────────────────────────────────────────────────

function estimateMessageTokens(message: ConversationMessage): number {
  return message.blocks.reduce((sum, block) => {
    if (block.type === "text") {
      return sum + Math.floor((block.text?.length ?? 0) / 4) + 1;
    }
    if (block.type === "tool_use") {
      return (
        sum +
        Math.floor(
          ((block.tool_name?.length ?? 0) +
            (block.tool_input?.length ?? 0)) /
            4,
        ) +
        1
      );
    }
    if (block.type === "tool_result") {
      return (
        sum +
        Math.floor(
          ((block.tool_name?.length ?? 0) +
            (block.tool_output?.length ?? 0)) /
            4,
        ) +
        1
      );
    }
    return sum;
  }, 0);
}

function compactedSummaryPrefixLen(session: Session): number {
  return extractExistingCompactedSummary(session) ? 1 : 0;
}

function summarizeBlock(block: ContentBlock): string {
  let raw: string;
  if (block.type === "text") {
    raw = block.text ?? "";
  } else if (block.type === "tool_use") {
    raw = `tool_use ${block.tool_name}(${block.tool_input ?? ""})`;
  } else {
    const err = block.is_error ? "error " : "";
    raw = `tool_result ${block.tool_name}: ${err}${block.tool_output ?? ""}`;
  }
  return truncateSummary(raw, DEFAULT_CONFIG.summary_truncate_chars);
}

function firstTextBlock(message: ConversationMessage): string | null {
  for (const block of message.blocks) {
    if (block.type === "text" && block.text?.trim()) {
      return block.text;
    }
  }
  return null;
}

function collectRecentRoleSummaries(
  messages: ConversationMessage[],
  role: MessageRole,
  limit: number,
  maxChars: number,
): string[] {
  return messages
    .filter((m) => m.role === role)
    .reverse()
    .map(firstTextBlock)
    .filter((t): t is string => t !== null)
    .slice(0, limit)
    .map((t) => truncateSummary(t, maxChars))
    .reverse();
}

const PENDING_KEYWORDS = [
  "todo",
  "next",
  "pending",
  "follow up",
  "remaining",
];

function inferPendingWork(
  messages: ConversationMessage[],
  maxChars: number,
): string[] {
  return messages
    .slice()
    .reverse()
    .map(firstTextBlock)
    .filter((t): t is string =>
      t !== null && PENDING_KEYWORDS.some((k) => t.toLowerCase().includes(k)),
    )
    .slice(0, 3)
    .reverse()
    .map((t) => truncateSummary(t, maxChars));
}

function collectKeyFiles(messages: ConversationMessage[]): string[] {
  const INTERESTING_EXTENSIONS = [
    "md",
    "ts",
    "tsx",
    "js",
    "json",
    "rs",
    "py",
  ];

  const candidates = messages.flatMap((m) =>
    m.blocks.flatMap((b) => {
      if (b.type === "text") return [b.text ?? ""];
      if (b.type === "tool_use") return [b.tool_input ?? ""];
      if (b.type === "tool_result") return [b.tool_output ?? ""];
      return [];
    }),
  );

  const files: string[] = [];
  for (const content of candidates) {
    for (const token of content.split(/\s+/)) {
      const clean = token.replace(/[,.:;()'"`]/g, "");
      if (
        clean.includes("/") &&
        INTERESTING_EXTENSIONS.some((ext) =>
          clean.toLowerCase().endsWith(`.${ext}`),
        )
      ) {
        files.push(clean);
      }
    }
  }

  return [...new Set(files)].slice(0, 8);
}

function inferCurrentWork(
  messages: ConversationMessage[],
  maxChars: number,
): string | null {
  for (const msg of [...messages].reverse()) {
    const text = firstTextBlock(msg);
    if (text?.trim()) {
      return truncateSummary(text, maxChars);
    }
  }
  return null;
}

function truncateSummary(content: string, maxChars: number): string {
  if (content.length <= maxChars) return content;
  return content.slice(0, maxChars) + "…";
}

function extractTagBlock(content: string, tag: string): string | null {
  const startTag = `<${tag}>`;
  const endTag = `</${tag}>`;
  const startIndex = content.indexOf(startTag);
  if (startIndex === -1) return null;
  const endIndex = content.indexOf(endTag, startIndex + startTag.length);
  if (endIndex === -1) return null;
  return content.slice(startIndex + startTag.length, endIndex);
}

function stripTagBlock(content: string, tag: string): string {
  const startTag = `<${tag}>`;
  const endTag = `</${tag}>`;
  const startIndex = content.indexOf(startTag);
  if (startIndex === -1) return content;
  const endIndex = content.indexOf(endTag, startIndex);
  if (endIndex === -1) return content;
  return content.slice(0, startIndex) + content.slice(endIndex + endTag.length);
}

function collapseBlankLines(content: string): string {
  const lines = content.split("\n");
  const result: string[] = [];
  let lastBlank = false;
  for (const line of lines) {
    const isBlank = line.trim() === "";
    if (isBlank && lastBlank) continue;
    result.push(line);
    lastBlank = isBlank;
  }
  return result.join("\n");
}

function extractExistingCompactedSummary(session: Session): string | null {
  const first = session.messages[0];
  if (!first || first.role !== "system") return null;

  const text = firstTextBlock(first);
  if (!text) return null;

  const prefix = COMPACT_CONTINUATION_PREAMBLE.trimEnd();
  const summary = text.startsWith(prefix)
    ? text.slice(prefix.length)
    : text;

  return summary
    .split(`\n\n${COMPACT_RECENT_MESSAGES_NOTE}`)[0]
    .split(`\n${COMPACT_DIRECT_RESUME_INSTRUCTION}`)[0]
    .trim();
}

function extractSummaryHighlights(summary: string): string[] {
  const formatted = formatCompactSummary(summary);
  const lines = formatted.split("\n");
  const highlights: string[] = [];
  let inTimeline = false;

  for (const line of lines) {
    const trimmed = line.trimEnd();
    if (
      trimmed === "" ||
      trimmed === "Summary:" ||
      trimmed === "Conversation summary:"
    )
      continue;
    if (trimmed === "- Key timeline:") {
      inTimeline = true;
      continue;
    }
    if (inTimeline) continue;
    highlights.push(trimmed);
  }

  return highlights;
}

function extractSummaryTimeline(summary: string): string[] {
  const formatted = formatCompactSummary(summary);
  const lines = formatted.split("\n");
  const timeline: string[] = [];
  let inTimeline = false;

  for (const line of lines) {
    const trimmed = line.trimEnd();
    if (trimmed === "- Key timeline:") {
      inTimeline = true;
      continue;
    }
    if (!inTimeline) continue;
    if (trimmed === "") break;
    timeline.push(trimmed);
  }

  return timeline;
}

// ─── CLI ─────────────────────────────────────────────────────────────

async function readInput(path: string): Promise<string> {
  const rl = readline.createInterface({
    input: fs.createReadStream(path),
    crlfDelay: Infinity,
  });
  const lines: string[] = [];
  for await (const line of rl) lines.push(line);
  return lines.join("\n");
}

async function main() {
  const args = process.argv.slice(2);
  const inputPath = args[0] ?? ".claude/sessions/current.json";
  const outputPath = args[1] ?? ".claude/sessions/compacted.md";

  if (!fs.existsSync(inputPath)) {
    // 尝试读取 Markdown 会话文件（plain text 格式）
    if (fs.existsSync(inputPath.replace(".json", ".md"))) {
      const mdPath = inputPath.replace(".json", ".md");
      const raw = await readInput(mdPath);
      // 从 Markdown 中解析消息（简化版）
      const session: Session = {
        version: 1,
        messages: raw
          .split(/(?=^## (user|assistant|tool|system):?)/gm)
          .filter(Boolean)
          .map((block) => {
            const roleMatch = block.match(/^## (\w+):?/);
            const role = (roleMatch?.[1] ?? "user") as MessageRole;
            const content = block.replace(/^## \w+:?\n?/, "");
            return {
              role,
              blocks: [{ type: "text", text: content }] as ContentBlock[],
              usage: null,
            };
          }),
      };

      const result = compactSession(session);
      if (result.removed_message_count === 0) {
        console.log("No compaction needed. Session is within limits.");
        return;
      }

      const summaryMd = `<!-- COMPACTED SUMMARY -->\n\n${result.formatted_summary}`;
      fs.mkdirSync(path.dirname(outputPath), { recursive: true });
      fs.writeFileSync(outputPath, summaryMd);
      console.log(
        `Compressed ${result.removed_message_count} messages. Summary written to ${outputPath}`,
      );
      return;
    }
    console.error(`Input file not found: ${inputPath}`);
    process.exit(1);
  }

  const raw = fs.readFileSync(inputPath, "utf-8");
  const session: Session = JSON.parse(raw);

  const result = compactSession(session);

  if (result.removed_message_count === 0) {
    console.log("No compaction needed.");
    return;
  }

  console.log(`=== Compaction Summary ===`);
  console.log(result.formatted_summary);
  console.log(`\nRemoved: ${result.removed_message_count} messages`);

  // 写入 compacted session JSON
  const compactedPath = inputPath.replace(
    /\.json$/,
    `.compacted-${Date.now()}.json`,
  );
  fs.writeFileSync(compactedPath, JSON.stringify(result.compacted_session, null, 2));
  console.log(`Compacted session saved to: ${compactedPath}`);

  // 写入 summary Markdown（供人类阅读 + 粘贴到 MEMORY.md）
  const summaryMd = `<!-- COMPACTED ${new Date().toISOString()} — ${result.removed_message_count} messages removed -->\n\n${result.formatted_summary}`;
  fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  fs.writeFileSync(outputPath, summaryMd);
  console.log(`Summary written to: ${outputPath}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
