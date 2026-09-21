"""Typed, fail-fast configuration. One place to read every environment
variable — never scatter os.environ["X"] across the codebase.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="FRAUD_")

    model_path: str = "models/fraud_model.joblib"
    block_threshold: float = 0.85
    log_level: str = "INFO"


settings = Settings()
