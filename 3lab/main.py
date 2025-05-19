from fastapi import FastAPI, APIRouter
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import json
from datetime import datetime
from app.api.endpoints import corpus_router, user_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # разрешаем все домены
    allow_credentials=True,
    allow_methods=["*"],  # разрешаем все HTTP-методы
    allow_headers=["*"],  # разрешаем все заголовки
)

app.include_router(user_router, prefix="/api")
app.include_router(corpus_router, prefix="/api")

router = APIRouter()

@router.get("/notifications/{client_id}") # возвращает сохранённые уведомления для указанного клиента
def get_notifications(client_id: str):
    file_path = f"notifications_{client_id}.json"
    if Path(file_path).exists():
        with open(file_path) as f:
            return {"notifications": [json.loads(line) for line in f]}
    return {"message": "No notifications found"}

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept() # принимаем соединение
    try:
        await websocket.send_json({ # отправляем JSON-приветствие
            "status": "CONNECTED",
            "client_id": client_id,
            "message": "WebSocket connection established"
        })
        await websocket.send_json({ # в любом месте, где отправляете сообщения
            "status": "STARTED",
            "task_id": "123",
            "word": "example",
            "algorithm": "levenshtein"
        })

        while True:
            data = await websocket.receive_text()  # обработка входящих сообщений (если нужно)

    except WebSocketDisconnect: # обработка разрыва соединения
        print(f"Client {client_id} disconnected")
    except Exception as e:
        print(f"Error with {client_id}: {str(e)}")
        await websocket.close()



