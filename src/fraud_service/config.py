"""Typed, fail-fast configuration. One place to read every environment
variable — never scatter os.environ["X"] across the codebase.

Settings() is constructed exactly once per process, from the
composition root (the FastAPI lifespan, or batch.main) — never at
import time. A bad value (an unknown field, a nonexistent model path,
an out-of-range threshold) raises a single crisp ValidationError right
there, before the process accepts any traffic. That beats discovering
the same problem on the first inbound request.
"""
from pathlib import Path

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_VALID_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="FRAUD_", extra="forbid")

    model_path: str = "models/fraud_model.joblib"
    block_threshold: float = Field(default=0.85, gt=0.0, le=1.0)
    log_level: str = "INFO"

    # Set via FRAUD_GITHUB_TOKEN. Never given a literal default — a
    # secret that "works" out of the box is a secret waiting to be
    # committed. SecretStr keeps the value out of repr()/str() and out
    # of accidental log lines; see logging_setup.mask_secrets for the
    # belt-and-suspenders structlog processor.
    github_token: SecretStr | None = None

    @field_validator("model_path")
    @classmethod
    def model_path_must_exist(cls, v: str) -> str:
        if not Path(v).is_file():
            raise ValueError(
                f"FRAUD_MODEL_PATH={v!r} does not exist - refusing to start. "
                "Check the path, or that the model volume/artifact is mounted."
            )
        return v

    @field_validator("log_level")
    @classmethod
    def log_level_must_be_known(cls, v: str) -> str:
        upper = v.upper()
        if upper not in _VALID_LOG_LEVELS:
            raise ValueError(
                f"FRAUD_LOG_LEVEL={v!r} must be one of {sorted(_VALID_LOG_LEVELS)}"
            )
        return upper
