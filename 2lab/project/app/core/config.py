import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()


class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///app/db/test.db")
    SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

    if JWT_SECRET_KEY is None:
        raise ValueError("ОШИБКА: JWT_SECRET_KEY не задан в переменных окружения!")


# app/core/config.py
import redislite
import os
from dotenv import load_dotenv
from typing import Optional  # Добавлен импорт

dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
load_dotenv(dotenv_path=dotenv_path)


class Settings:
    PROJECT_NAME: str = "Fuzzy Search API with Celery and WebSockets"

    _project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    REDISLITE_DB_PATH: str = os.getenv("REDISLITE_DB_PATH",
                                       os.path.join(_project_root, "data", "redislite.db"))

    os.makedirs(os.path.dirname(REDISLITE_DB_PATH), exist_ok=True)

    _redis_instance: Optional = None  # Указан тип
    REDISLITE_SOCKET_PATH: Optional[str] = None
    try:
        _redis_instance = redislite.Redis(REDISLITE_DB_PATH)
        REDISLITE_SOCKET_PATH = _redis_instance.socket_file
    except Exception as e:
        print(f"WARNING: Could not initialize redislite at {REDISLITE_DB_PATH}: {e}")

    if REDISLITE_SOCKET_PATH:
        CELERY_BROKER_URL: str = f"redis+socket://{REDISLITE_SOCKET_PATH}"
        CELERY_RESULT_BACKEND: str = f"redis+socket://{REDISLITE_SOCKET_PATH}"
    else:
        print("CRITICAL: redislite socket path not available. Celery will not use redislite.")
        CELERY_BROKER_URL: str = "memory://"
        CELERY_RESULT_BACKEND: str = "rpc://"

    API_V1_STR: str = "/api/v1"


settings = Settings()