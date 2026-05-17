"""Tests for the holistic revision planner."""

from __future__ import annotations

import pytest

from neurath.revision import HolisticReviser, RevisionPlan
from neurath.store.belief import Belief, BeliefStore
from neurath.store.truth import TruthValue


def _b(statement: str, freq: float = 0.9, conf: float = 0.7) -> Belief:
    return Belief(statement=statement, truth=TruthValue(frequency=freq, confidence=conf))


@pytest.fixture
def store() -> BeliefStore:
    return BeliefStore()


class TestPlanWithExplicitContradicts:
    def test_single_target_returns_single_plan(self, store: BeliefStore) -> None:
        target = _b("birds can fly")
        observation = _b("ostriches cannot fly", freq=1.0, conf=0.6)
        store.add(target)
        reviser = HolisticReviser(store)
        plans = reviser.plan(observation, contradicts=[target.id])
        assert len(plans) == 1
        assert plans[0].target_id == target.id

    def test_plans_sorted_by_ascending_mutilation(self, store: BeliefStore) -> None:
        # Two candidates: one with many downstream supporters (more painful to revise),
        # one isolated (least painful).
        isolated = _b("isolated claim")
        central = _b("central claim")
        d1 = _b("downstream-1")
        d2 = _b("downstream-2")
        d3 = _b("downstream-3")
        for b in (isolated, central, d1, d2, d3):
            store.add(b)
        store.link(central.id, d1.id, "supports")
        store.link(central.id, d2.id, "supports")
        store.link(central.id, d3.id, "supports")
        observation = _b("contradicts both", freq=0.0, conf=0.9)
        reviser = HolisticReviser(store)
        plans = reviser.plan(observation, contradicts=[central.id, isolated.id])
        assert plans[0].target_id == isolated.id  # cheaper to revise
        assert plans[1].target_id == central.id
        assert plans[0].mutilation_score < plans[1].mutilation_score


class TestPlanFromContradictsEdges:
    def test_reads_contradicts_edges_when_argument_omitted(self, store: BeliefStore) -> None:
        a = _b("A is true")
        b = _b("A is false")
        store.add(a)
        store.add(b)
        store.link(b.id, a.id, "contradicts")
        reviser = HolisticReviser(store)
        plans = reviser.plan(b)  # observation is b itself
        assert len(plans) == 1
        assert plans[0].target_id == a.id

    def test_observation_not_in_store_yields_empty(self, store: BeliefStore) -> None:
        floating = _b("not added")
        reviser = HolisticReviser(store)
        assert reviser.plan(floating) == []


class TestMutilationScore:
    def test_downstream_supports_increase_score(self, store: BeliefStore) -> None:
        a = _b("a")
        b = _b("b")
        store.add(a)
        store.add(b)
        reviser = HolisticReviser(store)
        observation = _b("contradicts a", freq=0.0, conf=0.9)

        score_no_link = reviser.plan(observation, contradicts=[a.id])[0].mutilation_score

        store.link(a.id, b.id, "supports")
        score_with_link = reviser.plan(observation, contradicts=[a.id])[0].mutilation_score

        assert score_with_link > score_no_link

    def test_irrelevant_edge_kind_does_not_count(self, store: BeliefStore) -> None:
        a = _b("a")
        b = _b("b")
        store.add(a)
        store.add(b)
        store.link(a.id, b.id, "contradicts")  # not in PROPAGATION_EDGES
        reviser = HolisticReviser(store)
        observation = _b("contradicts a", freq=0.0, conf=0.9)
        plan = reviser.plan(observation, contradicts=[a.id])[0]
        assert plan.affected_ids == ()


class TestApply:
    def test_apply_replaces_target_truth(self, store: BeliefStore) -> None:
        target = _b("target", freq=0.9, conf=0.7)
        store.add(target)
        reviser = HolisticReviser(store)
        observation = _b("contradicts target", freq=0.1, conf=0.95)
        plan = reviser.plan(observation, contradicts=[target.id])[0]
        revised = reviser.apply(plan)
        assert store.get(target.id).truth == plan.new_truth
        assert revised.id == target.id
        assert revised.truth != target.truth

    def test_apply_preserves_belief_id_and_provenance(self, store: BeliefStore) -> None:
        target = _b("p")
        store.add(target)
        original_created = target.created_at
        reviser = HolisticReviser(store)
        plan = RevisionPlan(
            target_id=target.id,
            new_truth=TruthValue(frequency=0.1, confidence=0.5),
            mutilation_score=0.0,
            affected_ids=(),
            rationale="manual",
        )
        revised = reviser.apply(plan)
        assert revised.id == target.id
        assert revised.created_at == original_created
        assert revised.statement == target.statement
