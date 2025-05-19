from typing import Dict
from fastapi import WebSocket

class ConnectionManager: # управление активными WebSocket-соединениями и рассылка сообщений
    def __init__(self):
        self.active_connections = {} # cловарь для хранения активных соединений

    async def connect(self, websocket: WebSocket, client_id: str): # установка соединения
        await websocket.accept()
        self.active_connections[client_id] = websocket # сохраняет соединение в словаре active_connections

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id] # удаляет соединение из словаря по client_id, предварительно проверив его наличие

    async def send_message(self, message: str, client_id: str):
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_text(message)
            except Exception as e:
                print(f"Failed to send to {client_id}: {str(e)}") # логирует проблему
                self.disconnect(client_id) # закрывает соединение