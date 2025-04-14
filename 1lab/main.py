
def main():
    
import socket
import struct
import json
import os
import time
import subprocess
import logging
import threading
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    filename='server_log.txt',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class ProgramServer:
    def __init__(self, host='127.0.0.1', port=12345, data_file='programs_data.json'):
        self.host = host
        self.port = port
        self.data_file = data_file
        self.programs = {}
        self.running = True
        
        # Загрузка данных из файла при запуске
        self.load_data()
        
        # Создание директорий для программ
        self.create_program_directories()
        
        # Запуск сервера
        self.start_server()

    def load_data(self):
        """Загрузка данных о программах из JSON/XML файла"""
        try:
            if os.path.exists(self.data_file):
                file_ext = self.data_file.split('.')[-1].lower()
                if file_ext == 'json':
                    with open(self.data_file, 'r') as f:
                        self.programs = json.load(f)
                elif file_ext in ['xml', 'xml.']:
                    tree = ET.parse(self.data_file)
                    root = tree.getroot()
                    self.programs = {}
                    for program in root.findall('program'):
                        name = program.get('name')
                        self.programs[name] = {
                            'path': program.find('path').text,
                            'runs': int(program.find('runs').text),
                            'last_run': program.find('last_run').text,
                            'output_files': [file.text for file in program.findall('output_file')]
                        }
                logging.info(f"Загружены данные о программах: {len(self.programs)}")
        except Exception as e:
            logging.error(f"Ошибка при загрузке данных: {e}")
            self.programs = {}


        def run_program_thread(self, program_name):
            """Поток для периодического запуска программы"""
            while self.running:
                try:
                    # Получаем информацию о программе
                    info = self.programs[program_name]
                    program_path = info['path']
                    
                    # Формируем имя файла для вывода
                    dir_path = os.path.join(program_name)
                    output_filename = os.path.join(
                        dir_path, 
                        f"{program_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                    )
                    
                    # Запускаем программу и записываем вывод в файл
                    with open(output_filename, 'w') as output_file:
                        process = subprocess.Popen(
                            [program_path], 
                            stdout=output_file, 
                            stderr=subprocess.STDOUT
                        )
                        process.wait()
                    
                    # Обновляем информацию о программе
                    self.programs[program_name]['runs'] += 1
                    self.programs[program_name]['last_run'] = datetime.now().isoformat()
                    self.programs[program_name]['output_files'].append(output_filename)
                    
                    logging.info(f"Выполнена программа {program_name}, вывод сохранен в {output_filename}")
                
                except Exception as e:
                    logging.error(f"Ошибка при выполнении программы {program_name}: {e}")
                
                # Ждем указанный интервал перед следующим запуском
                time.sleep(10)
                
        def handle_client(self, client_socket, address):
        """Обработка подключения клиента"""
        logging.info(f"Установлено соединение с клиентом {address}")
        
        try:
            while True:
                # Получаем длину команды
                data = client_socket.recv(4)
                if not data:
                    break
                
                command_length = struct.unpack('!I', data)[0]
                
                # Получаем команду
                command_data = client_socket.recv(command_length).decode('utf-8')
                logging.info(f"Получена команда от клиента {address}: {command_data}")
                
                # Разбираем команду
                parts = command_data.split(' ', 1)
                command = parts[0].upper()
                
                # Обработка команды ADD
                if command == "ADD":
                   
                # Обработка команды GET
                elif command == "GET":
                    if len(parts) < 2:
                        response = "Ошибка: не указано имя программы"
                    else:
                        program_name = parts[1]
                        output = self.get_combined_output(program_name)
                        if output:
                            
                        else:
                            response = f"Программа {program_name} не найдена"
                
    
                response_bytes = response.encode('utf-8')
                client_socket.send(struct.pack('!I', len(response_bytes)))
                client_socket.send(response_bytes)
        
        except Exception as e:
            logging.error(f"Ошибка при обработке запроса от клиента {address}: {e}")
        
        finally:
            client_socket.close()
            logging.info(f"Соединение с клиентом {address} закрыто")


    pass

if __name__ == "__main__":
    main()

