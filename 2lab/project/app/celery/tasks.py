# # app/celery/tasks.py
# import time
#
# from .celery_app import celery_app
# from thefuzz import fuzz
#
#
# @celery_app.task(bind=True, name="app.celery.tasks.fuzzy_search_task")
# def fuzzy_search_task(self, client_id: str, data_to_search: list, query_string: str, algorithm: str = "ratio",
#                       threshold: int = 70):
#     task_id = self.request.id
#     start_time = time.time()
#     results = [] # Инициализация списка
#
#     initial_meta = {
#         "task_id": task_id, "client_id": client_id,
#         "status_details": {"query_string": query_string, "algorithm": algorithm, "threshold": threshold,
#                            "total_items": len(data_to_search),
#                            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
#     }
#     self.update_state(state='STARTED', meta=initial_meta)
#
#     processed_count = 0
#     total_count = len(data_to_search)
#
#     for item in data_to_search:
#         score = fuzz.ratio(query_string, item) if algorithm == "ratio" else fuzz.partial_ratio(query_string, item)
#         if score >= threshold:
#             results.append({"original": item, "match_score": score, "query_match": query_string})
#         processed_count += 1
#         progress_percent = int((processed_count / total_count) * 100) if total_count > 0 else 0
#
#         progress_meta = {
#             "task_id": task_id, "client_id": client_id,
#             "status_details": {"progress_percent": progress_percent, "current_item_processed": item,
#                                "matches_found_so_far": len(results),
#                                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
#         }
#         time.sleep(0.01)
#         self.update_state(state='PROGRESS', meta=progress_meta)
#
#     execution_time = time.time() - start_time
#     final_meta = {
#         "task_id": task_id, "client_id": client_id,
#         "status_details": {"results": results, "execution_time_seconds": round(execution_time, 2),
#                            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
#     }
#     self.update_state(state='COMPLETED', meta=final_meta)
#     return final_meta

# app/celery/tasks.py
import time
import json
from celery import current_task
from .celery_app import celery_app
from thefuzz import fuzz


@celery_app.task(bind=True, name="app.celery.tasks.fuzzy_search_task")
def fuzzy_search_task(self, client_id: str, data_to_search: list, query_string: str, algorithm: str = "ratio",
                      threshold: int = 70):
    task_id = self.request.id
    start_time = time.time()
    results = [] # Инициализация списка

    # Формируем метаданные для STARTED
    initial_meta_details = {
        "word": query_string,  # По вашему формату
        "algorithm": algorithm  # По вашему формату
    }
    initial_meta_for_celery = {  # Это то, что сохраняется в Celery
        "task_id": task_id,
        "client_id": client_id,
        "status_details": initial_meta_details  # Вкладываем детали для консистентности
    }
    # Это сообщение, которое мы хотим видеть отправленным по WebSocket
    websocket_started_message = {
        "status": "STARTED",
        "task_id": task_id,
        **initial_meta_details  # Распаковываем детали сюда
    }
    print(f"CELERY WORKER (Task ID: {task_id}): Preparing STARTED state.")
    print(f"CELERY WORKER (Task ID: {task_id}): Meta for Celery backend (STARTED): {initial_meta_for_celery}")
    print(
        f"CELERY WORKER (Task ID: {task_id}): Expected WebSocket STARTED message structure: {websocket_started_message}")
    self.update_state(state='STARTED', meta=initial_meta_for_celery)

    processed_count = 0
    total_count = len(data_to_search)

    for i, item in enumerate(data_to_search):
        score = fuzz.ratio(query_string, item) if algorithm == "ratio" else fuzz.partial_ratio(query_string, item)
        if score >= threshold:
            results.append({"word": item, "distance": 100 - score})  # Пример distance, адаптируйте

        processed_count += 1
        progress_percent = int((processed_count / total_count) * 100) if total_count > 0 else 0

        # Формируем метаданные для PROGRESS
        progress_meta_details = {
            "progress": progress_percent,
            "current_word": f"processing word {processed_count}/{total_count}"  # По вашему формату
        }
        progress_meta_for_celery = {
            "task_id": task_id,
            "client_id": client_id,
            "status_details": progress_meta_details
        }
        websocket_progress_message = {
            "status": "PROGRESS",
            "task_id": task_id,
            **progress_meta_details
        }
        print(f"CELERY WORKER (Task ID: {task_id}, Item: {i + 1}/{total_count}): Preparing PROGRESS state.")
        print(f"CELERY WORKER (Task ID: {task_id}): Meta for Celery backend (PROGRESS): {progress_meta_for_celery}")
        print(
            f"CELERY WORKER (Task ID: {task_id}): Expected WebSocket PROGRESS message structure: {websocket_progress_message}")

        # Искусственная задержка для отладки, чтобы успеть увидеть PROGRESS
        time.sleep(0.5)  # Увеличьте, если нужно больше времени

        self.update_state(state='PROGRESS', meta=progress_meta_for_celery)

    execution_time = time.time() - start_time

    # Формируем метаданные для COMPLETED
    # Адаптируем 'results' к вашему формату: [{"word": "example", "distance": 0},...]
    # В моем примере 'results' уже содержит {"word": item, "distance":...}
    completed_meta_details = {
        "execution_time": round(execution_time, 2),
        "results": results  # 'results' уже должны быть в нужном формате
    }
    completed_meta_for_celery = {
        "task_id": task_id,
        "client_id": client_id,
        "status_details": completed_meta_details
    }
    websocket_completed_message = {
        "status": "COMPLETED",
        "task_id": task_id,
        **completed_meta_details
    }
    print(f"CELERY WORKER (Task ID: {task_id}): Preparing COMPLETED state.")
    print(f"CELERY WORKER (Task ID: {task_id}): Meta for Celery backend (COMPLETED): {completed_meta_for_celery}")
    print(
        f"CELERY WORKER (Task ID: {task_id}): Expected WebSocket COMPLETED message structure: {websocket_completed_message}")
    self.update_state(state='COMPLETED', meta=completed_meta_for_celery)

    return completed_meta_for_celery  # Возвращаем мета для Celery, FastAPI будет их читать