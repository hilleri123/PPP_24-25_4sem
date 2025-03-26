import socket
import select
import os
import csv
import json
import tempfile
import logging
from struct import pack, unpack

# Настройка логирования
logging.basicConfig(filename='server.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

class Server:
    def __init__(self, host='127.0.0.1', port=12345):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.sockets_list = [self.server_socket]
        self.clients = {}
        self.tables_dir = "tables"
        self.cache = {}
        os.makedirs(self.tables_dir, exist_ok=True)
        self.authenticated_clients = set()

    def parse_query(self, query):
        parts = query.lower().split()
        if parts[0] != "select":
            raise ValueError("поддерживаются только запросы SELECT")
        table = parts[3]
        where_idx = parts.index("where") if "where" in parts else -1
        if where_idx != -1:
            condition = " ".join(parts[where_idx+1:])
            column, operator, value = self.parse_condition(condition)
            return table, column, operator, value
        return table, None, None, None

    def parse_condition(self, condition):
        for op in ["=", "<", ">", "<=", ">=", "!="]:
            if op in condition:
                column, value = condition.split(op)
                return column.strip(), op, value.strip()
        raise ValueError("Недопустимое условие WHERE")
    def execute_query(self, table, column=None, operator=None, value=None):
        filepath = os.path.join(self.tables_dir, f"{table}.csv")
        if filepath in self.cache:
            rows = self.cache[filepath]
        else:
            with open(filepath, newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                rows = [row for row in reader]
                self.cache[filepath] = rows
        if column and operator and value:
            filtered = []
            for row in rows:
                if operator == "=" and row[column] == value:
                    filtered.append(row)
                elif operator == "!=" and row[column] != value:
                    filtered.append(row)
                elif operator == "<" and float(row[column]) < float(value):
                    filtered.append(row)
                elif operator == ">" and float(row[column]) > float(value):
                    filtered.append(row)
                elif operator == "<=" and float(row[column]) <= float(value):
                    filtered.append(row)
                elif operator == ">=" and float(row[column]) >= float(value):
                    filtered.append(row)
            rows = filtered
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as temp:
            writer = csv.DictWriter(temp, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
            temp_path = temp.name
        with open(temp_path, 'rb') as f:
            data = f.read()
        os.remove(temp_path)
        return data

    def get_structure_as_file(self):
        logging.info("Building table structure with data for file")
        structure = {}
        for filename in os.listdir(self.tables_dir):
            if filename.endswith(".csv"):
                table_name = filename[:-4]
                with open(os.path.join(self.tables_dir, filename), newline='') as csvfile:
                    reader = csv.DictReader(csvfile)
                    # Сохраняем все строки таблицы как список словарей
                    rows = [row for row in reader]
                    structure[table_name] = {
                        "columns": list(reader.fieldnames),  # Имена колонок
                        "data": rows  # Данные
                    }

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp:
            json.dump(structure, temp)
            temp_path = temp.name
        logging.info(f"Structure with data saved to temporary file: {temp_path}")

        with open(temp_path, 'rb') as f:
            data = f.read()
        os.remove(temp_path)
        logging.info(f"Read JSON file content: {data}")
        return data

    def authenticate(self, client_socket, data):
        username, password = data.decode().split(":")
        if username == "admin" and password == "12345":
            self.authenticated_clients.add(client_socket)
            client_socket.send(b"AUTH_OK")
            logging.info(f"Client {client_socket.getpeername()} authenticated")
        else:
            client_socket.send(b"AUTH_FAIL")
            logging.warning(f"Authentication failed for {client_socket.getpeername()}")

    def run(self):
        logging.info("Server started")
        while True:
            readable, _, _ = select.select(self.sockets_list, [], [])
            for sock in readable:
                if sock == self.server_socket:
                    client_socket, addr = self.server_socket.accept()
                    self.sockets_list.append(client_socket)
                    self.clients[client_socket] = addr
                    logging.info(f"New connection from {addr}")
                else:
                    try:
                        # Лог: Получение длины запроса
                        logging.info(f"Receiving query length from {self.clients[sock]}")
                        data_len = unpack('>I', sock.recv(4))[0]
                        # Лог: Получение запроса
                        logging.info(f"Receiving {data_len} bytes from {self.clients[sock]}")
                        data = sock.recv(data_len)
                        if not data:
                            self.remove_client(sock)
                            continue

                        if sock not in self.authenticated_clients:
                            self.authenticate(sock, data)
                            continue

                        query = data.decode()
                        # Лог: Обработка полученного запроса
                        logging.info(f"Processing query: {query}")
                        if query == "GET_STRUCTURE":
                            response = self.get_structure_as_file()  # Используем новый метод
                            logging.info(f"Sending response to {self.clients[sock]}: {response}")
                            sock.send(pack('>I', len(response)) + response)
                        else:
                            table, column, operator, value = self.parse_query(query)
                            response = self.execute_query(table, column, operator, value)
                            sock.send(pack('>I', len(response)) + response)
                            logging.info(f"Query processed: {query}")
                    except Exception as e:
                        sock.send(pack('>I', len(str(e).encode())) + str(e).encode())
                        logging.error(f"Error: {e}")

    def remove_client(self, sock):
        self.sockets_list.remove(sock)
        del self.clients[sock]
        if sock in self.authenticated_clients:
            self.authenticated_clients.remove(sock)
        sock.close()
        logging.info(f"Client {self.clients[sock]} disconnected")

if __name__ == "__main__":
    server = Server()
    server.run()