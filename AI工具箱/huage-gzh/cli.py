#!/usr/bin/env python3
# huage-gzh CLI - 公众号多Agent协同创作系统
# M2: 完整创作流程 + 用户确认节点

import argparse
import json
import os
import sys
import time
from pathlib import Path

from core import MessageHub, MessageType
from core.llm_client import create_llm_client
from agents import StyleLearnerAgent, PlannerAgent, OutlineAgent, WriterAgent, PolisherAgent
from core.review_gate import review_article


def print_header():
    print("=" * 60)
    print("  公众号多Agent协同创作系统 v0.3")
    print("=" * 60)


def print_status(agent: str, status: str, details: str = ""):
    emoji = {
        "started": "🔄",
        "completed": "✅",
        "failed": "❌",
        "pending": "⏳",
        "running": "⚙️",
    }.get(status, "📌")
    print(f"{emoji} [{agent}] {status.upper()}")
    if details:
        print(f"   {details}")


# ────────────────────────────────────────────────────────────────
# 冷启动（复用）
# ────────────────────────────────────────────────────────────────

SAMPLE_ARTICLE = """---
title: "【示例文章】AI工具链实战：从入门到精通"
date: 2026-01-15
tags: [AI, 工具, 实战]
---

# 【示例文章】AI工具链实战：从入门到精通

坦白说，这篇文章是给我自己写的。

## 一、为什么你需要这套工具链？

搞AI应用开发，最费时间的是什么？

不是写代码，是环境配置、版本兼容、上下文丢失。

我前前后后折腾了三个月，才把整套流程跑通。今天把这个过程捋一捋，你照着做，半小时就能跑起来。

## 二、我的工具链长什么样

先说我的技术栈：

- **模型**：Claude Code（主力）+ DeepSeek（推理）
- **框架**：TypeScript + Rust（核心模块）
- **存储**：Obsidian Vault（知识库）+ SQLite（项目数据）

这套组合不是我拍脑袋想的，是在实际项目里磨出来的。

## 三、具体怎么配置

### 第一步：环境准备

```bash
# 安装 Claude Code
npm install -g @anthropic/claude-code

# 配置 API Key
export ANTHROPIC_API_KEY=your_key_here
```

### 第二步：验证安装

```bash
claude --version
```

看到版本号就说明装好了。

## 四、实际效果

用了这套工具链之后，我的开发流程变成了这样：

1. 早上想一个选题
2. Claude帮我搜集资料、做大纲
3. 我审核之后，它写初稿
4. 我润色，发布

以前一天写一篇，现在可以写三篇。

当然，这不是躺平的理由。

## 五、总结

工具只是工具，关键还是用工具的人。

但好的工具，确实能让你把精力放在更重要的事情上。

---

配图：工具链流程图
"""

DEFAULT_ARTICLE_DIR = Path(__file__).resolve().parent.parent / "已发布文章参考库"


def check_cold_start(article_dir: Path) -> dict:
    if not article_dir.exists():
        return {
            "status": "no_dir",
            "dir": article_dir,
            "article_count": 0,
            "message": f"📁 文章目录不存在: {article_dir}",
        }

    md_files = list(article_dir.glob("*.md"))
    if not md_files:
        return {
            "status": "empty_dir",
            "dir": article_dir,
            "article_count": 0,
            "message": f"📂 目录为空: {article_dir}",
        }

    return {
        "status": "warm",
        "dir": article_dir,
        "article_count": len(md_files),
        "message": f"✅ 已找到 {len(md_files)} 篇已发布文章",
    }


def run_cold_start_wizard(article_dir: Path) -> bool:
    print()
    print("=" * 60)
    print("🧊 冷启动引导")
    print("=" * 60)
    print()
    print("首次使用需要提供已发布文章样本，")
    print("系统会学习你的写作风格，生成个性化写作指令。")
    print()
    print(f"📂 建议文章目录: {article_dir}")
    print()
    print("操作方式：")
    print("  1. 将已发布的公众号文章（Markdown格式）放入目录")
    print(f"  2. 放好后重新运行: huage-gzh style")
    print()
    print("─" * 40)
    print("要不要我帮你创建一个示例文章？")
    print("（示例文章仅用于测试风格学习功能，之后请替换为你的真实文章）")
    print()
    choice = input("输入 y 创建示例文章，其他跳过: ").strip().lower()
    print()

    if choice != "y":
        print("好的，你可以手动放入文章后重新运行。")
        return False

    article_dir.mkdir(parents=True, exist_ok=True)
    sample_path = article_dir / "示例文章-请替换为你的真实文章.md"
    sample_path.write_text(SAMPLE_ARTICLE, encoding="utf-8")

    print(f"✅ 示例文章已创建: {sample_path}")
    print()
    print("请替换为你的真实文章后，重新运行:")
    print("  huage-gzh style")
    print()
    return True


# ────────────────────────────────────────────────────────────────
# 实时状态订阅
# ────────────────────────────────────────────────────────────────

def create_status_printer() -> tuple[MessageHub, callable]:
    hub = MessageHub()

    def on_status(msg):
        content = msg.content or {}
        agent = content.get("agent", msg.agent)
        status = content.get("status", "unknown")
        progress = content.get("progress", "")
        print_status(agent, status, progress if progress else "")

    hub.subscribe(MessageType.STATUS, on_status)

    def cleanup():
        hub.unsubscribe(MessageType.STATUS, on_status)

    return hub, cleanup


# ────────────────────────────────────────────────────────────────
# 风格指纹加载
# ────────────────────────────────────────────────────────────────

def load_style_fingerprint(article_dir: Path = None) -> dict | None:
    """加载风格指纹，返回 dict 或 None"""
    search_paths = []
    if article_dir:
        search_paths.append(article_dir.parent / ".huage-gzh" / "style_fingerprint.json")
    search_paths.append(Path(__file__).resolve().parent.parent / ".huage-gzh" / "style_fingerprint.json")
    search_paths.append(Path.home() / ".huage-gzh" / "style_fingerprint.json")

    for p in search_paths:
        if p.exists():
            try:
                return json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                continue
    return None


def style_fingerprint_to_instructions(fp: dict) -> str:
    """将风格指纹转换为写作指令字符串"""
    if not fp:
        return ""

    lines = ["【风格写作指令（来自StyleLearner）】"]

    s = fp.get("sentence", {})
    if s:
        avg = s.get("avg_length", 0)
        short_r = s.get("short_ratio", 0)
        long_r = s.get("long_ratio", 0)
        var = s.get("variance", 0)
        lines.append(f"1. 句长控制：平均{int(avg)}字/句，短句{int(short_r*100)}%，长句{int(long_r*100)}%，burstiness方差{int(var)}")

    t = fp.get("tone", {})
    if t:
        markers = t.get("colloquial_markers", [])
        if markers:
            lines.append(f"2. 口语化词：{', '.join(markers[:5])}")
        fp_ratio = t.get("first_person", 0)
        lines.append(f"3. 第一人称使用比例：{int(fp_ratio*100)}%")

    st = fp.get("structure", {})
    if st:
        h2 = st.get("h2_count", 0)
        lines.append(f"4. H2段落数量：约{h2}个")

    return "\n".join(lines)


# ────────────────────────────────────────────────────────────────
# 用户确认节点
# ────────────────────────────────────────────────────────────────

def print_plan(plan_output: dict):
    """打印策划方案"""
    print()
    print("=" * 60)
    print("📋 主题策划方案")
    print("=" * 60)

    is_template = plan_output.get("is_template", False)
    if is_template:
        llm_error = plan_output.get("llm_error", "")
        print("⚠️  模板模式（未配置 LLM）")
        if llm_error:
            print(f"   LLM 错误：{llm_error}")
        print()

    print(f"📌 主题：{plan_output.get('topic', '')}")
    print()

    ta = plan_output.get("target_audience", {})
    if isinstance(ta, dict):
        print(f"👤 目标读者：{ta.get('persona', '')}")
        pps = ta.get('pain_points', [])
        if pps:
            print(f"   痛点：{', '.join(str(p) for p in pps)}")

    print(f"🔍 独特角度：{plan_output.get('unique_angle', '')}")
    print(f"💡 内容承诺：{plan_output.get('content_promise', '')}")
    print(f"🎯 内容调性：{plan_output.get('tone', '')}")

    titles = plan_output.get("title_options", [])
    if titles:
        print()
        print("📣 标题选项：")
        for i, t in enumerate(titles, 1):
            print(f"   {i}. {t}")


def confirm_plan(plan_output: dict) -> dict:
    """用户确认/修改策划方案。返回修改后的 plan_output"""
    print_plan(plan_output)
    print()
    print("─" * 40)
    print("操作选项：")
    print("  直接回车 — 接受当前方案")
    print("  r — 重新生成（需要配置 DASHSCOPE_API_KEY）")
    print("  m — 修改主题")
    print("  q — 退出")
    print()
    choice = input("请选择 [直接回车接受]: ").strip().lower()
    print()

    if choice == "q":
        print("已退出。")
        sys.exit(0)
    elif choice == "r":
        print("重新生成需要配置 LLM，请设置 DASHSCOPE_API_KEY 环境变量。")
        print("当前使用模板方案，继续进行...")
    elif choice == "m":
        new_topic = input("请输入新主题: ").strip()
        if new_topic:
            plan_output["topic"] = new_topic
            print(f"✅ 主题已更新: {new_topic}")

    return plan_output


def print_outline(outline_output: dict):
    """打印大纲"""
    print()
    print("=" * 60)
    print("📐 文章大纲")
    print("=" * 60)

    is_template = outline_output.get("is_template", False)
    if is_template:
        print("⚠️  模板模式（未配置 LLM）")
        print()

    title = outline_output.get("title", "")
    seo = outline_output.get("seo_keywords", {})
    print(f"📌 标题：{title}")
    print(f"🔑 核心关键词：{seo.get('primary', '')}")
    print(f"   次要关键词：{', '.join(seo.get('secondary', []))}")
    print()

    hook = outline_output.get("opening_hook", "")
    if hook:
        print(f"🪝 开头钩子：{hook}")
        print()

    outline_items = outline_output.get("outline", [])
    for i, item in enumerate(outline_items, 1):
        h2 = item.get("h2", "")
        points = item.get("key_points", [])
        wt = item.get("word_target", 0)
        print(f"  {i}. {h2}  (~{wt}字)")
        for p in points:
            print(f"     - {p}")
        print()


def confirm_outline(outline_output: dict) -> dict:
    """用户确认/修改大纲。返回修改后的 outline_output"""
    print_outline(outline_output)
    print()
    print("─" * 40)
    print("操作选项：")
    print("  直接回车 — 接受当前大纲，继续写作")
    print("  q — 退出")
    print()
    choice = input("请选择 [直接回车继续]: ").strip().lower()
    print()

    if choice == "q":
        print("已退出。")
        sys.exit(0)

    return outline_output


# ────────────────────────────────────────────────────────────────
# 质量报告
# ────────────────────────────────────────────────────────────────

def print_quality_report(q_report, retry_count: int = 0):
    """打印6维度质量评分报告"""
    print()
    print("=" * 60)
    print("🔍 质量评分报告（第{}次润色后）".format(retry_count + 1))
    print("=" * 60)
    print(q_report.format_summary())
    print()
    print("=" * 60)
    print(f"雷达图数据：{q_report.radar_labels}")
    print(f"维度分数：{[round(s, 1) for s in q_report.radar_scores]}")
    print()


def confirm_quality(q_report) -> dict:
    """
    用户确认质量报告。
    返回 {"action": "proceed"|"repolish"|"quit", "retry_count": int}
    """
    print()
    print("─" * 40)
    print("操作选项：")
    if q_report.gate_passed:
        print("  ✅ 质量达标 — 直接回车进入排版输出")
        print("  r — 强制重新润色（手动优化）")
    elif q_report.needs_human_decision:
        print("  ⚠️  已达最大重试次数(2次)，需人工决策")
        print("  直接回车 — 接受当前版本，进入排版")
        print("  r — 强制重新润色")
        print("  q — 退出，保存当前版本")
    else:
        remaining = 2 - q_report.retry_count
        print(f"  ⚠️  质量未达标（{q_report.weighted_score:.1f} < 85），将自动重新润色")
        print(f"  剩余自动润色次数：{remaining}次")
        print("  直接回车 — 继续自动润色流程")
        print("  q — 退出，保存当前版本")

    print()
    choice = input("请选择 [直接回车]: ").strip().lower()
    print()

    if choice == "q":
        return {"action": "quit", "retry_count": q_report.retry_count}
    elif choice == "r":
        return {"action": "repolish", "retry_count": q_report.retry_count}
    else:
        if q_report.gate_passed or q_report.needs_human_decision:
            return {"action": "proceed", "retry_count": q_report.retry_count}
        else:
            return {"action": "repolish", "retry_count": q_report.retry_count}


# ────────────────────────────────────────────────────────────────
# 主流程
# ────────────────────────────────────────────────────────────────

def cmd_create(args):
    """完整创作流程命令"""
    # 干运行模式
    if getattr(args, "dry_run", False):
        args.topic = args.topic  # already set
        cmd_dry_run(args)
        return

    hub = MessageHub()
    hub.set_session(f"gzh-{int(time.time())}")

    topic = args.topic.strip() if args.topic else ""
    if not topic:
        topic = input("请输入文章主题: ").strip()
        if not topic:
            print("❌ 主题不能为空")
            sys.exit(1)

    print(f"\n📝 开始创作：「{topic}」")
    print()

    # ── 1. 加载风格指纹 ───────────────────────────────────
    article_dir = Path(args.article_dir) if args.article_dir else DEFAULT_ARTICLE_DIR
    fp = load_style_fingerprint(article_dir)
    if fp:
        print(f"✅ 已加载风格指纹")
        style_instructions = style_fingerprint_to_instructions(fp)
    else:
        print(f"⚠️  未找到风格指纹，将使用默认风格写作")
        style_instructions = ""

    # ── 2. LLM 客户端初始化 ────────────────────────────────
    llm_client = None
    try:
        llm_client = create_llm_client(
            provider="qwen",
            api_key=os.environ.get("DASHSCOPE_API_KEY", ""),
        )
        print(f"✅ LLM 已就绪（qwen-plus）")
    except Exception as e:
        print(f"⚠️  LLM 未配置，使用模板模式: {e}")
        print("   要启用 LLM，请设置: export DASHSCOPE_API_KEY=your_key")

    # ── 3. 实时状态订阅 ──────────────────────────────────
    _, unsub = create_status_printer()

    try:
        # ── 4. PlannerAgent ────────────────────────────────
        print()
        print("─── ① 主题策划 ───")

        planner = PlannerAgent(hub=hub, llm_client=llm_client)
        plan_result = planner.run({"topic": topic, "num_options": 3})

        if not plan_result.success:
            print_status("Planner", "failed", plan_result.error)
            sys.exit(1)

        plan_output = plan_result.output

        # ── 5. 用户确认节点① ──────────────────────────────
        plan_output = confirm_plan(plan_output)

        # ── 6. OutlineAgent ────────────────────────────────
        print()
        print("─── ② 大纲规划 ───")

        outline_agent = OutlineAgent(hub=hub, llm_client=llm_client)
        outline_result = outline_agent.run({
            "topic": plan_output.get("topic", topic),
            "target_audience": plan_output.get("target_audience", {}),
            "style_instructions": style_instructions,
            "num_h2": args.num_h2 or 7,
        })

        if not outline_result.success:
            print_status("Outline", "failed", outline_result.error)
            sys.exit(1)

        outline_output = outline_result.output

        # ── 7. 用户确认节点② ──────────────────────────────
        outline_output = confirm_outline(outline_output)

        # ── 8. WriterAgent ───────────────────────────────
        print()
        print("─── ③ 内容写作 ───")

        writer = WriterAgent(hub=hub, llm_client=llm_client)
        writer_result = writer.run({
            "outline": outline_output,
            "target_audience": plan_output.get("target_audience", {}),
            "style_instructions": style_instructions,
            "style_fingerprint": fp,
        })

        if not writer_result.success:
            print_status("Writer", "failed", writer_result.error)
            sys.exit(1)

        writer_output = writer_result.output

        # ── 9. PolisherAgent + ReviewGate 循环 ─────────────────
        print()
        print("─── ④ 润色优化 ───")

        retry_count = 0
        polished_article = writer_output.get("content", "")
        current_content = polished_article
        seo_keywords = outline_output.get("seo_keywords", {})

        while True:
            # 运行润色Agent
            polisher = PolisherAgent(hub=hub, llm_client=llm_client)
            polish_result = polisher.run({
                "article": current_content,
                "seo_keywords": seo_keywords,
                "retry_count": retry_count,
            })

            if not polish_result.success:
                print_status("Polisher", "failed", polish_result.error)
                sys.exit(1)

            polished_article = polish_result.output["polished_article"]
            h_report_dict = polish_result.output["humanizer_report"]
            a_report_dict = polish_result.output["anti_slop_report"]

            # 运行ReviewGate评分
            gate_passed, q_report = review_article(
                polished_article,
                llm_client=llm_client,
                retry_count=retry_count,
            )

            # 打印报告
            print_quality_report(q_report, retry_count)

            # 用户决策
            decision = confirm_quality(q_report)

            if decision["action"] == "proceed":
                current_content = polished_article
                break
            elif decision["action"] == "quit":
                print("已退出，当前版本已保存。")
                sys.exit(0)
            else:  # repolish
                current_content = polished_article
                retry_count = decision["retry_count"] + 1
                if retry_count > 2:
                    print("⚠️  已达最大润色次数，进入排版阶段。")
                    break
                print(f"\n🔄 开始第{retry_count + 1}次润色...")

        # ── 10. 保存输出 ────────────────────────────────────
        print()
        print("=" * 60)
        print("📄 润色完成")
        print("=" * 60)

        title = writer_output.get("title", "无标题")
        h2_count = writer_output.get("h2_count", 0)
        is_template = writer_output.get("is_template", False)

        final_word_count = len(polished_article.replace("#", "").replace("\n", "").replace(" ", "").replace("-", "").replace(">", ""))

        print(f"标题：{title}")
        print(f"字数：约{final_word_count}字")
        print(f"H2数量：{h2_count}个")
        print(f"模式：{'模板' if is_template else 'LLM生成'}")
        print()

        # 保存到文件
        output_dir = Path(args.output_dir or f"./outputs/{int(time.time())}")
        output_dir.mkdir(parents=True, exist_ok=True)

        # 保存润色稿
        polished_path = output_dir / "polished.md"
        polished_path.write_text(polished_article, encoding="utf-8")
        print(f"💾 润色稿已保存: {polished_path}")

        # 同时保存初稿（来自WriterAgent）
        draft_content = writer_output.get("content", "")
        if draft_content and draft_content != polished_article:
            draft_path = output_dir / "draft.md"
            draft_path.write_text(draft_content, encoding="utf-8")
            print(f"💾 初稿已保存: {draft_path}")

        # 保存质量报告
        q_report_dict = q_report.to_dict()
        quality_path = output_dir / "quality_report.json"
        quality_path.write_text(json.dumps(q_report_dict, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"💾 质量报告已保存: {quality_path}")

        # 保存完整元数据
        meta = {
            "title": title,
            "topic": plan_output.get("topic", topic),
            "plan": plan_output,
            "outline": outline_output,
            "word_count": final_word_count,
            "h2_count": h2_count,
            "is_template": is_template,
            "style_fingerprint": fp,
            "quality_report": q_report_dict,
            "polish_retry_count": retry_count,
        }
        meta_path = output_dir / "meta.json"
        meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"💾 元数据已保存: {meta_path}")

        print()
        print("✅ 创作流程完成！")
        print()
        if is_template:
            print("⚠️  当前为模板模式，建议配置 DASHSCOPE_API_KEY 以启用 LLM 真实生成。")

    finally:
        unsub()


# ────────────────────────────────────────────────────────────────
# 其他命令（复用）
# ────────────────────────────────────────────────────────────────

def cmd_style_learn(args):
    """风格学习命令"""
    hub = MessageHub()
    hub.set_session(f"gzh-{int(time.time())}")

    article_dir = Path(args.article_dir) if args.article_dir else DEFAULT_ARTICLE_DIR
    check = check_cold_start(article_dir)

    if check["status"] != "warm":
        print(check["message"])
        if run_cold_start_wizard(article_dir):
            sys.exit(0)
        else:
            sys.exit(1)

    print(f"\n📚 开始风格学习...")
    print(f"   文章目录: {check['dir']}")
    print(f"   已发布文章: {check['article_count']} 篇")
    print()

    _, unsub = create_status_printer()

    try:
        agent = StyleLearnerAgent(hub=hub, article_dir=str(article_dir))
        input_data = {"topic": args.topic} if args.topic else {}
        result = agent.run(input_data)

        print()
        if result.success:
            print_status("StyleLearner", "completed",
                         f"分析了 {result.output['articles_analyzed']} 篇文章")
            print("\n" + "=" * 60)
            print("📋 风格摘要:")
            print("=" * 60)
            print(result.output["summary"])
            print("\n" + "=" * 60)
            print("📝 写作指令:")
            print("=" * 60)
            print(result.output["writing_instructions"])

            if args.output:
                output_path = Path(args.output)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(
                    json.dumps(result.output["style_fingerprint"], ensure_ascii=False, indent=2)
                )
                print(f"\n💾 风格指纹已保存到: {output_path}")

            default_fp = article_dir.parent / ".huage-gzh" / "style_fingerprint.json"
            default_fp.parent.mkdir(parents=True, exist_ok=True)
            default_fp.write_text(
                json.dumps(result.output["style_fingerprint"], ensure_ascii=False, indent=2)
            )
            print(f"💾 风格指纹默认位置: {default_fp}")
        else:
            print_status("StyleLearner", "failed", result.error)
            sys.exit(1)
    finally:
        unsub()


def cmd_analyze(args):
    """分析单篇文章命令"""
    print(f"\n📄 分析文章: {args.file}")

    from core.style_fingerprint import StyleFingerprintEngine

    engine = StyleFingerprintEngine()
    file_path = Path(args.file)

    if not file_path.exists():
        print(f"❌ 文件不存在: {file_path}")
        sys.exit(1)

    fp = engine.analyze_file(file_path)

    print("\n" + "=" * 60)
    print("📊 风格指纹:")
    print("=" * 60)
    print(json.dumps(fp.to_dict(), ensure_ascii=False, indent=2))

    if args.output:
        output_path = Path(args.output)
        output_path.write_text(json.dumps(fp.to_dict(), ensure_ascii=False, indent=2))
        print(f"\n💾 已保存到: {output_path}")


def cmd_status(args):
    """查看流水线状态"""
    hub = MessageHub()
    status = hub.get_status()

    print("\n📊 流水线状态:")
    print("=" * 60)
    if not status:
        print("  (暂无状态记录)")
    for msg_type, info in status.items():
        print(f"  {msg_type:12} | {info.get('agent', 'unknown'):15} | "
              f"{'✅' if info.get('has_content') else '⏳'}")


def cmd_dry_run(args):
    """LeadAgent 干运行命令（不调用 LLM）"""
    from agents.lead_agent import LeadAgent

    topic = args.topic.strip() if args.topic else ""
    if not topic:
        topic = input("请输入文章主题: ").strip()
        if not topic:
            print("❌ 主题不能为空")
            sys.exit(1)

    print()
    print("=" * 60)
    print("  LeadAgent 干运行模式")
    print("=" * 60)
    print(f"📝 主题：{topic}")
    print(f"🔧 不调用 LLM，模拟完整流水线")
    print()

    hub = MessageHub()
    hub.set_session(f"dryrun-{int(time.time())}")

    lead = LeadAgent(hub=hub, llm_client=None, dry_run=True)

    # 加载风格指纹
    article_dir = Path(args.article_dir) if args.article_dir else DEFAULT_ARTICLE_DIR
    fp = load_style_fingerprint(article_dir)
    if fp:
        instructions = style_fingerprint_to_instructions(fp)
        lead.set_style_instructions(instructions)
        print(f"✅ 已加载风格指纹")
    else:
        print(f"⚠️  未找到风格指纹，使用默认风格")

    # 立即进入用户确认模拟
    print()
    print("─── LeadAgent 流水线阶段预览 ───")
    print()
    print("  ① 主题策划     → [确认节点①]")
    print("  ② 深度研究     → [确认节点②]")
    print("  ③ 大纲规划     → [确认节点③]")
    print("  ④ 内容写作     →")
    print("  ⑤ 润色优化     → [确认节点④：质量审查]")
    print("  ⑥ 质量审查     → [循环，最多3次]")
    print("  ⑦ 配图封面     → [确认节点⑤] Phase 2 实现")
    print("  ⑧ 排版输出     →")
    print()
    print("  干运行仅展示阶段，不执行真实 LLM 调用")
    print()

    result = lead.run(topic, output_dir=args.output_dir)
    print()
    print("=" * 60)
    if result["success"]:
        print(f"✅ 干运行完成（输出: {result['output_dir']}）")
        print("   注意：实际运行需要配置 DASHSCOPE_API_KEY")
    else:
        print(f"❌ 干运行中断：{result.get('error', 'unknown')}")
    print("=" * 60)


def cmd_version(args):
    """版本信息"""
    print("公众号多Agent协同创作系统 v0.4")
    print("M3: PolisherAgent + ReviewGate + 去AI味双引擎")
    print("   + 润色优化循环 + 6维度质量评分门禁")


def cmd_polish(args):
    """独立润色命令"""
    hub = MessageHub()
    hub.set_session(f"polish-{int(time.time())}")

    file_path = Path(args.article)
    if not file_path.exists():
        print(f"❌ 文件不存在: {file_path}")
        sys.exit(1)

    article_content = file_path.read_text(encoding="utf-8")
    print(f"\n📄 润色文章: {file_path.name}")
    print(f"   字符数：{len(article_content)}字")

    # SEO关键词
    seo_keywords = {}
    if args.seo_keywords:
        try:
            seo_keywords = json.loads(args.seo_keywords)
        except json.JSONDecodeError:
            print(f"⚠️  SEO关键词格式错误，使用空配置")

    # LLM客户端
    llm_client = None
    try:
        llm_client = create_llm_client(
            provider="qwen",
            api_key=os.environ.get("DASHSCOPE_API_KEY", ""),
        )
        print(f"✅ LLM 已就绪")
    except Exception as e:
        print(f"⚠️  LLM 未配置，使用规则降级润色: {e}")

    _, unsub = create_status_printer()

    try:
        retry_count = 0
        current_content = article_content

        while True:
            polisher = PolisherAgent(hub=hub, llm_client=llm_client)
            result = polisher.run({
                "article": current_content,
                "seo_keywords": seo_keywords,
                "retry_count": retry_count,
            })

            if not result.success:
                print_status("Polisher", "failed", result.error)
                sys.exit(1)

            polished = result.output["polished_article"]
            gate_passed, q_report = review_article(
                polished,
                llm_client=llm_client,
                retry_count=retry_count,
            )

            print_quality_report(q_report, retry_count)

            if gate_passed:
                print("✅ 质量达标！")
                current_content = polished
                break
            elif retry_count >= 2:
                print("⚠️  已达最大润色次数，请人工决策后保存。")
                current_content = polished
                break
            else:
                print(f"🔄 继续第{retry_count + 2}次润色...")
                current_content = polished
                retry_count += 1

        # 保存
        output_path = Path(args.output) if args.output else file_path.with_name(file_path.stem + "-润色.md")
        output_path.write_text(current_content, encoding="utf-8")
        print(f"\n💾 润色稿已保存: {output_path}")

        # 保存质量报告
        if args.report:
            report_path = Path(args.report)
            report_path.write_text(json.dumps(q_report.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"💾 质量报告已保存: {report_path}")

    finally:
        unsub()


# ────────────────────────────────────────────────────────────────
# 主入口
# ────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="公众号多Agent协同创作系统",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # 风格学习
    parser_style = subparsers.add_parser("style", help="从已发布文章学习风格")
    parser_style.add_argument("--article-dir", "-d", help="文章目录路径")
    parser_style.add_argument("--topic", "-t", help="当前主题（供参考）")
    parser_style.add_argument("--output", "-o", help="输出风格指纹JSON文件")
    parser_style.set_defaults(func=cmd_style_learn)

    # 分析单篇文章
    parser_analyze = subparsers.add_parser("analyze", help="分析单篇文章风格")
    parser_analyze.add_argument("file", help="文章Markdown文件路径")
    parser_analyze.add_argument("--output", "-o", help="输出JSON文件")
    parser_analyze.set_defaults(func=cmd_analyze)

    # 流水线状态
    parser_status = subparsers.add_parser("status", help="查看流水线状态")
    parser_status.set_defaults(func=cmd_status)

    # 版本
    parser_version = subparsers.add_parser("version", help="版本信息")
    parser_version.set_defaults(func=cmd_version)

    # 完整创作流程（新增）
    parser_create = subparsers.add_parser("create", help="开始完整创作流程")
    parser_create.add_argument("topic", nargs="?", help="文章主题")
    parser_create.add_argument("--article-dir", "-d", help="文章目录（用于加载风格指纹）")
    parser_create.add_argument("--num-h2", "-n", type=int, default=7, help="H2段落数量（默认7）")
    parser_create.add_argument("--output-dir", "-o", help="输出目录（默认 ./outputs/{timestamp}）")
    parser_create.add_argument("--dry-run", action="store_true", help="干运行模式：不调用LLM，模拟完整流程")
    parser_create.set_defaults(func=cmd_create)

    # 干运行命令
    parser_dry = subparsers.add_parser("dry-run", help="LeadAgent干运行（不调用LLM，模拟流程）")
    parser_dry.add_argument("topic", nargs="?", help="文章主题")
    parser_dry.add_argument("--article-dir", "-d", help="文章目录（用于加载风格指纹）")
    parser_dry.add_argument("--output-dir", "-o", help="输出目录")
    parser_dry.set_defaults(func=cmd_dry_run)

    # 独立润色命令
    parser_polish = subparsers.add_parser("polish", help="对已有文章进行润色优化")
    parser_polish.add_argument("article", help="文章Markdown文件路径")
    parser_polish.add_argument("--seo", dest="seo_keywords", help='SEO关键词JSON，例：\'{"primary":"AI","secondary":["工具","技巧"]}\'')
    parser_polish.add_argument("--output", "-o", help="输出文件路径")
    parser_polish.add_argument("--report", "-r", help="质量报告JSON输出路径")
    parser_polish.set_defaults(func=cmd_polish)

    args = parser.parse_args()

    if not args.command:
        print_header()
        print("\n📖 使用指南:")
        print("  huage-gzh create [主题]   # 完整创作流程（主要命令）")
        print("  huage-gzh polish <file>   # 对已有文章润色优化 🆕")
        print("  huage-gzh style           # 从已发布文章学习风格")
        print("  huage-gzh analyze <file> # 分析单篇文章")
        print("  huage-gzh status         # 查看流水线状态")
        print()
        print("🆕 v0.4 新功能:")
        print("  1. huage-gzh create — 完整创作流程（含润色+评审）")
        print("  2. huage-gzh polish — 独立润色命令")
        print("  3. 去AI味双引擎（Humanizer + AntiSlop）")
        print("  4. 6维度质量评分门禁（≥85分通过）")
        print()
        print("📝 快速开始:")
        print("  huage-gzh create \"AI Agent 工具链实战\"")
        print("  huage-gzh polish 我的文章.md --seo '{\"primary\":\"AI\"}'")
        print()
        print("  # 首次使用:")
        print("  1. huage-gzh style  # 先学习你的写作风格")
        print("  2. huage-gzh create \"你的主题\"  # 开始创作")
        print()
        return

    print_header()
    args.func(args)


if __name__ == "__main__":
    main()
