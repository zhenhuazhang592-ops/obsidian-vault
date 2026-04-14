# format_html tool
from app.tools.base import BaseTool


class FormatHtmlTool(BaseTool):
    """Format article as HTML for WeChat."""

    name = "format_html"
    description = "Format article as WeChat-compatible HTML."

    def execute(
        self,
        article: str,
        images: list[str] | None = None,
        theme: str = "default",
        session_id: str | None = None,
        **kwargs,
    ) -> dict:
        """
        Format article as HTML with WeChat-compatible styling.

        WeChat official specs:
        - Cover: 900×383px (2.35:1)
        - Content width: 900px max
        - Font: 16px, line-height: 1.6
        """
        html = self._build_html(article, images, theme)

        return {
            "html_string": html,
            "status": "success",
            "word_count": len(article),
            "image_count": len(images) if images else 0,
        }

    def _build_html(
        self,
        article: str,
        images: list[str] | None,
        theme: str,
    ) -> str:
        """Build WeChat-compatible HTML."""
        # Simple HTML template with WeChat-compatible styling
        paragraphs = article.split("\n\n")
        content_html = "\n".join(
            f'<p>{p.strip()}</p>' for p in paragraphs if p.strip()
        )

        images_html = ""
        if images:
            images_html = "\n".join(
                f'<figure><img src="{img}" alt="cover"/></figure>'
                for img in images
            )

        return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif; font-size: 16px; line-height: 1.8; color: #333; max-width: 900px; margin: 0 auto; padding: 20px; }}
p {{ margin: 1em 0; text-align: justify; }}
img {{ max-width: 100%; height: auto; display: block; margin: 1em auto; }}
figure {{ margin: 1em 0; text-align: center; }}
</style>
</head>
<body>
{images_html}
{content_html}
</body>
</html>"""
