# agents/research_agent.py - 深度研究Agent
# Phase 2: Tavily搜索 + Obsidian知识库 + 风格分析

import json
from typing import Any, Optional

from core.base_agent import BaseAgent, AgentResult
from core.message_hub import MessageHub, Message, MessageType
from core.llm_client import LLMClient, LLMCallError
from core.tavily_client import TavilyClient, TavilySearchReport
from core.obsidian_search import ObsidianSearcher, ObsidianSearchReport


RESEARCH_PROMPT = """你是一个专业的研究员，擅长深度内容和数据分析。

给定一个主题和相关研究资料，生成一份研究报告。

```json
{
  "summary": "主题的一句话概括",
  "key_findings": ["发现1", "发现2", "发现3"],
  "key_statistics": [
    {"stat": "数据", "source": "来源", "claim": "数据说明"}
  ],
  "case_studies": [
    {"company": "公司名", "case": "具体案例"}
  ],
  "industry_insights": [
    "洞察1",
    "洞察2"
  ],
  "quotes_for_citation": [
    {"quote": "引言内容", "author": "作者", "source": "来源"}
  ]
}
```

请提供真实、有据可查的研究内容。"""


class ResearchAgent(BaseAgent):
    """
    深度研究Agent。

    Phase 2 增强：
    - Tavily 网络深度搜索
    - Obsidian 知识库检索
    - 已发布文章风格分析
    """

    name = "Research"
    description = "Tavily搜索 + Obsidian知识库 + 风格分析"

    def __init__(
        self,
        hub: MessageHub = None,
        llm_client: Optional[LLMClient] = None,
        tavily_api_key: str = None,
        obsidian_vault_path: str = None,
    ):
        super().__init__(hub)
        self.llm_client = llm_client
        self.tavily = TavilyClient(api_key=tavily_api_key)
        self.obsidian = ObsidianSearcher(vault_path=obsidian_vault_path)

    def execute(self, input_data: Any) -> AgentResult:
        """
        执行深度研究

        输入: {
            "topic": str,          # 研究主题
            "unique_angle": str,    # 独特角度（来自 Planner）
            "article_dir": str,     # 已发布文章目录（用于 Obsidian 搜索）
        }

        输出: {
            "source": str,          # "tavily" | "obsidian" | "template"
            "findings": list[str],
            "key_statistics": list[dict],
            "case_studies": list[dict],
            "industry_insights": list[str],
            "quotes_for_citation": list[dict],
            "seo_keywords": dict,
            "style_notes": list[str],
            "tavily_report": dict,   # 原始搜索报告快照
            "obsidian_report": dict, # 原始知识库报告快照
        }
        """
        if isinstance(input_data, str):
            topic = input_data
            unique_angle = ""
            article_dir = None
        else:
            topic = input_data.get("topic", "")
            unique_angle = input_data.get("unique_angle", "")
            article_dir = input_data.get("article_dir")

        if not topic:
            return AgentResult(success=False, error="研究主题不能为空")

        self.hub.publish(Message(
            type=MessageType.STATUS,
            agent=self.name,
            content={"status": "running", "agent": self.name,
                     "progress": f"深度研究: {topic}"}
        ))

        # 并行执行 Tavily 搜索和 Obsidian 搜索
        tavily_report: TavilySearchReport = None
        obsidian_report: ObsidianSearchReport = None

        # Tavily 搜索
        if self.tavily.is_available():
            tavily_report = self.tavily.search(topic, max_results=5)
            self.hub.publish(Message(
                type=MessageType.STATUS,
                agent=self.name,
                content={"status": "running", "agent": self.name,
                         "progress": f"Tavily搜索完成: {len(tavily_report.results)}条结果"}
            ))

        # Obsidian 搜索
        if article_dir:
            obsidian_report = self.obsidian.search(
                topic,
                max_results=3,
                article_dir=article_dir
            )
            self.hub.publish(Message(
                type=MessageType.STATUS,
                agent=self.name,
                content={"status": "running", "agent": self.name,
                         "progress": f"Obsidian搜索完成: {obsidian_report.total_files_searched}个文件"}
            ))

        # 整合结果
        if self.llm_client and (tavily_report or obsidian_report):
            return self._generate_with_llm(topic, tavily_report, obsidian_report)
        else:
            return self._generate_template(topic, tavily_report, obsidian_report)

    def _generate_template(
        self,
        topic: str,
        tavily_report: TavilySearchReport = None,
        obsidian_report: ObsidianSearchReport = None,
    ) -> AgentResult:
        """基于搜索结果生成研究报告（无 LLM 降级模式）"""
        findings = []
        statistics = []
        style_notes = []

        if tavily_report:
            findings.extend(tavily_report.key_findings)
            statistics.extend(tavily_report.statistics)
            if tavily_report.results:
                findings.append(f"从网络资源中找到 {len(tavily_report.results)} 条相关内容")

        if obsidian_report:
            for r in obsidian_report.results:
                if r.matched_content:
                    findings.append(f"【{r.file_name}】{r.matched_content[:80]}...")
            style_notes = obsidian_report.style_notes
            if obsidian_report.topic_tags:
                findings.append(f"相关话题标签: {', '.join(obsidian_report.topic_tags[:5])}")

        output = {
            "source": "tavily+obsidian" if tavily_report else "obsidian" if obsidian_report else "template",
            "findings": findings or [f"【关于{topic}的研究发现】"],
            "key_statistics": statistics or [
                {"stat": "【数据】", "source": "【来源】", "claim": f"{topic}相关的核心数据"}
            ],
            "case_studies": [
                {"company": "【公司名】", "case": f"{topic}相关的具体案例"}
            ],
            "industry_insights": [
                f"关于{topic}的行业洞察1",
                f"关于{topic}的行业洞察2",
            ],
            "quotes_for_citation": [
                {"quote": "【有见地的引言】", "author": "【作者】", "source": "【来源】"}
            ],
            "seo_keywords": {
                "primary": topic,
                "secondary": [f"{topic}技巧", f"{topic}方法"],
                "long_tail": [f"如何{topic}", f"{topic}入门"],
            },
            "style_notes": style_notes,
            "tavily_report_snapshot": tavily_report.to_dict() if tavily_report else {},
            "obsidian_report_snapshot": obsidian_report.to_dict() if obsidian_report else {},
        }

        self.hub.publish(Message(
            type=MessageType.STATUS,
            agent=self.name,
            content={"status": "completed", "agent": self.name,
                     "progress": f"研究完成（无LLM，降级模式）"}
        ))

        return AgentResult(success=True, output=output)

    def _generate_with_llm(
        self,
        topic: str,
        tavily_report: TavilySearchReport = None,
        obsidian_report: ObsidianSearchReport = None,
    ) -> AgentResult:
        """使用 LLM 基于搜索结果生成研究报告"""
        try:
            # 构建研究上下文
            context_parts = [f"研究主题：{topic}\n"]

            if tavily_report and tavily_report.results:
                context_parts.append("## Tavily 网络搜索结果\n")
                for r in tavily_report.results:
                    context_parts.append(f"- {r.title}: {r.content[:300]}...\n")
                if tavily_report.key_findings:
                    context_parts.append(f"\n关键发现: {'; '.join(tavily_report.key_findings)}")

            if obsidian_report and obsidian_report.results:
                context_parts.append("\n## Obsidian 知识库匹配\n")
                for r in obsidian_report.results:
                    context_parts.append(f"- {r.file_name}: {r.matched_content[:200]}...\n")
                if obsidian_report.topic_tags:
                    context_parts.append(f"\n相关标签: {', '.join(obsidian_report.topic_tags[:10])}")

            context = "\n".join(context_parts)

            schema = {
                "type": "object",
                "properties": {
                    "summary": {"type": "string"},
                    "key_findings": {"type": "array", "items": {"type": "string"}},
                    "key_statistics": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "stat": {"type": "string"},
                                "source": {"type": "string"},
                                "claim": {"type": "string"},
                            }
                        }
                    },
                    "case_studies": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "company": {"type": "string"},
                                "case": {"type": "string"},
                            }
                        }
                    },
                    "industry_insights": {"type": "array", "items": {"type": "string"}},
                    "quotes_for_citation": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "quote": {"type": "string"},
                                "author": {"type": "string"},
                                "source": {"type": "string"},
                            }
                        }
                    },
                    "seo_keywords": {
                        "type": "object",
                        "properties": {
                            "primary": {"type": "string"},
                            "secondary": {"type": "array", "items": {"type": "string"}},
                            "long_tail": {"type": "array", "items": {"type": "string"}},
                        }
                    },
                },
                "required": ["key_findings", "key_statistics", "case_studies",
                             "industry_insights", "quotes_for_citation"]
            }

            result = self.llm_client.chat_json(
                prompt=f"{RESEARCH_PROMPT}\n\n{context}",
                schema=schema,
                temperature=0.5,
            )

            # 合并 SEO keywords（优先用 LLM 生成的，但融合 Tavily 的发现）
            seo_keywords = result.get("seo_keywords", {})
            if tavily_report and tavily_report.key_findings:
                # 如果 LLM 没有生成 SEO keywords，从 topic 推断
                if not seo_keywords.get("primary"):
                    seo_keywords = {
                        "primary": topic,
                        "secondary": tavily_report.key_findings[:3],
                        "long_tail": [f"如何{topic}", f"{topic}技巧"],
                    }

            output = {
                "source": "tavily+llm" if tavily_report else "llm",
                "findings": result.get("key_findings", []),
                "key_statistics": result.get("key_statistics", []),
                "case_studies": result.get("case_studies", []),
                "industry_insights": result.get("industry_insights", []),
                "quotes_for_citation": result.get("quotes_for_citation", []),
                "seo_keywords": seo_keywords,
                "style_notes": [],
                "tavily_report_snapshot": tavily_report.to_dict() if tavily_report else {},
                "obsidian_report_snapshot": obsidian_report.to_dict() if obsidian_report else {},
            }

            self.hub.publish(Message(
                type=MessageType.STATUS,
                agent=self.name,
                content={"status": "completed", "agent": self.name,
                         "progress": f"研究完成（LLM模式）"}
            ))

            return AgentResult(success=True, output=output)

        except LLMCallError:
            return self._generate_template(topic, tavily_report, obsidian_report)

        except Exception as e:
            return AgentResult(success=False, error=f"ResearchAgent异常: {str(e)}")

    def _get_output_type(self) -> MessageType:
        return MessageType.RESEARCH
