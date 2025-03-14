import os
import socket
import json
import struct
import logging
import time
from hashlib import sha256

# Настройка логирования
logging.basicConfig(
    filename='../../pythonProject1/server.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


# Простое шифрование (XOR с ключом для безопасности передачи)
def xor_encrypt_decrypt(data, key='secret_key'):
    return bytes(a ^ b for a, b in zip(data, key.encode() * (len(data) // len(key) + 1)))


# Сканирование PATH и сбор информации о файлах
def scan_path():
    path_dirs = os.environ['PATH'].split(os.pathsep)
    tree = {}
    for directory in path_dirs:
        if os.path.exists(directory):
            executables = []
            try:
                for file in os.listdir(directory):
                    file_path = os.path.join(directory, file)
                    if os.path.isfile(file_path) and os.access(file_path, os.X_OK):
                        executables.append({
                            'name': file,
                            'size': os.path.getsize(file_path),
                            'modified': time.ctime(os.path.getmtime(file_path))
                        })
            except PermissionError:
                logging.warning(f"Permission denied for directory: {directory}")
                continue
            if executables:
                tree[directory] = executables
    return tree


# Сохранение данных в JSON
def save_to_json(data, filename='data.json'):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        logging.info(f"Data saved to {filename}")
    except Exception as e:
        logging.error(f"Error saving to JSON: {e}")


# Фильтрация и сортировка данных
def filter_and_sort(tree, filter_key=None, sort_key='name'):
    filtered_tree = {}
    for directory, files in tree.items():
        filtered_files = files
        if filter_key:
            filtered_files = [f for f in files if filter_key.lower() in f['name'].lower()]
        filtered_files = sorted(filtered_files, key=lambda x: x.get(sort_key, ''))
        if filtered_files:
            filtered_tree[directory] = filtered_files
    return filtered_tree


def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Повторное использование адреса
    server_socket.bind(('0.0.0.0', 9999))  # Доступен для всех интерфейсов
    server_socket.listen(5)
    logging.info("Server started on 0.0.0.0:9999")

    while True:
        try:
            client_socket, addr = server_socket.accept()
            logging.info(f"Connected to {addr}")

            # Прием длины данных и самих данных
            data_len = struct.unpack('>I', client_socket.recv(4))[0]
            encrypted_data = client_socket.recv(data_len)
            data = xor_encrypt_decrypt(encrypted_data).decode('utf-8')

            tree = scan_path()
            response = None

            if data == "get_file":
                save_to_json(tree)
                with open('../../pythonProject1/data.json', 'rb') as f:
                    file_data = f.read()
                response = file_data
                logging.info("Sent file data to client")

            elif data.startswith("update:"):
                new_env = data.split("update:")[1]
                os.environ['CUSTOM_ENV'] = new_env
                tree = scan_path()
                save_to_json(tree)
                response = b"Environment updated"
                logging.info(f"Environment updated with CUSTOM_ENV={new_env}")

            elif data.startswith("filter:"):
                filter_key = data.split("filter:")[1]
                filtered_tree = filter_and_sort(tree, filter_key=filter_key)
                save_to_json(filtered_tree, '../../pythonProject1/filtered_data.json')
                with open('../../pythonProject1/filtered_data.json', 'rb') as f:
                    file_data = f.read()
                response = file_data
                logging.info(f"Filtered data sent with key: {filter_key}")

            elif data.startswith("sort:"):
                sort_key = data.split("sort:")[1]
                sorted_tree = filter_and_sort(tree, sort_key=sort_key)
                save_to_json(sorted_tree, 'sorted_data.json')
                with open('sorted_data.json', 'rb') as f:
                    file_data = f.read()
                response = file_data
                logging.info(f"Sorted data sent by: {sort_key}")

            if response:
                encrypted_response = xor_encrypt_decrypt(response)
                client_socket.send(struct.pack('>I', len(encrypted_response)) + encrypted_response)

            client_socket.close()

        except Exception as e:
            logging.error(f"Server error: {e}")


if __name__ == "__main__":
    main()
