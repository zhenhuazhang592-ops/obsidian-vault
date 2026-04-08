#!/usr/bin/env python3
"""
prompt_optimizer.py — huage888 统一提示词优化层

对标 prompt-optimizer-develop 的核心能力，Port 为纯 Python 实现：

1. T2I 七维度重写（image-general-optimize）
2. I2I 四意图重写（image2image-optimize）
3. 视频 prompt 增强（video-enhanced-optimize）
4. System/User prompt 结构化（general-optimize / analytical-optimize）
5. 5 维度质量评估

用法：
  python3 config/prompt_optimizer.py optimize "漠玫在竹林中睁眼" --mode t2i
  python3 config/prompt_optimizer.py evaluate "A cyber bamboo forest"
  python3 config/prompt_optimizer.py batch shots.json --mode t2i

模块调用：
  from config.prompt_optimizer import PromptOptimizer
  opt = PromptOptimizer()
  improved = opt.optimize(raw_prompt, mode="t2i")
  scores  = opt.evaluate(improved)
"""

import json
import re
import sys
import os
from pathlib import Path
from typing import Optional

# ── 路径配置 ─────────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).parent.parent
QWEN_PIPELINE = BASE_DIR / "config" / "qwen_pipeline.py"


# ═══════════════════════════════════════════════════════════════════════════════
# 模板库（Port 自 prompt-optimizer-develop TypeScript 模板）
# ═══════════════════════════════════════════════════════════════════════════════

# Evidence 协议：零宽字符包裹原始 prompt，防止内容中有 {{ }} 被误解释
_EVIDENCE_WRAP = "\u0001{}\u0001"  # \u0001 = SOH，控制字符不干扰 LLM


def _wrap_evidence(prompt: str) -> str:
    """用零宽字符包裹 prompt，防止 prompt 内容干扰模板变量语法"""
    return _EVIDENCE_WRAP.format(prompt)


# ─────────────────────────────────────────────────────────────────────────────
# T2I 七维度优化模板（image-general-optimize）
# ─────────────────────────────────────────────────────────────────────────────

T2I_SYSTEM = """You are a professional image prompt optimizer.

TASK: Rewrite the user's raw image prompt into a structured 7-dimension English prompt for AI image generation (Doubao Seedream / Kling / Midjourney).

STRUCTURE — Write exactly 7 sentences, one per dimension:

  Sentence 1 — SUBJECT + ACTION + ENVIRONMENT ANCHOR
    Core subject with main action, environmental context anchor.
    Example: A Taoist maiden with a top-knot slowly opens her golden eyes in a misty bamboo forest.

  Sentence 2 — LIGHTING + TIME + COLOR PALETTE
    Light source direction, quality, time-of-day, primary and accent colors.
    Example: Backlit by deep teal dusk, warm golden rim light on her hair, cool shadow fill.

  Sentence 3 — MOOD + ABSTRACT STYLE KEYWORDS
    Emotional atmosphere, overall artistic style keywords.
    Example: Contemplative, solemn atmosphere. Cyber Ink painting style, Chinese ink wash texture.

  Sentence 4 — MATERIAL + TEXTURE
    Texture of key surfaces (skin, fabric, metal, natural materials).
    Example: Silk robes with micro circuit-board embossing texture, jade pendant glowing softly.

  Sentence 5 — COMPOSITION + VIEWPOINT + ASPECT RATIO
    Camera angle, framing, visual weight distribution, aspect ratio.
    Example: Low-angle medium close-up, rule-of-thirds composition, 16:9 cinematic.

  Sentence 6 — NARRATIVE TENSION + VISUAL METAPHOR
    Storytelling tension point, symbolic visual element.
    Example: Data particles stream from her golden irises like liquid light, frozen mid-flow.

  Sentence 7 — DYNAMIC FREEZE-FRAME
    A single decisive moment, the "just as / right when" capture.
    Example: Freeze-frame: right as her eyes open fully, pupils still dilating.

CONSTRAINTS:
- Output MUST be English only.
- Each dimension = exactly 1 sentence. No extra sentences.
- No parameters, no ( ), no weight syntax like (keyword:1.2).
- No negative prompts in this output.
- Preserve the core intent of the original prompt.
- If the original contains character/scene names, keep them verbatim.
- Merge duplicate information from multiple sentences into one.

OUTPUT FORMAT: Just output the 7 sentences, separated by newlines. No preamble."""


# ─────────────────────────────────────────────────────────────────────────────
# I2I 四意图优化模板（image2image-optimize）
# ─────────────────────────────────────────────────────────────────────────────

I2I_SYSTEM = """You are a professional image-editing prompt optimizer.

TASK: Given a source image description and an edit intent, rewrite into a precise English edit prompt for AI image-to-image generation.

EDIT INTENT CLASSIFICATION — identify the user's intent first:

  ADD     → The user wants to add new elements NOT present in the source.
            Write: Describe the NEW element: position/placement, size/proportion,
            appearance, and relationship to existing elements.
            Rule: Elements not mentioned are PRESERVED from the source.

  DELETE  → The user explicitly wants to remove something.
            Write: Describe what to remove and how the scene naturally fills the gap.
            Rule: Everything else is PRESERVED from the source.

  REPLACE → The user wants to transform/change something.
            Write: State the SCOPE of change and the NEW characteristics.
            Rule: Everything outside the scope is PRESERVED.

  ENHANCE → The user wants to intensify existing features.
            Write: Name the specific aspect and the degree of enhancement.
            Rule: All other elements stay exactly the same.

DEFAULT (no intent specified): Apply ENHANCE to the most impactful elements.

OUTPUT FORMAT:
  Line 1 — OPERATION: [ADD / DELETE / REPLACE / ENHANCE]
  Line 2 — EDIT PROMPT: [2-4 English sentences describing the edit]

CONSTRAINTS:
- English only.
- No weight syntax (keyword:1.2) or parameters.
- Default-preservation: elements NOT mentioned are kept unchanged.
- Preserve all specific names (character names, scene names) verbatim."""



# ─────────────────────────────────────────────────────────────────────────────
# 视频 prompt 增强模板
# ─────────────────────────────────────────────────────────────────────────────

VIDEO_SYSTEM = """You are a professional video generation prompt optimizer.

TASK: Rewrite the user's image description into a video prompt suitable for Doubao/Kling/Jimeng video generation models.

REQUIRED COMPONENTS (include ALL of the following):

  1. SUBJECT MOTION (≥3 verbs)
     Primary subject action described with motion verbs (e.g., opens eyes slowly, hair drifts, jade pendant sways).

  2. CAMERA MOVEMENT
     Choose ONE: slow push-in / slow pull-out / slow tracking / static fixed shot / gentle pan / zoom-in / zoom-out
     Default: slow push-in if not specified.

  3. SCENE MOTION
     Background/subtle scene movement (e.g., mist drifts through bamboo, particles float upward, light flickers).

  4. ART STYLE MANDATE
     Explicit style keywords: [Cyber Ink painting, ink wash, teal-gold palette, cinematic lighting]

  5. DURATION SIGNAL
     Infer 5s or 10s based on prompt complexity.
     5s = single action, single camera move
     10s = multiple actions, scene transition

OUTPUT FORMAT: Single paragraph, ≤200 words English. No lists.

Example output:
  A Taoist maiden slowly opens her golden eyes. Her long black hair drifts in the ambient breeze. Jade pendant sways gently at her waist. Data particles stream from her irises like liquid gold. Camera performs a slow push-in from medium to close-up. Cyber bamboo forest background: mist drifts between bamboo stalks, teal bioluminescent particles float upward. Cyber Ink painting style, blue-teal glow rim light, cinematic depth of field. 5s loop.

CONSTRAINTS:
- English only.
- Exactly ≥3 motion verbs describing subject action.
- Specify camera movement explicitly.
- Keep ≤200 words.
- No weight syntax."""


# ─────────────────────────────────────────────────────────────────────────────
# System Prompt 结构化优化（general-optimize）
# ─────────────────────────────────────────────────────────────────────────────

SYSTEM_GENERAL_SYSTEM = """You are a professional system prompt architect.

TASK: Rewrite the user's raw system prompt into a structured LangGPT-style prompt.

OUTPUT FORMAT:
  # Role: [One-line role definition]

  ## Profile
  - Language: [ZH-CN or EN]
  - Description: [2-3 sentences]

  ## Skills
  1. [Skill 1]
  2. [Skill 2]
  ...

  ## Rules
  - [Rule 1 — concrete and actionable]
  - [Rule 2]
  ...

  ## Workflows
  1. [Step-by-step workflow, numbered]
  2. ...

  ## Initialization
  [One sentence — how the agent introduces itself]

CONSTRAINTS:
- Each section must be substantive (no empty sections).
- Rules must be concrete and verifiable (not vague principles).
- If the original contains hard constraints (e.g., "never do X"), preserve them verbatim.
- Output in the same language as the original prompt.
- Maximum 500 words total."""


# ─────────────────────────────────────────────────────────────────────────────
# System Prompt 深度分析优化（analytical-optimize）
# ─────────────────────────────────────────────────────────────────────────────

SYSTEM_ANALYTICAL_SYSTEM = """You are a professional system prompt architect and critic.

TASK: Perform a deep analysis of the user's system prompt, then produce an optimized version.

ANALYSIS — evaluate the prompt on these 8 dimensions:
  1. Role clarity: Is the role well-defined?
  2. Background sufficiency: Is enough context provided?
  3. Skill coverage: Are all needed skills listed?
  4. Goal alignment: Does the prompt serve its intended purpose?
  5. Constraint completeness: Are all hard constraints stated?
  6. Workflow clarity: Is the process clear and non-circular?
  7. Output format clarity: Is the output format unambiguous?
  8. Ambiguity points: What could be misinterpreted?

OUTPUT FORMAT:
  ## Analysis
  [8 bullet points, one per dimension above]

  ## Optimized Prompt
  [Structured LangGPT prompt — see format below]

  ### Format
  # Role: [role]

  ## Background
  [Context and situation]

  ## Attention
  [Critical warnings and hard constraints]

  ## Profile
  - Language: [ZH-CN or EN]
  - [Key attributes]

  ### Skills
  1. [Skill]
  ...

  ## Goals
  [What success looks like]

  ## Constrains
  - [Hard constraints]
  ...

  ## Workflow
  1. [Step 1]
  2. [Step 2]
  ...

  ## OutputFormat
  [Expected output structure]

  ## Suggestions
  [Internal working notes for the model — not shown to user]

CONSTRAINTS:
- Analysis section: be specific, cite examples from the original.
- Output ≤800 words.
- Same language as original."""


# ─────────────────────────────────────────────────────────────────────────────
# User Prompt 专业优化（user-prompt-professional）
# ─────────────────────────────────────────────────────────────────────────────

USER_PROFESSIONAL_SYSTEM = """You are a professional prompt engineer.

TASK: Transform vague, generic user prompts into precise, specific, actionable prompts.

PRINCIPLES:
  - Replace vague adjectives with specific parameters (e.g., "好看" → "warm golden lighting, teal shadows")
  - Add missing context that affects the output (time, place, audience, platform)
  - Break compound requests into explicit sub-components
  - Define success criteria if not stated
  - Remove redundant or contradictory instructions

OUTPUT FORMAT:
  [Rewritten prompt — same language as original]

CONSTRAINTS:
- Preserve the core intent exactly.
- Do NOT add new intent not in the original.
- Add concrete details only where the original is vague.
- Output ≤300 words.
- If the original is already specific, return it unchanged."""


# ─────────────────────────────────────────────────────────────────────────────
# 5 维度评估模板
# ─────────────────────────────────────────────────────────────────────────────

EVAL_SYSTEM = """You are a professional prompt evaluator.

TASK: Evaluate the user's prompt and output a structured JSON score.

EVALUATION DIMENSIONS (all scored 0-100):

  1. goalClarity — 目标清晰度
     Is the goal unambiguous and specific?
     0 = completely vague, 100 = perfectly clear

  2. instructionCompleteness — 指令完备度
     Are all necessary instructions present?
     0 = missing critical info, 100 = fully complete

  3. structuralExecutability — 结构可执行性
     Can an AI follow this structurally without ambiguity?
     0 = contradictory or circular, 100 = linear and clear

  4. ambiguityControl — 歧义控制
     Are vague words avoided? Are constraints specific?
     0 = many ambiguous terms, 100 = no ambiguity

  5. robustness — 稳健性
     Does the prompt handle edge cases? Is it self-contained?
     0 = requires external context, 100 = fully self-contained

OUTPUT FORMAT — output ONLY valid JSON, no markdown, no explanation:

{
  "score": {
    "overall": [0-100],
    "dimensions": {
      "goalClarity": [0-100],
      "instructionCompleteness": [0-100],
      "structuralExecutability": [0-100],
      "ambiguityControl": [0-100],
      "robustness": [0-100]
    }
  },
  "improvements": [
    "[Improvement 1 — concrete action]",
    "[Improvement 2]"
  ],
  "summary": "[One-sentence overall verdict]"
}

CONSTRAINTS:
- Output ONLY the JSON. No preamble, no explanation.
- Scores must be integers 0-100.
- improvements array: 0-3 items, each a specific actionable improvement.
- summary: one sentence, same language as the evaluated prompt."""


# ═══════════════════════════════════════════════════════════════════════════════
# PromptOptimizer 核心类
# ═══════════════════════════════════════════════════════════════════════════════

class PromptOptimizer:
    """
    huage888 统一提示词优化层

    用法：
      opt = PromptOptimizer()
      improved = opt.optimize("raw prompt", mode="t2i")
      scores   = opt.evaluate("improved prompt")
      batch    = opt.optimize_batch(["p1", "p2"], mode="t2i")

    模型选择：
      optimize()   → qwen-plus（速度优先，成本低）
      evaluate()    → qwen-plus（评分不需要 qwen-max）
      batch()       → qwen-plus，串行调用

    集成开关（全局环境变量）：
      HUAGE888_OPTIMIZE_T2I=1   → generate_shot_images.py 自动优化 imagePrompt
      HUAGE888_OPTIMIZE_VIDEO=1  → video_pipeline.py 自动优化 libtvPrompt
    """

    MODES = {
        "t2i":        {"system": T2I_SYSTEM,             "desc": "图生图七维度"},
        "i2i":        {"system": I2I_SYSTEM,             "desc": "图生图四意图"},
        "video":      {"system": VIDEO_SYSTEM,            "desc": "视频prompt增强"},
        "system":     {"system": SYSTEM_GENERAL_SYSTEM,   "desc": "System prompt结构化"},
        "system-deep":{"system": SYSTEM_ANALYTICAL_SYSTEM, "desc": "System prompt深度分析"},
        "user":       {"system": USER_PROFESSIONAL_SYSTEM,"desc": "User prompt专业优化"},
        "eval":       {"system": EVAL_SYSTEM,             "desc": "5维度评估"},
    }

    def __init__(
        self,
        model: str = "qwen-plus",
        optimize_model: str | None = None,
        eval_model: str | None = None,
    ):
        """
        Args:
            model:          默认模型（optimize + evaluate 共用）
            optimize_model: 覆盖 optimize 专用模型（默认同 model）
            eval_model:     覆盖 evaluate 专用模型（默认同 model）
        """
        self.default_model = model
        self.optimize_model = optimize_model or model
        self.eval_model = eval_model or model

    # ── 核心方法 ──────────────────────────────────────────────────────────────

    def optimize(
        self,
        prompt: str,
        mode: str = "t2i",
        model: str | None = None,
        dry_run: bool = False,
    ) -> str:
        """
        优化单个 prompt

        Args:
            prompt:   原始 prompt
            mode:     t2i | i2i | video | system | system-deep | user
            model:    可覆盖默认模型
            dry_run:  不调 API，只返回模板 system prompt（用于调试）

        Returns:
            优化后的 prompt 字符串
        """
        if mode not in self.MODES:
            raise ValueError(f"不支持的模式: {mode}，可用: {list(self.MODES.keys())}")

        tpl = self.MODES[mode]
        system = tpl["system"]

        if dry_run:
            return f"[DRY][{mode}] {prompt}"

        # Evidence 包裹，防止 prompt 内容干扰
        evidence_prompt = _wrap_evidence(prompt)

        # 构建 user message
        user_msg = f"原始提示词：\n{evidence_prompt}"

        model = model or self.optimize_model
        raw = self._call_qwen(system, user_msg, model=model)

        # 清理零宽字符
        result = raw.replace("\u0001", "").strip()
        return result

    def optimize_batch(
        self,
        prompts: list[str],
        mode: str = "t2i",
        model: str | None = None,
        dry_run: bool = False,
    ) -> list[str]:
        """
        批量优化多个 prompt（串行）

        Returns:
            与输入等长的结果列表（顺序对应）
        """
        results = []
        for i, p in enumerate(prompts):
            try:
                result = self.optimize(p, mode=mode, model=model, dry_run=dry_run)
                results.append(result)
            except Exception as e:
                print(f"  [WARN] prompt {i+1}/{len(prompts)} 失败: {e}", file=sys.stderr)
                results.append(p)  # 失败时返回原文
        return results

    def evaluate(self, prompt: str) -> dict:
        """
        5 维度评估 prompt

        Returns:
            {
              "score": {
                "overall": 0-100,
                "dimensions": {
                  "goalClarity": 0-100,
                  "instructionCompleteness": 0-100,
                  "structuralExecutability": 0-100,
                  "ambiguityControl": 0-100,
                  "robustness": 0-100
                }
              },
              "improvements": [...],
              "summary": "..."
            }
        """
        evidence_prompt = _wrap_evidence(prompt)
        user_msg = f"请评估以下提示词：\n{evidence_prompt}"
        raw = self._call_qwen(EVAL_SYSTEM, user_msg, model=self.eval_model)

        # 清理零宽字符
        raw = raw.replace("\u0001", "").strip()

        # 提取 JSON（可能在 LLM 输出前后有 markdown 块）
        json_str = self._extract_json(raw)
        return json.loads(json_str)

    # ── 辅助方法 ──────────────────────────────────────────────────────────────

    def _call_qwen(self, system: str, user: str, model: str) -> str:
        """调用 qwen_pipeline.py（--system 模式，不走 agent 文件）"""
        if not QWEN_PIPELINE.exists():
            raise RuntimeError(f"qwen_pipeline.py 不存在: {QWEN_PIPELINE}")

        import subprocess

        cmd = [
            sys.executable,
            str(QWEN_PIPELINE),
            "--system", system,        # 直接传 system prompt（覆盖 agent 文件）
            "--user", user,
            "--model", model,
            "--temperature", "0.3",   # 优化任务低温度，结果稳定
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            raise RuntimeError(f"qwen_pipeline 调用失败: {result.stderr[:300]}")
        content = result.stdout.strip()
        if not content:
            raise RuntimeError("qwen_pipeline 返回为空")
        return content

    def _extract_json(self, text: str) -> str:
        """从 LLM 输出中提取 JSON（支持 markdown 包裹）"""
        text = text.strip()

        # 尝试直接解析
        try:
            json.loads(text)
            return text
        except ValueError:
            pass

        # 尝试从 markdown 块提取
        match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
        if match:
            return match.group(1).strip()

        # 尝试找到第一个 { 到最后一个 }
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return text[start:end + 1]

        raise ValueError(f"无法从输出中提取 JSON: {text[:200]}")

    def list_modes(self) -> dict[str, str]:
        """列出所有可用模式"""
        return {k: v["desc"] for k, v in self.MODES.items()}


# ═══════════════════════════════════════════════════════════════════════════════
# 全局便捷函数（集成点）
# ═══════════════════════════════════════════════════════════════════════════════

# 缓存单例（避免重复初始化）
_optimizer: PromptOptimizer | None = None


def get_optimizer() -> PromptOptimizer:
    """获取全局 PromptOptimizer 单例"""
    global _optimizer
    if _optimizer is None:
        _optimizer = PromptOptimizer()
    return _optimizer


def optimize_t2i(prompt: str, **kwargs) -> str:
    """快捷函数：优化图生图 prompt"""
    return get_optimizer().optimize(prompt, mode="t2i", **kwargs)


def optimize_video(prompt: str, **kwargs) -> str:
    """快捷函数：优化视频 prompt"""
    return get_optimizer().optimize(prompt, mode="video", **kwargs)


def optimize_i2i(prompt: str, **kwargs) -> str:
    """快捷函数：优化图生图编辑 prompt"""
    return get_optimizer().optimize(prompt, mode="i2i", **kwargs)


# ─────────────────────────────────────────────────────────────────────────────
# CLI 入口
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="huage888 提示词优化器")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # optimize 命令
    p_opt = sub.add_parser("optimize", help="优化单个 prompt")
    p_opt.add_argument("prompt", help="原始 prompt")
    p_opt.add_argument("--mode", "-m", default="t2i",
                       choices=["t2i", "i2i", "video", "system", "system-deep", "user"],
                       help="优化模式")
    p_opt.add_argument("--model", default=None, help="指定模型")
    p_opt.add_argument("--dry-run", action="store_true", help="不调 API")

    # batch 命令
    p_batch = sub.add_parser("batch", help="批量优化")
    p_batch.add_argument("file", help="JSON 文件（含 prompts: list[str]）")
    p_batch.add_argument("--mode", "-m", default="t2i",
                         choices=["t2i", "i2i", "video", "system", "system-deep", "user"])
    p_batch.add_argument("--output", "-o", help="输出 JSON 文件")

    # evaluate 命令
    p_eval = sub.add_parser("evaluate", help="5维度评估")
    p_eval.add_argument("prompt", help="待评估 prompt")

    # list 命令
    sub.add_parser("list", help="列出所有模式")

    args = parser.parse_args()

    if args.cmd == "list":
        opt = PromptOptimizer()
        for mode, desc in opt.list_modes().items():
            print(f"  {mode:15s} — {desc}")

    elif args.cmd == "optimize":
        opt = PromptOptimizer()
        result = opt.optimize(args.prompt, mode=args.mode, model=args.model, dry_run=args.dry_run)
        print(result)

    elif args.cmd == "batch":
        with open(args.file) as f:
            data = json.load(f)
        prompts = data.get("prompts", data) if isinstance(data, dict) else data

        opt = PromptOptimizer()
        results = opt.optimize_batch(prompts, mode=args.mode)

        output = {"results": results}
        if args.output:
            with open(args.output, "w") as f:
                json.dump(output, f, ensure_ascii=False, indent=2)
            print(f"✅ 已写入: {args.output}")
        else:
            for i, r in enumerate(results):
                print(f"\n--- prompt {i+1} ---")
                print(r)

    elif args.cmd == "evaluate":
        opt = PromptOptimizer()
        result = opt.evaluate(args.prompt)
        print(json.dumps(result, ensure_ascii=False, indent=2))
