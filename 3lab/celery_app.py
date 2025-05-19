from celery import Celery
from kombu.transport.sqlalchemy import Transport
import os
from app.core.config import settings
from app.websocket.manager import ConnectionManager
import json
from datetime import datetime
import time

# Используем SQLite в качестве брокера
app = Celery(
    'tasks',
    broker='sqla+sqlite:///celerydb.sqlite',
    backend='db+sqlite:///results.sqlite'
)

# Конфигурация
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Europe/Moscow',
    enable_utc=True,
)

manager = ConnectionManager()


@app.task(bind=True)
def fuzzy_search_task(self, word, algorithm, corpus_id, client_id):
    try:
        # Отправка STARTED
        self.send_update(client_id, {
            "status": "STARTED",
            "task_id": self.request.id,
            "word": word,
            "algorithm": algorithm
        })

        # Имитация обработки с отправкой PROGRESS
        for i in range(100):
            time.sleep(0.1)  # Задержка для имитации
            if i % 10 == 0:
                self.send_update(client_id, {
                    "status": "PROGRESS",
                    "progress": i,
                    "current_word": f"Processing {i}/100"
                })

        # Отправка COMPLETED
        self.send_update(client_id, {
            "status": "COMPLETED",
            "results": [{"word": "example", "distance": 0}]
        })

    except Exception as e:
        self.send_update(client_id, {"status": "ERROR", "error": str(e)})


def send_update(self, client_id, message):
    from app.websocket.manager import manager
    log_file = f"celery_notifications.log"

    with open(log_file, "a") as f:
        f.write(json.dumps({
            "timestamp": str(datetime.now()),
            "client_id": client_id,
            "data": message
        }) + "\n")

    manager.send_message(json.dumps(message), client_id)



