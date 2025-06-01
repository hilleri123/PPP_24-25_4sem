# Лабораторная работа №3: Асинхронный API с WebSocket и Celery (redislite)

Этот проект демонстрирует интеграцию **FastAPI**, **WebSocket** и **Celery**  
с использованием **redislite** в качестве брокера и бэкенда, а также включает консольный клиент.

## Быстрый старт

```bash
# Клонируем / распаковываем проект
pip install -r requirements.txt

# Запускаем API
uvicorn main:app --reload

# В отдельном терминале – Celery‑воркер
celery -A app.celery.config.celery_app worker --loglevel=info

# Запускаем CLI‑клиент
python client.py --url https://example.com --max-depth 2 --user-id ivan
```

По ходу выполнения парсинга клиент будет получать WebSocket‑уведомления:
`STARTED`, `PROGRESS`, `COMPLETED`.

## Структура

```text
project_lab3/
├── README.md
├── requirements.txt
├── main.py
├── client.py
└── app/
    ├── __init__.py
    ├── api/
    │   ├── __init__.py
    │   └── routes.py
    ├── websocket/
    │   ├── __init__.py
    │   ├── manager.py
    │   └── routes.py
    ├── celery/
    │   ├── __init__.py
    │   ├── config.py
    │   └── tasks.py
    └── services/
        ├── __init__.py
        └── parser.py
```

> **Важно:** redislite автоматически поднимает локальный Redis‑экземпляр,  
> никакого отдельного сервера устанавливать не нужно.
