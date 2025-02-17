import os  # Импортируем модуль для работы с операционной системой
import sys  # Импортируем модуль для работы с системными параметрами и функциями
import json  # Импортируем модуль для работы с JSON
import time  # Импортируем модуль для работы со временем
import threading  # Импортируем модуль для работы с потоками
import socket  # Импортируем модуль для работы с сетью
import subprocess  # Импортируем модуль для запуска внешних процессов
import logging  # Импортируем модуль для логирования
import shutil  # Импортируем модуль для работы с файлами и директориями

# Константы и конфигурация
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "programs_info.json") # Файл для хранения данных о программах
SERVER_HOST = "127.0.0.1"  # IP-адрес сервера
SERVER_PORT = 5000  # Порт сервера
DEFAULT_INTERVAL = int(os.environ.get("LAUNCH_INTERVAL", "10"))  # Интервал запуска программ (по умолчанию 10 секунд)

logging.basicConfig(level=logging.INFO,  # Настройка уровня логирования
                    format="%(asctime)s [%(levelname)s] %(message)s")  # Формат логов

programs_data = {}  # Словарь для хранения данных о программах
program_controls = {}  # Словарь для управления программами
shutdown_event = threading.Event()  # Событие для завершения работы сервера
threads = []  # Список для хранения потоков
data_lock = threading.Lock()  # Блокировка для синхронизации доступа к данным


def load_data():  # Функция загрузки данных из JSON-файла
    global programs_data  # Глобальная переменная для хранения данных
    if os.path.exists(DATA_FILE):  # Проверяем, существует ли файл
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:  # Открываем файл для чтения
                programs_data = json.load(f)  # Загружаем данные из файла
        except Exception as e:  # Обрабатываем ошибки при загрузке
            logging.error(f"Ошибка загрузки данных из {DATA_FILE}: {e}")  # Логируем ошибку
            programs_data = {}  # Очищаем данные
    else:
        programs_data = {}  # Если файл не существует, инициализируем пустой словарь


def save_data():  # Функция сохранения данных в JSON-файл
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:  # Открываем файл для записи
                json.dump(programs_data, f, indent=4, ensure_ascii=False)  # Сохраняем данные в файл
        except Exception as e:  # Обрабатываем ошибки при сохранении
            logging.error(f"Ошибка сохранения данных в {DATA_FILE}: {e}")  # Логируем ошибку


def sanitize_folder_name(name):  # Функция очистки имени папки
    return "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in name)  # Заменяем недопустимые символы на "_"


def ensure_folder(program_name):  # Функция создания папки для программы
    folder = sanitize_folder_name(program_name)  # Очищаем имя папки
    if not os.path.exists(folder):  # Проверяем, существует ли папка
        os.makedirs(folder)  # Создаём папку
    return folder  # Возвращаем путь к папке


def is_program_executable(program_command):  # Функция проверки доступности программы
    parts = program_command.split()  # Разбиваем команду на части
    cmd = parts[0]  # Берём первую часть (команду)
    if cmd.endswith('.py'):  # Если это Python-скрипт
        abs_path = os.path.abspath(cmd)
        logging.info(f"Проверяем путь к Python-скрипту: {abs_path}")
        return os.path.isfile(cmd) and os.access(cmd, os.R_OK)  # Проверяем, существует ли файл и доступен ли он для чтения
    else:
        logging.info(f"Проверяем команду через shutil.which: {cmd}")
        return shutil.which(cmd) is not None  # Проверяем, доступна ли команда в PATH


def run_program(program_name):  # Функция циклического запуска программы
    logging.info(f"Начинаем циклический запуск программы '{program_name}'")  # Логируем начало работы
    folder = programs_data[program_name]["folder"]  # Получаем путь к папке программы
    while not shutdown_event.is_set() and not program_controls[program_name]["stop_event"].is_set():  # Цикл до завершения работы
        timestamp = time.strftime("%Y%m%d_%H%M%S")  # Формируем метку времени
        output_filename = os.path.join(folder, f"output_{timestamp}.txt")  # Формируем имя файла для вывода
        try:
            if program_name.endswith('.py'):  # Если это Python-скрипт
                cmd = f"{sys.executable} {os.path.abspath(program_name)}"  # Формируем команду для запуска
            else:
                cmd = os.path.abspath(program_name)  # Формируем команду для запуска
            # logging.info(f"Запускаем команду: {cmd}")  # Логируем команду
            result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=30)  # Запускаем программу
            output = result.stdout  # Получаем вывод программы
        except Exception as e:  # Обрабатываем ошибки при запуске
            logging.error(f"Ошибка при запуске программы '{program_name}': {e}")  # Логируем ошибку
            output = f"Ошибка при запуске программы: {e}"  # Формируем сообщение об ошибке
        try:
            with open(output_filename, "w", encoding="utf-8") as f:  # Открываем файл для записи
                f.write(output)  # Записываем вывод программы в файл
        except Exception as e:  # Обрабатываем ошибки при записи
            logging.error(f"Ошибка записи в файл {output_filename}: {e}")  # Логируем ошибку
        programs_data[program_name]["runs"].append({  # Добавляем информацию о запуске
                "timestamp": timestamp,
                "file": output_filename
        })
        save_data()  # Сохраняем данные
        for _ in range(program_controls[program_name]["interval"]):  # Ждём интервал между запусками
            if shutdown_event.is_set() or program_controls[program_name]["stop_event"].is_set():  # Проверяем завершение работы
                break
            time.sleep(1)  # Ждём 1 секунду
    logging.info(f"Циклический запуск программы '{program_name}' завершён.")  # Логируем завершение работы


def send_msg(sock, message):  # Функция отправки сообщения через сокет
    msg = message.encode("utf-8")  # Кодируем сообщение в байты
    header = f"{len(msg):010d}".encode("utf-8")  # Формируем заголовок с длиной сообщения
    try:
        sock.sendall(header + msg)  # Отправляем сообщение
    except Exception as e:  # Обрабатываем ошибки
        logging.error(f"Ошибка отправки сообщения: {e}")  # Логируем ошибку


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


def format_show(json):
    header_row = f"| {'process':^{max([len(key) for key in json.keys()]+[len('process')])}} | {'outputs folder':^{max([len(json[key]["folder"]) for key in json.keys()]+[len('outputs folder')])}} | {'runs':^{max([len(str(len(json[key]["runs"]))) for key in json.keys()]+[len('runs')])}} |\n"

    header_row += f"|{'-' * (len(header_row.split('|')[1]))}|{'-' * (len(header_row.split('|')[2]))}|{'-' * (len(header_row.split('|')[3]))}|\n"
    data_rows = ""
    for key in json.keys():
        data_row = f"|{key:^{len(header_row.split('|')[1])}}|{json[key]["folder"]:^{len(header_row.split('|')[2])}}|{len(json[key]["runs"]):^{len(header_row.split('|')[3])}}|\n"
        data_rows += data_row
     
    table = header_row + data_rows
    return table
        

def handle_client(client_socket):  # Функция обработки клиентских запросов
    try:
        while not shutdown_event.is_set():  # Цикл до завершения работы
            data = client_socket.recv(1024)  # Получаем данные от клиента
            if not data:  # Если данных нет, выходим
                break
            command = data.decode("utf-8").strip()  # Декодируем команду
            logging.info(f"Получена команда от клиента: {command}")  # Логируем команду
            parts = command.split()  # Разбиваем команду на части
            if not parts:  # Если частей нет, продолжаем
                continue
            cmd = parts[0].upper()  # Берём первую часть (команду) и переводим её в верхний регистр
            if cmd == "ADD" and len(parts) >= 2:  # Если команда ADD
                new_program = " ".join(parts[1:])  # Формируем имя программы
                if not is_program_executable(new_program):  # Проверяем доступность программы
                    response = f"Ошибка: программа '{new_program}' не найдена или нет доступа."  # Формируем сообщение об ошибке
                    send_msg(client_socket, response)  # Отправляем сообщение клиенту
                    continue
                if new_program in programs_data:  # Если программа уже существует
                        response = f"Программа '{new_program}' уже существует."  # Формируем сообщение
                else:
                        folder = ensure_folder(new_program)  # Создаём папку для программы
                        programs_data[new_program] = {"folder": folder, "runs": []}  # Добавляем данные о программе
                        program_controls[new_program] = {  # Добавляем управление программой
                            "interval": DEFAULT_INTERVAL,
                            "stop_event": threading.Event()
                        }
                        thread = threading.Thread(target=run_program, args=(new_program,))  # Создаём поток для запуска программы
                        thread.start()  # Запускаем поток
                        program_controls[new_program]["thread"] = thread  # Сохраняем ссылку на поток
                        threads.append(thread)  # Добавляем поток в список
                        response = f"Программа '{new_program}' добавлена."  # Формируем сообщение
                        logging.info(response)  # Логируем добавление программы
                        save_data()  # Сохраняем данные
                send_msg(client_socket, response)  # Отправляем сообщение клиенту
            elif cmd == "GET" and len(parts) >= 2:  # Если команда GET
                prog = " ".join(parts[1:])  # Формируем имя программы
                if prog not in programs_data:  # Если программы нет в списке
                        response = f"Программа '{prog}' не найдена."  # Формируем сообщение об ошибке
                        send_msg(client_socket, response)  # Отправляем сообщение клиенту
                        continue
                runs = programs_data[prog]["runs"][:]  # Получаем список запусков программы
                combined_output = ""  # Инициализируем объединённый вывод
                for run in runs:  # Проходим по всем запускам
                    try:
                        with open(run["file"], "r", encoding="utf-8") as f:  # Открываем файл для чтения
                            combined_output += f"----- {run['timestamp']} -----\n" + f.read() + "\n"  # Добавляем содержимое файла
                    except Exception as e:  # Обрабатываем ошибки чтения
                        combined_output += f"Ошибка чтения файла {run['file']}: {e}\n"  # Формируем сообщение об ошибке
                send_msg(client_socket, combined_output)  # Отправляем объединённый вывод клиенту
            elif cmd == "STOP" and len(parts) >= 2:  # Если команда STOP
                prog = " ".join(parts[1:])  # Формируем имя программы
                if prog not in program_controls:  # Если программы нет в списке
                        response = f"Программа '{prog}' не найдена."  # Формируем сообщение об ошибке
                else:
                        if program_controls[prog]["stop_event"].is_set():  # Если программа уже остановлена
                            response = f"Программа '{prog}' уже остановлена."  # Формируем сообщение
                        else:
                            program_controls[prog]["stop_event"].set()  # Устанавливаем событие остановки
                            response = f"Программа '{prog}' остановлена."  # Формируем сообщение
                            logging.info(response)  # Логируем остановку программы
                send_msg(client_socket, response)  # Отправляем сообщение клиенту
            elif cmd == "RESUME" and len(parts) >= 2:  # Если команда RESUME
                prog = " ".join(parts[1:])  # Формируем имя программы
                
                if not is_program_executable(prog):  # Проверяем доступность программы
                    response = f"Ошибка: программа '{new_program}' не найдена или нет доступа."  # Формируем сообщение об ошибке
                    send_msg(client_socket, response)  # Отправляем сообщение клиенту
                    continue
                
                elif prog not in programs_data:  # Если программы нет в списке
                        response = f"Программа '{prog}' не найдена."  # Формируем сообщение об ошибке
                
                else:
                    if not( prog in program_controls.keys()):
                        program_controls[prog] = {  # Добавляем управление программой
                            "interval": DEFAULT_INTERVAL,
                            "stop_event": threading.Event()
                        }
                        thread = threading.Thread(target=run_program, args=(prog,))  # Создаём поток для запуска программы
                        thread.start()  # Запускаем поток
                        program_controls[prog]["thread"] = thread  # Сохраняем ссылку на поток
                        threads.append(thread)  # Добавляем поток в список
                        response = f"Программа '{prog}' добавлена."  # Формируем сообщение
                        logging.info(response)  # Логируем добавление программы
                        save_data()  # Сохраняем данные
                    else:                        
                        if not program_controls[prog]["stop_event"].is_set():  # Если программа уже запущена
                            response = f"Программа '{prog}' уже запущена."  # Формируем сообщение
                        else:
                            program_controls[prog]["stop_event"].clear()  # Снимаем событие остановки
                            
                            thread = threading.Thread(target=run_program, args=(prog,))  # Создаём поток для запуска программы
                            thread.start()  # Запускаем поток
                            program_controls[prog]["thread"] = thread  # Сохраняем ссылку на поток
                            threads.append(thread)  # Добавляем поток в список
                            response = f"Программа '{prog}' возобновлена."  # Формируем сообщение
                            logging.info(response)  # Логируем возобновление программы
                send_msg(client_socket, response)  # Отправляем сообщение клиенту
            elif cmd == "CHANGE" and len(parts) >= 3:  # Если команда CHANGE
                try:
                    new_interval = int(parts[-1])  # Получаем новый интервал
                    if new_interval <= 0:  # Если интервал некорректный
                        response = "Интервал должен быть положительным числом."  # Формируем сообщение об ошибке
                    else:
                        prog = " ".join(parts[1:-1])  # Формируем имя программы
                        if prog not in program_controls:  # Если программы нет в списке
                                response = f"Программа '{prog}' не найдена."  # Формируем сообщение об ошибке
                        else:
                                program_controls[prog]["interval"] = new_interval  # Изменяем интервал
                                response = f"Интервал для программы '{prog}' изменён на {new_interval} секунд."  # Формируем сообщение
                                logging.info(response)  # Логируем изменение интервала
                except ValueError:  # Обрабатываем ошибки преобразования
                    response = "Неверный формат интервала."  # Формируем сообщение об ошибке
                send_msg(client_socket, response)  # Отправляем сообщение клиенту
            elif cmd == "SHOW" and len(parts) >= 1:
                try:
                    logging.info(f'Выполняется показ таблицы программ из файла {DATA_FILE}')
                    response = '\n\n'+format_show(programs_data)
                except:
                    response = f'Нет информации о программах. На сервере ничего не запускалось'
                send_msg(client_socket, response)
            elif cmd == "EXIT" and len(parts)>=1:
                response = 'Клиент выбрал выйти из цикла'
                logging.info(response)
                
                logging.info("Получен сигнал завершения. Начинаем graceful shutdown...")  # Логируем завершение
                
                client_socket.close()  # Закрываем сокет клиента
                logging.info("Клиент завершил работу.")  # Логируем завершение работы
                
                shutdown_event.set()  # Устанавливаем событие завершения работы
                
                for thread in threads:  # Ждём завершения всех потоков
                    thread.join()
                save_data()  # Сохраняем данные
                logging.info("Сервер завершил работу корректно.")  # Логируем завершение работы
                
            else:  # Если команда не распознана
                response = (
                    "Доступные команды:\n"
                    "ADD <program>\n"
                    "GET <program>\n"
                    "STOP <program>\n"
                    "RESUME <program>\n"
                    "CHANGE <program> <new_interval>\n"
                    "SHOW\n"
                    "EXIT\n> "
                )
                send_msg(client_socket, response)  # Отправляем справку клиенту
    except Exception as e:  # Обрабатываем ошибки
        logging.error(f"Ошибка обработки клиента: {e}")  # Логируем ошибку
    finally:
        client_socket.close()  # Закрываем сокет клиента


def start_server():  # Функция запуска сервера
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Создаём сокет
    try:
        server.bind((SERVER_HOST, SERVER_PORT))  # Привязываем сокет к адресу и порту
    except Exception as e:  # Обрабатываем ошибки привязки
        logging.error(f"Ошибка привязки к {SERVER_HOST}:{SERVER_PORT} - {e}")  # Логируем ошибку
        shutdown_event.set()  # Устанавливаем событие завершения работы
        return
    server.listen(5)  # Начинаем прослушивание подключений
    server.settimeout(1)  # Устанавливаем таймаут для accept
    logging.info(f"Сервер запущен и слушает {SERVER_HOST}:{SERVER_PORT}")  # Логируем запуск сервера
    while not shutdown_event.is_set():  # Цикл до завершения работы
        try:
            client_sock, addr = server.accept()  # Принимаем подключение клиента
            logging.info(f"Подключился клиент {addr}")  # Логируем подключение
            client_thread = threading.Thread(target=handle_client, args=(client_sock,))  # Создаём поток для обработки клиента
            client_thread.start()  # Запускаем поток
            threads.append(client_thread)  # Добавляем поток в список
        except socket.timeout:  # Обрабатываем таймаут
            continue
        except Exception as e:  # Обрабатываем другие ошибки
            logging.error(f"Ошибка при принятии соединения: {e}")  # Логируем ошибку
    server.close()  # Закрываем сокет сервера
    logging.info("Сервер остановил приём соединений.")  # Логируем остановку сервера


def main():  # Основная функция сервера
    load_data()  # Загружаем данные из файла
    for prog in sys.argv[1:]:  # Проходим по аргументам командной строки
        if not is_program_executable(prog):  # Проверяем доступность программы
            logging.warning(f"Программа '{prog}' не найдена или нет прав доступа. Пропускаем.")  # Логируем предупреждение
            continue
        if prog not in programs_data:  # Если программы нет в списке
                folder = ensure_folder(prog)  # Создаём папку для программы
                programs_data[prog] = {"folder": folder, "runs": []}  # Добавляем данные о программе
                program_controls[prog] = {  # Добавляем управление программой
                    "interval": DEFAULT_INTERVAL,
                    "stop_event": threading.Event()
                }
                thread = threading.Thread(target=run_program, args=(prog,))  # Создаём поток для запуска программы
                thread.start()  # Запускаем поток
                program_controls[prog]["thread"] = thread  # Сохраняем ссылку на поток
                threads.append(thread)  # Добавляем поток в список
    save_data()  # Сохраняем данные
    server_thread = threading.Thread(target=start_server)  # Создаём поток для запуска сервера
    server_thread.start()  # Запускаем поток
    threads.append(server_thread)  # Добавляем поток в список
    try:
        while not shutdown_event.is_set():  # Цикл до завершения работы
            time.sleep(1)  # Ждём 1 секунду
    except KeyboardInterrupt:  # Обрабатываем прерывание клавишами Ctrl+C
        logging.info("Получен сигнал завершения. Начинаем graceful shutdown...")  # Логируем завершение
        shutdown_event.set()  # Устанавливаем событие завершения работы
    for thread in threads:  # Ждём завершения всех потоков
        thread.join()
    save_data()  # Сохраняем данные
    logging.info("Сервер завершил работу корректно.")  # Логируем завершение работы

if __name__ == '__main__':  # Проверяем, что скрипт запущен как главная программа
    main()  # Вызываем основную функцию