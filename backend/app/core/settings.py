from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Shipped defaults that must never reach production. Kept out of production by
# the validator below; development/tests fall back to a clearly-labeled dev
# secret so auth keeps working without an env var.
_INSECURE_SECRET_DEFAULTS = {
    "changeme",
    "supersecretkeyreplaceinproduction",
    "dev-only-insecure-change-me",
}


class Settings(BaseSettings):
    APP_NAME: str = "CodeSense"
    APP_ENV: str = "development"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "dev-only-insecure-change-me"

    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "codesense"
    POSTGRES_PORT: str = "5432"
    DATABASE_URL: str | None = None

    # AI Settings (Optional for MVP)
    OPENROUTER_API_KEY: str | None = None
    LLM_MODEL: str | None = "google/antigravity-gemini-3.5-flash"
    AI_GATEWAY_URL: str | None = None

    # ML Settings
    ML_MODELS_PATH: str = "ml_models"
    FEATURE_STORE_ENABLED: bool = True
    DEFAULT_MODEL_VERSION: str = "1.0.0"
    FUSION_CONFIDENCE_THRESHOLD: float = 0.7

    # Redis / Cache / Queue Settings (Phase 2)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str | None = None
    REDIS_URL: str | None = None
    CACHE_TTL_SECONDS: int = 300
    ENABLE_REDIS: bool = True

    # Celery / Worker Settings
    CELERY_BROKER_URL: str | None = None
    CELERY_RESULT_BACKEND: str | None = None
    ENABLE_WORKER: bool = True
    WORKER_CONCURRENCY: int = 2

    # Observability Settings
    ENABLE_METRICS: bool = True
    ENABLE_TRACING: bool = True
    PROMETHEUS_PORT: int = 9090
    OTEL_EXPORTER_OTLP_ENDPOINT: str | None = None

    # Privacy & Offline (Phase 20)
    MIN_TEAM_SIZE: int = 5
    # Set in production so actor pseudonyms stay stable across restarts.
    # Unset -> the policy module falls back to a real SECRET_KEY, and
    # finally to a random per-process secret (never a shipped placeholder).
    PRIVACY_PSEUDONYM_SALT: str = ""
    EXPOSE_RAW_PAYLOADS: bool = False
    # Trailing window (days) a detection's contributor count is measured
    # over. A detection is masked when either its all-time count or its
    # window count is below MIN_TEAM_SIZE.
    PRIVACY_DETECTION_WINDOW_DAYS: int = 30
    OFFLINE_PROBE_URL: str = "https://connectivitycheck.gstatic.com/generate_204"
    OFFLINE_PROBE_TIMEOUT_SECONDS: float = 2.0
    OFFLINE_PROBE_INTERVAL_SECONDS: int = 30

    # Auth (Phase 22)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"
    BCRYPT_ROUNDS: int = 12

    @property
    def REDIS_URI(self) -> str:
        if self.REDIS_URL:
            return self.REDIS_URL
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    @property
    def CELERY_BROKER_URI(self) -> str:
        if self.CELERY_BROKER_URL:
            return self.CELERY_BROKER_URL
        return self.REDIS_URI

    @property
    def CELERY_BACKEND_URI(self) -> str:
        if self.CELERY_RESULT_BACKEND:
            return self.CELERY_RESULT_BACKEND
        return self.REDIS_URI

    @model_validator(mode="after")
    def _require_secret_in_production(self) -> "Settings":
        """Require a real SECRET_KEY via env var in production.

        In development/tests a labeled dev default keeps auth functional, but
        production must not start with an insecure placeholder.
        """
        if self.APP_ENV == "production" and (
            not self.SECRET_KEY or self.SECRET_KEY in _INSECURE_SECRET_DEFAULTS
        ):
            raise ValueError(
                "SECRET_KEY must be set via environment variable in production; "
                "insecure defaults are prohibited"
            )
        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"


settings = Settings()
