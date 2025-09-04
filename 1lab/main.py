import socket
import os
import json
import struct
import time
import sys
from collections import defaultdict

CMD_REQUEST_FROM_CLIENT = 1
CMD_RESPONSE_FROM_SERVER = 2
CMD_SEND_FILE = 3

class MyServer:
    def __init__(self, host="0.0.0.0", port=4200):
        self.host = host
        self.port = port
        self.state_file_path = "server_state.json"
        self.refresh_info()
        self.running = False

    def build_executables_structure(self):
        """Создает древовидную структуру исполняемых файлов из PATH"""
        path_dirs = os.getenv("PATH", "").split(os.pathsep)
        structure = defaultdict(dict)
        
        for directory in path_dirs:
            if os.path.isdir(directory):
                try:
                    files = [f for f in os.listdir(directory) 
                            if os.access(os.path.join(directory, f), os.X_OK)]
                    if files:
                        structure[directory] = files
                except (PermissionError, OSError):
                    continue
        return dict(structure)

    def save_current_state(self):
        """Сохраняет текущее состояние в JSON файл"""
        state = {
            "environment": dict(os.environ),
            "executables": self.executables_structure
        }
        with open(self.state_file_path, "w") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)

    def refresh_info(self):
        """Обновляет информацию о системе"""
        self.executables_structure = self.build_executables_structure()
        self.save_current_state()

    def process_set_environment(self, var_value):
        """Обрабатывает команду SET для переменных окружения"""
        try:
            var, value = var_value.split("=", 1)
            os.environ[var] = value
            self.refresh_info()
            return f"Установлена переменная: {var}={value}"
        except ValueError:
            return "Ошибка: неверный формат. Используйте SET VAR=value"

    def handle_client_connection(self, conn, addr):
        """Обрабатывает соединение с клиентом"""
        print(f"Начало работы с клиентом: {addr}")
        try:
            while True:
                try:
                    header = receive_exactly(conn, 8)
                    cmd, length = struct.unpack("II", header)
                    
                    if cmd != CMD_REQUEST_FROM_CLIENT:
                        self.send_response(conn, "Неизвестная команда")
                        continue

                    data = receive_exactly(conn, length).decode().strip()
                    
                    if data.upper() == "EXIT":
                        print(f"Клиент {addr} запросил отключение")
                        self.send_response(conn, "Соединение будет закрыто")
                        break
                        
                    if data == "REFRESH":
                        self.refresh_info()
                        self.send_response(conn, "Данные обновлены")
                        continue
                        
                    if data == "DOWNLOAD_FILE":
                        with open(self.state_file_path, "rb") as f:
                            file_data = f.read()
                        conn.sendall(struct.pack("II", CMD_SEND_FILE, len(file_data)) + file_data)
                        continue
                        
                    if data.startswith("SET"):
                        response = self.process_set_environment(data[4:])
                        self.send_response(conn, response)
                        continue
                        
                    if data == "SHOW_ENV":
                        env_str = "\n".join(f"{k}: {v}" for k, v in os.environ.items())
                        self.send_response(conn, f"Переменные окружения:\n{env_str}")
                        continue
                        
                    if data == "HELP":
                        help_msg = """Доступные команды:
REFRESH - обновить данные
DOWNLOAD_FILE - получить файл состояния
SET VAR=value - установить переменную
SHOW_ENV - показать переменные окружения
HELP - эта справка
EXIT - отключиться от сервера"""
                        self.send_response(conn, help_msg)
                        continue
                        
                    self.send_response(conn, "Неизвестная команда. Введите HELP для справки")

                except (TimeoutError, ConnectionError) as e:
                    print(f"Ошибка соединения с клиентом {addr}: {e}")
                    break
        finally:
            conn.close()
            print(f"Соединение с клиентом {addr} закрыто")

    def send_response(self, conn, message):
        """Отправляет текстовый ответ клиенту"""
        try:
            msg_bytes = message.encode()
            conn.sendall(struct.pack("II", CMD_RESPONSE_FROM_SERVER, len(msg_bytes)) + msg_bytes)
            return True
        except Exception as e:
            print(f"Ошибка отправки ответа: {e}")
            return False

    def run(self):
        self.running = True
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((self.host, self.port))
            s.listen(5)
            print(f"Сервер запущен на {self.host}:{self.port}")

            try:
                while self.running:
                    try:
                        conn, addr = s.accept()
                        print(f"Подключен клиент: {addr}")
                        self.handle_client_connection(conn, addr)
                    except KeyboardInterrupt:
                        print("\nПолучен сигнал завершения работы...")
                        break
                    except Exception as e:
                        print(f"Ошибка обработки клиента: {e}")
            finally:
                s.close()
                self.running = False
                print("Сервер остановлен")

def receive_exactly(sock, size, timeout=60):
    """Получает точно size байт данных"""
    sock.settimeout(timeout)
    data = b""
    start_time = time.time()
    
    while len(data) < size:
        try:
            chunk = sock.recv(size - len(data))
            if not chunk:
                raise ConnectionError("Соединение прервано")
            data += chunk
        except socket.timeout:
            if time.time() - start_time > timeout:
                raise TimeoutError(f"Превышено время ожидания. Допустимый таймаут {timeout} сек")
    
    return data

if __name__ == "__main__":
    port_number = int(sys.argv[1]) if len(sys.argv) > 1 else 4200
    server_instance = MyServer(port=port_number)
    server_instance.run()