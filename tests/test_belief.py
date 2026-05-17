"""Tests for Belief and BeliefStore."""

from __future__ import annotations

import pytest

from neurath.store.belief import Belief, BeliefStore
from neurath.store.truth import TruthValue, from_observation


@pytest.fixture
def store() -> BeliefStore:
    return BeliefStore()


@pytest.fixture
def factory():
    def make(statement: str, freq: float = 0.8, conf: float = 0.5) -> Belief:
        return Belief(statement=statement, truth=TruthValue(frequency=freq, confidence=conf))

    return make


class TestAddAndQuery:
    def test_add_returns_id_and_is_retrievable(self, store: BeliefStore, factory) -> None:
        b = factory("Socrates is mortal")
        bid = store.add(b)
        assert bid == b.id
        assert b.id in store
        assert store.get(b.id) == b
        assert len(store) == 1

    def test_get_unknown_id_raises(self, store: BeliefStore) -> None:
        with pytest.raises(KeyError):
            store.get("does-not-exist")

    def test_duplicate_add_raises(self, store: BeliefStore, factory) -> None:
        b = factory("x")
        store.add(b)
        with pytest.raises(ValueError, match="already present"):
            store.add(b)

    def test_iter_visits_every_belief(self, store: BeliefStore, factory) -> None:
        beliefs = [factory(f"claim_{i}") for i in range(5)]
        for b in beliefs:
            store.add(b)
        recovered = list(store)
        assert {b.id for b in recovered} == {b.id for b in beliefs}


class TestLink:
    def test_link_records_edge(self, store: BeliefStore, factory) -> None:
        a, b = factory("a"), factory("b")
        store.add(a)
        store.add(b)
        store.link(a.id, b.id, "entails")
        neighbours = store.neighbours(a.id)
        assert (b, "entails") in neighbours

    def test_link_unknown_id_raises(self, store: BeliefStore, factory) -> None:
        a = factory("a")
        store.add(a)
        with pytest.raises(KeyError):
            store.link(a.id, "missing", "entails")

    def test_contradictions_filtered(self, store: BeliefStore, factory) -> None:
        a, b, c = factory("a"), factory("b"), factory("c")
        for x in (a, b, c):
            store.add(x)
        store.link(a.id, b.id, "contradicts")
        store.link(a.id, c.id, "supports")
        assert store.contradictions_of(a.id) == [b]


class TestReplace:
    def test_replace_keeps_edges(self, store: BeliefStore, factory) -> None:
        a, b = factory("a"), factory("b")
        store.add(a)
        store.add(b)
        store.link(a.id, b.id, "entails")
        # revise a's truth-value with one positive observation
        revised = a.revise_with(from_observation(positive=True))
        store.replace(a.id, revised)
        assert store.get(a.id).truth == revised.truth
        # edge survives
        assert store.contradictions_of(a.id) == []
        assert (b, "entails") in store.neighbours(a.id)

    def test_replace_with_mismatched_id_raises(self, store: BeliefStore, factory) -> None:
        a = factory("a")
        store.add(a)
        other = factory("other")
        with pytest.raises(ValueError, match="differs"):
            store.replace(a.id, other)


class TestBeliefRevision:
    def test_revise_with_new_truth_is_immutable_copy(self, factory) -> None:
        b = factory("x", freq=0.5, conf=0.5)
        revised = b.revise_with(TruthValue(frequency=0.5, confidence=0.5))
        assert revised is not b
        assert revised.id == b.id
        assert revised.truth.confidence > b.truth.confidence
