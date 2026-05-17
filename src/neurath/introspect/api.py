"""Introspection API: surface the revision history behind any current truth-value.

A core commitment of neurath is that revisions are *legible* — when a belief
ends up at frequency 0.3 instead of 0.9, the user can ask the store *why* and
get back the ordered list of revisions that brought it there, each carrying the
observation that triggered it and the rationale recorded by the planner.

This is what Quine's *naturalized epistemology* looks like in code: the act of
believing is itself an object that can be inspected.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from neurath.store.belief import BeliefId, BeliefStore
from neurath.store.truth import TruthValue


@dataclass(frozen=True, slots=True)
class RevisionRecord:
    """One step in a belief's revision history."""

    target_id: BeliefId
    before: TruthValue
    after: TruthValue
    observation_id: BeliefId | None
    rationale: str
    timestamp: datetime = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        # Cannot use default_factory on frozen dataclass + slots, so set here.
        if self.timestamp is None:
            object.__setattr__(self, "timestamp", datetime.now(UTC))


class Introspector:
    """Read-only view into a store's revision history."""

    def __init__(self, store: BeliefStore) -> None:
        self.store = store

    def why(self, belief_id: BeliefId) -> list[RevisionRecord]:
        """Return the ordered revision history for `belief_id`.

        The first record's `before` is the belief's truth-value at insertion;
        each subsequent record's `before` equals the previous record's `after`.
        An empty list means the belief has never been revised since insertion.
        """
        if belief_id not in self.store:
            raise KeyError(f"unknown belief id: {belief_id!r}")
        # `store.history_for` returns `list[object]` to keep the store free of an
        # L4 import; every record we put in is in fact a `RevisionRecord`.
        return [r for r in self.store.history_for(belief_id) if isinstance(r, RevisionRecord)]

    def trace(self, belief_id: BeliefId) -> dict[str, Any]:
        """Return a JSON-serialisable trace dict for `belief_id`."""
        belief = self.store.get(belief_id)
        history = self.why(belief_id)
        return {
            "belief_id": belief_id,
            "statement": belief.statement,
            "current": {
                "frequency": belief.truth.frequency,
                "confidence": belief.truth.confidence,
                "expectation": belief.truth.expectation(),
            },
            "revisions": [
                {
                    "before": {"f": r.before.frequency, "c": r.before.confidence},
                    "after": {"f": r.after.frequency, "c": r.after.confidence},
                    "observation_id": r.observation_id,
                    "rationale": r.rationale,
                    "timestamp": r.timestamp.isoformat(),
                }
                for r in history
            ],
        }

    def network_view(self) -> dict[str, Any]:
        """Return a node-link representation of the current belief web."""
        graph = self.store.graph_view()
        return {
            "nodes": [
                {
                    "id": belief_id,
                    "statement": belief.statement,
                    "frequency": belief.truth.frequency,
                    "confidence": belief.truth.confidence,
                }
                for belief_id, data in graph.nodes(data=True)
                for belief in [data["belief"]]
            ],
            "edges": [
                {"source": src, "target": tgt, "kind": kind}
                for src, tgt, kind in graph.edges(keys=True)
            ],
        }
