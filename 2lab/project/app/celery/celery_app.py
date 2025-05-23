# app/celery/celery_app.py
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "project",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=['app.celery.tasks']
)

celery_app.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='Europe/Moscow',
    enable_utc=True,
    task_track_started=True,
)

if __name__ == '__main__':
    celery_app.start()