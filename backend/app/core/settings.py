from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "CodeSense"
    APP_ENV: str = "development"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "supersecretkeyreplaceinproduction"
    
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "codesense"
    POSTGRES_PORT: str = "5432"
    DATABASE_URL: Optional[str] = None

    # AI Settings (Optional for MVP)
    OPENROUTER_API_KEY: Optional[str] = None
    LLM_MODEL: Optional[str] = "google/antigravity-gemini-3.5-flash"
    AI_GATEWAY_URL: Optional[str] = None
    
    # ML Settings
    ML_MODELS_PATH: str = "ml_models"
    FEATURE_STORE_ENABLED: bool = True
    DEFAULT_MODEL_VERSION: str = "1.0.0"
    FUSION_CONFIDENCE_THRESHOLD: float = 0.7

    # Redis / Cache / Queue Settings (Phase 2)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    REDIS_URL: Optional[str] = None
    CACHE_TTL_SECONDS: int = 300
    ENABLE_REDIS: bool = True

    # Celery / Worker Settings
    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None
    ENABLE_WORKER: bool = True
    WORKER_CONCURRENCY: int = 2

    # Observability Settings
    ENABLE_METRICS: bool = True
    ENABLE_TRACING: bool = True
    PROMETHEUS_PORT: int = 9090
    OTEL_EXPORTER_OTLP_ENDPOINT: Optional[str] = None

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
