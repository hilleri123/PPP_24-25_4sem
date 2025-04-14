import socket
import struct
import json
import sys

CMD_REQUEST_FROM_CLIENT = 1
CMD_RESPONSE_FROM_SERVER = 2
CMD_SEND_FILE = 3

class MyClient:
    def __init__(self, host='localhost', port=4200):
        self.host = host
        self.port = port
        self.socket_instance = None
        self.connected = False

    def connect_to_server(self):
        try:
            self.socket_instance = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket_instance.connect((self.host, self.port))
            print(f"Подключено к {self.host}:{self.port}")
            self.connected = True
            return True
        except ConnectionRefusedError:
            print("Ошибка: сервер недоступен")
            return False
        except Exception as e:
            print(f"Ошибка подключения: {e}")
            return False

    def send_command_to_server(self, command):
        try:
            cmd_bytes = command.encode()
            header = struct.pack("II", CMD_REQUEST_FROM_CLIENT, len(cmd_bytes))
            self.socket_instance.sendall(header + cmd_bytes)
            return True
        except Exception as e:
            print(f"Ошибка отправки команды: {e}")
            self.connected = False
            return False

    def receive_server_response(self):
        try:
            header = self.socket_instance.recv(8)
            if not header:
                raise ConnectionError("Соединение закрыто сервером")
                
            cmd_type, length_of_data = struct.unpack("II", header)
            
            if cmd_type == CMD_RESPONSE_FROM_SERVER:
                data_received = self.socket_instance.recv(length_of_data)
                return data_received.decode()
                
            elif cmd_type == CMD_SEND_FILE:
                data_received = self.socket_instance.recv(length_of_data)
                filename_to_save_as = f"server_state_{len(data_received)}_bytes.json"
                with open(filename_to_save_as, 'wb') as f:
                    f.write(data_received)
                return f"Файл сохранен как {filename_to_save_as}"
                
            else:
                return f"Неизвестный тип ответа: {cmd_type}"
        except Exception as e:
            print(f"Ошибка получения ответа: {e}")
            self.connected = False
            return None

    def display_state_file_content(self, filename):
        try:
            with open(filename) as f:
                data_content = json.load(f)
                
            print("\n=== Переменные окружения ===")
            for k, v in data_content.get('environment', {}).items():
                print(f"{k}: {v}")
                
            print("\n=== Исполняемые файлы ===")
            for path_key, files_list in data_content.get('executables', {}).items():
                print(f"\n{path_key}:")
                for file_name in files_list:
                    print(f"  - {file_name}")
                    
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Ошибка чтения файла: {e}")

    def interactive_command_loop(self):
        print("\nДоступные команды:")
        print("REFRESH - обновить данные на сервере")
        print("DOWNLOAD_FILE - получить файл состояния")
        print("SET VAR=value - установить переменную окружения")
        print("SHOW_ENV - показать переменные окружения")
        print("HELP - показать справку")
        print("EXIT - завершить работу\n")
        
        while self.connected:
            try:
                command_input = input("Введите команду: ").strip()
                
                if command_input.upper() == "EXIT":
                    print("Завершение работы клиента...")
                    break
                    
                if not command_input:
                    continue
                    
                if not self.send_command_to_server(command_input):
                    break
                    
                response_from_server = self.receive_server_response()
                
                if response_from_server is None:
                    break
                    
                if response_from_server.endswith(".json"):
                    self.display_state_file_content(response_from_server.split()[-1])
                else:
                    print("\nОтвет сервера:")
                    print(response_from_server)
                    
            except KeyboardInterrupt:
                print("\nЗавершение работы по запросу пользователя...")
                break
            except Exception as e:
                print(f"\nОшибка: {e}")
                break

    def close_connection(self):
        if self.socket_instance:
            try:
                self.socket_instance.close()
            except:
                pass
            finally:
                self.socket_instance = None
        self.connected = False

if __name__ == "__main__":
    server_host_name = sys.argv[1] if len(sys.argv) > 1 else 'localhost'
    server_port_number = int(sys.argv[2]) if len(sys.argv) > 2 else 4200
    
    client_instance = MyClient(server_host_name, server_port_number)
    if client_instance.connect_to_server():
        try:
            client_instance.interactive_command_loop()
        finally:
            client_instance.close_connection()