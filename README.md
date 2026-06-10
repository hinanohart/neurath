# neurath

[![ci](https://github.com/hinanohart/neurath/actions/workflows/ci.yml/badge.svg)](https://github.com/hinanohart/neurath/actions/workflows/ci.yml) [![license](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE) [![python](https://img.shields.io/badge/python-3.11%2B-blue)](pyproject.toml) [![release](https://img.shields.io/github/v/release/hinanohart/neurath)](https://github.com/hinanohart/neurath/releases)

**neurath** is a Python belief-revision library that bridges [NARS](https://www.opennars.org/) truth-value math and LLM-derived claims. When new evidence contradicts an existing belief, neurath computes the *minimum mutilation* revision plan — the smallest surgical edit that preserves the most of what was already believed.

Plain English: give neurath a set of beliefs (each tagged with a NARS `<frequency, confidence>` pair), connect them with typed edges, and when a contradiction arrives it will tell you *which belief to retract* and *why*, with the least collateral damage to the rest of the network.

> *"We are like sailors who on the open sea must reconstruct their ship but are never able to start afresh from the bottom."*
> — Otto Neurath, *Anti-Spengler* (1921), cited by W.V.O. Quine as the epigraph of *Word and Object*.

## Why neurath?

`NARS-Python` has truth-value math but no LLM I/O.
`LiteLLM` has LLM I/O but no truth-value math.
`DSPy` optimizes prompts but does not persist beliefs.

neurath fills the bridge: every LLM-derived claim becomes a NARS `<frequency, confidence>` node in a `networkx` graph, and a single new observation can trigger a global revision that surfaces *why* a particular belief had to be retracted.

## Quick start

### Install

A wheel + sdist (and a CycloneDX SBOM, from `v0.1.1` onward) are attached to each [GitHub Release](https://github.com/hinanohart/neurath/releases). For the latest `0.1.x`:

```bash
pip install https://github.com/hinanohart/neurath/releases/download/v0.1.1/neurath-0.1.1-py3-none-any.whl
```

For other versions, see the [Releases page](https://github.com/hinanohart/neurath/releases). Each tagged wheel is verified in a clean Python 3.12 venv as part of the release process.

PyPI publication is wired into `release.yml` via Trusted Publisher OIDC and will activate once the project is configured at [pypi.org/manage/account/publishing/](https://pypi.org/manage/account/publishing/). Until then, install from the GitHub Release URL above.

### Minimal example — holistic revision

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
plans = reviser.plan(ostriches_dont)   # ranked by mutilation_score
reviser.apply(plans[0])                # apply the cheapest plan

# Ask why the truth-value moved.
trace = Introspector(store).trace(birds_fly.id)
print(trace["revisions"][0]["rationale"])
```

### LLM-backed translation

`LLMTranslator` turns a natural-language claim into a NARS `TruthValue` via a JSON-mode LLM call (provider-agnostic through `litellm`):

```python
from neurath import LLMTranslator

translator = LLMTranslator(model="gpt-4o-mini")
estimate = translator.claim_to_truth("Penguins are birds that cannot fly")
print(estimate.truth)           # TruthValue(frequency=..., confidence=...)
print(estimate.justification)  # model's reasoning
```

You can inject a stub `completion_fn` to avoid live API calls in tests.

## How it works

### 1. Belief graph (`BeliefStore`)

Every belief is a Pydantic model holding a `statement` string and a NARS `TruthValue(frequency, confidence)`. Beliefs are stored as nodes in a `networkx.MultiDiGraph`; directed edges carry one of four relation types: `entails`, `contradicts`, `supports`, or `specializes`.

### 2. Truth-value algebra (`TruthValue`)

Implements NARS algebra: revision (`.revise()`), choice (keep higher evidence), negation, and expectation (`E = c(f − 0.5) + 0.5`). Property-based tests (Hypothesis) verify commutativity, associativity, confidence monotonicity, and the huge-evidence clamp.

### 3. Holistic revision (`HolisticReviser`)

When an observation arrives, `plan()` finds all beliefs connected via a `contradicts` edge, applies the NARS choice rule to each candidate, and scores each revision by:

```
mutilation_score = |ΔE| + propagation_weight × |ΔE| × |downstream beliefs|
```

Plans are returned sorted by ascending score. `apply()` commits the cheapest plan and records a `RevisionRecord` in the store's history.

### 4. Introspection (`Introspector`)

`why(belief_id)` returns the full revision history for a belief. `trace(belief_id)` bundles it with the current truth-value. `network_view()` exports the entire graph as a JSON-serialisable dict for visualisation or downstream processing.

## Architecture

```mermaid
flowchart TD
    NL[Natural language claim] --> LLMTranslator
    LLMTranslator -->|frequency + confidence| TruthValue
    TruthValue --> Belief
    Belief --> BeliefStore
    BeliefStore -->|networkx MultiDiGraph| Graph[Belief graph]
    Graph -->|contradicts edge| HolisticReviser
    HolisticReviser -->|ranked RevisionPlans| Planner[Minimum mutilation planner]
    Planner -->|apply cheapest plan| BeliefStore
    BeliefStore --> Introspector
    Introspector -->|why + trace + network_view| Output[JSON-serialisable audit trail]
```

## Quinean concepts in code

| Quine concept            | Layer                       |
|--------------------------|-----------------------------|
| Web of Belief            | `BeliefStore` (networkx)    |
| Duhem-Quine / Holism     | `HolisticReviser`           |
| Naturalized Epistemology | `Introspector.why()`        |

## Status — scaffold release (`0.1.x`)

The four layers are implemented and unit-tested (61 cases in `v0.1.1`, including Hypothesis property-based tests for the NARS algebra and Quinean-invariant tests for the planner).

### What is verified

- NARS truth-value algebra: commutativity, associativity, confidence monotonicity, negation involution, and the huge-evidence c→1 clamp.
- Holistic revision: ranked plans, mutilation scoring, in-place application with history recording; configurable `propagation_weight`; irrelevance preservation and rank-stability under irrelevant insertions.
- Introspection: `why()` / `trace()` / `network_view()` JSON-serialisable.
- Clean-venv install from the release wheel.

### Engineering limitations (please read before depending on this)

- **The Hase et al. 2024 numerical replication is not done.** The harness in `benchmark/` runs end-to-end, but a comparison with the paper's reported accuracies has not been carried out for any 0.1.x tag. The acceptance-inversion semantics are implemented at the conceptual level; numerical agreement is unproven.
- **No VCR cassettes; no LLM cost accounting.** `LLMTranslator` requires a live API call (or a stubbed `completion_fn` in tests). Replay-only CI for LLM-touching tests is deferred.
- **PyPI publication is gated on Trusted Publisher setup.** `pip install neurath` does not yet work; use the GitHub Release wheel.

### Conceptual gaps (the philosophy is sketched, not finished)

`v0.1.x` ships the *structure* into which Quinean revision fits, not a finished theory. To prevent overselling:

- **`mutilation_score` is a placeholder.** It is `|ΔE| · (1 + propagation_weight · |downstream|)` with `propagation_weight=0.1` by default. There is no semantic distance, no prior probability, no network centrality. A learned or topology-aware kernel is left for `v0.2`.
- **`plan()` returns one alternative per contradicting target, not a richer alternatives space.** It does not yet emit a "reject the observation" plan, joint revisions over connected components, or Duhemian auxiliary-hypothesis weakenings.
- **Introspection is per-belief change history.** `why()` returns the revisions on one belief; it does not yet walk the observation chain across beliefs or surface the meta-rules as first-class introspectable objects.
- **The `specializes` edge label is reserved but unused** by the planner — the taxonomy semantics are not yet wired into mutilation.
- **The LLM prompt is generic JSON estimation.** It does not yet flag observational vs theoretical claims (Quine, *Roots of Reference*) or request auxiliary-hypothesis annotations.

If you depend on any of these as "implemented," please pin to a future release that promotes the relevant item out of this list.

## License

MIT
