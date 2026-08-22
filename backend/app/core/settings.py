import os
from pydantic_settings import BaseSettings

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

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
