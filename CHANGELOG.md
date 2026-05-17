# Changelog

All notable changes follow [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Project skeleton: Apache 2.0 license, hatchling build, Python 3.11+ support.
- `neurath.store.truth.TruthValue`: NARS `<frequency, confidence>` algebra with
  revision, choice, negation, and the evidence-space bijection.
- `neurath.store.belief.Belief` and `BeliefStore`: networkx-backed web of beliefs
  with labelled edges (`entails` / `contradicts` / `supports` / `specializes`).
- Property-based tests (Hypothesis) for revision commutativity, associativity,
  and confidence monotonicity.
- CI workflow: ruff lint + mypy + pytest on Python 3.11/3.12, plus CycloneDX SBOM.
