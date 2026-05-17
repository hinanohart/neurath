"""Tests for the introspection API."""

from __future__ import annotations

import pytest

from neurath.introspect import Introspector, RevisionRecord
from neurath.revision import HolisticReviser
from neurath.store.belief import Belief, BeliefStore
from neurath.store.truth import TruthValue


def _b(statement: str, freq: float = 0.9, conf: float = 0.5) -> Belief:
    return Belief(statement=statement, truth=TruthValue(frequency=freq, confidence=conf))


@pytest.fixture
def store() -> BeliefStore:
    return BeliefStore()


class TestWhyOnFreshBelief:
    def test_unrevised_belief_has_empty_history(self, store: BeliefStore) -> None:
        b = _b("never revised")
        store.add(b)
        assert Introspector(store).why(b.id) == []

    def test_unknown_id_raises(self, store: BeliefStore) -> None:
        with pytest.raises(KeyError):
            Introspector(store).why("missing")


class TestWhyAfterRevision:
    def test_single_revision_recorded(self, store: BeliefStore) -> None:
        target = _b("target", freq=0.9, conf=0.7)
        observation = _b("anti", freq=0.0, conf=0.95)
        store.add(target)
        reviser = HolisticReviser(store)
        plan = reviser.plan(observation, contradicts=[target.id])[0]
        reviser.apply(plan)

        history = Introspector(store).why(target.id)
        assert len(history) == 1
        record = history[0]
        assert isinstance(record, RevisionRecord)
        assert record.target_id == target.id
        assert record.before == target.truth
        assert record.after == plan.new_truth

    def test_multiple_revisions_ordered(self, store: BeliefStore) -> None:
        target = _b("target", freq=0.9, conf=0.7)
        store.add(target)
        reviser = HolisticReviser(store)
        obs1 = _b("anti-1", freq=0.0, conf=0.6)
        obs2 = _b("anti-2", freq=0.0, conf=0.95)
        reviser.apply(reviser.plan(obs1, contradicts=[target.id])[0])
        reviser.apply(reviser.plan(obs2, contradicts=[target.id])[0])

        history = Introspector(store).why(target.id)
        assert len(history) == 2
        # second record's `before` equals first record's `after`
        assert history[1].before == history[0].after


class TestTrace:
    def test_trace_is_json_serialisable(self, store: BeliefStore) -> None:
        import json

        target = _b("Socrates is mortal")
        observation = _b("anti", freq=0.0, conf=0.9)
        store.add(target)
        reviser = HolisticReviser(store)
        reviser.apply(reviser.plan(observation, contradicts=[target.id])[0])
        trace = Introspector(store).trace(target.id)

        encoded = json.dumps(trace)
        assert "Socrates is mortal" in encoded
        assert "revisions" in trace
        assert len(trace["revisions"]) == 1
        assert "rationale" in trace["revisions"][0]


class TestNetworkView:
    def test_view_lists_nodes_and_edges(self, store: BeliefStore) -> None:
        a = _b("A")
        b = _b("B")
        store.add(a)
        store.add(b)
        store.link(a.id, b.id, "supports")
        view = Introspector(store).network_view()
        ids = {n["id"] for n in view["nodes"]}
        assert ids == {a.id, b.id}
        assert view["edges"] == [{"source": a.id, "target": b.id, "kind": "supports"}]

    def test_view_includes_truth_values(self, store: BeliefStore) -> None:
        a = _b("A", freq=0.7, conf=0.4)
        store.add(a)
        node = Introspector(store).network_view()["nodes"][0]
        assert node["frequency"] == 0.7
        assert node["confidence"] == 0.4
