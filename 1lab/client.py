import socket
import csv
import json
import logging
from struct import pack, unpack

# Настройка логирования
logging.basicConfig(filename='client.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

class Client:
    def __init__(self, host='127.0.0.1', port=12345):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))
        self.authenticated = False

    def send_auth(self, username, password):
        auth_data = f"{username}:{password}".encode()
        self.socket.send(pack('>I', len(auth_data)) + auth_data)
        response = self.socket.recv(1024).decode()
        if response == "AUTH_OK":
            self.authenticated = True
            logging.info("Authentication successful")
            print("Authentication successful")
        else:
            logging.warning("Authentication failed")
            print("Authentication failed")
            self.socket.close()
            exit(1)

    def send_query(self, query):
        if not self.authenticated:
            print("Please authenticate first")
            return
        # Лог: Отправка запроса серверу
        logging.info(f"Sending query to server: {query}")
        encoded_query = query.encode()
        self.socket.send(pack('>I', len(encoded_query)) + encoded_query)
        # Лог: Ожидание длины ответа
        logging.info("Waiting for response length from server")
        data_len = unpack('>I', self.socket.recv(4))[0]
        # Лог: Получение данных
        logging.info(f"Receiving {data_len} bytes of data from server")
        data = self.socket.recv(data_len)
        # Лог: Данные получены
        logging.info(f"Received data: {data}")
        return data

    def display_csv(self, data):
        with open("temp_result.csv", "wb") as f:
            f.write(data)
        with open("temp_result.csv", newline='') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                print(", ".join(row))
        logging.info("Displayed query result")

    def display_structure(self, data):
        logging.info(f"Processing structure data: {data}")
        with open("structure.json", "wb") as f:
            f.write(data)
        logging.info("Saved structure to structure.json")

        structure = json.loads(data.decode())
        logging.info(f"Parsed structure: {structure}")
        for table, info in structure.items():
            print(f"Table: {table}")
            print(f"Columns: {', '.join(info['columns'])}")
            print("Data:")
            for row in info['data']:
                print(", ".join(f"{key}: {value}" for key, value in row.items()))
            print()
        logging.info("Displayed table structure with data")

    def run(self):
        self.send_auth("admin", "12345")
        while True:
            logging.info("Prompting user for query input")
            query = input("Enter query (or 'GET_STRUCTURE' for table structure, 'exit' to quit): ")
            logging.info(f"User entered query: {query}")
            if query.lower() == "exit":
                break
            elif query == "GET_STRUCTURE":
                result = self.send_query(query)  # Отправка запроса серверу
                self.display_structure(result)  # Обработка ответа
            else:
                result = self.send_query(query)
                try:
                    self.display_csv(result)
                except Exception as e:
                    print(f"Error: {result.decode()}")
        self.socket.close()
        logging.info("Client disconnected")

if __name__ == "__main__":
    client = Client()
    client.run()