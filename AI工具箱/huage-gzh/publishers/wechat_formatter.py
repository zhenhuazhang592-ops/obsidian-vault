# publishers/wechat_formatter.py - 微信公众号HTML排版器
# Phase 4: 公众号原生排版风格 + 图片占位符 + 话题标签

import re
from typing import Optional


WECHAT_CSS = """
<style>
    /* 漠玫创作 · 公众号排版样式 */
    body {
        font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", sans-serif;
        font-size: 16px;
        line-height: 1.8;
        color: #333;
        max-width: 677px;
        margin: 0 auto;
        padding: 20px 15px;
        background: #fff;
    }
    h1 {
        font-size: 24px;
        font-weight: bold;
        text-align: center;
        margin: 20px 0 10px 0;
        color: #1a1a1a;
        line-height: 1.4;
    }
    .article-meta {
        text-align: center;
        color: #999;
        font-size: 13px;
        margin-bottom: 25px;
        padding-bottom: 15px;
        border-bottom: 1px solid #eee;
    }
    .article-meta span {
        margin: 0 8px;
    }
    h2 {
        font-size: 18px;
        font-weight: bold;
        margin: 28px 0 12px 0;
        color: #1a1a1a;
        border-left: 3px solid #555;
        padding-left: 10px;
        line-height: 1.5;
    }
    p {
        margin: 12px 0;
        text-align: justify;
        text-indent: 2em;
        line-height: 1.8;
        font-size: 15px;
        color: #333;
    }
    /* 封面图 */
    .cover-image {
        width: 100%;
        max-width: 677px;
        margin: 0 auto 20px auto;
        display: block;
    }
    .cover-image img {
        width: 100%;
        height: auto;
        display: block;
    }
    /* 内嵌图片 */
    .image-placeholder {
        background: #f5f5f5;
        border: 1px dashed #ccc;
        border-radius: 4px;
        padding: 30px 20px;
        text-align: center;
        margin: 20px 0;
        color: #999;
        font-size: 13px;
    }
    .image-placeholder .caption {
        margin-top: 8px;
        font-size: 12px;
        color: #bbb;
    }
    /* 引用块 */
    blockquote {
        margin: 15px 0;
        padding: 10px 15px;
        background: #f7f7f7;
        border-left: 3px solid #555;
        color: #555;
        font-size: 14px;
        line-height: 1.7;
        text-indent: 0;
    }
    /* 加粗 */
    strong {
        color: #1a1a1a;
        font-weight: bold;
    }
    /* 列表 */
    ul, ol {
        margin: 10px 0;
        padding-left: 1.5em;
        font-size: 15px;
        color: #333;
    }
    li {
        margin: 5px 0;
        line-height: 1.7;
    }
    /* 分割线 */
    hr {
        border: none;
        border-top: 1px solid #eee;
        margin: 25px 0;
    }
    /* 话题标签 */
    .hashtags {
        margin: 30px 0 20px 0;
        padding: 15px 0;
        border-top: 1px solid #eee;
        font-size: 13px;
        color: #555;
    }
    .hashtags a {
        color: #576b95;
        text-decoration: none;
        margin-right: 10px;
    }
    .hashtags a:hover {
        text-decoration: underline;
    }
    /* 尾部信息 */
    .footer {
        margin-top: 30px;
        padding-top: 20px;
        border-top: 1px solid #eee;
        text-align: center;
        color: #999;
        font-size: 12px;
    }
    .footer .qr {
        width: 120px;
        height: 120px;
        margin: 10px auto;
        background: #f5f5f5;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #ccc;
        font-size: 11px;
    }
    /* 端网文摘 */
    .quote-block {
        margin: 20px 0;
        padding: 15px 20px;
        background: #fafafa;
        border-radius: 4px;
        font-style: italic;
        color: #666;
        text-indent: 0;
        font-size: 14px;
        line-height: 1.7;
    }
    /* 图片说明 */
    .image-caption {
        text-align: center;
        color: #999;
        font-size: 12px;
        margin-top: -10px;
        margin-bottom: 20px;
    }
</style>
"""


class WechatFormatter:
    """
    微信公众号HTML格式化器

    功能：
    - Markdown → 公众号HTML
    - 封面图占位符
    - 配图占位符
    - 话题标签生成
    - 尾部落款
    """

    def __init__(self, account_name: str = "漠玫创作"):
        self.account_name = account_name

    def format(
        self,
        title: str,
        content: str,
        author: str = "",
        publish_date: str = "",
        cover_image_path: Optional[str] = None,
        image_placeholders: list[dict] = None,
        hashtags: list[str] = None,
        include_qr: bool = False,
    ) -> str:
        """
        将Markdown文章格式化为公众号HTML。

        Args:
            title: 文章标题
            content: Markdown正文
            author: 作者
            publish_date: 发布日期
            cover_image_path: 封面图路径（可选）
            image_placeholders: [{"path": str, "caption": str}] 配图占位列表
            hashtags: 话题标签列表
            include_qr: 是否包含二维码占位

        Returns:
            完整HTML字符串
        """
        image_placeholders = image_placeholders or []
        hashtags = hashtags or []

        # 封面图
        cover_html = ""
        if cover_image_path:
            cover_html = f'''
<div class="cover-image">
    <img src="{cover_image_path}" alt="封面图">
</div>'''
        elif cover_image_path is False:
            # 用户明确不想要封面图
            pass

        # Meta信息
        meta_parts = []
        if publish_date:
            meta_parts.append(f'<span>📅 {publish_date}</span>')
        if author:
            meta_parts.append(f'<span>✍️ {author}</span>')
        meta_parts.append(f'<span>📖 {self._count_words(content)}字</span>')

        meta_html = ""
        if meta_parts:
            meta_html = f'''
<div class="article-meta">
    {"".join(meta_parts)}
</div>'''

        # Markdown → HTML
        body_html = self._markdown_to_html(content, image_placeholders)

        # 话题标签
        hashtags_html = ""
        if hashtags:
            tag_links = "".join(
                f'<a href="#">#{tag}</a>' for tag in hashtags
            )
            hashtags_html = f'''
<div class="hashtags">
    {tag_links}
</div>'''

        # 尾部落款
        footer_html = ""
        if include_qr:
            footer_html = f'''
<div class="footer">
    <p>—— {self.account_name} ——</p>
    <div class="qr">[二维码占位]</div>
    <p>长按识别二维码，关注公众号</p>
</div>'''
        else:
            footer_html = f'''
<div class="footer">
    <p>—— {self.account_name} ——</p>
</div>'''

        html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta name="description" content="{self._escape_html(title)}">
    <title>{self._escape_html(title)}</title>
    {WECHAT_CSS}
</head>
<body>
    <h1>{self._escape_html(title)}</h1>
    {meta_html}
    {cover_html}
    {body_html}
    {hashtags_html}
    {footer_html}
</body>
</html>'''

        return html

    def _markdown_to_html(self, md: str, image_placeholders: list[dict]) -> str:
        """将Markdown转换为HTML"""
        html = md

        # 处理标题
        html = re.sub(r'^#### (.+)$', r'<h4>\1</h4>', html, flags=re.MULTILINE)
        html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)

        # 处理加粗
        html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)

        # 处理图片占位符 <!-- IMAGE: caption -->
        img_idx = [0]

        def replace_image(m):
            idx = img_idx[0]
            img_idx[0] += 1
            if idx < len(image_placeholders):
                placeholder = image_placeholders[idx]
                caption = placeholder.get("caption", "")
                return f'''<div class="image-placeholder">
    📷 图片{idx + 1}
    <div class="caption">{caption}</div>
</div>'''
            return '<div class="image-placeholder">📷 图片占位符</div>'

        # 处理 ![alt](url) 格式的图片
        def replace_md_image(m):
            alt = m.group(1)
            url = m.group(2)
            idx = img_idx[0]
            img_idx[0] += 1
            if url.startswith("http"):
                return f'<img src="{url}" alt="{alt}" style="max-width:100%;margin:20px 0;">'
            if idx < len(image_placeholders):
                caption = image_placeholders[idx].get("caption", alt)
                return f'''<div class="image-placeholder">
    📷 {alt}
    <div class="caption">{caption}</div>
</div>'''
            return f'''<div class="image-placeholder">
    📷 {alt}
</div>'''

        html = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', replace_md_image, html)

        # 处理引用块 > quote
        html = re.sub(r'^> (.+)$', r'<blockquote>\1</blockquote>', html, flags=re.MULTILINE)

        # 处理分割线
        html = re.sub(r'^---+$', '<hr>', html, flags=re.MULTILINE)
        html = re.sub(r'^\*\*\*+$', '<hr>', html, flags=re.MULTILINE)

        # 处理列表
        html = re.sub(r'^- (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)
        html = re.sub(r'^(\d+)\. (.+)$', r'<li>\2</li>', html, flags=re.MULTILINE)

        # 包裹连续li为ul
        html = re.sub(r'(<li>.*?</li>\n?)+', lambda m: f'<ul>{m.group()}</ul>', html, flags=re.DOTALL)

        # 处理段落（双换行分割）
        paragraphs = re.split(r'\n\n+', html)
        processed = []
        for p in paragraphs:
            p = p.strip()
            if not p:
                continue
            # 已经是块级元素的不需要包裹
            if re.match(r'^<(h[1-6]|ul|ol|blockquote|hr|div)', p):
                processed.append(p)
            else:
                # 换行替换为空格（处理单换行）
                p = re.sub(r'\n', ' ', p)
                processed.append(f'<p>{p}</p>')

        return '\n'.join(processed)

    def _count_words(self, text: str) -> int:
        """统计中文字数"""
        chinese = re.findall(r'[\u4e00-\u9fff]', text)
        return len(chinese)

    def _escape_html(self, text: str) -> str:
        """HTML转义"""
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )

    def generate_hashtags(self, keywords: list[str] = None, count: int = 3) -> list[str]:
        """
        根据关键词生成话题标签。

        Args:
            keywords: SEO关键词列表
            count: 生成数量

        Returns:
            话题标签列表
        """
        tags = []
        if keywords:
            for kw in keywords[:count]:
                # 去掉太长的关键词
                if len(kw) <= 6:
                    tags.append(kw)
                else:
                    # 取前5字
                    tags.append(kw[:5])
        return tags


def format_wechat_article(
    title: str,
    content: str,
    **kwargs,
) -> str:
    """
    快捷函数：格式化为公众号HTML。
    """
    formatter = WechatFormatter()
    return formatter.format(title, content, **kwargs)
