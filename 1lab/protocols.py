import struct

class SizeProtocol:
    def __init__(self, conn):
        self.conn = conn

    def send(self, text: str):
        data = text.encode('utf-8')
        size = len(data)
        self.conn.sendall(struct.pack('I', size))
        self.conn.sendall(data)

    def recv(self) -> str:
        size_data = self.conn.recv(struct.calcsize('I'))
        if not size_data:
            return ""
        size, = struct.unpack('I', size_data)
        data = b""
        while len(data) < size:
            chunk = self.conn.recv(size - len(data))
            if not chunk:
                break
            data += chunk
        return data.decode('utf-8')
