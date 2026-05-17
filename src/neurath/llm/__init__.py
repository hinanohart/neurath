"""L2 — LLM Adapter: translates natural-language claims to NARS truth-values."""

from neurath.llm.adapter import LLMTranslator, TranslationError, TruthEstimate

__all__ = ["LLMTranslator", "TranslationError", "TruthEstimate"]
