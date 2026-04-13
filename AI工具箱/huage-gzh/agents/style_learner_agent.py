# StyleLearnerAgent - 风格学习Agent
# 读取已发布文章参考库，提取风格指纹，生成个性化写作指令
# Phase 3 核心Agent

import json
from pathlib import Path
from typing import Any

from core.base_agent import BaseAgent, AgentResult
from core.message_hub import MessageHub, Message, MessageType
from core.style_fingerprint import StyleFingerprintEngine, StyleFingerprint


class StyleLearnerAgent(BaseAgent):
    """风格学习Agent"""

    name = "StyleLearner"
    description = "从已发布文章提取风格特征，生成个性化写作指令"

    def __init__(self, hub: MessageHub = None, article_dir: str = None):
        super().__init__(hub)
        self.engine = StyleFingerprintEngine()
        self.article_dir = Path(article_dir) if article_dir else None

    def execute(self, input_data: Any) -> AgentResult:
        """
        执行风格学习

        输入: {
            "article_dir": str (可选，默认使用预设目录),
            "topic": str (可选，当前主题供参考),
            "target_audience": str (可选，受众画像)
        }

        输出: {
            "style_fingerprint": dict,
            "writing_instructions": str,
            "articles_analyzed": int,
            "summary": str
        }
        """
        if isinstance(input_data, dict):
            article_dir = input_data.get("article_dir", self.article_dir)
            topic = input_data.get("topic", "")
        else:
            article_dir = self.article_dir
            topic = ""

        if not article_dir:
            # 默认目录: 相对于vault根目录
            # agents/style_learner_agent.py -> agents/ -> huage-gzh/ -> AI工具箱/ -> Obsidian Vault/
            vault_root = Path(__file__).resolve().parent.parent.parent.parent
            article_dir = vault_root / "01-输出内容/公众号学习资料/已发布文章参考库"
        else:
            article_dir = Path(article_dir)

        if not article_dir.exists():
            return AgentResult(
                success=False,
                error=f"文章目录不存在: {article_dir}"
            )

        # 分析所有已发布文章
        fingerprints = []
        article_files = list(article_dir.glob("*.md"))

        if not article_files:
            return AgentResult(
                success=False,
                error=f"目录为空: {article_dir}，请先上传已发布文章"
            )

        for i, file in enumerate(article_files):
            # 发布进度状态
            self.hub.publish(Message(
                type=MessageType.STATUS,
                agent=self.name,
                content={
                    "status": "running",
                    "agent": self.name,
                    "progress": f"分析文章 {i+1}/{len(article_files)}: {file.name}"
                }
            ))
            try:
                fp = self.engine.analyze_file(file)
                fingerprints.append(fp)
            except Exception:
                continue

        if not fingerprints:
            return AgentResult(
                success=False,
                error="无法解析任何文章，请检查文件格式"
            )

        # 合并风格指纹
        merged_fp = self._merge_fingerprints(fingerprints)

        # 生成写作指令
        instructions = self.engine.generate_writing_instructions(merged_fp)

        # 生成摘要
        summary = self._generate_summary(merged_fp, len(fingerprints), topic)

        return AgentResult(
            success=True,
            output={
                "style_fingerprint": merged_fp.to_dict(),
                "writing_instructions": instructions,
                "articles_analyzed": len(fingerprints),
                "summary": summary,
                "article_dir": str(article_dir)
            }
        )

    def _merge_fingerprints(self, fingerprints: list[StyleFingerprint]) -> StyleFingerprint:
        """合并多个风格指纹"""
        if len(fingerprints) == 1:
            return fingerprints[0]

        merged = StyleFingerprint()

        # 句长：取平均
        from core.style_fingerprint import SentenceMetrics
        merged.sentence = SentenceMetrics(
            avg_length=sum(f.sentence.avg_length for f in fingerprints) / len(fingerprints),
            variance=sum(f.sentence.variance for f in fingerprints) / len(fingerprints),
            short_ratio=sum(f.sentence.short_ratio for f in fingerprints) / len(fingerprints),
            long_ratio=sum(f.sentence.long_ratio for f in fingerprints) / len(fingerprints),
            max_length=max(f.sentence.max_length for f in fingerprints),
            min_length=min(f.sentence.min_length for f in fingerprints),
        )

        # 词汇：第一个的
        merged.vocabulary = fingerprints[0].vocabulary

        # 结构：取平均
        from core.style_fingerprint import StructureMetrics
        merged.structure = StructureMetrics(
            h2_count=sum(f.structure.h2_count for f in fingerprints) // len(fingerprints),
            quote_ratio=sum(f.structure.quote_ratio for f in fingerprints) / len(fingerprints),
            list_ratio=sum(f.structure.list_ratio for f in fingerprints) / len(fingerprints),
            code_ratio=sum(f.structure.code_ratio for f in fingerprints) / len(fingerprints),
            callout_count=sum(f.structure.callout_count for f in fingerprints) // len(fingerprints),
        )

        # 格式：合并
        from core.style_fingerprint import FormatMetrics
        merged.format = FormatMetrics(
            has_emoji=any(f.format.has_emoji for f in fingerprints),
            emoji_count=max(f.format.emoji_count for f in fingerprints),
            has_divider=any(f.format.has_divider for f in fingerprints),
            has_table=any(f.format.has_table for f in fingerprints),
            image_caption_style=fingerprints[0].format.image_caption_style,
        )

        # 语气：取平均
        from core.style_fingerprint import ToneMetrics
        merged.tone = ToneMetrics(
            first_person=sum(f.tone.first_person for f in fingerprints) / len(fingerprints),
            question_ratio=sum(f.tone.question_ratio for f in fingerprints) / len(fingerprints),
            exclamation_ratio=sum(f.tone.exclamation_ratio for f in fingerprints) / len(fingerprints),
            colloquial_markers=fingerprints[0].tone.colloquial_markers,
        )

        return merged

    def _generate_summary(self, fp: StyleFingerprint, count: int, topic: str = "") -> str:
        """生成风格摘要说明"""
        lines = [
            f"已分析 {count} 篇已发布文章，提取风格特征如下：",
            "",
            f"【句长特点】平均{fp.sentence.avg_length:.0f}字/句，",
            f"短句{fp.sentence.short_ratio:.0%}，长句{fp.sentence.long_ratio:.0%}，",
            f"burstiness方差{fp.sentence.variance:.1f}（越大越像人写）",
            "",
            f"【第一人称】{fp.tone.first_person:.0%}使用'我/我们'，",
        ]
        if fp.tone.colloquial_markers:
            lines.append(f"口语化词：{', '.join(fp.tone.colloquial_markers[:3])}")
        else:
            lines.append("口语化词：较少")

        lines.extend([
            "",
            f"【段落结构】约{fp.structure.h2_count}个H2，",
            f"引用{fp.structure.quote_ratio:.0%}，列表{fp.structure.list_ratio:.0%}",
            "",
            f"【格式特征】表情{'有' if fp.format.has_emoji else '无'}，",
            f"配图说明：{fp.format.image_caption_style or '标准'}"
        ])

        if topic:
            lines.insert(0, f"基于当前主题「{topic}」，适配写作风格如下：\n")

        return "\n".join(lines)

    def _get_output_type(self) -> MessageType:
        return MessageType.STYLE


if __name__ == "__main__":
    # 测试
    agent = StyleLearnerAgent()

    result = agent.run({})

    if result.success:
        print("✅ 风格学习成功")
        print(f"分析了 {result.output['articles_analyzed']} 篇文章")
        print("\n--- 风格指纹 ---")
        print(json.dumps(result.output["style_fingerprint"], ensure_ascii=False, indent=2))
        print("\n--- 写作指令 ---")
        print(result.output["writing_instructions"])
        print("\n--- 摘要 ---")
        print(result.output["summary"])
    else:
        print(f"❌ 失败: {result.error}")
