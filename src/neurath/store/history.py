"""Revision history records — shared L1 type used by both the planner (writer)
and the introspector (reader).

Lives in :mod:`neurath.store` so that ``revision.planner`` can write a record
without importing the :mod:`neurath.introspect` (L4) module, which would
either invert the layering or force a runtime-local import.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from neurath.store.truth import TruthValue

BeliefId = str
"""Mirrors :data:`neurath.store.belief.BeliefId`; kept as a local alias to
keep this module a leaf of the L1 dependency graph."""


@dataclass(frozen=True, slots=True)
class RevisionRecord:
    """One step in a belief's revision history.

    Recorded by :class:`neurath.revision.HolisticReviser.apply` and surfaced
    by :class:`neurath.introspect.Introspector.why` / ``trace``.
    """

    target_id: BeliefId
    before: TruthValue
    after: TruthValue
    observation_id: BeliefId | None
    rationale: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
