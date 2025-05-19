from fastapi import FastAPI, APIRouter
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import json
from datetime import datetime
from app.api.endpoints import corpus_router, user_router
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

router = APIRouter()

@router.get("/notifications/{client_id}")
def get_notifications(client_id: str):
    file_path = f"notifications_{client_id}.json"
    if Path(file_path).exists():
        with open(file_path) as f:
            return {"notifications": [json.loads(line) for line in f]}
    return {"message": "No notifications found"}

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()
    try:
        # Отправляем JSON-приветствие
        await websocket.send_json({
            "status": "CONNECTED",
            "client_id": client_id,
            "message": "WebSocket connection established"
        })
        # В любом месте, где отправляете сообщения
        await websocket.send_json({
            "status": "STARTED",
            "task_id": "123",
            "word": "example",
            "algorithm": "levenshtein"
        })

        while True:
            data = await websocket.receive_text()
            # Обработка входящих сообщений (если нужно)

    except WebSocketDisconnect:
        print(f"Client {client_id} disconnected")
    except Exception as e:
        print(f"Error with {client_id}: {str(e)}")
        await websocket.close()




app.include_router(user_router, prefix="/api")
app.include_router(corpus_router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "API is working"}