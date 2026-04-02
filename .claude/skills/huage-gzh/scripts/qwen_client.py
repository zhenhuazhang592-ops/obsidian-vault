#!/usr/bin/env python3
"""
Qwen3-Max 客户端 - 华哥公众号 huage-gzh 核心推理引擎
通过 DashScope API 调用 Qwen3-Max（qwen-max 模型）
"""

import os
import json
from typing import Optional

try:
    from openai import OpenAI
    _HAS_OPENAI = True
except ImportError:
    _HAS_OPENAI = False


class QwenClient:
    """Qwen3-Max API 客户端"""

    def __init__(self, api_key: Optional[str] = None):
        if not _HAS_OPENAI:
            raise RuntimeError("openai package required: pip install openai")

        self.api_key = api_key or os.environ.get("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "DASHSCOPE_API_KEY not set. "
                "Set it via: export DASHSCOPE_API_KEY=your_key"
            )

        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )

    def chat(
        self,
        messages: list,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        model: str = "qwen-max",
    ) -> str:
        """
        发送对话请求到 Qwen3-Max

        Args:
            messages: [{"role": "system"|"user"|"assistant", "content": str}, ...]
            temperature: 创造性写作用 0.7，精确分析用 0.3
            max_tokens: 最大输出 token 数
            model: 模型名称，默认 qwen-max（Qwen3-Max）

        Returns:
            模型回复的文本内容
        """
        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content

    def research_analyze(self, research_content: str, topic: str) -> str:
        """研究分析：Qwen3-Max 阅读研究材料，生成洞察摘要"""
        system = """你是一个专业的内容研究员。你的任务是将收集到的研究材料进行分析，
提取核心洞察，识别不同观点和立场，并生成供写作使用的摘要。

输出格式：
- 核心发现（3-5条）
- 关键数据点（带来源）
- 不同观点摘要（含反面证据）
- 可引用的金句和引用"""

        return self.chat(
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": f"主题：{topic}\n\n研究材料：\n{research_content}"}
            ],
            temperature=0.3,
            max_tokens=2048,
        )

    def generate_style_options(self) -> str:
        """生成4种预设风格描述，供用户选择"""
        system = """你是一个专业公众号内容策划师。根据华哥公众号的风格体系，
生成4种预设写作风格供用户选择。

每种风格输出：风格名称、特点描述、适用场景、语气示例。"""
        return self.chat(
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": "请输出4种预设风格：亲和力强、专业严谨、幽默风趣、极简干货。"}
            ],
            temperature=0.8,
            max_tokens=2048,
        )

    def generate_titles_and_outline(
        self,
        topic: str,
        style: str,
        research_summary: str,
    ) -> str:
        """生成3个标题选项 + 完整大纲"""
        system = """你是一个专业公众号内容策划师，擅长生成爆款标题和结构化大纲。

任务：根据主题、选定风格和研究摘要，一次性输出：
1. 3个爆款标题（覆盖不同类型：冲突对比/疑问引导/数字效果/否定反转）
2. 完整文章大纲（Markdown格式：H1标题 + H2核心论点 + H3小节）

格式要求：
```
## 标题选项

### 选项1：[标题]（类型：冲突对比）
### 选项2：[标题]（类型：疑问引导）
### 选项3：[标题]（类型：数字效果/否定反转）

## 大纲（基于用户选定的标题）

# [H1标题]
## [H2核心论点1]
### [H3小节1.1]
### [H3小节1.2]
## [H2核心论点2]
...
```
"""
        return self.chat(
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": f"主题：{topic}\n选定风格：{style}\n\n研究摘要：\n{research_summary}"}
            ],
            temperature=0.8,
            max_tokens=4096,
        )

    def write_article(
        self,
        topic: str,
        style: str,
        outline: str,
        research_summary: str,
        anti_ai_rules: str,
    ) -> str:
        """正文写作：严格遵循去AI味规则"""
        system = f"""你是一个资深公众号内容创作者，写作风格为：{style}。

你的核心原则：**每一句话都必须像真人写的，不能有任何AI味。**

{anti_ai_rules}

字数要求：目标 1500-2500 字，最多 3000 字。

Markdown格式：
- H1：标题（文章标题）
- H2：核心论点（每个论点一个H2）
- H3：小节（克制使用，每个H2最多1-2个H3）
- 不用 `---` 分割线
- 图片占位：`![配图描述](图片文件路径)`

写作流程：
1. 先在脑海中按大纲展开每个论点
2. 写每段时问自己："这像不像真人写的？"
3. 写完后通读，检查是否有AI高频词
4. 确保节奏有变化（长短段落交替）
"""
        return self.chat(
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": f"主题：{topic}\n\n选定风格：{style}\n\n确认的大纲：\n{outline}\n\n研究摘要（仅作参考，不直接引用，可化用数据和观点）：\n{research_summary}\n\n请开始写正文。"}
            ],
            temperature=0.7,
            max_tokens=8192,
        )

    def plan_image_scheme(
        self,
        article_content: str,
        topic: str,
    ) -> str:
        """规划配图方案：封面 + 内文配图"""
        system = """你是一个专业的内容视觉策划师。根据文章内容，规划配图方案。

输出格式：
```
## 封面图

- 类型：[概念图/场景图/信息图/摄影风]
- 风格：[写实/插画/中国风/极简]
- 配色关键词：[3-5个颜色关键词]
- 画面描述：[50字以内的画面描述，用于生成提示词]
- 尺寸：900x500px

## 文章配图（共N张）

### 配图1：[位置：H2核心论点1之后]
- 类型：[信息图/场景/对比]
- 风格：[与封面保持一致的风格]
- 画面描述：[30字]

### 配图2：[位置：H2核心论点2之后]
...
```
"""
        return self.chat(
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": f"主题：{topic}\n\n文章内容：\n{article_content}"}
            ],
            temperature=0.5,
            max_tokens=2048,
        )


def main():
    """CLI 入口：python qwen_client.py <method> [args...]"""
    import sys
    client = QwenClient()

    if len(sys.argv) < 2:
        print("Usage: python qwen_client.py <method> [args...]")
        print("Methods: research_analyze, generate_style_options, generate_titles_and_outline, write_article, plan_image_scheme")
        sys.exit(1)

    method = sys.argv[1]

    if method == "generate_style_options":
        print(client.generate_style_options())
    elif method == "research_analyze" and len(sys.argv) >= 4:
        content = sys.argv[2]
        topic = sys.argv[3]
        print(client.research_analyze(content, topic))
    elif method == "generate_titles_and_outline" and len(sys.argv) >= 5:
        topic = sys.argv[2]
        style = sys.argv[3]
        research = sys.argv[4]
        print(client.generate_titles_and_outline(topic, style, research))
    elif method == "write_article" and len(sys.argv) >= 6:
        topic = sys.argv[2]
        style = sys.argv[3]
        outline = sys.argv[4]
        research = sys.argv[5]
        anti_ai = sys.argv[6] if len(sys.argv) >= 7 else ""
        print(client.write_article(topic, style, outline, research, anti_ai))
    elif method == "plan_image_scheme" and len(sys.argv) >= 4:
        article = sys.argv[2]
        topic = sys.argv[3]
        print(client.plan_image_scheme(article, topic))
    else:
        print(f"Unknown method or missing args: {sys.argv}")
        sys.exit(1)


if __name__ == "__main__":
    main()
