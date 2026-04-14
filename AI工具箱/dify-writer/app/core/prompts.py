# Prompts loader with externalized prompt management
import json
from pathlib import Path
from typing import Optional

# Base prompts directory
PROMPTS_DIR = Path(__file__).parent.parent.parent / ".claude" / "skills" / "dify-writer" / "prompts"


class PromptsLoader:
    """
    Externalized prompts loader.
    Loads prompt templates from .claude/skills/dify-writer/prompts/
    """

    def __init__(self, prompts_dir: Optional[Path] = None):
        self.prompts_dir = prompts_dir or PROMPTS_DIR
        self._cache: dict[str, str] = {}

    def load(self, name: str) -> str:
        """
        Load prompt by name, e.g. 'deep_research' -> 'prompts/deep_research.md'
        """
        if name in self._cache:
            return self._cache[name]

        prompt_file = self.prompts_dir / f"{name}.md"
        if not prompt_file.exists():
            raise FileNotFoundError(f"Prompt not found: {prompt_file}")

        with open(prompt_file) as f:
            content = f.read()

        self._cache[name] = content
        return content

    def render(self, name: str, **kwargs) -> str:
        """
        Load and render prompt template with variables.
        Uses {{variable}} syntax.
        """
        template = self.load(name)
        for key, value in kwargs.items():
            template = template.replace(f"{{{{{key}}}}}", str(value))
        return template

    def reload(self, name: Optional[str] = None) -> None:
        """Clear cache for specific prompt or all prompts."""
        if name:
            self._cache.pop(name, None)
        else:
            self._cache.clear()


# Global instance
_prompts_loader: Optional[PromptsLoader] = None


def get_prompts_loader() -> PromptsLoader:
    global _prompts_loader
    if _prompts_loader is None:
        _prompts_loader = PromptsLoader()
    return _prompts_loader
