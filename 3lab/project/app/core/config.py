from pydantic_settings import BaseSettings
from pydantic import AnyUrl, PostgresDsn, RedisDsn


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./sql_app.db"

    SECRET_KEY: str = "Rita_key" 
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    REDIS_URL: RedisDsn = "redis://localhost:6379/0"
    CELERY_BROKER_URL: RedisDsn = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: RedisDsn = "redis://localhost:6379/0"


    DEBUG: bool = True
    PROJECT_NAME: str = "Fuzzy Search API"

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        case_sensitive = False


settings = Settings()
