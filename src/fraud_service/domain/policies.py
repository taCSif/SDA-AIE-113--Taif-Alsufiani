"""Business policy: thresholds are BUSINESS decisions, not model decisions.

Extracted from the legacy notebook Cell 4 (SMELL 5: hardcoded
BLOCK_THRESHOLD / REVIEW_BAND buried inside the scoring function).
A pure function with no external dependencies: unit-testable directly,
and reviewable by a risk officer without reading any model code.
"""

from __future__ import annotations

from fraud_service.domain.entities import Decision

BLOCK_THRESHOLD_DEFAULT = 0.85
REVIEW_BAND = 0.15


def decide(
    fraud_probability: float,
    block_threshold: float = BLOCK_THRESHOLD_DEFAULT,
) -> Decision:
    """Map a fraud probability onto a business action.

    >= block_threshold                -> "block"
    >= block_threshold - REVIEW_BAND  -> "review"
    otherwise                         -> "allow"
    """
    if fraud_probability >= block_threshold:
        return "block"
    if fraud_probability >= block_threshold - REVIEW_BAND:
        return "review"
    return "allow"
