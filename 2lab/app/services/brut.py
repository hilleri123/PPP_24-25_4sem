import subprocess
import itertools
import rarfile
from app.core.endpoints import FastApiServerInfo

UNRAR_TOOL = FastApiServerInfo.UNRAR_TOOL

rarfile.UNRAR_TOOL = UNRAR_TOOL

r"C:\Program Files\WinRAR\UnRAR.exe"

def extract_rar_hash(archive_path):
    """
    Извлекает хеш RAR-архива с помощью утилиты rar2john.
    """
    try:
        command = r"Johntheripper\run\rar2john.exe "+ archive_path + ' > ' + archive_path.split('.')[0] + '.txt'
        result = subprocess.run(command.split(' '), shell=True)
    except Exception as e:
        print("Ошибка извлечения хеша из архива:", e)
        return None

def generate_passwords(charset, max_length, output_file):
    """
    Генерирует все возможные комбинации символов от длины 1 до max_length
    и записывает их построчно в output_file.
    """
    with open(output_file, "w", encoding="utf-8") as f:
        for length in range(1, max_length + 1):
            for pwd_tuple in itertools.product(charset, repeat=length):
                password = ''.join(pwd_tuple)
                f.write(password + "\n")
    print(f"Сгенерировано паролей записано в файл {output_file}")

def brute_force_rar(archive_path, passwords_file):
    """
    Перебирает список сгенерированных паролей и пытается открыть архив с каждым из них.
    В случае успеха возвращает найденный пароль.
    """
    # Открываем архив. Убедитесь, что у вас установлен 'unrar' (или 'rar') для работы модуля.
    try:
        rf = rarfile.RarFile(archive_path)
    except Exception as e:
        print("Ошибка открытия архива:", e)
        return None

    with open(passwords_file, "r", encoding="utf-8") as f:
        for line in f:
            password = line.strip()
            try:
                # Пробуем извлечь содержимое в тестовом режиме.
                # Если пароль неверный, скорее всего, будет выброшено исключение.
                rf.extractall(path=".", pwd=password.encode())
                print("Найден пароль:", password)
                return password
            except rarfile.BadRarFile:
                # Это исключение может возникнуть, если архив поврежден или пароль неверный.
                print("Неверный пароль:", password)
            except rarfile.RarCRCError:
                # Ошибка контрольной суммы (CRC) свидетельствует о неверном пароле.
                print("Неверный пароль:", password)
            except Exception as e:
                # Для отладки можно выводить и другие возможные ошибки.
                print(f"Ошибка при проверке пароля '{password}': {e}")
    print("Пароль не найден")
    return None
