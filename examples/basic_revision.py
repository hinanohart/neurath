"""A minimal end-to-end example of holistic belief revision in neurath.

Run with:

    python examples/basic_revision.py

It does not call any LLM — the LLMTranslator example lives in
`examples/llm_translation.py` because it needs an API key.
"""

from __future__ import annotations

import json

from neurath import (
    Belief,
    BeliefStore,
    HolisticReviser,
    Introspector,
    TruthValue,
)


def main() -> None:
    store = BeliefStore()

    # A confident generalisation about birds, and a counter-example.
    birds_fly = Belief(
        statement="Birds can fly.",
        truth=TruthValue(frequency=0.95, confidence=0.7),
    )
    ostriches_dont = Belief(
        statement="Ostriches cannot fly, and ostriches are birds.",
        truth=TruthValue(frequency=1.0, confidence=0.95),
    )
    store.add(birds_fly)
    store.add(ostriches_dont)
    store.link(ostriches_dont.id, birds_fly.id, "contradicts")

    # Plan the revision that least mutilates the rest of the web.
    reviser = HolisticReviser(store)
    plans = reviser.plan(ostriches_dont)
    cheapest = plans[0]
    print("Cheapest revision plan:")
    print(f"  target id: {cheapest.target_id}")
    print(f"  new truth: {cheapest.new_truth!r}")
    print(f"  mutilation_score: {cheapest.mutilation_score:.4f}")
    print(f"  rationale: {cheapest.rationale}")
    print()

    reviser.apply(cheapest, observation_id=ostriches_dont.id)

    # Introspect why the truth-value moved.
    trace = Introspector(store).trace(birds_fly.id)
    print("Trace for 'birds can fly' after revision:")
    print(json.dumps(trace, indent=2))


if __name__ == "__main__":
    main()
