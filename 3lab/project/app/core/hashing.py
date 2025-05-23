import hashlib
import os


# Генерация соли (random salt) для улучшения безопасности хеширования
def get_salt():
    return os.urandom(32)


# Хеширование пароля с использованием алгоритма SHA-256 и соли
def get_password_hash(password: str) -> str:
    salt = get_salt()  # генерируем соль
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
    return salt + hashed  # возвращаем соль и хеш (соль нужна для проверки пароля в будущем)


# Проверка пароля путем сравнения с ранее захешированным значением
def verify_password(plain_password: str, hashed_password: str) -> bool:
    salt = hashed_password[:32]  # извлекаем соль (первые 32 байта)
    stored_hash = hashed_password[32:]  # извлекаем сам хеш пароля
    new_hash = hashlib.pbkdf2_hmac('sha256', plain_password.encode(), salt, 100000)
    return new_hash == stored_hash
