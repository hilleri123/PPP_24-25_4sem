# API для библиотеки

## Установка

1. Создайте виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate  # для Linux/Mac
# или
venv\Scripts\activate  # для Windows
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

## Запуск

```bash
python run.py
```

После запуска API будет доступно по адресу: http://localhost:8000

## API Endpoints

### Авторы

- GET /authors - получить список всех авторов
- POST /authors - создать нового автора
- GET /authors/{id} - получить автора по ID
- PUT /authors/{id} - обновить автора
- DELETE /authors/{id} - удалить автора

### Книги

- GET /books - получить список всех книг
- GET /books?author_id={id} - получить книги конкретного автора
- POST /books - создать новую книгу

## Документация API

После запуска приложения доступна автоматическая документация:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc 