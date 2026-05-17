# neurath

> *"We are like sailors who on the open sea must reconstruct their ship but are never able to start afresh from the bottom."*
> — Otto Neurath, *Anti-Spengler* (1921), cited by W.V.O. Quine as the epigraph of *Word and Object*.

**neurath** is a belief revision library that bridges [NARS](https://www.opennars.org/) truth-value math and LLM belief tracking. When new evidence contradicts an LLM's belief web, neurath computes the *minimum mutilation* revision plan — the surgical edit that preserves the most of what was already believed.

It embodies three concepts from W.V.O. Quine's philosophy in working code:

| Quine concept            | Layer                       |
|--------------------------|-----------------------------|
| Web of Belief            | `BeliefStore` (networkx)    |
| Duhem-Quine / Holism     | `HolisticReviser`           |
| Naturalized Epistemology | `Introspector.why()`        |

## Why neurath?

`NARS-Python` has truth-value math but no LLM I/O.
`LiteLLM` has LLM I/O but no truth-value math.
`DSPy` optimizes prompts but does not persist beliefs.

neurath fills the bridge: every LLM-derived claim becomes a NARS `<frequency, confidence>` node in a `networkx` graph, and a single new observation can trigger a global revision that surfaces *why* a particular belief had to be retracted.

## Quick start

```python
from neurath import (
    Belief, BeliefStore, HolisticReviser, Introspector, TruthValue,
)

store = BeliefStore()

# Two beliefs that contradict each other.
birds_fly = Belief(statement="birds can fly",
                   truth=TruthValue(frequency=0.95, confidence=0.7))
ostriches_dont = Belief(statement="ostriches cannot fly",
                        truth=TruthValue(frequency=1.0, confidence=0.95))
store.add(birds_fly)
store.add(ostriches_dont)
store.link(ostriches_dont.id, birds_fly.id, "contradicts")

# Plan the revision that least mutilates the web.
reviser = HolisticReviser(store)
plans = reviser.plan(ostriches_dont)            # ranked by mutilation_score
reviser.apply(plans[0])                          # apply the cheapest

# Ask why the truth-value moved.
trace = Introspector(store).trace(birds_fly.id)
print(trace["revisions"][0]["rationale"])
```

For the LLM-backed translator that turns natural-language claims into NARS
truth-values, see `neurath.LLMTranslator`.

## Status

`v0.1.0` — alpha. The four layers (BeliefStore, LLMTranslator, HolisticReviser,
Introspector) are implemented and unit-tested (Hypothesis property-based for the
NARS algebra). The Hase 2024 benchmark harness is in `benchmark/`; numbers are
not yet published with the release — see `benchmark/README.md` to reproduce.

## License

Apache 2.0
