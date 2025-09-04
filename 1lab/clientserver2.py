import os
import io
import json
import socket
import threading
import logging
import tempfile
from pydub import AudioSegment
import struct

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='server.log',
    filemode='w'
)

class AudioServer:
    def __init__(self, host='localhost', port=5000, audio_dir=None):
        self.host = host
        self.port = port
        self.audio_dir = os.path.join(os.path.dirname(__file__), 'audio_files')
        print(f"Путь к аудиофайлам: {self.audio_dir}")
        self.metadata_file = 'audio_metadata.json'
        self.metadata = {}
        self.setup()

    def setup(self):
        # Создание директории, если её нет
        if not os.path.exists(self.audio_dir):
            os.makedirs(self.audio_dir)
        
        # Генерация метаданных
        self.generate_metadata()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.host, self.port))
        self.socket.listen(5)
        logging.info(f"Server started on {self.host}:{self.port}")

    def generate_metadata(self):
        self.metadata = {}
        for filename in os.listdir(self.audio_dir):
            if filename.lower().endswith(('.mp3', '.wav', '.ogg')):
                filepath = os.path.join(self.audio_dir, filename)
                audio = AudioSegment.from_file(filepath)
                self.metadata[filename] = {
                    'duration': len(audio) / 1000,  # в секундах
                    'format': os.path.splitext(filename)[1][1:]
                }
        
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f)
        logging.info("Metadata generated")
        print("Найдены файлы:", os.listdir(self.audio_dir))
        
        
        

        print(f"Путь к аудио-папке: {os.path.abspath(self.audio_dir)}")
        print(f"Файлы в папке: {os.listdir(self.audio_dir)}")
        
        for filename in os.listdir(self.audio_dir):
            full_path = os.path.join(self.audio_dir, filename)
            print(f"Проверяем файл: {filename}")
            print(f"Существует: {os.path.exists(full_path)}")
            print(f"Это файл: {os.path.isfile(full_path)}")
            if filename.lower().endswith(('.mp3', '.wav', '.ogg')):
                print(f"Обрабатываем файл: {filename}")
                try:
                    audio = AudioSegment.from_file(full_path)
                    self.metadata[filename] = {
                        'duration': len(audio) / 1000,
                        'format': os.path.splitext(filename)[1][1:]
                    }
                except Exception as e:
                    print(f"Ошибка обработки {filename}: {e}")

    def handle_client(self, client_socket):
        try:
            while True:
                command = client_socket.recv(1024).decode().strip()
                if not command:
                    break

                logging.info(f"Received command: {command}")

                if command == 'list':
                    with open(self.metadata_file, 'rb') as f:
                        data = f.read()
                        client_socket.sendall(struct.pack('!I', len(data)))
                        client_socket.sendall(data)

                elif command.startswith('get'):
                    try:
                        _, filename, start, end = command.split()
                        if filename not in self.metadata:
                            client_socket.sendall(struct.pack('!I', 0))
                            continue

                        filepath = os.path.join(self.audio_dir, filename)
                        audio = AudioSegment.from_file(filepath)
                        
                        # Конвертация
                        start_ms = int(float(start) * 1000)
                        end_ms = int(float(end) * 1000)
                        segment = audio[start_ms:end_ms]

                        # Отправка
                        buffer = io.BytesIO()
                        segment.export(buffer, format="mp3")
                        data = buffer.getvalue()
                        
                        client_socket.sendall(struct.pack('!I', len(data)))
                        client_socket.sendall(data)
                        logging.info(f"Sent {len(data)} bytes")

                    except Exception as e:
                        logging.error(f"Error processing 'get': {e}")
                        client_socket.sendall(struct.pack('!I', 0))

                else:
                    client_socket.send(b'Unknown command')

        except Exception as e:
            logging.error(f"Connection error: {e}")
        finally:
            client_socket.close()

    def run(self):
        while True:
            client_sock, addr = self.socket.accept()
            logging.info(f"Accepted connection from {addr}")
            client_handler = threading.Thread(
                target=self.handle_client,
                args=(client_sock,)
            )
            client_handler.start()



if __name__ == '__main__':
    server = AudioServer()
    server.run()

