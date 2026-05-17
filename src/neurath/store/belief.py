"""Belief and BeliefStore — the web of belief over which holistic revision operates."""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Literal

import networkx as nx
from pydantic import BaseModel, ConfigDict, Field

from neurath.store.truth import TruthValue

BeliefId = str
"""Stable identifier assigned at insertion. Treated as opaque by callers."""

RelationKind = Literal["entails", "contradicts", "supports", "specializes"]
"""Edge label between two beliefs. `contradicts` is what triggers holistic revision."""


class Belief(BaseModel):
    """A single proposition together with its NARS truth-value and provenance."""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    id: BeliefId = Field(default_factory=lambda: str(uuid.uuid4()))
    statement: str
    truth: TruthValue
    sources: tuple[str, ...] = ()
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def revise_with(self, new_truth: TruthValue) -> Belief:
        """Return a copy whose truth-value is the NARS revision of self with `new_truth`."""
        return self.model_copy(update={"truth": self.truth.revise(new_truth)})


class BeliefStore:
    """In-memory web of beliefs backed by a `networkx.MultiDiGraph`.

    Each node is a :class:`Belief`; edges are labelled with a :data:`RelationKind`.
    The store is intentionally small: the holistic revision engine is what reasons
    over the graph; the store only owns identity, lookup, and structural mutation.
    """

    def __init__(self) -> None:
        self._graph: nx.MultiDiGraph = nx.MultiDiGraph()

    def __len__(self) -> int:
        return self._graph.number_of_nodes()

    def __contains__(self, belief_id: BeliefId) -> bool:
        return self._graph.has_node(belief_id)

    def __iter__(self) -> Iterator[Belief]:
        for _, data in self._graph.nodes(data=True):
            yield data["belief"]

    # -- mutation -----------------------------------------------------------

    def add(self, belief: Belief) -> BeliefId:
        """Insert a belief. Raises if its id is already present."""
        if belief.id in self:
            raise ValueError(f"belief id already present: {belief.id}")
        self._graph.add_node(belief.id, belief=belief)
        return belief.id

    def link(self, source: BeliefId, target: BeliefId, kind: RelationKind) -> None:
        """Add a labelled edge `source --kind--> target`."""
        if source not in self or target not in self:
            raise KeyError(f"unknown belief id: {source!r} or {target!r}")
        self._graph.add_edge(source, target, key=kind, kind=kind)

    def replace(self, belief_id: BeliefId, new_belief: Belief) -> None:
        """Replace the belief at `belief_id` in-place, preserving edges."""
        if belief_id not in self:
            raise KeyError(f"unknown belief id: {belief_id!r}")
        if new_belief.id != belief_id:
            raise ValueError(f"new belief id {new_belief.id!r} differs from target {belief_id!r}")
        self._graph.nodes[belief_id]["belief"] = new_belief

    # -- query --------------------------------------------------------------

    def get(self, belief_id: BeliefId) -> Belief:
        if belief_id not in self:
            raise KeyError(f"unknown belief id: {belief_id!r}")
        return self._graph.nodes[belief_id]["belief"]

    def neighbours(
        self,
        belief_id: BeliefId,
        kind: RelationKind | None = None,
    ) -> list[tuple[Belief, RelationKind]]:
        """Outgoing neighbours, optionally filtered by edge `kind`."""
        if belief_id not in self:
            raise KeyError(f"unknown belief id: {belief_id!r}")
        out: list[tuple[Belief, RelationKind]] = []
        for _, target, edge_kind in self._graph.out_edges(belief_id, keys=True):
            if kind is None or edge_kind == kind:
                out.append((self.get(target), edge_kind))
        return out

    def contradictions_of(self, belief_id: BeliefId) -> list[Belief]:
        """All beliefs reachable via a single `contradicts` edge."""
        return [b for b, _ in self.neighbours(belief_id, kind="contradicts")]

    def graph_view(self) -> nx.MultiDiGraph:
        """Return the underlying graph for read-only inspection (do not mutate)."""
        return self._graph
