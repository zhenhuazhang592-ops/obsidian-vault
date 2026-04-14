# Safe JSON parsing with 2-retry fallback
import json
import re
from typing import Any, Optional


def safe_json_parse(content: str, schema: Optional[dict] = None) -> dict:
    """
    Parse JSON with 2-retry fallback for LLM output.

    LLM outputs often include:
    - Markdown code fences: ```json ... ```
    - Trailing commas
    - Comments

    Strategy:
    1. Try direct json.loads
    2. Strip markdown fences, retry
    3. Strip trailing commas, retry
    4. Return {"text": content} as fallback
    """
    if not content or not content.strip():
        return {"text": ""}

    # First attempt: direct parse
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    # Second attempt: strip markdown code fences
    cleaned = re.sub(r"^```(?:json)?\s*", "", content.strip())
    cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Third attempt: remove trailing commas
    cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Fallback: return as text field
    return {"text": content.strip()}


def extract_json_from_text(text: str) -> Optional[dict]:
    """Extract first JSON object from mixed text (e.g., LLM output with explanation)."""
    match = re.search(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    return None
