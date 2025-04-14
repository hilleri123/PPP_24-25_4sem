import os
import json
import socket
import threading
from time import sleep

class ProgramServer:
    def __init__(self, host='127.0.0.1', port=5000):
        self.host = host
        self.port = port
        self.programs = {}
        self.load_data()

    def load_data(self):
       
        if os.path.exists('program_data.json'):
            with open('program_data.json', 'r') as file:
                self.programs = json.load(file)
        else:
            self.programs = {}

    def save_data(self):
   
        with open('program_data.json', 'w') as file:
            json.dump(self.programs, file)

    def create_program_directory(self, program_name):
 
        if program_name not in self.programs:
            os.makedirs(program_name, exist_ok=True)
            self.programs[program_name] = {"output_files": []}

    def run_program(self, program_name):
 
        while True:
            output_file = f"{program_name}/output_{int(time.time())}.txt"
            with open(output_file, 'w') as file:
                file.write(f"Output of {program_name} at {time.ctime()}")
            self.programs[program_name]["output_files"].append(output_file)
            sleep(10)

    def start_program_threads(self):

        for program_name in self.programs.keys():
            threading.Thread(target=self.run_program, args=(program_name,), daemon=True).start()

    def handle_client(self, conn):

        while True:
            try:
                data = conn.recv(1024).decode()
                if not data:
                    break

                request = json.loads(data)
                command = request.get("command")
                program_name = request.get("program_name")

                if command == "add_program":
                    self.create_program_directory(program_name)
                    threading.Thread(target=self.run_program, args=(program_name,), daemon=True).start()
                    conn.sendall(b"Program added and started.\n")
                elif command == "get_output":
                    output_files = self.programs.get(program_name, {}).get("output_files", [])
                    response = {"program": program_name, "outputs": output_files}
                    conn.sendall(json.dumps(response).encode())
                else:
                    conn.sendall(b"Unknown command.\n")
            except Exception as e:
                print(f"Error: {e}")
                break

    def start_server(self):
     
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind((self.host, self.port))
            server_socket.listen(5)
            print(f"Server started on {self.host}:{self.port}")

            while True:
                conn, addr = server_socket.accept()
                print(f"Connection from {addr}")
                threading.Thread(target=self.handle_client, args=(conn,), daemon=True).start()

if __name__ == "__main__":
    server = ProgramServer()
    server.start_program_threads()
    try:
        server.start_server()
    except KeyboardInterrupt:
        server.save_data()
