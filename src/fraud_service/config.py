"""Typed, fail-fast configuration.

One place reads the environment — never scatter `os.environ["X"]`
across the codebase, and never hardcode a relative path mid-module the
way the notebook did (SMELL 2).
"""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Reads FRAUD_-prefixed env vars; see configs/settings.example.env."""

    model_config = SettingsConfigDict(
        env_prefix="FRAUD_",
        env_file=".env",
        extra="ignore",
        protected_namespaces=(),
    )

    model_path: Path = Path("models/fraud_model.joblib")
    data_path: Path = Path("data/transactions_sample.csv")
    output_path: Path = Path("scored.csv")
    block_threshold: float = 0.85
    log_level: str = "INFO"
