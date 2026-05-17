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

## Status

Pre-alpha. `v0.1.0` targets:

- L1 BeliefStore with NARS truth-value algebra
- L2 LiteLLM-backed claim ↔ truth-value translator
- L3 Holistic revision with `minimum_mutilation` scoring
- L4 `belief.why()` introspection
- Reproducible baseline numbers on the [Hase 2024 LLM-belief-revision dataset](https://github.com/peterbhase/LLM-belief-revision)

## License

Apache 2.0
