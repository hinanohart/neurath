"""Tests for the LLM Adapter using injected fake completion functions.

Real LLM calls are exercised by the benchmark suite, not by unit tests.
"""

from __future__ import annotations

import pytest

from neurath.llm import LLMTranslator, TranslationError
from neurath.store.truth import TruthValue


def fake_completion(payload: str):
    """Return a callable that mimics `litellm.completion` and yields `payload`."""

    def _call(**_kwargs):
        return {"choices": [{"message": {"content": payload}}]}

    return _call


class TestClaimToTruth:
    def test_well_formed_response_parses(self) -> None:
        translator = LLMTranslator(
            completion_fn=fake_completion(
                '{"frequency": 0.85, "confidence": 0.6, "justification": "ok"}'
            )
        )
        estimate = translator.claim_to_truth("Socrates is mortal.")
        assert estimate.truth == TruthValue(frequency=0.85, confidence=0.6)
        assert estimate.justification == "ok"
        assert estimate.model == "gpt-4o-mini"

    def test_context_is_passed_through(self) -> None:
        captured: dict[str, list[dict[str, str]]] = {}

        def capture(**kwargs):
            captured["messages"] = kwargs["messages"]
            return {
                "choices": [
                    {
                        "message": {
                            "content": '{"frequency": 0.5, "confidence": 0.0, "justification": ""}'
                        }
                    }
                ]
            }

        LLMTranslator(completion_fn=capture).claim_to_truth(
            "It will rain tomorrow.", context="Cloudy sky now."
        )
        user_msg = captured["messages"][1]["content"]
        assert "Cloudy sky now." in user_msg

    def test_empty_claim_rejected(self) -> None:
        translator = LLMTranslator(completion_fn=fake_completion("{}"))
        with pytest.raises(ValueError, match="non-empty"):
            translator.claim_to_truth("   ")

    def test_invalid_json_raises_translation_error(self) -> None:
        translator = LLMTranslator(completion_fn=fake_completion("not-json"))
        with pytest.raises(TranslationError, match="could not parse"):
            translator.claim_to_truth("any")

    def test_out_of_range_frequency_raises(self) -> None:
        translator = LLMTranslator(
            completion_fn=fake_completion(
                '{"frequency": 1.5, "confidence": 0.5, "justification": ""}'
            )
        )
        with pytest.raises(TranslationError):
            translator.claim_to_truth("any")

    def test_confidence_at_one_raises(self) -> None:
        translator = LLMTranslator(
            completion_fn=fake_completion(
                '{"frequency": 0.5, "confidence": 1.0, "justification": ""}'
            )
        )
        with pytest.raises(TranslationError):
            translator.claim_to_truth("any")

    def test_extra_fields_rejected(self) -> None:
        translator = LLMTranslator(
            completion_fn=fake_completion(
                '{"frequency": 0.5, "confidence": 0.5, "justification": "", "bonus": 1}'
            )
        )
        with pytest.raises(TranslationError):
            translator.claim_to_truth("any")

    def test_malformed_response_shape_raises(self) -> None:
        def bad(**_kwargs):
            return {"choices": []}

        translator = LLMTranslator(completion_fn=bad)
        with pytest.raises(TranslationError, match="response shape"):
            translator.claim_to_truth("any")
