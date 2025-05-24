from fastapi import WebSocket, WebSocketDisconnect, APIRouter, Query
from app.models.user import User
from app.celery_worker import celery_app
from celery.result import AsyncResult
from jose import jwt, JWTError
import os
import json

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=[os.getenv("ALGORITHM")])
        user_id = int(payload.get("sub"))
    except (JWTError, ValueError):
        await websocket.close(code=1008)
        return

    await websocket.accept()
    print(f"WebSocket подключён: user_id={user_id}")

    try:
        while True:
            try:
                data = await websocket.receive_text()
                parsed = json.loads(data)
            except json.JSONDecodeError:
                await websocket.send_json({
                    "error": "Invalid JSON format"
                })
                continue

            if isinstance(parsed, dict) and "task_id" in parsed and len(parsed) == 1:
                task_id = parsed.get("task_id")
                if not isinstance(task_id, str):
                    await websocket.send_json({"error": "Invalid task_id format"})
                    continue

                result = celery_app.AsyncResult(task_id)

                if result.successful():
                    await websocket.send_json({
                        "status": "COMPLETED",
                        "task_id": task_id,
                        "execution_time": result.result.get("execution_time"),
                        "results": result.result.get("results")
                    })
                elif result.state == "PROGRESS":
                    await websocket.send_json({
                        "status": "PROGRESS",
                        "task_id": task_id,
                        "progress": result.info.get("progress", 0),
                        "current_word": f"processing word {result.info.get('current_word', '?')}"
                    })
                else:
                    await websocket.send_json({
                        "status": result.state,
                        "task_id": task_id
                    })

            elif all(k in parsed for k in ("word", "algorithm", "corpus_id")):
                word = parsed.get("word")
                algorithm = parsed.get("algorithm")
                corpus_id = parsed.get("corpus_id")

                if not isinstance(word, str) or not isinstance(algorithm, str) or not isinstance(corpus_id, int):
                    await websocket.send_json({"error": "Invalid search task format"})
                    continue

                task = celery_app.send_task(
                    "fuzzy_search_task",
                    args=[word, algorithm, corpus_id]
                )

                await websocket.send_json({
                    "status": "STARTED",
                    "task_id": task.id,
                    "word": word,
                    "algorithm": algorithm
                })

            else:
                await websocket.send_json({
                    "error": "Invalid message structure. Expected 'task_id' or {word, algorithm, corpus_id}."
                })

    except WebSocketDisconnect:
        print(f"WebSocket отключён: user_id={user_id}")