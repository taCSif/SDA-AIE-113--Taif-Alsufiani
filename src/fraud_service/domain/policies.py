"""Business policy: thresholds are BUSINESS decisions, not model decisions.

Pure function => property-based-testable, reviewable by risk officers.

TODO (Lab 1, step 3 — ~15 min):
Extract the inline decision logic from the legacy notebook
(notebooks/fraud_exploration.ipynb, Cell 5: SMELL 5 — hardcoded
BLOCK_THRESHOLD / REVIEW_BAND) into a pure function here. It must take
NO external dependencies (no sklearn, no I/O) so it can be unit-tested
directly, and so risk officers can change the threshold value without
touching model code.

Suggested shape:

    BLOCK_THRESHOLD_DEFAULT = 0.85
    REVIEW_BAND = 0.15

    def decide(fraud_probability: float, block_threshold: float = BLOCK_THRESHOLD_DEFAULT) -> str:
        if fraud_probability >= block_threshold:
            return "block"
        if fraud_probability >= block_threshold - REVIEW_BAND:
            return "review"
        return "allow"
"""

# TODO: implement decide(...) — do NOT hardcode the threshold inline
# anywhere else in the codebase once this exists.
