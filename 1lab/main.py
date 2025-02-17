import subprocess  # Импортируем модуль для запуска внешних процессов
import signal  # Импортируем модуль для обработки сигналов (например, SIGINT)
import sys  # Импортируем модуль для работы с системными параметрами и функциями
import os  # Импортируем модуль для работы с операционной системой
import time  # Импортируем модуль для работы со временем

def main():  # Определяем основную функцию программы
    base_dir = os.path.dirname(os.path.abspath(__file__))  # Получаем абсолютный путь к директории текущего файла
    os.chdir(base_dir)
    server_script = os.path.join(base_dir, "server.py")  # Формируем путь к файлу server.py
    client_script = os.path.join(base_dir, "client.py")  # Формируем путь к файлу client.py

    if not os.path.exists(server_script):  # Проверяем, существует ли файл server.py
        print(f"Ошибка: {server_script} не найден!")  # Если нет, выводим сообщение об ошибке
        sys.exit(1)  # Завершаем программу с кодом ошибки 1
    if not os.path.exists(client_script):  # Проверяем, существует ли файл client.py
        print(f"Ошибка: {client_script} не найден!")  # Если нет, выводим сообщение об ошибке
        sys.exit(1)  # Завершаем программу с кодом ошибки 1

    try:
        # Запускаем сервер как отдельный процесс
        server_proc = subprocess.Popen([sys.executable, server_script])  # Запускаем server.py через интерпретатор Python
        print("Сервер запущен.")  # Выводим сообщение о запуске сервера
    except Exception as e:  # Обрабатываем возможные ошибки при запуске сервера
        print("Ошибка при запуске сервера:", e)  # Выводим сообщение об ошибке
        sys.exit(1)  # Завершаем программу с кодом ошибки 1

    time.sleep(1)  # Добавляем задержку в 1 секунду для завершения инициализации сервера

    try:
        # Запускаем клиент как отдельный процесс
        client_proc = subprocess.Popen([sys.executable, client_script])  # Запускаем client.py через интерпретатор Python
        print("Клиент запущен.")  # Выводим сообщение о запуске клиента
    except Exception as e:  # Обрабатываем возможные ошибки при запуске клиента
        print("Ошибка при запуске клиента:", e)  # Выводим сообщение об ошибке
        server_proc.send_signal(signal.SIGINT)  # Отправляем сигнал завершения серверу
        sys.exit(1)  # Завершаем программу с кодом ошибки 1

    def signal_handler(sig, frame):  # Определяем обработчик сигналов
        print("\nПолучен сигнал завершения. Отправляем SIGINT процессам для graceful shutdown...")  # Выводим сообщение о получении сигнала
        try:
            client_proc.send_signal(signal.SIGINT)  # Отправляем сигнал завершения клиенту
        except Exception:
            pass  # Игнорируем ошибки при отправке сигнала клиенту
        try:
            server_proc.send_signal(signal.SIGINT)  # Отправляем сигнал завершения серверу
        except Exception:
            pass  # Игнорируем ошибки при отправке сигнала серверу
        try:
            client_proc.wait(timeout=10)  # Ждём завершения клиента (не более 10 секунд)
            server_proc.wait(timeout=10)  # Ждём завершения сервера (не более 10 секунд)
        except Exception:
            pass  # Игнорируем ошибки при ожидании завершения процессов
        sys.exit(0)  # Завершаем программу с кодом успеха

    signal.signal(signal.SIGINT, signal_handler)  # Регистрируем обработчик для сигнала SIGINT (Ctrl+C)
    signal.signal(signal.SIGTERM, signal_handler)  # Регистрируем обработчик для сигнала SIGTERM

    try:
        while True:  # Бесконечный цикл для мониторинга состояния клиентского процесса
            if client_proc.poll() is not None:  # Проверяем, завершился ли клиентский процесс
                print("Клиент завершил работу. Отправляем сигнал завершения серверу.")  # Выводим сообщение о завершении клиента
                try:
                    server_proc.send_signal(signal.SIGINT)  # Отправляем сигнал завершения серверу
                except Exception:
                    pass  # Игнорируем ошибки при отправке сигнала серверу
                break  # Выходим из цикла
            time.sleep(0.5)  # Ждём 0.5 секунды перед следующей проверкой
    except KeyboardInterrupt:  # Обрабатываем прерывание клавишами Ctrl+C
        signal_handler(None, None)  # Вызываем обработчик сигналов

if __name__ == "__main__":  # Проверяем, что скрипт запущен как главная программа
    main()  # Вызываем основную функцию