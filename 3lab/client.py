import asyncio
import websockets
import json
from pprint import pprint
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def save_to_json(client_id: str, message: str) -> None:
    """Сохраняет сообщение в JSON-файл с историей всех уведомлений"""
    log_file = f"notifications_{client_id}.json"
    try:
        # Создаем структуру для сохранения
        entry = {
            "timestamp": datetime.now().isoformat(),
            "data": json.loads(message)
        }

        # Читаем существующие данные
        try:
            with open(log_file, 'r') as f:
                history = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            history = []

        # Добавляем новую запись
        history.append(entry)

        # Сохраняем обновленные данные
        with open(log_file, 'w') as f:
            json.dump(history, f, indent=2)

    except Exception as e:
        logger.error(f"Failed to save notification: {str(e)}")


async def listen_notifications(client_id: str) -> None:
    """Основная функция для прослушивания уведомлений"""
    uri = f"ws://localhost:8000/ws/{client_id}"
    reconnect_delay = 5

    while True:
        try:
            async with websockets.connect(uri) as websocket:
                logger.info(f"Connected to WebSocket. Client ID: {client_id}")

                # Обработка приветственного сообщения
                welcome = await websocket.recv()
                await save_to_json(client_id, welcome)
                welcome_data = json.loads(welcome)
                logger.info(f"Server: {welcome_data['message']}")

                # Основной цикл обработки сообщений
                async for message in websocket:
                    await save_to_json(client_id, message)
                    data = json.loads(message)

                    if data["status"] == "STARTED":
                        logger.info(f"\nTask started [{data['task_id']}]")
                        logger.info(f"Search: '{data['word']}' using {data['algorithm']}")

                    elif data["status"] == "PROGRESS":
                        print(f"Progress: {data['progress']}% | {data['current_word']}", end='\r')

                    elif data["status"] == "COMPLETED":
                        logger.info(f"\nTask completed in {data['execution_time']}s")
                        logger.info("Top results:")
                        pprint(data["results"])
                        return

                    elif data["status"] == "ERROR":
                        logger.error(f"\nError: {data['error']}")
                        return

        except websockets.exceptions.ConnectionClosed:
            logger.warning(f"Connection lost. Reconnecting in {reconnect_delay} seconds...")
            await asyncio.sleep(reconnect_delay)
        except Exception as e:
            logger.error(f"Error: {str(e)}")
            await asyncio.sleep(reconnect_delay)


async def main():
    client_id = "2f5a513a-c07b-48c8-99eb-3f8dc312ec7f"
    logger.info(f"Starting client with ID: {client_id}")
    await listen_notifications(client_id)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Client stopped by user")


