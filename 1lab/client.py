import socket  # Импортируем модуль для работы с сетью
import sys  # Импортируем модуль для работы с системными параметрами и функциями
import logging  # Импортируем модуль для логирования
import signal  # Импортируем модуль для обработки сигналов
import readline
# Список доступных команд и их возможных аргументов для автодополнения
COMMANDS = [
    "ADD",
    "GET",
    "STOP",
    "RESUME",
    "CHANGE",
    "SHOW",
    "VERBOSE",
    "EXIT",
    "HELP"]
ARGS = {
    "ADD": ["<program_name>"],
    "GET": ["<program_name>"],
    "STOP": ["<program_name>"],
    "RESUME": ["<program_name>"],
    "CHANGE": ["<program_name>", "<new_interval>"],
    "VERBOSE": ["TRUE", "FALSE", "<program_name>"],
}

# Функция автодополнения для readline


def completer(text, state):
    buffer = readline.get_line_buffer()
    tokens = buffer.split()
    # Если пользователь ещё вводит название команды (первый токен)
    if len(tokens) == 0 or (len(tokens) == 1 and not buffer.endswith(" ")):
        matches = [cmd for cmd in COMMANDS if cmd.startswith(text.upper())]
    else:
        # Если уже введена команда, предлагаем подсказки для аргументов
        cmd = tokens[0].upper()
        if cmd in ARGS:
            matches = [arg for arg in ARGS[cmd] if arg.startswith(text)]
        else:
            matches = []
    try:
        return matches[state]
    except IndexError:
        return None


# Настройка автодополнения при нажатии Tab
readline.set_completer(completer)
readline.parse_and_bind("tab: complete")

SERVER_HOST = "127.0.0.1"  # IP-адрес сервера
SERVER_PORT = 5000  # Порт сервера
LOGGING = True

logging.basicConfig(level=logging.INFO,  # Настройка уровня логирования
                    # Формат логов
                    format="%(asctime)s [%(levelname)s] %(message)s")

shutdown = False  # Флаг завершения работы клиента


def recvall(sock, n):  # Функция получения всех данных из сокета
    data = b""  # Инициализируем пустые данные
    while len(data) < n:  # Читаем данные до достижения нужной длины
        packet = sock.recv(n - len(data))  # Получаем пакет данных
        if not packet:  # Если данных нет, выходим
            return None
        data += packet  # Добавляем данные
    return data  # Возвращаем полученные данные


def recv_msg(sock):  # Функция получения сообщения через сокет
    header = recvall(sock, 10)  # Получаем заголовок с длиной сообщения
    if not header:  # Если заголовка нет, выходим
        return None
    try:
        msg_len = int(header.decode("utf-8"))  # Декодируем длину сообщения
    except ValueError:  # Обрабатываем ошибки декодирования
        return None
    data = recvall(sock, msg_len)  # Получаем само сообщение
    if data is None:  # Если данных нет, выходим
        return None
    return data.decode("utf-8")  # Возвращаем декодированное сообщение


def send_msg(sock, message):  # Функция отправки сообщения через сокет
    msg = message.encode("utf-8")  # Кодируем сообщение в байты
    # Формируем заголовок с длиной сообщения
    header = f"{len(msg):010d}".encode("utf-8")
    try:
        sock.sendall(header + msg)  # Отправляем сообщение
    except Exception as e:  # Обрабатываем ошибки
        if LOGGING:
            logging.error(f"Ошибка отправки сообщения: {e}")  # Логируем ошибку


def signal_handler(sig, frame):  # Обработчик сигналов
    global shutdown  # Используем глобальный флаг завершения работы
    if LOGGING:
        # Логируем завершение
        logging.info("Клиент получает сигнал завершения.")
    shutdown = True  # Устанавливаем флаг завершения работы


def main():  # Основная функция клиента
    # Регистрируем обработчик для сигнала SIGINT (Ctrl+C)
    signal.signal(signal.SIGINT, signal_handler)
    # Регистрируем обработчик для сигнала SIGTERM
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        client_socket = socket.socket(
            socket.AF_INET, socket.SOCK_STREAM)  # Создаём сокет
        client_socket.connect((SERVER_HOST, SERVER_PORT)
                              )  # Подключаемся к серверу
        if LOGGING:
            # Логируем подключение
            logging.info("Подключение к серверу установлено.")
    except Exception as e:  # Обрабатываем ошибки подключения
        if LOGGING:
            # Логируем ошибку
            logging.error(f"Ошибка подключения к серверу: {e}")
        sys.exit(1)  # Завершаем программу с кодом ошибки 1

    try:
        while not shutdown:  # Цикл до завершения работы
            command = input("> ").strip()  # Вводим команду
            try:
                # Отправляем команду серверу
                client_socket.send(command.encode("utf-8"))
            except Exception as e:  # Обрабатываем ошибки отправки
                if LOGGING:
                    logging.error(
                        f"Ошибка отправки команды: {e}")  # Логируем ошибку
                break
            response = recv_msg(client_socket)  # Получаем ответ от сервера
            if response is None:  # Если ответа нет
                if LOGGING:
                    # Логируем предупреждение
                    logging.warning("Нет ответа от сервера.")
                break
            print("Ответ сервера:")  # Выводим ответ сервера
            print(response)  # Выводим содержимое ответа
    except Exception as e:  # Обрабатываем ошибки
        if LOGGING:
            logging.error(f"Ошибка: {e}")  # Логируем ошибку
    finally:
        client_socket.close()  # Закрываем сокет клиента
        if LOGGING:
            # Логируем завершение работы
            logging.info("Клиент завершил работу.")


if __name__ == '__main__':  # Проверяем, что скрипт запущен как главная программа
    main()  # Вызываем основную функцию
