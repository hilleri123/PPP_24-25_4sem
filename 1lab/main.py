from server import Server
from client import Client
import threading
import sys
import socket

def run_server():
    """Функция запуска сервера"""
    try:
        server = Server()
        server.start()
    except Exception as e:
        print(f"Server error: {str(e)}", file=sys.stderr)
        sys.exit(1)

def run_client():
    """Функция запуска клиента"""
    client = Client()
    client.interactive_mode()

if __name__ == "__main__":
    # Запускаем сервер в отдельном потоке
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()

    try:
        # Запускаем клиент в основном потоке
        run_client()
    except KeyboardInterrupt:
        pass  # Игнорируем Ctrl+C
    finally:
        # При завершении пытаемся корректно остановить сервер
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(("localhost", 12345))
                s.sendall(b"SHUTDOWN")
        except:
            pass
        
        sys.exit(0)
