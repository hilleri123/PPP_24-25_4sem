import os
import json
import socket
import logging

logging.basicConfig(filename='server.log', level=logging.INFO, format='%(asctime)s - %(message)s')
# в файле srver.log ведется ронологическая запись информации о работе системы, уровень info говорит об общих событиях сервера

def get_processes_info():
    processes = os.popen('tasklist').read() # список процессов в Windows
    return processes

def save_to_json(data, filename):
    with open(filename, 'w') as f:
        json.dump(data, f)

processes_list = []
def convert_to_dict(processes):
    lines = processes.strip().split('\n')

    for line in lines[3:]: #скипаем первые три строки - заголовки и разделитель "==="
        columns = line.split()
        if len(columns) >= 5: # поколоночно разбиваем данные
            process_name = columns[0]
            pid = columns[1]
            session_name = columns[2]
            session_number = columns[3]
            memory_usage = columns[4]
            processes_list.append({
                'Process Name': process_name,
                'PID': pid,
                'Session Name': session_name,
                'Session Number': session_number,
                'Memory Usage': memory_usage})

    return processes_list
def handle_client(conn):
    while True:
        command = conn.recv(1024).decode('utf-8')
        if not command:
            break

        logging.info(f"Received command: {command}")

        if command == "update":
            filename = "processes1.json"
            convert_to_dict(get_processes_info())
            save_to_json(processes_list, filename)
            with open(filename, 'rb') as f:
                conn.sendall(f.read())
            logging.info("Sent updated process info to client")

        elif command.startswith("signal"):
            _, pid, sig = command.split() # Process ID
            try:
                os.kill(int(pid), int(sig))
                conn.sendall(f"Signal {sig} sent to process {pid}".encode('utf-8'))
                logging.info(f"Signal {sig} sent to process {pid}")
            except ProcessLookupError:
                conn.sendall(f"Process {pid} not found".encode('utf-8'))
                logging.error(f"Process {pid} not found")
            except PermissionError:
                conn.sendall(f"Permission denied to send signal to process {pid}".encode('utf-8'))
                logging.error(f"Permission denied to send signal to process {pid}")

    conn.close()

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('localhost', 12345))
    server_socket.listen(5)
    logging.info("Server started and listening on port 12345")
    print('Server started and listening on port 12345!!')
    while True:
        conn, addr = server_socket.accept()
        logging.info(f"Connected by {addr}")
        handle_client(conn)

if __name__ == "__main__":
    start_server()