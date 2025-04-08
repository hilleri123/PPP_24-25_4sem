import logging
import sys
import socket
import traceback
import scheme
import query_analyzer

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


class Server:
    def __init__(self, host=HOST, port=PORT):
        self.host = host
        self.port = port
        self.logger = logging.getLogger('Server')

    def handle_client(self, client_socket):
        received_text = client_socket.recv(1000).decode("utf-8")
        while received_text.lower() != 'exit':
            if received_text.lower() == 'json':
                self.logger.info(f'Query: {received_text}')
                client_socket.send(bytes(scheme.get_json_scheme(), 'utf-8'))
                self.logger.info(f'Answer: {query_analyzer.process_query(received_text)}')
            else:
                self.logger.info(f'Query: {received_text}')
                client_socket.send(bytes(query_analyzer.process_query(received_text), 'utf-8'))
                self.logger.info(f'Answer: {query_analyzer.process_query(received_text)}')
            received_text = client_socket.recv(1000).decode("utf-8")

    def run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((self.host, self.port))
            self.logger.info(f'started on {(self.host, self.port)}')
            s.listen(1)
            while True:
                try:
                    client, addr = s.accept()
                    with client:
                        self.logger.info(f'connect {addr}')
                        self.handle_client(client)

                    self.logger.info(f'closed on {(self.host, self.port)}')
                except Exception as e:
                    self.logger.error(e)
                    self.logger.error(traceback.format_exc())


if __name__ == '__main__':
    my_server = Server()
    my_server.run()
