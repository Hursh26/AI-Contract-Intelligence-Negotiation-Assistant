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

    # --- ML/NLP service (ml/api.py, run separately: uvicorn ml.api:app --port 8001) ---
    ML_SERVICE_URL: str = "http://localhost:8001"
    ML_SERVICE_TIMEOUT_SECONDS: float = 120.0  # first call may download models
    # ML keeps ONE search index (the last analyzed contract). The backend tracks
    # which contract it holds in process memory, which is only correct with a
    # single backend worker. Set True when running >1 worker/instance: every
    # /ask then re-analyzes first (slower, but always the right contract).
    ML_REINDEX_EVERY_ASK: bool = False
    # How long a request waits for the ML slot before giving up with 503.
    ML_LOCK_TIMEOUT_SECONDS: float = 60.0

    # --- File uploads ---
    # Relative to backend/ (resolved via pathlib in app/utils/storage.py, so
    # this works unchanged on macOS/Linux/Windows regardless of separator).
    STORAGE_DIR: str = "storage/contracts"
    MAX_UPLOAD_SIZE_MB: int = 10

    # --- CORS ---
    # 5173 = Vite dev server (frontend/); 3000 kept for other dev setups.
    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
