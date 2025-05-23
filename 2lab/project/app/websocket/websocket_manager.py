# app/websocket/websocket_manager.py
from typing import Dict, List
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        # Словарь для хранения активных соединений: {client_id: WebSocket}
        self.active_connections: Dict = {}

    async def connect(self, client_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        print(f"Клиент {client_id} подключен. Активные соединения: {list(self.active_connections.keys())}")

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            print(f"Клиент {client_id} отключен. Активные соединения: {list(self.active_connections.keys())}")

    async def send_personal_message(self, message: dict, client_id: str):
        websocket = self.active_connections.get(client_id)
        if websocket:
            try:
                await websocket.send_json(message)
            except Exception as e:
                print(f"Ошибка отправки сообщения клиенту {client_id}: {e}")
        else:
            print(f"Клиент {client_id} не найден для отправки сообщения.")

    async def broadcast(self, message: dict):
        for client_id, connection in self.active_connections.items():
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Ошибка широковещательной отправки клиенту {client_id}: {e}")

manager = ConnectionManager()