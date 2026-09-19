"""Typed, fail-fast configuration. One place to read every environment
variable — never scatter `os.environ["X"]` across the codebase (that
was one of the "common mistakes" called out in Module 1).

TODO (Lab 1, step 3-4):
Define a pydantic-settings Settings class with at least: model_path,
block_threshold. Read configs/settings.example.env for the expected
variable names (FRAUD_ prefix).

Suggested shape:

    from pydantic_settings import BaseSettings

    class Settings(BaseSettings):
        model_path: str = "models/fraud_model.joblib"
        block_threshold: float = 0.85

        class Config:
            env_prefix = "FRAUD_"
"""

# TODO: implement Settings.
