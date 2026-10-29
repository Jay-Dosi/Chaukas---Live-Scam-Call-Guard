"""LLM Assessor — optional second opinion with strict bounds.

PRD §6.6, §8.3:
- Called at most once every 6s, only when level >= caution or >=40 new tokens
- 3s timeout, max_tokens <= 300
- Blend: 0.7*rule + 0.3*llm, clamp
- LLM can raise by +20, lower by -15, never below hard floor
- Transcript only in user message, never system prompt
"""

from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass

try:
    from anthropic import AsyncAnthropic
except Exception:
    AsyncAnthropic = None

from chaukas.config import get_settings
from chaukas.llm.prompt import SYSTEM_PROMPT, build_user_prompt
from chaukas.models.base import LlmAssessment


@dataclass
class LlmAssessor:
    """Manages optional LLM assessment calls."""

    client: AsyncAnthropic | None = None
    enabled: bool = False
    model: str = "claude-haiku-5-5"
    _last_call_ms: int = 0

    def __init__(self):
        settings = get_settings()
        self.enabled = settings.resolved_llm_enabled()
        self.model = settings.llm_model
        if self.enabled and settings.anthropic_api_key and AsyncAnthropic is not None:
            self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        else:
            self.client = None
            self.enabled = False

    async def assess(self, transcript: str, lang: str, rule_score: int, hard_floor: int) -> LlmAssessment | None:
        """Assess transcript and return classification, or None if disabled/failed."""
        if not self.enabled or not self.client:
            return None

        now = int(asyncio.get_event_loop().time() * 1000)
        if now - self._last_call_ms < 6000:
            return None  # rate limit

        self._last_call_ms = now

        try:
            response = await asyncio.wait_for(
                self.client.messages.create(
                    model=self.model,
                    system=SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": build_user_prompt(transcript, lang)}],
                    max_tokens=256,
                    temperature=0,
                ),
                timeout=3.0,
            )

            # Parse response
            text = response.content[0].text if response.content else "{}"
            # Strip potential code fences
            if "```" in text:
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]

            data = json.loads(text)

            # Validate
            assessment = LlmAssessment(**data)

            # Apply blend bounds
            blended = int(round(0.7 * rule_score + 0.3 * (100 * assessment.scam_probability)))
            delta = blended - rule_score

            if delta > 20:
                blended = rule_score + 20
            elif delta < -15:
                blended = rule_score - 15

            if hard_floor > 0:
                blended = max(blended, hard_floor)

            # Return adjusted assessment (engine will re-blend)
            return assessment

        except Exception:
            return None