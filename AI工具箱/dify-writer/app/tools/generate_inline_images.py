# generate_inline_images tool (stub)
from app.tools.base import BaseTool


class GenerateInlineImagesTool(BaseTool):
    """Generate inline images for article content."""

    name = "generate_inline_images"
    description = "Generate inline images for article sections."

    def execute(
        self,
        article: str,
        style: dict | None = None,
        platform: str = "wechat",
        session_id: str | None = None,
        **kwargs,
    ) -> dict:
        """
        Generate inline images based on article content.

        Returns list of local_image_paths.
        """
        # TODO: Implement Jimeng API integration
        return {
            "local_paths": [],
            "status": "stub",
            "message": "Jimeng API not configured. Set JIMENG_API_KEY environment variable.",
            "count": 0,
        }
