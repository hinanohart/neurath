"""LLM-backed translator between natural-language claims and NARS truth-values."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from neurath.llm.prompts import claim_to_truth_messages
from neurath.store.truth import TruthValue


class TranslationError(RuntimeError):
    """Raised when the LLM response cannot be parsed into a TruthValue."""


class _LLMResponse(BaseModel):
    """Schema that the model must return."""

    model_config = ConfigDict(extra="forbid")

    frequency: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, lt=1.0)
    justification: str


@dataclass(frozen=True, slots=True)
class TruthEstimate:
    """A truth-value together with the model's justification and call metadata."""

    truth: TruthValue
    justification: str
    model: str
    raw_response: str


class LLMTranslator:
    """Translate claims to NARS truth-values via a JSON-mode LLM call.

    The completion function is injected so tests can stub it without going
    through the network. By default it is `litellm.completion`, which gives
    us provider-agnostic access (OpenAI, Anthropic, local models, …).
    """

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        *,
        temperature: float = 0.0,
        completion_fn: Any = None,
    ) -> None:
        self.model = model
        self.temperature = temperature
        self._completion_fn = completion_fn or _default_completion

    def claim_to_truth(self, claim: str, context: str | None = None) -> TruthEstimate:
        """Ask the model for a `<frequency, confidence>` estimate of `claim`."""
        if not claim or not claim.strip():
            raise ValueError("claim must be a non-empty string")

        messages = claim_to_truth_messages(claim, context)
        raw = self._completion_fn(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            response_format={"type": "json_object"},
        )
        content = _extract_content(raw)

        try:
            parsed = _LLMResponse.model_validate_json(content)
        except (ValidationError, json.JSONDecodeError) as exc:
            raise TranslationError(
                f"could not parse LLM response into <freq, conf>: {content!r}"
            ) from exc

        truth = TruthValue(frequency=parsed.frequency, confidence=parsed.confidence)
        return TruthEstimate(
            truth=truth,
            justification=parsed.justification,
            model=self.model,
            raw_response=content,
        )


# helpers ------------------------------------------------------------------


def _default_completion(**kwargs: Any) -> Any:
    """Import-time lazy: only import litellm when actually needed."""
    import litellm

    return litellm.completion(**kwargs)


def _extract_content(response: Any) -> str:
    """Pull `choices[0].message.content` out of a LiteLLM-shaped response."""
    try:
        return response["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise TranslationError(f"unexpected LLM response shape: {response!r}") from exc
