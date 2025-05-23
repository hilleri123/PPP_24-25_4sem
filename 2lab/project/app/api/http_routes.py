# app/api/http_routes.py
from fastapi import APIRouter, HTTPException, Body
from app.celery.tasks import fuzzy_search_task
# Предполагается, что схемы Pydantic определены в app.schemas
# from app.schemas import SearchTaskCreate, SearchTaskResponse

router = APIRouter()

@router.post("/start_search", status_code=202) # response_model=SearchTaskResponse
async def start_fuzzy_search_http(
    # Вместо отдельных полей можно использовать Pydantic модель
    # search_params: SearchTaskCreate
    client_id: str = Body(...),
    data_to_search: list = Body(...),
    query_string: str = Body(...),
    algorithm: str = Body(default="ratio"),
    threshold: int = Body(default=70)
):
    try:
        task = fuzzy_search_task.delay(
            client_id=client_id,
            data_to_search=data_to_search,
            query_string=query_string,
            algorithm=algorithm,
            threshold=threshold
        )
        return {"message": "Задача нечеткого поиска запущена", "task_id": task.id, "client_id": client_id}
    except Exception as e:
        print(f"Ошибка запуска задачи Celery: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка запуска задачи Celery: {str(e)}")

# В main.py этот роутер будет подключен:
# from app.api import http_routes
# app.include_router(http_routes.router, prefix="/api/v1", tags=["search"])