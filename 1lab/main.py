import os
import subprocess


def clear_screen():
    """Очищает экран терминала."""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_menu():
    """Выводит меню выбора."""
    print("=" * 40)
    print("Файловый менеджер: Клиент-Серверное приложение")
    print("""Для коректной работы программы, пожалуйста,
          запустите клиент и сервер в отдельных терминалах""")
    print("=" * 40)
    print("1. Запустить сервер")
    print("2. Запустить клиент")
    print("3. Выйти")
    print("=" * 40)


def main():
    """Основная функция для запуска сервера или клиента."""
    while True:
        clear_screen()
        print_menu()
        choice = input("Выберите опцию (1-3): ").strip()

        if choice == "1":
            print("Запуск сервера...")
            print("Сервер будет работать на 127.0.0.1:65432.")
            print("Для остановки сервера нажмите Ctrl+C.")
            input("Нажмите Enter, чтобы продолжить...")
            subprocess.run(["python", "server.py"])
        elif choice == "2":
            print("Запуск клиента...")
            print("Подключение к серверу 127.0.0.1:65432.")
            input("Нажмите Enter, чтобы продолжить...")
            subprocess.run(["python", "client.py"])
        elif choice == "3":
            print("Выход...")
            break
        else:
            input("Неверный выбор. Нажмите Enter, чтобы продолжить...")


if __name__ == "__main__":
    main()
