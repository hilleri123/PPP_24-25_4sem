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
DATA_FILE = os.path.join(
    os.path.dirname(
        os.path.abspath(__file__)),
    "programs_info.json")  # Файл для хранения данных о программах
SERVER_HOST = "127.0.0.1"  # IP-адрес сервера
SERVER_PORT = 5000  # Порт сервера
# Интервал запуска программ (по умолчанию 10 секунд)
DEFAULT_INTERVAL = int(os.environ.get("LAUNCH_INTERVAL", "10"))
LOGGING = True

logging.basicConfig(level=logging.INFO,  # Настройка уровня логирования
                    # Формат логов
                    format="%(asctime)s [%(levelname)s] %(message)s")

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
            if LOGGING:
                logging.error(
                    f"Ошибка загрузки данных из {DATA_FILE}: {e}")  # Логируем ошибку
            programs_data = {}  # Очищаем данные
    else:
        programs_data = {}  # Если файл не существует, инициализируем пустой словарь


def save_data():  # Функция сохранения данных в JSON-файл
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:  # Открываем файл для записи
            # Сохраняем данные в файл
            json.dump(programs_data, f, indent=4, ensure_ascii=False)
    except Exception as e:  # Обрабатываем ошибки при сохранении
        if LOGGING:
            # Логируем ошибку
            logging.error(f"Ошибка сохранения данных в {DATA_FILE}: {e}")


def sanitize_folder_name(name):  # Функция очистки имени папки
    # Заменяем недопустимые символы на "_"
    return "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in name)


def ensure_folder(program_name):  # Функция создания папки для программы
    folder = sanitize_folder_name(program_name)  # Очищаем имя папки
    if not os.path.exists(folder):  # Проверяем, существует ли папка
        os.makedirs(folder)  # Создаём папку
    return folder  # Возвращаем путь к папке


# Функция проверки доступности программы
def is_program_executable(program_command):
    parts = program_command.split()  # Разбиваем команду на части
    cmd = parts[0]  # Берём первую часть (команду)
    if cmd.endswith('.py'):  # Если это Python-скрипт
        abs_path = os.path.abspath(cmd)
        if LOGGING:
            logging.info(f"Проверяем путь к Python-скрипту: {abs_path}")
        # Проверяем, существует ли файл и доступен ли он для чтения
        return os.path.isfile(cmd) and os.access(cmd, os.R_OK)
    else:
        if LOGGING:
            logging.info(f"Проверяем команду через shutil.which: {cmd}")
        # Проверяем, доступна ли команда в PATH
        return shutil.which(cmd) is not None


def run_program(program_name):  # Функция циклического запуска программы
    if LOGGING:
        # Логируем начало работы
        logging.info(f"Начинаем циклический запуск программы '{program_name}'")
    # Получаем путь к папке программы
    folder = programs_data[program_name]["folder"]
    while not shutdown_event.is_set(
    ) and not program_controls[program_name]["stop_event"].is_set():  # Цикл до завершения работы
        timestamp = time.strftime("%Y%m%d_%H%M%S")  # Формируем метку времени
        # Формируем имя файла для вывода
        output_filename = os.path.join(folder, f"output_{timestamp}.txt")
        try:
            if program_name.endswith('.py'):  # Если это Python-скрипт
                # Формируем команду для запуска
                cmd = f"{sys.executable} {os.path.abspath(program_name)}"
            else:
                # Формируем команду для запуска
                cmd = os.path.abspath(program_name)
            # logging.info(f"Запускаем команду: {cmd}")  # Логируем команду
            result = subprocess.run(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=30)  # Запускаем программу
            output = result.stdout  # Получаем вывод программы
            if program_controls[program_name]["verbose"].is_set():
                if LOGGING:
                    # Отправляем сообщение клиенту
                    logging.info(f'[OUTPUT] [{program_name}] : {output}')
        except Exception as e:  # Обрабатываем ошибки при запуске
            if LOGGING:
                logging.error(
                    f"Ошибка при запуске программы '{program_name}': {e}")  # Логируем ошибку
            # Формируем сообщение об ошибке
            output = f"Ошибка при запуске программы: {e}"
        try:
            with open(output_filename, "w", encoding="utf-8") as f:  # Открываем файл для записи
                f.write(output)  # Записываем вывод программы в файл
        except Exception as e:  # Обрабатываем ошибки при записи
            if LOGGING:
                logging.error(
                    f"Ошибка записи в файл {output_filename}: {e}")  # Логируем ошибку
        programs_data[program_name]["runs"].append({  # Добавляем информацию о запуске
            "timestamp": timestamp,
            "file": output_filename
        })
        save_data()  # Сохраняем данные
        for _ in range(
                program_controls[program_name]["interval"]):  # Ждём интервал между запусками
            if shutdown_event.is_set() or program_controls[program_name]["stop_event"].is_set(
            ):  # Проверяем завершение работы
                break
            time.sleep(1)  # Ждём 1 секунду
    if LOGGING:
        # Логируем завершение работы
        logging.info(
            f"Циклический запуск программы '{program_name}' завершён.")


def send_msg(sock, message):  # Функция отправки сообщения через сокет
    msg = message.encode("utf-8")  # Кодируем сообщение в байты
    # Формируем заголовок с длиной сообщения
    header = f"{len(msg):010d}".encode("utf-8")
    try:
        sock.sendall(header + msg)  # Отправляем сообщение
    except Exception as e:  # Обрабатываем ошибки
        if LOGGING:
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
    header_row = f"| {'process':^{max([len(key) for key in json.keys()] +
                                      [len('process')])}} | {'outputs folder':^{max([len(json[key]["folder"]) for key in json.keys()] +
                                                                                    [len('outputs folder')])}} | {'runs':^{max([len(str(len(json[key]["runs"]))) for key in json.keys()] +
                                                                                                                               [len('runs')])}} |\n"

    header_row += f"|{'-' *
                      (len(header_row.split('|')[1]))}|{'-' *
                                                        (len(header_row.split('|')[2]))}|{'-' *
                                                                                          (len(header_row.split('|')[3]))}|\n"
    data_rows = ""
    for key in json.keys():
        data_row = f"|{
            key:^{
                len(
                    header_row.split('|')[1])}}|{
            json[key]["folder"]:^{
                len(
                    header_row.split('|')[2])}}|{
            len(
                json[key]["runs"]):^{
                len(
                    header_row.split('|')[3])}}|\n"
        data_rows += data_row

    table = header_row + data_rows
    return table


def strtobool(val):
    """Convert a string representation of truth to true (1) or false (0).
    True values are 'y', 'yes', 't', 'true', 'on', and '1'; false values
    are 'n', 'no', 'f', 'false', 'off', and '0'.  Raises ValueError if
    'val' is anything else.
    """
    val = val.lower()
    if val in ('y', 'yes', 't', 'true', 'on', '1'):
        return 1
    elif val in ('n', 'no', 'f', 'false', 'off', '0'):
        return 0
    else:
        raise ValueError("invalid truth value %r" % (val,))


def handle_client(client_socket):  # Функция обработки клиентских запросов
    try:
        while not shutdown_event.is_set():  # Цикл до завершения работы
            data = client_socket.recv(1024)  # Получаем данные от клиента
            if not data:  # Если данных нет, выходим
                break
            command = data.decode("utf-8").strip()  # Декодируем команду
            if LOGGING:
                # Логируем команду
                logging.info(f"Получена команда от клиента: {command}")
            parts = command.split()  # Разбиваем команду на части
            if not parts:  # Если частей нет, продолжаем
                continue
            # Берём первую часть (команду) и переводим её в верхний регистр
            cmd = parts[0].upper()
            if cmd == "ADD" and len(parts) >= 2:  # Если команда ADD
                new_program = " ".join(parts[1:])  # Формируем имя программы
                if not is_program_executable(
                        new_program):  # Проверяем доступность программы
                    # Формируем сообщение об ошибке
                    response = f"Ошибка: программа '{new_program}' не найдена или нет доступа."
                    # Отправляем сообщение клиенту
                    send_msg(client_socket, response)
                    continue
                if new_program in programs_data:  # Если программа уже существует
                    # Формируем сообщение
                    response = f"Программа '{new_program}' уже существует."
                else:
                    # Создаём папку для программы
                    folder = ensure_folder(new_program)
                    programs_data[new_program] = {
                        "folder": folder, "runs": []}  # Добавляем данные о программе
                    program_controls[new_program] = {  # Добавляем управление программой
                        "interval": DEFAULT_INTERVAL,
                        "stop_event": threading.Event(),
                        "verbose": threading.Event()
                    }
                    thread = threading.Thread(target=run_program, args=(
                        new_program,))  # Создаём поток для запуска программы
                    thread.start()  # Запускаем поток
                    # Сохраняем ссылку на поток
                    program_controls[new_program]["thread"] = thread
                    threads.append(thread)  # Добавляем поток в список
                    # Формируем сообщение
                    response = f"Программа '{new_program}' добавлена."
                    if LOGGING:
                        logging.info(response)  # Логируем добавление программы
                    save_data()  # Сохраняем данные
                # Отправляем сообщение клиенту
                send_msg(client_socket, response)
            elif cmd == "GET" and len(parts) >= 2:  # Если команда GET
                prog = " ".join(parts[1:])  # Формируем имя программы
                if prog not in programs_data:  # Если программы нет в списке
                    # Формируем сообщение об ошибке
                    response = f"Программа '{prog}' не найдена."
                    # Отправляем сообщение клиенту
                    send_msg(client_socket, response)
                    continue
                # Получаем список запусков программы
                runs = programs_data[prog]["runs"][:]
                combined_output = ""  # Инициализируем объединённый вывод
                for run in runs:  # Проходим по всем запускам
                    try:
                        # Открываем файл для чтения
                        with open(run["file"], "r", encoding="utf-8") as f:
                            # Добавляем содержимое файла
                            combined_output += f"----- {
                                run['timestamp']} -----\n" + f.read() + "\n"
                    except Exception as e:  # Обрабатываем ошибки чтения
                        # Формируем сообщение об ошибке
                        combined_output += f"Ошибка чтения файла {
                            run['file']}: {e}\n"
                # Отправляем объединённый вывод клиенту
                send_msg(client_socket, combined_output)
            elif cmd == "STOP" and len(parts) >= 2:  # Если команда STOP
                prog = " ".join(parts[1:])  # Формируем имя программы
                if prog not in program_controls:  # Если программы нет в списке
                    # Формируем сообщение об ошибке
                    response = f"Программа '{prog}' не найдена."
                else:
                    if program_controls[prog]["stop_event"].is_set(
                    ):  # Если программа уже остановлена
                        # Формируем сообщение
                        response = f"Программа '{prog}' уже остановлена."
                    else:
                        # Устанавливаем событие остановки
                        program_controls[prog]["stop_event"].set()
                        # Формируем сообщение
                        response = f"Программа '{prog}' остановлена."
                        if LOGGING:
                            # Логируем остановку программы
                            logging.info(response)
                # Отправляем сообщение клиенту
                send_msg(client_socket, response)
            elif cmd == "RESUME" and len(parts) >= 2:  # Если команда RESUME
                prog = " ".join(parts[1:])  # Формируем имя программы

                if not is_program_executable(
                        prog):  # Проверяем доступность программы
                    # Формируем сообщение об ошибке
                    response = f"Ошибка: программа '{new_program}' не найдена или нет доступа."
                    # Отправляем сообщение клиенту
                    send_msg(client_socket, response)
                    continue

                elif prog not in programs_data:  # Если программы нет в списке
                    # Формируем сообщение об ошибке
                    response = f"Программа '{prog}' не найдена."

                else:
                    if not (prog in program_controls.keys()):
                        program_controls[prog] = {  # Добавляем управление программой
                            "interval": DEFAULT_INTERVAL,
                            "stop_event": threading.Event(),
                            "verbose": threading.Event()
                        }
                        thread = threading.Thread(
                            target=run_program, args=(
                                prog,))  # Создаём поток для запуска программы
                        thread.start()  # Запускаем поток
                        # Сохраняем ссылку на поток
                        program_controls[prog]["thread"] = thread
                        threads.append(thread)  # Добавляем поток в список
                        # Формируем сообщение
                        response = f"Программа '{prog}' добавлена."
                        if LOGGING:
                            # Логируем добавление программы
                            logging.info(response)
                        save_data()  # Сохраняем данные
                    else:
                        if not program_controls[prog]["stop_event"].is_set(
                        ):  # Если программа уже запущена
                            # Формируем сообщение
                            response = f"Программа '{prog}' уже запущена."
                        else:
                            # Снимаем событие остановки
                            program_controls[prog]["stop_event"].clear()

                            # Создаём поток для запуска программы
                            thread = threading.Thread(
                                target=run_program, args=(prog,))
                            thread.start()  # Запускаем поток
                            # Сохраняем ссылку на поток
                            program_controls[prog]["thread"] = thread
                            threads.append(thread)  # Добавляем поток в список
                            # Формируем сообщение
                            response = f"Программа '{prog}' возобновлена."
                            if LOGGING:
                                # Логируем возобновление программы
                                logging.info(response)
                # Отправляем сообщение клиенту
                send_msg(client_socket, response)
            elif cmd == "CHANGE" and len(parts) >= 3:  # Если команда CHANGE
                try:
                    new_interval = int(parts[-1])  # Получаем новый интервал
                    if new_interval <= 0:  # Если интервал некорректный
                        # Формируем сообщение об ошибке
                        response = "Интервал должен быть положительным числом."
                    else:
                        prog = " ".join(parts[1:-1])  # Формируем имя программы
                        if prog not in program_controls:  # Если программы нет в списке
                            # Формируем сообщение об ошибке
                            response = f"Программа '{prog}' не найдена."
                        else:
                            # Изменяем интервал
                            program_controls[prog]["interval"] = new_interval
                            # Формируем сообщение
                            response = f"Интервал для программы '{prog}' изменён на {new_interval} секунд."
                            if LOGGING:
                                # Логируем изменение интервала
                                logging.info(response)
                except ValueError:  # Обрабатываем ошибки преобразования
                    response = "Неверный формат интервала."  # Формируем сообщение об ошибке
                # Отправляем сообщение клиенту
                send_msg(client_socket, response)

            elif cmd == 'VERBOSE' and len(parts) >= 2 and LOGGING:
                if len(parts) >= 3:
                    prog = " ".join(parts[2:])  # Формируем имя программы
                    if prog not in program_controls:  # Если программы нет в списке
                        # Формируем сообщение об ошибке
                        response = f"Программа '{prog}' не найдена."
                    else:
                        if program_controls[prog]["stop_event"].is_set(
                        ):  # Если программа не работает
                            # Формируем сообщение
                            response = f"Программа '{prog}' не работает"
                        else:
                            if strtobool(parts[1]):
                                # Формируем сообщение
                                response = f"Циклические выводы программы '{prog}' начали осуществляться "
                                program_controls[prog]["verbose"].set()
                            else:
                                # Формируем сообщение
                                response = f"Циклические выводы программы '{prog}' прекратили осуществляться "
                                program_controls[prog]["verbose"].clear()

                else:
                    response = ''
                    for element in program_controls.keys():
                        if program_controls[element]["stop_event"].is_set(
                        ):  # Если программа не работает
                            # Формируем сообщение
                            response = f"Программа '{element}' не работает\n"
                        else:
                            if strtobool(parts[1]):
                                # Формируем сообщение
                                response += f"Циклические выводы программы '{element}' начали осуществляться\n"
                                program_controls[element]["verbose"].set()
                            else:
                                # Формируем сообщение
                                response = f"Циклические выводы программы '{element}' прекратили осуществляться\n"
                                program_controls[element]["verbose"].set()

                if LOGGING:
                    logging.info(response)  # Логируем начало выводов
                # Отправляем сообщение клиенту
                send_msg(client_socket, response)

            elif cmd == "SHOW" and len(parts) >= 1:
                try:
                    if LOGGING:
                        logging.info(
                            f'Выполняется показ таблицы программ из файла {DATA_FILE}')
                    response = '\n\n' + format_show(programs_data)
                except BaseException:
                    response = f'Нет информации о программах. На сервере ничего не запускалось'
                send_msg(client_socket, response)

            elif cmd == "EXIT" and len(parts) >= 1:
                response = 'Клиент выбрал выйти из цикла'
                if LOGGING:
                    logging.info(response)

                if LOGGING:
                    # Логируем завершение
                    logging.info(
                        "Получен сигнал завершения. Начинаем graceful shutdown...")

                client_socket.close()  # Закрываем сокет клиента
                if LOGGING:
                    # Логируем завершение работы
                    logging.info("Клиент завершил работу.")

                shutdown_event.set()  # Устанавливаем событие завершения работы

                for thread in threads:  # Ждём завершения всех потоков
                    thread.join()
                save_data()  # Сохраняем данные
                if LOGGING:
                    # Логируем завершение работы
                    logging.info("Сервер завершил работу корректно.")

            elif cmd == "HELP" and len(parts) >= 1:
                response = (
                    "Доступные команды:\n"
                    "ADD <program>\n"
                    "GET <program>\n"
                    "STOP <program>\n"
                    "RESUME <program>\n"
                    "CHANGE <program> <new_interval>\n"
                    "SHOW\n"
                    "VERBOSE <TRUE/FALSE> [optional: <program>]\n"
                    "EXIT\n> "
                )

                send_msg(client_socket, response)  # Отправляем справку клиенту

            else:  # Если команда не распознана
                response = "> "
                send_msg(client_socket, response)  # Отправляем справку клиенту
    except Exception as e:  # Обрабатываем ошибки
        if LOGGING:
            logging.error(f"Ошибка обработки клиента: {e}")  # Логируем ошибку
    finally:
        client_socket.close()  # Закрываем сокет клиента


def start_server():  # Функция запуска сервера
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Создаём сокет
    try:
        # Привязываем сокет к адресу и порту
        server.bind((SERVER_HOST, SERVER_PORT))
    except Exception as e:  # Обрабатываем ошибки привязки
        if LOGGING:
            # Логируем ошибку
            logging.error(
                f"Ошибка привязки к {SERVER_HOST}:{SERVER_PORT} - {e}")
        shutdown_event.set()  # Устанавливаем событие завершения работы
        return
    server.listen(5)  # Начинаем прослушивание подключений
    server.settimeout(1)  # Устанавливаем таймаут для accept
    if LOGGING:
        # Логируем запуск сервера
        logging.info(f"Сервер запущен и слушает {SERVER_HOST}:{SERVER_PORT}")
    while not shutdown_event.is_set():  # Цикл до завершения работы
        try:
            client_sock, addr = server.accept()  # Принимаем подключение клиента
            if LOGGING:
                # Логируем подключение
                logging.info(f"Подключился клиент {addr}")
            client_thread = threading.Thread(target=handle_client, args=(
                client_sock,))  # Создаём поток для обработки клиента
            client_thread.start()  # Запускаем поток
            threads.append(client_thread)  # Добавляем поток в список
        except socket.timeout:  # Обрабатываем таймаут
            continue
        except Exception as e:  # Обрабатываем другие ошибки
            if LOGGING:
                logging.error(
                    f"Ошибка при принятии соединения: {e}")  # Логируем ошибку
    server.close()  # Закрываем сокет сервера
    if LOGGING:
        # Логируем остановку сервера
        logging.info("Сервер остановил приём соединений.")


def main():  # Основная функция сервера
    load_data()  # Загружаем данные из файла
    for prog in sys.argv[1:]:  # Проходим по аргументам командной строки
        if not is_program_executable(prog):  # Проверяем доступность программы
            if LOGGING:
                # Логируем предупреждение
                logging.warning(
                    f"Программа '{prog}' не найдена или нет прав доступа. Пропускаем.")
            continue
        if prog not in programs_data:  # Если программы нет в списке
            folder = ensure_folder(prog)  # Создаём папку для программы
            # Добавляем данные о программе
            programs_data[prog] = {"folder": folder, "runs": []}
            program_controls[prog] = {  # Добавляем управление программой
                "interval": DEFAULT_INTERVAL,
                "stop_event": threading.Event()
            }
            thread = threading.Thread(
                target=run_program, args=(
                    prog,))  # Создаём поток для запуска программы
            thread.start()  # Запускаем поток
            # Сохраняем ссылку на поток
            program_controls[prog]["thread"] = thread
            threads.append(thread)  # Добавляем поток в список
    save_data()  # Сохраняем данные
    # Создаём поток для запуска сервера
    server_thread = threading.Thread(target=start_server)
    server_thread.start()  # Запускаем поток
    threads.append(server_thread)  # Добавляем поток в список
    try:
        while not shutdown_event.is_set():  # Цикл до завершения работы
            time.sleep(1)  # Ждём 1 секунду
    except KeyboardInterrupt:  # Обрабатываем прерывание клавишами Ctrl+C
        if LOGGING:
            # Логируем завершение
            logging.info(
                "Получен сигнал завершения. Начинаем graceful shutdown...")
        shutdown_event.set()  # Устанавливаем событие завершения работы
    for thread in threads:  # Ждём завершения всех потоков
        thread.join()
    save_data()  # Сохраняем данные
    if LOGGING:
        # Логируем завершение работы
        logging.info("Сервер завершил работу корректно.")


if __name__ == '__main__':  # Проверяем, что скрипт запущен как главная программа
    main()  # Вызываем основную функцию
