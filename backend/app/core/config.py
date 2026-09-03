"""Application configuration, loaded from environment variables / .env.

See ../../.env.example for the full list of variables a local .env needs.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- App ---
    PROJECT_NAME: str = "AI Contract Intelligence & Negotiation Assistant"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"

    # --- Database ---
    # Dev-friendly default so the app boots without a .env file for local
    # scaffolding/testing; override this in every real environment.
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/contract_assistant"

    # --- Auth (JWT) ---
    JWT_SECRET_KEY: str = "dev-secret-change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # --- LLM integration ---
    # Provider/base URL is not finalized yet; left blank until decided.
    LLM_API_KEY: str | None = None
    LLM_API_BASE_URL: str | None = None

    # --- File uploads ---
    # Relative to backend/ (resolved via pathlib in app/utils/storage.py, so
    # this works unchanged on macOS/Linux/Windows regardless of separator).
    STORAGE_DIR: str = "storage/contracts"
    MAX_UPLOAD_SIZE_MB: int = 10

    # --- CORS ---
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
