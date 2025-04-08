import logging
import sys
import socket

file_handler = logging.FileHandler(filename='tmp.log')
stdout_handler = logging.StreamHandler(stream=sys.stdout)
handlers = [stdout_handler]
# handlers = [file_handler, stdout_handler]

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] %(name)s - %(message)s',
    handlers=handlers
)
HOST = 'localhost'
PORT = 12345


class Client:
    def __init__(self, host=HOST, port=PORT):
        self.host = host
        self.port = port
        self.logger = logging.getLogger('Client')

    def run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.host, self.port))
            command = input("Type query:\n")
            while command.lower() != 'exit':
                s.send(bytes(command, 'utf-8'))
                received_text = s.recv(1000).decode("utf-8")
                print(received_text)
                command = input("Type query:\n")


if __name__ == '__main__':
    my_client = Client()
    my_client.run()
