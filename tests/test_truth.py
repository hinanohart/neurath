"""Property-based and unit tests for the NARS truth-value algebra."""

from __future__ import annotations

import math

import pytest
from hypothesis import assume, given
from hypothesis import strategies as st

from neurath.store.truth import (
    DEFAULT_HORIZON,
    UNKNOWN,
    TruthValue,
    from_observation,
)

# strategies ---------------------------------------------------------------

frequencies = st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
confidences = st.floats(min_value=0.0, max_value=1.0, exclude_max=True, allow_nan=False)
evidence_weights = st.floats(min_value=0.0, max_value=1e6, allow_nan=False, allow_infinity=False)


@st.composite
def truth_values(draw: st.DrawFn) -> TruthValue:
    return TruthValue(frequency=draw(frequencies), confidence=draw(confidences))


# construction & invariants ------------------------------------------------


class TestConstruction:
    def test_unknown_has_zero_confidence(self) -> None:
        assert UNKNOWN.confidence == 0.0
        assert UNKNOWN.frequency == 0.5

    @pytest.mark.parametrize("bad", [-0.01, 1.01, math.nan])
    def test_frequency_out_of_range_rejected(self, bad: float) -> None:
        with pytest.raises(ValueError, match="frequency"):
            TruthValue(frequency=bad, confidence=0.5)

    @pytest.mark.parametrize("bad", [-0.01, 1.0, 1.01, math.nan])
    def test_confidence_out_of_range_rejected(self, bad: float) -> None:
        with pytest.raises(ValueError, match="confidence"):
            TruthValue(frequency=0.5, confidence=bad)


# evidence-space bijection -------------------------------------------------


class TestEvidenceBijection:
    @given(truth_values())
    def test_roundtrip(self, tv: TruthValue) -> None:
        # When confidence is at or below the denormal floor, the evidence
        # weight underflows to zero and the frequency is unrecoverable.
        assume(tv.confidence > 1e-9)
        w_pos, w_neg, _ = tv.evidence()
        recovered = TruthValue.from_evidence(w_pos, w_neg)
        assert tv.is_close(recovered, tol=1e-9)

    @given(evidence_weights, evidence_weights)
    def test_from_evidence_then_back(self, w_pos: float, w_neg: float) -> None:
        assume(w_pos + w_neg > 0)
        tv = TruthValue.from_evidence(w_pos, w_neg)
        w_pos_r, w_neg_r, _ = tv.evidence()
        assert math.isclose(w_pos, w_pos_r, rel_tol=1e-9, abs_tol=1e-9)
        assert math.isclose(w_neg, w_neg_r, rel_tol=1e-9, abs_tol=1e-9)

    def test_zero_evidence_is_unknown(self) -> None:
        tv = TruthValue.from_evidence(0.0, 0.0)
        assert tv.is_close(UNKNOWN)

    def test_horizon_must_be_positive(self) -> None:
        with pytest.raises(ValueError, match="horizon"):
            TruthValue.from_evidence(1.0, 1.0, horizon=0.0)


# revision -----------------------------------------------------------------


class TestRevision:
    # Bounding away from c=1 keeps Hypothesis off the underflow-clamp region
    # where two evidence weights of size ~1e16 lose associativity in float.
    _SAFE_C = 0.99

    @given(truth_values(), truth_values())
    def test_revision_is_commutative(self, a: TruthValue, b: TruthValue) -> None:
        assume(a.confidence <= self._SAFE_C and b.confidence <= self._SAFE_C)
        assert a.revise(b).is_close(b.revise(a), tol=1e-9)

    @given(truth_values(), truth_values(), truth_values())
    def test_revision_is_associative(self, a: TruthValue, b: TruthValue, c: TruthValue) -> None:
        assume(
            a.confidence <= self._SAFE_C
            and b.confidence <= self._SAFE_C
            and c.confidence <= self._SAFE_C
        )
        left = a.revise(b).revise(c)
        right = a.revise(b.revise(c))
        assert left.is_close(right, tol=1e-7)

    @given(truth_values(), truth_values())
    def test_revision_does_not_decrease_confidence(self, a: TruthValue, b: TruthValue) -> None:
        assume(a.confidence <= self._SAFE_C and b.confidence <= self._SAFE_C)
        merged = a.revise(b)
        assert merged.confidence + 1e-9 >= max(a.confidence, b.confidence)

    def test_revision_with_unknown_is_identity(self) -> None:
        a = TruthValue(frequency=0.8, confidence=0.6)
        assert a.revise(UNKNOWN).is_close(a)


# expectation --------------------------------------------------------------


class TestExpectation:
    def test_unknown_expectation_is_half(self) -> None:
        assert UNKNOWN.expectation() == 0.5

    @given(truth_values())
    def test_expectation_in_unit_interval(self, tv: TruthValue) -> None:
        e = tv.expectation()
        assert 0.0 <= e <= 1.0


# observations -------------------------------------------------------------


class TestObservation:
    def test_positive_observation(self) -> None:
        tv = from_observation(positive=True)
        assert tv.frequency == 1.0
        assert math.isclose(tv.confidence, 1.0 / (1.0 + DEFAULT_HORIZON))

    def test_negative_observation(self) -> None:
        tv = from_observation(positive=False)
        assert tv.frequency == 0.0

    def test_two_positive_observations_revise_to_higher_confidence(self) -> None:
        single = from_observation(positive=True)
        double = single.revise(from_observation(positive=True))
        assert double.confidence > single.confidence
        assert double.frequency == 1.0


# negation -----------------------------------------------------------------


class TestNegation:
    @given(truth_values())
    def test_negation_is_involution(self, tv: TruthValue) -> None:
        assert tv.negate().negate().is_close(tv)

    @given(truth_values())
    def test_negation_preserves_confidence(self, tv: TruthValue) -> None:
        assert tv.negate().confidence == tv.confidence
