# Base agent class for all 9-agent pipeline
import json
import logging
import os
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class AgentResult:
    """Standard return type from all agents."""

    success: bool
    data: dict = field(default_factory=dict)
    error: str | None = None
    agent_name: str = ""

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "agent": self.agent_name,
            "data": self.data,
            "error": self.error,
        }


class BaseAgent(ABC):
    """
    Base class for all pipeline agents.

    Each agent:
    - Receives the shared data_bus dict
    - Reads relevant fields, writes outputs back to data_bus
    - Returns AgentResult
    """

    name: str = "base_agent"
    description: str = ""

    # LLM settings
    model: str = "claude-sonnet-4-6"
    max_tokens: int = 4096
    temperature: float = 0.7

    def __init__(self):
        self._client = None

    @property
    def client(self):
        """Lazy-init Anthropic client."""
        if self._client is None:
            import anthropic

            self._client = anthropic.Anthropic(
                api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
            )
        return self._client

    def _call_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> str:
        """
        Call Claude via Anthropic Messages API.
        Falls back to mock response when API key is absent.
        """
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            logger.warning(f"[{self.name}] ANTHROPIC_API_KEY not set — using mock response")
            return self._mock_response(user_prompt)

        response = self.client.messages.create(
            model=model or self.model,
            max_tokens=max_tokens or self.max_tokens,
            temperature=temperature or self.temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return response.content[0].text

    def _mock_response(self, user_prompt: str) -> str:
        """Return a structured mock response for development without API key."""
        return json.dumps({
            "mock": True,
            "agent": self.name,
            "input_length": len(user_prompt),
            "output": f"[Mock output from {self.name}]",
        })

    @abstractmethod
    def execute(self, context: dict) -> AgentResult:
        """
        Execute the agent's task.

        Args:
            context: Shared data_bus dict. Agent reads inputs from context,
                    writes outputs back to context, returns AgentResult.

        Returns:
            AgentResult with success=True/False and optional data dict.
        """
        ...

    def _extract_json(self, text: str) -> dict:
        """Extract JSON from LLM response text."""
        # Try direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try markdown code fence
        match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # Try first { ... } block
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end])
            except json.JSONDecodeError:
                pass

        return {"raw": text}

    def _read(self, context: dict, *keys: str, default: Any = None) -> Any:
        """Read nested keys from context, e.g. _read(ctx, "outline", "sections")."""
        val = context
        for k in keys:
            if isinstance(val, dict):
                val = val.get(k)
            else:
                return default
            if val is None:
                return default
        return val

    def _write(self, context: dict, key: str, value: Any) -> None:
        """Write a value to context[key]."""
        context[key] = value
