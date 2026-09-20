"""Boundary tests for the business policy — no model, no I/O, no fixtures."""

import pytest

from fraud_service.domain.policies import decide


@pytest.mark.parametrize(
    ("probability", "expected"),
    [
        (0.99, "block"),
        (0.85, "block"),
        (0.8499, "review"),
        (0.70, "review"),
        (0.6999, "allow"),
        (0.0, "allow"),
    ],
)
def test_decide_default_threshold(probability: float, expected: str) -> None:
    assert decide(probability) == expected


def test_decide_respects_injected_threshold() -> None:
    assert decide(0.80, block_threshold=0.75) == "block"
    assert decide(0.80) == "review"
