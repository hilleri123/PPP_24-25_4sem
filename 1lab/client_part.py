import socket
import os
import logging
import json
from datetime import datetime

logging.basicConfig(filename='client.log', level=logging.INFO, format='%(asctime)s - %(message)s')

def create_directory():
    now = datetime.now()
    directory = now.strftime("./%d-%m-%Y") #директория в таком формате
    os.makedirs(directory, exist_ok=True)
    # print(directory)
    return directory

def generate_filename(directory, extension):
    now = datetime.now()
    filename = now.strftime("%H-%M-%S") + f".{extension}"  # формат hh-mm-ss.json для файла
    return os.path.join(directory, filename)

def save_data(data, extension="json"):
    directory = create_directory()
    filename = generate_filename(directory, extension)  #генерация имени файла

    save_to_json(data, filename)

def receive_all_data(client_socket, buffer_size=1024): #получаем все данные сразу, чобы потом их отделять
    data = b""
    while True:
        part = client_socket.recv(buffer_size)
        data += part
        if is_valid_json(data):  # если данных меньше, чем buffer_size, то конец
            break
    return data
def save_to_json(data, filename):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)
def is_valid_json(data_str):
    try:
        json.loads(data_str)
        return True
    except json.JSONDecodeError:
        return False
def send_command(command):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('localhost', 12345))
    client_socket.send(command.encode('utf-8'))

    if command == "update":
        data = receive_all_data(client_socket)
        # print(data)
        data_str = data.decode('utf-8')
        # print(data_str)

        if is_valid_json(data_str): #проверка на валидность для json
            data = json.loads(data_str)
            # print(type(data))
            save_data(data)

        else:
            print("Error: the data is not valid JSON")

    client_socket.close()

def main():
    while True:
        print("1. Update process info")
        print("2. Send signal to process")
        print("3. Exit")
        choice = input("Choose an option: ")

        if choice == "1":
            send_command("update")
        elif choice == "2":
            pid = input("Enter PID: ")
            sig = input("Enter signal (e.g., 15 for SIGTERM, 9 for SIGKILL): ")
            send_command(f"signal {pid} {sig}")
        elif choice == "3":
            break
        else:
            print("Invalid option")

if __name__ == "__main__":
    main()