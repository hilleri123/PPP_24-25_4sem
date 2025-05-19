from celery import Celery
from kombu.transport.sqlalchemy import Transport
import os
from app.core.config import settings
from app.websocket.manager import ConnectionManager
import json
from datetime import datetime
import time

app = Celery(
    'tasks',
    broker='sqla+sqlite:///celerydb.sqlite', # очередь задач (в файле celerydb.sqlite)
    backend='db+sqlite:///results.sqlite' # хранилище результатов (в файле results.sqlite)
)

app.conf.update( # конфигурация
    task_serializer='json',      # cериализация задач в JSON
    accept_content=['json'],     # принимаем только JSON
    result_serializer='json',    # результаты в JSON
    timezone='Europe/Moscow',    # часовой пояс
    enable_utc=True              # использовать UTC время
)

manager = ConnectionManager()


@app.task(bind=True)
def fuzzy_search_task(self, word, algorithm, corpus_id, client_id):
    try:
        self.send_update(client_id, { # отправка STARTED
            "status": "STARTED",
            "task_id": self.request.id,
            "word": word,
            "algorithm": algorithm
        })


        for i in range(100): # имитация обработки с отправкой PROGRESS
            time.sleep(0.1)  # задержка для имитации
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


def send_update(self, client_id, message): # логирует уведомления в файл celery_notifications.log
    from app.websocket.manager import manager
    log_file = f"celery_notifications.log"

    with open(log_file, "a") as f:
        f.write(json.dumps({
            "timestamp": str(datetime.now()),
            "client_id": client_id,
            "data": message
        }) + "\n")

    manager.send_message(json.dumps(message), client_id)



