import os
import socket
import logging
from datetime import datetime

# Настройка логирования
logging.basicConfig(filename='client.log', level=logging.INFO,
                    format='%(asctime)s - %(message)s')


def create_directory():
    """Создает директорию для сохранения файлов."""
    now = datetime.now()
    dir_name = now.strftime("./%d-%m-%Y")
    os.makedirs(dir_name, exist_ok=True)
    print(f"Создана директория для сохранения: {dir_name}")
    return dir_name


def save_file(data, dir_name, command):
    """Сохраняет полученные данные в файл с именем 
       в формате hh-mm-ss_<command>.json."""
    now = datetime.now()
    # Заменяем двоеточия на дефисы и убираем пробелы в команде
    safe_command = command.replace(" ", "_").replace(":", "-")
    file_name = now.strftime(f"%H-%M-%S_{safe_command}.json")
    file_path = os.path.join(dir_name, file_name)
    try:
        with open(file_path, 'wb') as f:
            f.write(data)
        print(f"Файл успешно сохранен: {file_path}")
        logging.info(f"Файл сохранен в {file_path}")
    except Exception as e:
        print(f"Ошибка при сохранении файла: {e}")
        logging.error(f"Ошибка при сохранении файла: {e}")


def send_command(command):
    """Отправляет команду серверу и получает ответ."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(('127.0.0.1', 65432))
            print(f"Отправка команды серверу: {command}")
            s.sendall(command.encode('utf-8'))

            # Получаем ответ от сервера
            data = s.recv(4096)
            if data:
                print("Данные получены.")
                dir_name = create_directory()
                save_file(data, dir_name, command)
            else:
                print("Ошибка: данные от сервера не получены.")

    except ConnectionResetError:
        print("Сервер разорвал соединение.")
        logging.error("Сервер разорвал соединение.")
    except Exception as e:
        print(f"Ошибка при отправке команды: {e}")
        logging.error(f"Ошибка при отправке команды: {e}")


def main():
    """Основной цикл клиента."""
    print("Клиент запущен. Подключение к серверу...")
    while True:
        print("\nДоступные команды:")
        print("update - обновить информацию о процессах")
        print("signal <pid> <sig> - отправить сигнал процессу")
        print("exit - выйти")
        choice = input("Введите команду: ").strip()

        if choice == "exit":
            print("Завершение работы клиента...")
            break
        elif choice == "update" or choice.startswith("signal"):
            send_command(choice)
        else:
            print("Неверная команда. Попробуйте снова.")


if __name__ == "__main__":
    main()
