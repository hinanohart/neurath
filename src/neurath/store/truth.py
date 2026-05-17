"""NARS truth-value algebra.

A NARS belief is characterised by a pair `<frequency, confidence>`:

- `frequency f ∈ [0, 1]`: proportion of positive evidence so far,
  equivalent to the maximum-likelihood estimate of the underlying probability.
- `confidence c ∈ [0, 1)`: the fraction of currently observed evidence in the
  total evidence the agent will eventually have. `c → 1` only in the limit.

Evidence is modelled as a pair `<w+, w−>` where `w+ + w− = w` is the
total amount of evidence observed. The bijection with `<f, c>` is:

    f = w+ / w       c = w / (w + k)

with `k = 1` (the standard NARS horizon).

See Pei Wang, *Rigid Flexibility: The Logic of Intelligence* (2006),
chapters 3-4, and the Non-Axiomatic Logic reference.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Self

DEFAULT_HORIZON: float = 1.0
"""NARS horizon constant `k`. Standard value is 1 (Wang, *Rigid Flexibility*, §3.2, p. 67)."""


@dataclass(frozen=True, slots=True)
class TruthValue:
    """A NARS truth-value `<frequency, confidence>`.

    Invariants enforced at construction:

    - `0.0 ≤ frequency ≤ 1.0`
    - `0.0 ≤ confidence < 1.0`  (confidence of exactly 1 is unreachable)
    """

    frequency: float
    confidence: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.frequency <= 1.0:
            raise ValueError(f"frequency out of [0,1]: {self.frequency!r}")
        if not 0.0 <= self.confidence < 1.0:
            raise ValueError(f"confidence out of [0,1): {self.confidence!r}")

    # -- evidence-space coordinates -------------------------------------------------

    def evidence(self, horizon: float = DEFAULT_HORIZON) -> tuple[float, float, float]:
        """Return `(w_positive, w_negative, w_total)` in evidence space."""
        if horizon <= 0:
            raise ValueError(f"horizon must be positive, got {horizon!r}")
        c = self.confidence
        w = horizon * c / (1.0 - c) if c < 1.0 else math.inf
        w_pos = w * self.frequency
        w_neg = w - w_pos
        return w_pos, w_neg, w

    @classmethod
    def from_evidence(
        cls,
        w_positive: float,
        w_negative: float,
        horizon: float = DEFAULT_HORIZON,
    ) -> Self:
        """Inverse of :meth:`evidence`."""
        if w_positive < 0 or w_negative < 0:
            raise ValueError(f"negative evidence: {w_positive=}, {w_negative=}")
        if horizon <= 0:
            raise ValueError(f"horizon must be positive, got {horizon!r}")
        w = w_positive + w_negative
        f = w_positive / w if w > 0 else 0.5
        c = w / (w + horizon)
        # With enormous evidence weights, c rounds up to exactly 1.0; clamp to
        # the largest float strictly below 1 so the NARS invariant c<1 holds.
        if c >= 1.0:
            c = math.nextafter(1.0, 0.0)
        return cls(frequency=f, confidence=c)

    # -- derived quantities ---------------------------------------------------------

    def expectation(self) -> float:
        """Subjective probability estimate `E = c·(f − 0.5) + 0.5`."""
        return self.confidence * (self.frequency - 0.5) + 0.5

    # -- NARS truth-functions -------------------------------------------------------

    def revise(self, other: TruthValue, horizon: float = DEFAULT_HORIZON) -> TruthValue:
        """NARS *revision*: merge two independent evidence streams about the same claim.

        Revision is commutative and assumes the two evidence sources do not
        overlap. Confidence strictly increases (no information is discarded).
        """
        w1p, w1n, _ = self.evidence(horizon)
        w2p, w2n, _ = other.evidence(horizon)
        return TruthValue.from_evidence(w1p + w2p, w1n + w2n, horizon=horizon)

    def choose(self, other: TruthValue) -> TruthValue:
        """NARS *choice*: pick whichever truth-value carries more confidence.

        Used for resolving competing beliefs that *cannot* be revised (e.g.
        because they are based on the same evidence and would be double-counted).
        Ties break in favour of `self`.
        """
        return self if self.confidence >= other.confidence else other

    def negate(self) -> TruthValue:
        """NARS *negation*: same confidence, frequency `1 − f`."""
        return TruthValue(frequency=1.0 - self.frequency, confidence=self.confidence)

    # -- comparison & repr ----------------------------------------------------------

    def is_close(self, other: TruthValue, tol: float = 1e-9) -> bool:
        return math.isclose(self.frequency, other.frequency, abs_tol=tol) and math.isclose(
            self.confidence, other.confidence, abs_tol=tol
        )

    def __repr__(self) -> str:
        return f"TruthValue<f={self.frequency:.3f}, c={self.confidence:.3f}>"


# convenience constructors -------------------------------------------------------

UNKNOWN: TruthValue = TruthValue(frequency=0.5, confidence=0.0)
"""Maximum-ignorance truth-value: no information, equally probable in both directions."""


def from_observation(positive: bool, horizon: float = DEFAULT_HORIZON) -> TruthValue:
    """Truth-value carried by a single positive or negative observation."""
    return TruthValue.from_evidence(
        w_positive=1.0 if positive else 0.0,
        w_negative=0.0 if positive else 1.0,
        horizon=horizon,
    )
