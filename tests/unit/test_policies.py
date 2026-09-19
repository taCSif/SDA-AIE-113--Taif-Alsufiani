"""TODO (fast-finisher bonus, per instructor notes):
Once domain/policies.py::decide() exists, write a parametrized test
covering the block / review / allow boundaries, e.g.:

    import pytest
    from fraud_service.domain.policies import decide

    @pytest.mark.parametrize("prob,expected", [
        (0.90, "block"),
        (0.85, "block"),
        (0.75, "review"),
        (0.70, "review"),
        (0.50, "allow"),
    ])
    def test_decide(prob, expected):
        assert decide(prob) == expected
"""
