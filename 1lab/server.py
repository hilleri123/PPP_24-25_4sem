import os
import json
import socket
import logging
import threading
import platform
import subprocess
from datetime import datetime
import time

class ProgramManager:
    """Класс для управления выполнением программ и сохранения результатов"""
    
    def __init__(self, output_dir="program_outputs"):
        """
        Инициализация менеджера программ
        :param output_dir: директория для сохранения результатов
        """
        self.output_dir = output_dir
        # Создаем директорию для результатов, если она не существует
        os.makedirs(self.output_dir, exist_ok=True)

    def create_program_dir(self, program_name):
        """
        Создает директорию для хранения результатов программы
        :param program_name: имя программы
        :return: путь к созданной директории
        """
        program_dir = os.path.join(self.output_dir, program_name)
        os.makedirs(program_dir, exist_ok=True)
        return program_dir

    def run_program(self, program_path):
        """
        Выполняет программу и сохраняет результаты
        :param program_path: путь к исполняемому файлу
        :return: путь к файлу с результатами или None в случае ошибки
        """
        try:
            # Получаем имя программы из пути
            program_name = os.path.basename(program_path)
            # Создаем директорию для результатов
            program_dir = self.create_program_dir(program_name)
            # Генерируем имя файла с временной меткой
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(program_dir, f"output_{timestamp}.txt")

            # Формируем команду в зависимости от ОС
            if platform.system() == "Windows":
                command = program_path
            else:
                # Для Unix-систем проверяем права на выполнение
                if not os.access(program_path, os.X_OK):
                    os.chmod(program_path, 0o755)  # Устанавливаем права на выполнение
                command = f"./{program_path}" if not os.path.isabs(program_path) else program_path

            # Выполняем программу и записываем вывод
            with open(output_file, 'wb') as f:
                process = subprocess.Popen(
                    command,
                    shell=True,
                    stdout=f,
                    stderr=subprocess.STDOUT
                )
                process.wait()  # Ожидаем завершения

            logging.info(f"Executed program: {program_path}, output saved to {output_file}")
            return output_file
        except Exception as e:
            logging.error(f"Error executing {program_path}: {e}")
            return None


class Server:
    """Основной класс сервера для управления программами"""
    
    def __init__(self):
        """Инициализация сервера"""
        self.running = True  # Флаг работы сервера
        self.config_file = "server_config.json"  # Файл конфигурации
        self._setup_logging()  # Настройка логгера
        self.config = {
            "programs": [],  # Список программ для выполнения
            "interval": 10,  # Интервал выполнения (сек)
            "host": "localhost",  # Хост для подключения
            "port": 12345  # Порт для подключения
        }
        self.program_manager = ProgramManager()  # Менеджер программ
        self.server_socket = None  # Сокет сервера
        self.processing_thread = None  # Поток выполнения программ
        self.client_threads = []  # Список клиентских потоков
        self.load_config()  # Загрузка конфигурации

    def _setup_logging(self):
        """Настройка системы логирования для сервера"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('server.log')  # Логи только в файл
            ]
        )

    def load_config(self):
        """Загрузка конфигурации из файла"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    self.config.update(json.load(f))
                logging.info("Configuration loaded successfully")
        except Exception as e:
            logging.error(f"Config load error: {e}")
            # Создаем новый конфиг при ошибке загрузки
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            logging.info("Created new default configuration")

    def save_config(self):
        """Сохранение текущей конфигурации в файл"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            logging.info("Configuration saved successfully")
        except Exception as e:
            logging.error(f"Config save error: {e}")

    def start_processing(self):
        """Основной цикл выполнения программ"""
        logging.info("Starting program processing loop")
        while self.running:
            for program in self.config["programs"]:
                if not self.running:  # Проверка флага остановки
                    break
                
                # Выполняем программу
                output_file = self.program_manager.run_program(program)
                if output_file:
                    logging.info(f"Program {program} executed, output in {output_file}")
                
                # Ожидаем указанный интервал
                time.sleep(self.config["interval"])

    def handle_client(self, conn, addr):
        """
        Обработчик клиентского подключения
        :param conn: объект соединения
        :param addr: адрес клиента
        """
        logging.info(f"Client connected: {addr[0]}:{addr[1]}")
        try:
            while self.running:
                try:
                    # Получаем данные от клиента
                    data = conn.recv(1024).decode('utf-8').strip()
                    if not data:
                        break  # Пустое сообщение - разрыв соединения

                    # Обрабатываем команду
                    response = self.process_command(data)
                    # Отправляем ответ
                    conn.send(response.encode('utf-8'))
                    logging.info(f"Processed command: {data}, response: {response}")

                    if data.upper() == "SHUTDOWN":
                        break  # Завершаем при команде SHUTDOWN
                        
                except (socket.timeout, ConnectionResetError):
                    if not self.running:
                        break
        except Exception as e:
            logging.error(f"Client error: {e}")
        finally:
            # Завершаем соединение
            conn.close()
            logging.info(f"Client disconnected: {addr[0]}:{addr[1]}")

    def process_command(self, command):
        """
        Обработка команд от клиента
        :param command: текстовая команда
        :return: ответ сервера
        """
        # Разбиваем команду на части
        parts = command.split()
        if not parts:
            logging.warning("Received empty command")
            return "ERROR: Empty command"

        cmd = parts[0].upper()  # Основная команда
        args = parts[1:]  # Аргументы команды

        try:
            if cmd == "ADD" and args:
                return self._add_program(args[0])
            elif cmd == "REMOVE" and args:
                return self._remove_program(args[0])
            elif cmd == "LIST":
                return self._list_programs()
            elif cmd == "GET_OUTPUT" and args:
                return self._get_output(args[0])
            elif cmd == "SET_INTERVAL" and args:
                return self._set_interval(args[0])
            elif cmd == "SHUTDOWN":
                self.stop()
                return "OK: Server shutting down"
            else:
                logging.warning(f"Received invalid command: {command}")
                return "ERROR: Invalid command"
        except Exception as e:
            logging.error(f"Error processing command {command}: {e}")
            return f"ERROR: {str(e)}"

    def _add_program(self, program_path):
        """
        Добавление программы в список выполнения
        :param program_path: путь к программе
        :return: статус операции
        """
        if not os.path.exists(program_path):
            return "ERROR: Program not found"

        if program_path in self.config["programs"]:
            return "WARNING: Program already added"

        self.config["programs"].append(program_path)
        self.save_config()
        return "OK: Program added"

    def _remove_program(self, program_path):
        """
        Удаление программы из списка выполнения
        :param program_path: путь к программе
        :return: статус операции
        """
        if program_path in self.config["programs"]:
            self.config["programs"].remove(program_path)
            self.save_config()
            return "OK: Program removed"
        return "ERROR: Program not found"

    def _list_programs(self):
        """Получение списка всех программ"""
        return "\n".join(self.config["programs"]) or "No programs"

    def _get_output(self, program_name):
        """
        Получение результатов выполнения программы
        :param program_name: имя программы
        :return: объединенные результаты или сообщение об ошибке
        """
        program_dir = os.path.join(self.program_manager.output_dir, program_name)
        if not os.path.exists(program_dir):
            return "ERROR: No output available"

        # Получаем список файлов с результатами
        output_files = sorted(
            f for f in os.listdir(program_dir) 
            if f.startswith("output_") and f.endswith(".txt")
        )

        if not output_files:
            return "ERROR: No output files"

        # Читаем и объединяем результаты
        results = []
        for fname in output_files:
            with open(os.path.join(program_dir, fname), 'r', encoding='utf-8') as f:
                results.append(f"=== {fname} ===\n{f.read()}")

        return "\n\n".join(results)

    def _set_interval(self, interval_str):
        """
        Установка интервала выполнения программ
        :param interval_str: интервал в секундах (строка)
        :return: статус операции
        """
        try:
            interval = int(interval_str)
            if interval <= 0:
                raise ValueError("Interval must be positive")
            
            self.config["interval"] = interval
            self.save_config()
            return f"OK: Interval set to {interval} seconds"
        except ValueError as e:
            return f"ERROR: {str(e)}"

    def start(self):
        """Запуск сервера"""
        logging.info("Starting server...")
        self.running = True
        
        # Создаем сокет сервера
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.settimeout(1)  # Таймаут для проверки флага running
        self.server_socket.bind((self.config["host"], self.config["port"]))
        self.server_socket.listen(5)
        logging.info(f"Server started on {self.config['host']}:{self.config['port']}")

        # Запускаем поток выполнения программ
        self.processing_thread = threading.Thread(target=self.start_processing)
        self.processing_thread.daemon = True
        self.processing_thread.start()

        try:
            while self.running:
                try:
                    # Принимаем новое подключение
                    conn, addr = self.server_socket.accept()
                    logging.info(f"New client connected: {addr[0]}:{addr[1]}")
                    
                    # Создаем поток для обработки клиента
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(conn, addr)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    self.client_threads.append(client_thread)
                    
                except socket.timeout:
                    continue  # Игнорируем таймаут, проверяем флаг running
                    
        except Exception as e:
            if self.running:  # Логируем только неожиданные ошибки
                logging.error(f"Server error: {e}")
        finally:
            # Завершаем работу сервера
            self.server_socket.close()
            
            # Ожидаем завершения клиентских потоков
            for t in self.client_threads:
                t.join(timeout=1)
            
            # Ожидаем завершения потока выполнения программ
            self.processing_thread.join(timeout=1)
            logging.info("Server stopped")

    def stop(self):
        """Корректная остановка сервера"""
        logging.info("Stopping server...")
        self.running = False
        self.save_config()
        
        # Создаем временное подключение для выхода из accept
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.config["host"], self.config["port"]))
                s.sendall(b"SHUTDOWN")
        except:
            pass


if __name__ == "__main__":
    # Создаем и запускаем сервер
    server = Server()
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()
    except Exception as e:
        # Записываем критические ошибки
        logging.error(f"Critical server error: {str(e)}")
        raise
