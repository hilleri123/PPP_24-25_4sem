import logging
import sys
import socket
from blocking_protocol import BlockingProtocol


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
    def __init__(self, protocol_handler, host=HOST, port=PORT):
        self.host = host
        self.port = port
        self.protocol_handler = protocol_handler
        self.logger = logging.getLogger('Client')

    def run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.host, self.port))
            command = input("Type query:\n")
            while command.lower() != 'exit':
                self.protocol_handler.send(s, command)
                received_text = self.protocol_handler.recv(s)
                print(received_text)
                command = input("Type query:\n")


if __name__ == '__main__':
    my_client = Client(BlockingProtocol())
    my_client.run()

