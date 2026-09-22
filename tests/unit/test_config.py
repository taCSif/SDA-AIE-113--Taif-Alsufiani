import pytest
from pydantic import ValidationError

from fraud_service.config import Settings


@pytest.mark.unit
def test_missing_model_path_fails_fast_with_a_crisp_message():
    with pytest.raises(ValidationError) as exc_info:
        Settings(model_path="/nope/does-not-exist.joblib")
    assert "does not exist" in str(exc_info.value)


@pytest.mark.unit
@pytest.mark.parametrize("threshold", [0.0, -0.1, 1.1])
def test_block_threshold_out_of_range_rejected(threshold):
    with pytest.raises(ValidationError):
        Settings(block_threshold=threshold)


@pytest.mark.unit
def test_unknown_log_level_rejected():
    with pytest.raises(ValidationError):
        Settings(log_level="VERBOSE")


@pytest.mark.unit
def test_log_level_is_case_insensitive():
    assert Settings(log_level="debug").log_level == "DEBUG"


@pytest.mark.unit
def test_unknown_field_rejected():
    with pytest.raises(ValidationError):
        Settings(totally_unknown_field="x")


@pytest.mark.unit
def test_github_token_defaults_to_none_and_is_not_a_plain_string():
    settings = Settings()
    assert settings.github_token is None


@pytest.mark.unit
def test_github_token_is_masked_in_repr(monkeypatch):
    monkeypatch.setenv("FRAUD_GITHUB_TOKEN", "ghp_" + "a" * 36)
    settings = Settings()
    assert "ghp_" not in repr(settings)
    assert settings.github_token is not None
    assert settings.github_token.get_secret_value() == "ghp_" + "a" * 36
