# agents/publish_agent.py - 发布Agent
# Phase 4: 排版输出 + 多格式导出 + SEO报告

import json
import time
from pathlib import Path
from typing import Any, Optional

from core.base_agent import BaseAgent, AgentResult
from core.message_hub import MessageHub, Message, MessageType
from core.seo_reporter import SEOReporter, generate_seo_report
from publishers.wechat_formatter import WechatFormatter


class PublishAgent(BaseAgent):
    """
    发布Agent

    Phase 4 职责：
    - 将终稿格式化（Markdown + HTML）
    - 生成SEO报告
    - 生成质量报告（继承ReviewGate结果）
    - 输出完整发布包
    """

    name = "Publish"
    description = "排版输出 + 多格式导出 + SEO报告"

    def __init__(self, hub: MessageHub = None, llm_client: Optional[LLMClient] = None):
        super().__init__(hub)
        self.llm_client = llm_client
        self.wechat_formatter = WechatFormatter()

    def execute(self, input_data: Any) -> AgentResult:
        """
        执行排版输出

        输入: {
            "title": str,                    # 文章标题
            "content": str,                  # 终稿正文
            "outline": dict,                 # 原始大纲（含关键词）
            "seo_keywords": dict,           # SEO关键词
            "quality_report": dict,         # 质量报告（来自ReviewGate）
            "humanizer_score": float,       # Humanizer评分
            "anti_slop_score": float,      # AntiSlop评分
            "image_plan": dict,             # 配图方案（可选）
            "author": str,                  # 作者
            "publish_date": str,            # 发布日期
            "account_name": str,            # 公众号名称
            "output_dir": str,              # 输出目录
        }

        输出: {
            "preview": {
                "title": str,
                "html": str,               # 公众号HTML
                "word_count": int,
                "reading_time": str,
            },
            "seo_report": dict,
            "files": {
                "markdown": str,           # .md文件路径
                "html": str,               # .html文件路径
                "meta": str,               # .json元数据路径
            },
            "hashtags": list[str],
        }
        """
        if not isinstance(input_data, dict):
            return AgentResult(success=False, error="输入必须是字典")

        title = input_data.get("title", "")
        content = input_data.get("content", "")
        outline = input_data.get("outline", {})
        seo_keywords = input_data.get("seo_keywords", {})
        quality_report = input_data.get("quality_report", {})
        humanizer_score = input_data.get("humanizer_score", 100.0)
        anti_slop_score = input_data.get("anti_slop_score", 100.0)
        image_plan = input_data.get("image_plan", {})
        author = input_data.get("author", "")
        publish_date = input_data.get("publish_date", time.strftime("%Y-%m-%d"))
        account_name = input_data.get("account_name", "漠玫创作")
        output_dir = input_data.get("output_dir", "./outputs")

        self.hub.publish(Message(
            type=MessageType.STATUS,
            agent=self.name,
            content={"status": "running", "agent": self.name,
                     "progress": "开始排版输出"}
        ))

        # 1. 生成SEO报告
        seo_report = generate_seo_report(
            article_content=content,
            title=title,
            seo_keywords=seo_keywords,
            humanizer_score=humanizer_score,
            anti_slop_score=anti_slop_score,
        )

        # 2. 生成话题标签
        primary_kw = seo_keywords.get("primary", "")
        hashtags = self.wechat_formatter.generate_hashtags(
            [primary_kw] + seo_keywords.get("secondary", [])[:2]
        )

        # 3. 构建配图占位列表
        image_placeholders = []
        image_ideas = image_plan.get("image_ideas", [])
        for idea in image_ideas:
            image_placeholders.append({
                "path": "",
                "caption": idea.get("description", ""),
            })

        # 4. 格式化为公众号HTML
        html = self.wechat_formatter.format(
            title=title,
            content=content,
            author=author,
            publish_date=publish_date,
            cover_image_path=None,  # 封面由用户手动上传
            image_placeholders=image_placeholders,
            hashtags=hashtags,
            include_qr=False,
        )

        # 5. 保存文件
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # 清理标题用于文件名
        slug = title.replace("/", "-").replace(" ", "-")[:30]

        # Markdown文件（带frontmatter）
        md_content = f"""---
title: "{title}"
date: {publish_date}
tags: [{', '.join(f'"{h}"' for h in hashtags)}]
author: "{author}"
word_count: {len(content)}
---

# {title}

{content}
"""
        md_path = output_path / f"{slug}.md"
        md_path.write_text(md_content, encoding="utf-8")

        # HTML文件
        html_path = output_path / f"{slug}.html"
        html_path.write_text(html, encoding="utf-8")

        # Meta JSON
        meta = {
            "title": title,
            "author": author,
            "publish_date": publish_date,
            "account_name": account_name,
            "word_count": len(content),
            "reading_time": f"{max(1, len(content) // 500)}分钟",
            "seo_keywords": seo_keywords,
            "quality_report": quality_report,
            "seo_report": seo_report.to_dict(),
            "image_plan": image_plan,
            "hashtags": hashtags,
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        meta_path = output_path / f"{slug}-meta.json"
        meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

        self.hub.publish(Message(
            type=MessageType.STATUS,
            agent=self.name,
            content={"status": "completed", "agent": self.name,
                     "progress": f"输出已保存: {output_path}"}
        ))

        return AgentResult(success=True, output={
            "preview": {
                "title": title,
                "html": html,
                "word_count": len(content),
                "reading_time": f"{max(1, len(content) // 500)}分钟",
            },
            "seo_report": seo_report.to_dict(),
            "files": {
                "markdown": str(md_path),
                "html": str(html_path),
                "meta": str(meta_path),
            },
            "hashtags": hashtags,
        })

    def _get_output_type(self) -> MessageType:
        return MessageType.FORMATTED
