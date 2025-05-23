import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()


class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

    if JWT_SECRET_KEY is None:
        raise ValueError("ОШИБКА: JWT_SECRET_KEY не задан в переменных окружения!")
