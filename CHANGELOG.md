# Changelog

All notable changes follow [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] — 2026-05-18 (post-release audit fixes)

A same-day patch release that fixes defects surfaced by a 3-agent
post-release audit and adds honest disclosure of the philosophical scope of
`0.1.x`. No public API was removed; one constructor argument was added.

### Fixed
- `BeliefStore.link`: dropped the explicit `key=kind` on the underlying
  `MultiDiGraph`, so two `link(a, b, "entails")` calls now record two edges
  instead of silently collapsing into one.
- `benchmark/runner.py` now passes `observation_id` into `reviser.apply`, so
  benchmark traces preserve the observation chain that powers
  `Introspector.trace`.
- `HolisticReviser` no longer uses a runtime-local import of `RevisionRecord`;
  the record type was promoted to `neurath.store.history.RevisionRecord` so
  the L3 → L4 dependency is gone and the planner has no implicit coupling
  to the introspection module.
- `RevisionRecord.timestamp` now uses `dataclasses.field(default_factory=...)`,
  removing the `object.__setattr__` post-init workaround that was tampering
  with `frozen=True` semantics.
- `release.yml`: `pypi_publish` now `needs: [build, github_release]` so PyPI
  never publishes ahead of (or in parallel with) the GitHub Release.
- `release.yml`: CycloneDX SBOM is generated at release time and attached as
  a release asset (`sbom.cyclonedx.json`), not just kept as a CI artifact.

### Added
- `HolisticReviser(propagation_weight=…)` — the constant is now a constructor
  argument; the module-level `PROPAGATION_WEIGHT` remains as the default.
- Direct test of the huge-evidence c→1 clamp in
  `TruthValue.from_evidence`.
- Quinean-invariant tests: `irrelevance_preservation` (revising a
  disconnected belief leaves all bystanders bit-identical) and
  `plan_rank_invariant_under_irrelevant_insertion`.
- README *Conceptual gaps* section documenting what `0.1.x` does **not** yet
  implement of the underlying Quinean philosophy (mutilation kernel,
  alternatives space, observation-chain walk, `specializes` semantics, prompt
  philosophy-awareness).
- LLM prompt now includes an explicit "confidence < 1.0" example to reduce
  the rate at which models emit `1.0`.

### Removed
- `tests/__init__.py` (unused; pytest does not require it).
- Unused `EPSILON` module constant in `neurath.store.truth`.

### Project
- Test count: 56 → 61 (5 new audit-driven tests).
- All existing public-API behaviour is preserved.

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
