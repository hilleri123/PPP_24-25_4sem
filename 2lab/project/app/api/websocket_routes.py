# # app/api/websocket_routes.py
# from fastapi import APIRouter, WebSocket, WebSocketDisconnect
# from ..websocket.websocket_manager import manager # Корректный путь
#
# # app/api/websocket_routes.py
# import asyncio
# import json
# from fastapi import APIRouter, WebSocket, WebSocketDisconnect
# from celery.result import AsyncResult
# from app.celery.celery_app import celery_app
# from app.websocket.websocket_manager import manager
#
# router = APIRouter() # Уже определен, если это тот же файл
#
#
# @router.websocket("/ws/{client_id}")
# async def websocket_task_updates_endpoint(websocket: WebSocket, client_id: str):
#     await manager.connect(client_id, websocket)
#     try:
#         while True:
#             data = await websocket.receive_text()
#             await manager.send_personal_message({"response": f"Команда '{data}' получена для клиента {client_id}"},
#                                                 client_id)
#     except WebSocketDisconnect:
#         manager.disconnect(client_id)
#     except Exception as e:
#         print(f"Ошибка WebSocket для клиента {client_id}: {e}")
#         manager.disconnect(client_id)
#
#
# async def poll_task_status(client_id: str, task_id: str, ws: WebSocket):
#     last_known_state = None
#     last_known_meta_str = None
#
#     while True:
#         if client_id not in manager.active_connections:
#             break
#         try:
#             celery_task = AsyncResult(task_id, app=celery_app)
#             current_state = celery_task.state
#             current_meta = celery_task.info
#             current_meta_str = json.dumps(current_meta, sort_keys=True) if isinstance(current_meta, dict) else str(current_meta)
#
#             if current_state!= last_known_state or current_meta_str!= last_known_meta_str:
#                 status_details = current_meta.get("status_details") if isinstance(current_meta, dict) else (current_meta if not isinstance(current_meta, (type(None), bool)) else {})
#                 update_message = {"task_id": task_id, "client_id": client_id, "status": current_state, "details": status_details}
#                 await manager.send_personal_message(update_message, client_id)
#                 last_known_state = current_state
#                 last_known_meta_str = current_meta_str
#             if celery_task.ready():
#                 break
#             await asyncio.sleep(1)
#         except asyncio.CancelledError:
#             break
#         except Exception as e:
#             print(f"Ошибка при опросе задачи {task_id} для клиента {client_id}: {e}")
#             await asyncio.sleep(5)

# app/api/websocket_routes.py
import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from celery.result import AsyncResult
from app.celery.celery_app import celery_app
from app.websocket.websocket_manager import manager

router = APIRouter()


# ... ваш @router.websocket("/ws/{client_id}") эндпоинт...
# Убедитесь, что он вызывает poll_task_status правильно, например:
# async def websocket_task_updates_endpoint(websocket: WebSocket, client_id: str):
#     await manager.connect(client_id, websocket)
#     polling_task = None
#     try:
#         while True:
#             data = await websocket.receive_json() # Ожидаем JSON от клиента
#             action = data.get("action")
#             if action == "track_task":
#                 task_id_to_poll = data.get("task_id")
#                 if task_id_to_poll:
#                     print(f"FASTAPI SERVER (Client: {client_id}): Received track_task for Task ID: {task_id_to_poll}")
#                     if polling_task: # Если уже есть задача опроса, отменяем ее
#                         polling_task.cancel()
#                     polling_task = asyncio.create_task(poll_task_status(client_id, task_id_to_poll, websocket))
#                     # Отправляем подтверждение начала отслеживания, если нужно
#                     # await manager.send_personal_message({"status": "TRACKING_STARTED", "task_id": task_id_to_poll}, client_id)
#                 else:
#                     await manager.send_personal_message({"error": "task_id не предоставлен для отслеживания"}, client_id)
#             #... другая логика обработки команд от клиента...
#     except WebSocketDisconnect:
#         print(f"FASTAPI SERVER (Client: {client_id}): WebSocket disconnected.")
#         if polling_task:
#             polling_task.cancel()
#         manager.disconnect(client_id)
#     except Exception as e:
#         print(f"FASTAPI SERVER (Client: {client_id}): WebSocket error: {e}")
#         if polling_task:
#             polling_task.cancel()
#         manager.disconnect(client_id)
#         # Consider closing websocket if not already closed by disconnect
#         # await websocket.close(code=1011)


async def poll_task_status(client_id: str, task_id: str, ws: WebSocket):
    print(f"FASTAPI SERVER (Client: {client_id}, Task: {task_id}): Starting to poll task status.")
    last_known_state = None
    last_known_meta_str = None

    while True:
        if client_id not in manager.active_connections:
            print(f"FASTAPI SERVER (Client: {client_id}, Task: {task_id}): Client disconnected, stopping poll.")
            break
        try:
            celery_task = AsyncResult(task_id, app=celery_app)
            current_state = celery_task.state
            current_meta = celery_task.info  # Это метаданные, установленные задачей Celery

            print(
                f"FASTAPI SERVER (Client: {client_id}, Task: {task_id}): Polled Celery. State='{current_state}'. Meta from Celery='{current_meta}'")

            current_meta_str = json.dumps(current_meta, sort_keys=True) if isinstance(current_meta, dict) else str(
                current_meta)

            if current_state != last_known_state or current_meta_str != last_known_meta_str:
                # Формируем сообщение для WebSocket на основе current_state и current_meta
                # и ваших целевых JSON структур

                websocket_message = {
                    "status": current_state,  # STARTED, PROGRESS, COMPLETED, FAILURE
                    "task_id": task_id
                }

                # Извлекаем 'status_details' из current_meta, если они есть
                status_details = {}
                if isinstance(current_meta, dict) and "status_details" in current_meta:
                    status_details = current_meta["status_details"]

                # Добавляем поля из status_details в корневой уровень WebSocket сообщения
                # в соответствии с вашими примерами JSON
                if current_state == "STARTED":
                    websocket_message.update(status_details if isinstance(status_details, dict) else {})
                elif current_state == "PROGRESS":
                    websocket_message.update(status_details if isinstance(status_details, dict) else {})
                elif current_state == "COMPLETED":
                    websocket_message.update(status_details if isinstance(status_details, dict) else {})
                elif current_state == "FAILURE":  # Обработка ошибок
                    websocket_message["error_message"] = str(
                        current_meta.get("exc_message", ["Unknown error"])) if isinstance(current_meta,
                                                                                          dict) and "exc_message" in current_meta else "Unknown error"

                print(
                    f"FASTAPI SERVER (Client: {client_id}, Task: {task_id}): State changed or meta updated. Preparing to send WebSocket message: {websocket_message}")
                await manager.send_personal_message(websocket_message, client_id)
                print(f"FASTAPI SERVER (Client: {client_id}, Task: {task_id}): WebSocket message sent.")

                last_known_state = current_state
                last_known_meta_str = current_meta_str

            if celery_task.ready():  # Задача завершена (SUCCESS, FAILURE, REVOKED)
                print(
                    f"FASTAPI SERVER (Client: {client_id}, Task: {task_id}): Celery task is ready (state: {current_state}). Stopping poll.")
                break

            await asyncio.sleep(1)  # Интервал опроса
        except asyncio.CancelledError:
            print(f"FASTAPI SERVER (Client: {client_id}, Task: {task_id}): Polling task cancelled.")
            break
        except Exception as e:
            print(f"FASTAPI SERVER (Client: {client_id}, Task: {task_id}): Error during polling: {e}")
            # Можно добавить логику повторных попыток или прекращения опроса при определенных ошибках
            await asyncio.sleep(5)  # Пауза перед следующей попыткой в случае ошибки