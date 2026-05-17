"""Hase 2024 belief-revision benchmark runner — skeleton harness.

This module is intentionally minimal: it provides the shape into which a real
benchmark fits. The dataset is not bundled with the package because of license
considerations; the runner expects the user to pre-download the dataset and
pass a path.

Usage:

    python -m benchmark.runner --dataset path/to/hase2024.jsonl \\
        --model gpt-4o-mini --num-cases 50 --seed 0

Each case is a dict with at least `claim`, `observation`, and `gold_truth` (a
`<frequency, confidence>` pair).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from neurath import Belief, BeliefStore, HolisticReviser, LLMTranslator, TruthValue

DEFAULT_NUM_BOOTSTRAP = 1000


@dataclass(frozen=True, slots=True)
class CaseResult:
    case_index: int
    accuracy: float


def load_cases(path: Path, *, num_cases: int | None, seed: int) -> list[dict[str, Any]]:
    with path.open() as fh:
        cases = [json.loads(line) for line in fh if line.strip()]
    random.Random(seed).shuffle(cases)
    if num_cases is not None:
        cases = cases[:num_cases]
    return cases


def dataset_hash(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def evaluate_case(translator: LLMTranslator, case: dict[str, Any]) -> float:
    """One end-to-end revision pass on a single case; returns accuracy in [0,1]."""
    store = BeliefStore()
    initial = translator.claim_to_truth(case["claim"])
    target = Belief(statement=case["claim"], truth=initial.truth)
    store.add(target)

    observation_estimate = translator.claim_to_truth(case["observation"])
    observation = Belief(statement=case["observation"], truth=observation_estimate.truth)
    store.add(observation)
    store.link(observation.id, target.id, "contradicts")

    reviser = HolisticReviser(store)
    plans = reviser.plan(observation)
    if not plans:
        return 0.0
    reviser.apply(plans[0])

    revised = store.get(target.id).truth
    gold = TruthValue(
        frequency=case["gold_truth"]["frequency"],
        confidence=case["gold_truth"]["confidence"],
    )
    return 1.0 - abs(revised.expectation() - gold.expectation())


def bootstrap_ci(values: list[float], n: int, seed: int) -> tuple[float, float]:
    rng = random.Random(seed)
    means = [statistics.fmean(rng.choices(values, k=len(values))) for _ in range(n)]
    means.sort()
    lo = means[int(0.025 * n)]
    hi = means[int(0.975 * n)]
    return lo, hi


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--model", default="gpt-4o-mini")
    parser.add_argument("--num-cases", type=int, default=None)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--bootstrap", type=int, default=DEFAULT_NUM_BOOTSTRAP)
    parser.add_argument("--out", type=Path, default=Path("benchmark/results"))
    args = parser.parse_args()

    cases = load_cases(args.dataset, num_cases=args.num_cases, seed=args.seed)
    translator = LLMTranslator(model=args.model)

    results: list[CaseResult] = []
    for i, case in enumerate(cases):
        acc = evaluate_case(translator, case)
        results.append(CaseResult(case_index=i, accuracy=acc))

    accuracies = [r.accuracy for r in results]
    mean = statistics.fmean(accuracies)
    lo, hi = bootstrap_ci(accuracies, args.bootstrap, args.seed)

    args.out.mkdir(parents=True, exist_ok=True)
    payload = {
        "dataset_sha256": dataset_hash(args.dataset),
        "model": args.model,
        "num_cases": len(cases),
        "mean_accuracy": mean,
        "bootstrap_95_ci": [lo, hi],
        "per_case": [r.__dict__ for r in results],
    }
    out_file = args.out / f"results_{args.model.replace('/', '_')}.json"
    out_file.write_text(json.dumps(payload, indent=2))
    print(f"mean accuracy {mean:.4f}  95% CI [{lo:.4f}, {hi:.4f}]  → {out_file}")


if __name__ == "__main__":
    main()
