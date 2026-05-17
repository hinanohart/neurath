"""Holistic revision planner — chooses revision targets that least mutilate the web.

When an observation contradicts one or more existing beliefs, there are usually
several ways to dissolve the contradiction: each candidate target gets revised
toward the observation. The planner enumerates these candidates, scores each by
the *mutilation* it would inflict on the rest of the web, and returns the plans
ranked from least to most disruptive — Duhem-Quine *minimum mutilation* made
mechanical.

`mutilation_score` is the sum of:

- the direct shift in the target's expectation (`|E(t') - E(t)|`), and
- a propagation penalty equal to ``propagation_weight`` × the absolute shift,
  multiplied by the number of beliefs reachable from the target via
  ``entails`` or ``supports`` edges (the propagation closure).

The default `propagation_weight` is small (`0.1`) — see the *Conceptual gaps*
section of the README for why this is a placeholder rather than a learned
weight, and for what a richer minimum-mutilation kernel would look like.
``HolisticReviser`` takes ``propagation_weight`` as a constructor argument so
callers can tune it without monkey-patching the module.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from neurath.store.belief import Belief, BeliefId, BeliefStore
from neurath.store.history import RevisionRecord
from neurath.store.truth import TruthValue

PROPAGATION_WEIGHT: float = 0.1
"""Default fraction of the direct shift that each downstream belief contributes."""

PROPAGATION_EDGES: tuple[str, ...] = ("entails", "supports")
"""Edge kinds that count as `target depends on this belief` for mutilation.

Excludes ``contradicts`` (semantically inverse, not a dependency edge) and
``specializes`` (a taxonomy edge, currently not used to propagate mutilation —
see *Conceptual gaps* in the README).
"""


@dataclass(frozen=True, slots=True)
class RevisionPlan:
    """One candidate way to incorporate an observation."""

    target_id: BeliefId
    new_truth: TruthValue
    mutilation_score: float
    affected_ids: tuple[BeliefId, ...]
    rationale: str


class HolisticReviser:
    """Compute and apply minimum-mutilation revision plans on a :class:`BeliefStore`."""

    def __init__(
        self,
        store: BeliefStore,
        *,
        propagation_weight: float = PROPAGATION_WEIGHT,
    ) -> None:
        if propagation_weight < 0:
            raise ValueError(f"propagation_weight must be >= 0, got {propagation_weight!r}")
        self.store = store
        self.propagation_weight = propagation_weight

    # -- planning -----------------------------------------------------------

    def plan(
        self,
        observation: Belief,
        contradicts: Iterable[BeliefId] | None = None,
    ) -> list[RevisionPlan]:
        """Enumerate revision plans for incorporating `observation`.

        `contradicts` lists belief ids whose current truth-value the
        observation contradicts. If omitted, the planner reads the
        observation's incoming `contradicts` edges from the store.

        Returned plans are sorted by ascending `mutilation_score`.
        """
        targets = list(self._resolve_targets(observation, contradicts))
        plans: list[RevisionPlan] = []
        for target_id in targets:
            target = self.store.get(target_id)
            # NARS choice: keep whichever of {target, ¬observation} carries more
            # evidence. This is the rule for "two beliefs whose evidence cannot
            # be revised together" (Pei Wang, NAL §3.3).
            new_truth = target.truth.choose(observation.truth.negate())
            affected = self._downstream(target_id)
            score = self._mutilation_score(target.truth, new_truth, affected)
            plans.append(
                RevisionPlan(
                    target_id=target_id,
                    new_truth=new_truth,
                    mutilation_score=score,
                    affected_ids=tuple(affected),
                    rationale=(
                        f"revise belief {target_id} to accommodate observation "
                        f"(NARS choice between current {target.truth!r} and "
                        f"negated observation {observation.truth.negate()!r})"
                    ),
                )
            )
        plans.sort(key=lambda p: p.mutilation_score)
        return plans

    # -- application --------------------------------------------------------

    def apply(self, plan: RevisionPlan, observation_id: BeliefId | None = None) -> Belief:
        """Mutate the store so that `plan.target_id` carries `plan.new_truth`.

        Records a :class:`RevisionRecord` in the store's history. The record
        type lives in :mod:`neurath.store.history` so this writer does not
        depend on the L4 introspection module.
        """
        target = self.store.get(plan.target_id)
        before = target.truth
        revised = target.model_copy(update={"truth": plan.new_truth})
        self.store.replace(plan.target_id, revised)
        record = RevisionRecord(
            target_id=plan.target_id,
            before=before,
            after=plan.new_truth,
            observation_id=observation_id,
            rationale=plan.rationale,
        )
        self.store.record_revision(plan.target_id, record)
        return revised

    # -- internals ----------------------------------------------------------

    def _resolve_targets(
        self,
        observation: Belief,
        contradicts: Iterable[BeliefId] | None,
    ) -> Iterable[BeliefId]:
        if contradicts is not None:
            return contradicts
        if observation.id not in self.store:
            return ()
        # Beliefs reachable from `observation` via a `contradicts` edge.
        return [b.id for b in self.store.contradictions_of(observation.id)]

    def _downstream(self, target_id: BeliefId) -> list[BeliefId]:
        graph = self.store.graph_view()
        seen: set[BeliefId] = set()
        frontier: list[BeliefId] = [target_id]
        while frontier:
            current = frontier.pop()
            for _, neighbour, data in graph.out_edges(current, data=True):
                if data["kind"] in PROPAGATION_EDGES and neighbour not in seen:
                    seen.add(neighbour)
                    frontier.append(neighbour)
        return sorted(seen)

    def _mutilation_score(
        self,
        before: TruthValue,
        after: TruthValue,
        affected: list[BeliefId],
    ) -> float:
        direct = abs(after.expectation() - before.expectation())
        return direct + self.propagation_weight * direct * len(affected)
