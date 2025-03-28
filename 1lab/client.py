import socket
import logging
import sys

class Client:
    """Класс клиента"""
    
    def __init__(self, host="localhost", port=12345):
        """
        Инициализация клиента
        :param host: хост сервера
        :param port: порт сервера
        """
        self.host = host
        self.port = port
        self.connection = None  # Будет хранить активное соединение
        self.logger = self._setup_logger()
        self.connect()  # Устанавливаем соединение при инициализации

    def _setup_logger(self):
        """Настройка системы логирования"""
        logger = logging.getLogger('Client')
        logger.setLevel(logging.INFO)
        
        file_handler = logging.FileHandler('client.log')
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(file_handler)
        logger.propagate = False
        
        return logger

    def connect(self):
        """Установка соединения с сервером"""
        try:
            if self.connection:
                self.connection.close()
                
            self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.connection.settimeout(10)  # Таймаут 10 секунд
            self.connection.connect((self.host, self.port))
            self.logger.info("Successfully connected to server")
            return True
        except Exception as e:
            self.logger.error(f"Connection error: {e}")
            return False

    def send_command(self, command):
        """
        Отправка команды серверу
        :param command: текстовая команда
        :return: ответ сервера
        """
        try:
            # Проверяем соединение и переподключаемся при необходимости
            if not self.connection:
                if not self.connect():
                    return "ERROR: Connection failed"

            # Отправляем команду
            self.connection.sendall(command.encode('utf-8'))
            self.logger.info(f"Sent command: {command}")

            # Особый случай - команда SHUTDOWN
            if command.upper() == "SHUTDOWN":
                response = self.connection.recv(1024).decode('utf-8')
                self.connection.close()
                self.connection = None
                return response

            # Получаем ответ
            response = []
            while True:
                part = self.connection.recv(4096).decode('utf-8')
                if not part:
                    break
                response.append(part)
                if len(part) < 4096:
                    break

            full_response = ''.join(response)
            self.logger.info(f"Received response: {full_response}")
            return full_response

        except socket.timeout:
            self.logger.warning("Connection timeout, reconnecting...")
            if self.connect():
                return self.send_command(command)  # Повторяем запрос
            return "ERROR: Connection timeout"

        except ConnectionResetError:
            self.logger.warning("Connection reset, reconnecting...")
            if self.connect():
                return self.send_command(command)
            return "ERROR: Connection reset"

        except Exception as e:
            self.logger.error(f"Error sending command: {e}")
            return f"ERROR: {str(e)}"

    def interactive_mode(self):
        """Интерактивный режим работы"""
        print("Available commands:")
        print("  ADD <program_path> - Add program")
        print("  REMOVE <program_path> - Remove program")
        print("  LIST - List programs")
        print("  GET_OUTPUT <program_name> - Get outputs")
        print("  SET_INTERVAL <seconds> - Set interval")
        print("  SHUTDOWN - Stop server")
        print("  EXIT - Exit client")

        while True:
            try:
                cmd = input("> ").strip()
                if not cmd:
                    continue

                if cmd.upper() == "EXIT":
                    if self.connection:
                        self.connection.close()
                    self.logger.info("Client shutdown")
                    break

                response = self.send_command(cmd)
                print(response)

                if cmd.upper() == "SHUTDOWN":
                    self.connection = None  # Соединение закрыто сервером

            except KeyboardInterrupt:
                print("\nUse 'EXIT' to quit")
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    logging.basicConfig(handlers=[logging.NullHandler()])
    client = Client()
    client.interactive_mode()
