# from fastapi import FastAPI
# from app.api.api import router
#
# app = FastAPI(debug=True)
#
# app.include_router(router)
#
# if __name__ == "__main__":
#     import uvicorn
#
#     uvicorn.run(app, host="0.0.0.0", port=8000)

# main.py
# ["Пользователи", "Аутентификация"]

# main.py
from fastapi import FastAPI
from app.core.config import settings # Предполагаем, что настройки используются для префикса, заголовка и т.д.

# Импортируем существующий роутер из app/api/api.py
from app.api.api import router as main_api_router

# Импортируем новые роутеры (если вы решили разместить их в отдельных файлах)
from app.api.http_routes import router as celery_task_http_router # Для эндпоинта /start_search
from app.api.websocket_routes import router as websocket_router   # Для WebSocket эндпоинтов

app = FastAPI(title=settings.PROJECT_NAME, debug=True)

# 1. Подключаем ваш ОСНОВНОЙ роутер с существующими эндпоинтами
app.include_router(
    main_api_router,
    prefix=settings.API_V1_STR,  # Используйте ваш обычный префикс, например "/api/v1"
    tags=["Пользователи и Корпусы"]  # Пример тега для группировки в документации
)

# 2. Подключаем НОВЫЙ HTTP роутер для задач Celery
app.include_router(
    celery_task_http_router,
    prefix=settings.API_V1_STR,  # Можно использовать тот же префикс или другой
    tags=["Асинхронные Задачи Поиска"] # Тег для новых задач
)

# 3. Подключаем НОВЫЙ WebSocket роутер
app.include_router(
    websocket_router,
    # prefix="/ws",  # Опционально: можно задать префикс для всех WebSocket путей
    tags= ["Пользователи", "Аутентификация"]# Тег для WebSocket
)

@app.get("/")
async def root():
    return {"message": f"Welcome to {settings.PROJECT_NAME}"}

# Этот блок нужен, если вы запускаете приложение напрямую через `python main.py`
# Для запуска через `./start.sh` (который использует `uvicorn main:app --reload`), он не так критичен,
# но является хорошей практикой.
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)