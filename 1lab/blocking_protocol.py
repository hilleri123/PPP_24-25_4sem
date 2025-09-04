from abc import ABC, abstractmethod


class RecvSendMsgsProtocol(ABC):
    MSG_SIZE = 16

    @abstractmethod
    def recv(self, connected_socket):
        return ''

    @abstractmethod
    def send(self, connected_socket, text):
        pass


class BlockingProtocol(RecvSendMsgsProtocol):
    def recv(self, connected_socket):
        res_data = b''
        data = connected_socket.recv(BlockingProtocol.MSG_SIZE)
        connected_socket.setblocking(False)
        while data:
            res_data += data
            try:
                data = connected_socket.recv(BlockingProtocol.MSG_SIZE)
            except:
                break
        connected_socket.setblocking(True)
        connected_socket.send(b'ok')
        return res_data.decode()

    def send(self, connected_socket, text):
        connected_socket.sendall(text.encode())
        response = connected_socket.recv(BlockingProtocol.MSG_SIZE).decode()
        if response != 'ok':
            pass
