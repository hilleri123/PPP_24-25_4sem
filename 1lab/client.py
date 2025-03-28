import socket
import sys
from protocols import SizeProtocol

HOST = 'localhost'
PORT = 65432

def run_client():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
            protocol = SizeProtocol(s)

            print("[Client] Connected to server.")
            while True:
                cmd = input("> ")
                if not cmd:
                    continue
                protocol.send(cmd)
                resp = protocol.recv()
                print("[Server response]:")
                print(resp)
                if cmd.strip().upper() == "QUIT":
                    break
    except ConnectionRefusedError:
        print("[Client] Cannot connect")
    except KeyboardInterrupt:
        print("\n[Client] Stopped by user")
