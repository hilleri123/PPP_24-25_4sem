import subprocess  # Импортируем модуль для запуска внешних процессов
import signal  # Импортируем модуль для обработки сигналов (например, SIGINT)
import sys  # Импортируем модуль для работы с системными параметрами и функциями
import os  # Импортируем модуль для работы с операционной системой
import time  # Импортируем модуль для работы со временем


def main():  # Определяем основную функцию программы
    # Получаем абсолютный путь к директории текущего файла
    base_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(base_dir)
    # Формируем путь к файлу server.py
    server_script = os.path.join(base_dir, "server.py")
    # Формируем путь к файлу client.py
    client_script = os.path.join(base_dir, "client.py")

    if not os.path.exists(
            server_script):  # Проверяем, существует ли файл server.py
        # Если нет, выводим сообщение об ошибке
        print(f"Ошибка: {server_script} не найден!")
        sys.exit(1)  # Завершаем программу с кодом ошибки 1
    if not os.path.exists(
            client_script):  # Проверяем, существует ли файл client.py
        # Если нет, выводим сообщение об ошибке
        print(f"Ошибка: {client_script} не найден!")
        sys.exit(1)  # Завершаем программу с кодом ошибки 1

    try:
        # Запускаем сервер как отдельный процесс
        # Запускаем server.py через интерпретатор Python
        server_proc = subprocess.Popen([sys.executable, server_script])
        print("Сервер запущен.")  # Выводим сообщение о запуске сервера
    except Exception as e:  # Обрабатываем возможные ошибки при запуске сервера
        print("Ошибка при запуске сервера:", e)  # Выводим сообщение об ошибке
        sys.exit(1)  # Завершаем программу с кодом ошибки 1

    # Добавляем задержку в 1 секунду для завершения инициализации сервера
    time.sleep(1)

    try:
        # Запускаем клиент как отдельный процесс
        # Запускаем client.py через интерпретатор Python
        client_proc = subprocess.Popen([sys.executable, client_script])
        print("Клиент запущен.")  # Выводим сообщение о запуске клиента
    except Exception as e:  # Обрабатываем возможные ошибки при запуске клиента
        print("Ошибка при запуске клиента:", e)  # Выводим сообщение об ошибке
        # Отправляем сигнал завершения серверу
        server_proc.send_signal(signal.SIGINT)
        sys.exit(1)  # Завершаем программу с кодом ошибки 1

    def signal_handler(sig, frame):  # Определяем обработчик сигналов
        # Выводим сообщение о получении сигнала
        print("\nПолучен сигнал завершения. Отправляем SIGINT процессам для graceful shutdown...")
        try:
            # Отправляем сигнал завершения клиенту
            client_proc.send_signal(signal.SIGINT)
        except Exception:
            pass  # Игнорируем ошибки при отправке сигнала клиенту
        try:
            # Отправляем сигнал завершения серверу
            server_proc.send_signal(signal.SIGINT)
        except Exception:
            pass  # Игнорируем ошибки при отправке сигнала серверу
        try:
            # Ждём завершения клиента (не более 10 секунд)
            client_proc.wait(timeout=10)
            # Ждём завершения сервера (не более 10 секунд)
            server_proc.wait(timeout=10)
        except Exception:
            pass  # Игнорируем ошибки при ожидании завершения процессов
        sys.exit(0)  # Завершаем программу с кодом успеха

    # Регистрируем обработчик для сигнала SIGINT (Ctrl+C)
    signal.signal(signal.SIGINT, signal_handler)
    # Регистрируем обработчик для сигнала SIGTERM
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        while True:  # Бесконечный цикл для мониторинга состояния клиентского процесса
            if client_proc.poll() is not None:  # Проверяем, завершился ли клиентский процесс
                # Выводим сообщение о завершении клиента
                print("Клиент завершил работу. Отправляем сигнал завершения серверу.")
                try:
                    # Отправляем сигнал завершения серверу
                    server_proc.send_signal(signal.SIGINT)
                except Exception:
                    pass  # Игнорируем ошибки при отправке сигнала серверу
                break  # Выходим из цикла
            time.sleep(0.5)  # Ждём 0.5 секунды перед следующей проверкой
    except KeyboardInterrupt:  # Обрабатываем прерывание клавишами Ctrl+C
        signal_handler(None, None)  # Вызываем обработчик сигналов


if __name__ == "__main__":  # Проверяем, что скрипт запущен как главная программа
    main()  # Вызываем основную функцию