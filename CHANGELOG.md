# Changelog

All notable changes follow [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] — 2026-05-18 (scaffold release)

This is a scaffold / preview release. The four layers are implemented and the
release wheel installs cleanly in a fresh venv. The benchmark numbers from
Hase et al. 2024 are *not* yet reproduced for this tag — see Limitations in
the README for what is and is not verified.

### Added
- L1 — `TruthValue`: NARS `<frequency, confidence>` algebra (revision, choice,
  negation, expectation, evidence-space bijection); `Belief` and `BeliefStore`
  with networkx-backed web of beliefs and labelled edges
  (`entails` / `contradicts` / `supports` / `specializes`).
- L2 — `LLMTranslator`: provider-agnostic JSON-mode translator from
  natural-language claims to truth-values via LiteLLM, with an injectable
  completion seam for offline tests.
- L3 — `HolisticReviser`: ranked revision plans with `mutilation_score`
  combining direct expectation shift and a propagation penalty across
  `entails`/`supports` edges; `apply()` writes a `RevisionRecord`.
- L4 — `Introspector`: `why()` returns the ordered revision history;
  `trace()` emits a JSON-serialisable dict; `network_view()` emits node-link
  form for visualisation.
- Benchmark harness for the Hase 2024 LLM-belief-revision dataset
  (`python -m benchmark.runner`), with bootstrap 95% CI and dataset hash
  pinning. Numbers are not bundled — users reproduce locally.
- CI workflow: ruff + mypy + pytest on Python 3.11/3.12, plus CycloneDX SBOM.
- Release workflow: tag-driven build, GitHub Release with artifacts, optional
  PyPI Trusted Publisher publish.
- 56 unit tests, all property-based tests passing.

### Project
- Apache 2.0 license; Python ≥ 3.11; deps `networkx`, `pydantic`, `litellm`, `pyyaml`.

### Known limitations
- **Hase et al. 2024 numerical replication unfinished.** The harness runs;
  agreement with the published accuracies is unproven.
- **No VCR cassettes for LLM tests.** Real-API replay-only CI is deferred.
- **PyPI publish gated on Trusted Publisher.** Install via the GitHub Release
  wheel until the project is configured at pypi.org.
