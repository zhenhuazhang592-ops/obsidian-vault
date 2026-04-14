# generate_cover tool (stub)
from app.tools.base import BaseTool


class GenerateCoverTool(BaseTool):
    """Generate cover image using Jimeng/Jiemeng API."""

    name = "generate_cover"
    description = "Generate cover image for article."

    def execute(
        self,
        spec: dict,
        platform: str = "wechat",
        session_id: str | None = None,
        **kwargs,
    ) -> dict:
        """
        Generate cover image.

        Wechat: 900×383px (2.35:1)
        XHS: 1242×1660px (3:4)

        Returns local_image_path or error.
        """
        # TODO: Implement Jimeng API integration
        # Until API key is available, return stub response
        return {
            "local_image_path": None,
            "status": "stub",
            "message": "Jimeng API not configured. Set JIMENG_API_KEY environment variable.",
            "spec": spec,
        }
