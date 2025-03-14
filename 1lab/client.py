import socket
import json
import struct
import logging
import time

# Настройка логирования
logging.basicConfig(
    filename='client.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


# Простое шифрование/дешифрование (должно совпадать с сервером)
def xor_encrypt_decrypt(data, key='secret_key'):
    return bytes(a ^ b for a, b in zip(data, key.encode() * (len(data) // len(key) + 1)))


# Отправка команды на сервер и получение ответа
def send_command(command):
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(('localhost', 9999))

        encrypted_command = xor_encrypt_decrypt(command.encode('utf-8'))
        client_socket.send(struct.pack('>I', len(encrypted_command)) + encrypted_command)

        data_len = struct.unpack('>I', client_socket.recv(4))[0]
        encrypted_data = client_socket.recv(data_len)
        data = xor_encrypt_decrypt(encrypted_data)

        client_socket.close()
        return data
    except Exception as e:
        logging.error(f"Client error: {e}")
        return None


# Отображение данных в удобном формате
def display_data(data):
    try:
        tree = json.loads(data.decode('utf-8'))
        for directory, files in tree.items():
            print(f"\nDirectory: {directory}")
            print(f"{'Name':<30} {'Size (bytes)':<15} {'Last Modified':<25}")
            print("-" * 70)
            for file in files:
                print(f"{file['name']:<30} {file['size']:<15} {file['modified']:<25}")
    except Exception as e:
        logging.error(f"Error displaying data: {e}")
        print("Error displaying data")


def main():
    print("Available commands: get_file, update <value>, filter <keyword>, sort <key>, exit")
    while True:
        try:
            cmd = input("Enter command: ").strip()
            logging.info(f"Command entered: {cmd}")

            if cmd == "exit":
                break

            elif cmd == "get_file":
                data = send_command("get_file")
                if data:
                    display_data(data)

            elif cmd.startswith("update "):
                value = cmd.split("update ")[1]
                response = send_command(f"update:{value}")
                if response:
                    print(response.decode('utf-8'))

            elif cmd.startswith("filter "):
                keyword = cmd.split("filter ")[1]
                data = send_command(f"filter:{keyword}")
                if data:
                    display_data(data)

            elif cmd.startswith("sort "):
                key = cmd.split("sort ")[1]
                if key not in ['name', 'size', 'modified']:
                    print("Invalid sort key. Use: name, size, modified")
                    continue
                data = send_command(f"sort:{key}")
                if data:
                    display_data(data)

            else:
                print("Unknown command")

        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            logging.error(f"Client main loop error: {e}")
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
