# клиент
import socket
import struct
import logging
import os
import json
#логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='client.log',
    filemode='w'
)

class AudioClient:
    def __init__(self, host='localhost', port=5000):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))
        logging.info(f"Connected to {self.host}:{self.port}")

    def get_list(self):
        self.socket.sendall(b'list')
        size_data = self.socket.recv(4)
        print(f"DEBUG: Received size bytes: {size_data}")  # Должно быть 4 байта
        if len(size_data) != 4:
            print("ERROR: Invalid size data")
            return {}
        size = struct.unpack('!I', size_data)[0]
        print(f"DEBUG: Expected data size: {size} bytes")
        data = self.socket.recv(size)
        print(f"DEBUG: Received data: {data}")
        return json.loads(data.decode())

    def get_segment(self, filename, start, end, save_path=None):
        def get_segment(self, filename, start, end, save_path=None):
            # Путь
            base_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Создаем папку 
            save_dir = os.path.join(base_dir, "segments")
            os.makedirs(save_dir, exist_ok=True)
            
            # Полный путь к файлу
            save_path = os.path.join(save_dir, f"segment_{filename}")
            print(f"Файл будет сохранён в: {save_path}")
        

        try:
            #таймаут
            self.socket.settimeout(10.0)
            
            command = f'get {filename} {start} {end}'
            self.socket.sendall(command.encode())

            #  размер файла
            size_data = self._recv_all(4)
            size = struct.unpack('!I', size_data)[0]
            
            if size == 0:
                print("Ошибка: файл не найден на сервере")
                return False

            # Получение данных
            with open(save_path, 'wb') as f:
                remaining = size
                while remaining > 0:
                    chunk = self.socket.recv(min(4096, remaining))
                    if not chunk:
                        raise ConnectionError("Сервер прервал передачу")
                    f.write(chunk)
                    remaining -= len(chunk)

            print(f"Файл успешно сохранён: {save_path}")
            return True

        except Exception as e:
            print(f"Ошибка при загрузке: {str(e)}")
            if os.path.exists(save_path):
                os.remove(save_path)
            return False

    def _recv_all(self, size):
        """Гарантированно получает указанное количество байт"""
        data = b''
        while len(data) < size:
            packet = self.socket.recv(size - len(data))
            if not packet:
                raise ConnectionError("Соединение закрыто сервером")
            data += packet
        return data

    def run(self):
        while True:
            print("Commands: list, get <filename> <start> <end>, exit")
            cmd = input("> ").strip()
            if cmd == 'exit':
                break
            elif cmd == 'list':
                files = self.get_list()
                for name, info in files.items():
                    print(f"{name} ({info['format']}), {info['duration']}s")
            elif cmd.startswith('get'):
                parts = cmd.split()
                if len(parts) != 4:
                    print("Invalid command")
                    continue
                filename = parts[1]
                start = parts[2]
                end = parts[3]
                save_path = f"segment_{filename}"
                self.get_segment(filename, start, end, save_path)
                print(f"Segment saved as {save_path}")
            else:
                print("Unknown command")


if __name__ == '__main__':
    client = AudioClient()
    client.run()

