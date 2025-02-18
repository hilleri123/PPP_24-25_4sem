import socket  # Импортируем модуль для работы с сетью
import sys  # Импортируем модуль для работы с системными параметрами и функциями
import logging  # Импортируем модуль для логирования
import signal  # Импортируем модуль для обработки сигналов

SERVER_HOST = "127.0.0.1"  # IP-адрес сервера
SERVER_PORT = 5000  # Порт сервера
LOGGING = False

logging.basicConfig(level=logging.INFO,  # Настройка уровня логирования
                    format="%(asctime)s [%(levelname)s] %(message)s")  # Формат логов

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
    header = f"{len(msg):010d}".encode("utf-8")  # Формируем заголовок с длиной сообщения
    try:
        sock.sendall(header + msg)  # Отправляем сообщение
    except Exception as e:  # Обрабатываем ошибки
        if LOGGING:
            logging.error(f"Ошибка отправки сообщения: {e}")  # Логируем ошибку

def signal_handler(sig, frame):  # Обработчик сигналов
    global shutdown  # Используем глобальный флаг завершения работы
    if LOGGING:
        logging.info("Клиент получает сигнал завершения.")  # Логируем завершение
    shutdown = True  # Устанавливаем флаг завершения работы

def main():  # Основная функция клиента
    signal.signal(signal.SIGINT, signal_handler)  # Регистрируем обработчик для сигнала SIGINT (Ctrl+C)
    signal.signal(signal.SIGTERM, signal_handler)  # Регистрируем обработчик для сигнала SIGTERM

    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Создаём сокет
        client_socket.connect((SERVER_HOST, SERVER_PORT))  # Подключаемся к серверу
        if LOGGING:
            logging.info("Подключение к серверу установлено.")  # Логируем подключение
    except Exception as e:  # Обрабатываем ошибки подключения
        if LOGGING:
            logging.error(f"Ошибка подключения к серверу: {e}")  # Логируем ошибку
        sys.exit(1)  # Завершаем программу с кодом ошибки 1

    try:
        while not shutdown:  # Цикл до завершения работы
            command = input("> ").strip()  # Вводим команду
            try:
                client_socket.send(command.encode("utf-8"))  # Отправляем команду серверу
            except Exception as e:  # Обрабатываем ошибки отправки
                if LOGGING:
                    logging.error(f"Ошибка отправки команды: {e}")  # Логируем ошибку
                break
            response = recv_msg(client_socket)  # Получаем ответ от сервера
            if response is None:  # Если ответа нет
                if LOGGING:
                    logging.warning("Нет ответа от сервера.")  # Логируем предупреждение
                break
            print("Ответ сервера:")  # Выводим ответ сервера
            print(response)  # Выводим содержимое ответа
    except Exception as e:  # Обрабатываем ошибки
        if LOGGING:
            logging.error(f"Ошибка: {e}")  # Логируем ошибку
    finally:
        client_socket.close()  # Закрываем сокет клиента
        if LOGGING:
            logging.info("Клиент завершил работу.")  # Логируем завершение работы

if __name__ == '__main__':  # Проверяем, что скрипт запущен как главная программа
    main()  # Вызываем основную функцию