import pytest

from fraud_service.logging_setup import MASK, mask_secrets

FAKE_GITHUB_TOKEN = "ghp_" + "a" * 36  # shape only — not a real credential


@pytest.mark.unit
@pytest.mark.parametrize("key", ["token", "github_token", "password", "secret",
                                  "api_key", "authorization", "Token", "API_KEY"])
def test_masks_known_secret_field_names(key):
    event = mask_secrets(None, "info", {"event": "debug", key: "super-secret-value"})
    assert event[key] == MASK


def test_leaves_non_secret_fields_alone():
    event = mask_secrets(None, "info", {"event": "prediction_served", "latency_ms": 12.3})
    assert event["latency_ms"] == 12.3
    assert event["event"] == "prediction_served"


def test_masks_github_token_shape_even_in_a_free_text_field():
    event = mask_secrets(None, "info", {"message": f"using token {FAKE_GITHUB_TOKEN} for auth"})
    assert FAKE_GITHUB_TOKEN not in event["message"]
    assert MASK in event["message"]
